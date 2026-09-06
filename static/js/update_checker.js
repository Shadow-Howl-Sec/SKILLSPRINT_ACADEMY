// Update Checker - handles periodic update checks and UI notifications
(function() {
    'use strict';

    let updateCheckTimer = null;
    let dismissedVersion = null;
    const CHECK_INTERVAL = 4 * 60 * 60 * 1000; // 4 hours
    const API_URL = '/api/update/check';

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setCookie(name, value, days = 30) {
        const expires = new Date(Date.now() + days * 86400000).toUTCString();
        document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
    }

    function showUpdateBanner(updateInfo) {
        const banner = document.getElementById('update-banner');
        const versionText = document.getElementById('update-version-text');
        const releaseNotes = document.getElementById('update-release-notes');
        
        if (!banner) return;

        const current = updateInfo.current_version || 'unknown';
        const latest = updateInfo.latest_version || 'unknown';
        versionText.textContent = `v${current} → v${latest}`;

        if (updateInfo.release_notes) {
            releaseNotes.textContent = updateInfo.release_notes;
            releaseNotes.style.display = 'block';
        }

        // Store download URL for apply button
        banner.dataset.downloadUrl = updateInfo.download_url || '';
        banner.dataset.latestVersion = latest;
        
        banner.style.display = 'block';
    }

    function hideUpdateBanner() {
        const banner = document.getElementById('update-banner');
        if (banner) banner.style.display = 'none';
    }

    function dismissUpdateBanner() {
        const banner = document.getElementById('update-banner');
        if (banner && banner.dataset.latestVersion) {
            setCookie('update_dismissed', banner.dataset.latestVersion, 7);
        }
        hideUpdateBanner();
    }

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    async function checkForUpdates(force = false) {
        // Don't check if we're offline or update already dismissed for this version
        if (typeof OFFLINE_MODE !== 'undefined' && OFFLINE_MODE) {
            return;
        }

        const dismissed = getCookie('update_dismissed');
        if (dismissed && !force) {
            // Check if there's a cached update that matches dismissed version
            try {
                const response = await fetch('/api/update/status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ force }),
                });
                const cached = await response.json();
                if (cached.latest_version === dismissed) {
                    return; // User dismissed this version
                }
            } catch (e) {
                // Ignore errors
            }
        }

        try {
            const url = force ? `${API_URL}?force=1` : API_URL;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ force }),
            });

            if (!response.ok) return;

            const data = await response.json();
            
            if (data.update_available === true) {
                showUpdateBanner(data);
            } else if (data.update_available === false) {
                hideUpdateBanner();
                // Clear dismissed cookie if no update available
                document.cookie = 'update_dismissed=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            }
        } catch (e) {
            // Silently fail - offline or network error
            console.debug('Update check failed:', e);
        }
    }

    async function applyUpdate() {
        const banner = document.getElementById('update-banner');
        if (!banner || !banner.dataset.downloadUrl) return;

        const downloadUrl = banner.dataset.downloadUrl;

        // Disable button
        const btn = banner.querySelector('.btn-primary');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Downloading...';
        }

        try {
            const response = await fetch('/settings/apply-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ download_url: downloadUrl }),
            });

            if (response.ok) {
                btn.innerHTML = '<i class="bi bi-check me-1"></i>Applying...';
                // App will restart automatically
            }
        } catch (e) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-download me-1"></i>Install Now';
            console.error('Update apply failed:', e);
        }
    }

    // Expose for inline onclick
    window.dismissUpdateBanner = dismissUpdateBanner;
    window.applyUpdate = applyUpdate;

    // Start periodic checks
    function startUpdateChecks() {
        // Initial check after 5 seconds
        setTimeout(() => checkForUpdates(false), 5000);

        // Periodic checks
        updateCheckTimer = setInterval(() => checkForUpdates(false), CHECK_INTERVAL);
    }

    // Start when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startUpdateChecks);
    } else {
        startUpdateChecks();
    }
})();
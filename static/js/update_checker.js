// update_checker.js — Handles periodic update checks and banner display
// NOTE: applyUpdate() and dismissUpdateBanner() are defined in main.js.
//       This module only handles polling, state, and banner show/hide.
(function () {
  'use strict';

  const CHECK_INTERVAL = 4 * 60 * 60 * 1000; // 4 hours

  // ------------------------------------------------------------------
  // Cookie helpers
  // ------------------------------------------------------------------
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

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // ------------------------------------------------------------------
  // Banner helpers (only show/hide — not dismiss, that's in main.js)
  // ------------------------------------------------------------------
  function showUpdateBanner(updateInfo) {
    const banner = document.getElementById('update-banner');
    const versionText = document.getElementById('update-version-text');
    const releaseNotes = document.getElementById('update-release-notes');

    if (!banner) return;

    const current = updateInfo.current_version || 'unknown';
    const latest = updateInfo.latest_version || 'unknown';
    if (versionText) versionText.textContent = `v${current} → v${latest}`;

    if (releaseNotes && updateInfo.release_notes) {
      releaseNotes.textContent = updateInfo.release_notes;
      releaseNotes.style.display = 'block';
    }

    // Store download URL for the apply button (consumed by main.js applyUpdate)
    banner.dataset.downloadUrl = updateInfo.download_url || '';
    banner.dataset.latestVersion = latest;

    banner.style.display = 'block';
  }

  function hideUpdateBanner() {
    const banner = document.getElementById('update-banner');
    if (banner) banner.style.display = 'none';
  }

  // ------------------------------------------------------------------
  // Update check logic
  // ------------------------------------------------------------------
  async function checkForUpdates(force = false) {
    // Never check in offline mode
    if (window.OFFLINE_MODE === true) return;

    const dismissed = getCookie('update_dismissed');

    if (dismissed && !force) {
      // Verify the cached update against the dismissed version
      try {
        const response = await fetch('/api/update/status', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({ force }),
        });
        if (response.ok) {
          const cached = await response.json();
          if (cached.latest_version === dismissed) return; // Still dismissed
        }
      } catch (e) {
        // Network/parse error — skip silently
      }
    }

    try {
      const url = force ? '/api/update/check?force=1' : '/api/update/check';
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ force }),
      });

      if (!response.ok) return;

      const data = await response.json();

      if (data.update_available === true) {
        showUpdateBanner(data);
      } else if (data.update_available === false) {
        hideUpdateBanner();
        // Clear any stale dismissed cookie
        document.cookie = 'update_dismissed=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      }
    } catch (e) {
      console.debug('[UpdateChecker] Check failed (offline or network error):', e);
    }
  }

  // ------------------------------------------------------------------
  // Periodic polling — starts 5s after load
  // ------------------------------------------------------------------
  function startUpdateChecks() {
    setTimeout(() => checkForUpdates(false), 5000);
    setInterval(() => checkForUpdates(false), CHECK_INTERVAL);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startUpdateChecks);
  } else {
    startUpdateChecks();
  }

  // Expose force-check for debugging / settings page use
  window._forceUpdateCheck = () => checkForUpdates(true);
})();
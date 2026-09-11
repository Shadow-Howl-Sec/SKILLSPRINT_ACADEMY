// main.js — Shared UI logic (CSP-compliant, no inline handlers)
// Single source of truth for: showToast, applyUpdate, dismissUpdateBanner

// ------------------------------------------------------------------
// Toast notification system
// ------------------------------------------------------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-bg-${type} border-0`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;
  container.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
  bsToast.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
  container.style.zIndex = '1080';
  document.body.appendChild(container);
  return container;
}

// ------------------------------------------------------------------
// Update banner — Apply & Dismiss
// ------------------------------------------------------------------

/**
 * Apply the pending update. Content is offline-first, but signed application
 * updates are allowed to use the network.
 */
function applyUpdate() {
  const banner = document.getElementById('update-banner');
  const downloadUrl = banner?.dataset?.downloadUrl;

  if (!downloadUrl) {
    console.error('[Update] No download URL available');
    showToast('No update download URL available. Please try again.', 'danger');
    return;
  }

  const metaCsrf = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = metaCsrf ? metaCsrf.getAttribute('content') : '';

  // Disable the install button while in progress
  const btn = banner.querySelector('[data-action="apply-update"]');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Downloading…';
  }

  fetch('/settings/apply-update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      download_url: downloadUrl,
      signature_url: banner?.dataset?.signatureUrl || '',
    }),
  })
    .then(r => {
      if (r.ok) {
        dismissUpdateBanner();
        document.body.innerHTML =
          '<div class="container text-center py-5">' +
          '<div class="spinner-border text-primary" role="status">' +
          '<span class="visually-hidden">Applying update…</span>' +
          '</div>' +
          '<p class="mt-3">Applying update, please wait…</p>' +
          '</div>';
      } else {
        return r.json().then(err => {
          throw new Error(err.error || `Update failed: ${r.status}`);
        });
      }
    })
    .catch(e => {
      console.error('[Update] Error:', e);
      showToast(e.message || 'Update failed. Check console for details.', 'danger');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-download me-1"></i>Install Now';
      }
    });
}

/**
 * Dismiss the update banner and set a 7-day cookie for the dismissed version.
 */
function dismissUpdateBanner() {
  const banner = document.getElementById('update-banner');
  if (!banner) return;

  // Record the dismissed version to suppress future checks for same version
  if (banner.dataset.latestVersion) {
    const expires = new Date(Date.now() + 7 * 86400000).toUTCString();
    document.cookie = `update_dismissed=${banner.dataset.latestVersion}; expires=${expires}; path=/; SameSite=Lax`;
  }

  banner.style.display = 'none';
}

// ------------------------------------------------------------------
// Event listener binding (CSP-compliant — no inline onclick handlers)
// ------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const applyBtn = document.querySelector('[data-action="apply-update"]');
  const dismissBtn = document.querySelector('[data-action="dismiss-update"]');
  const checkUpdateBtns = document.querySelectorAll('[data-action="check-update"]');

  if (applyBtn) applyBtn.addEventListener('click', applyUpdate);
  if (dismissBtn) dismissBtn.addEventListener('click', dismissUpdateBanner);
  checkUpdateBtns.forEach(btn => btn.addEventListener('click', () => {
    if (typeof window._forceUpdateCheck === 'function') {
      window._forceUpdateCheck();
    }
  }));
});

// ------------------------------------------------------------------
// Global exports (used by templates that call window.* directly)
// ------------------------------------------------------------------
window.applyUpdate = applyUpdate;
window.dismissUpdateBanner = dismissUpdateBanner;
window.showToast = showToast;
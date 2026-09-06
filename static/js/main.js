// main.js — Shared UI logic (CSP-compliant, no inline handlers)

document.addEventListener('DOMContentLoaded', () => {
  // Update banner handlers
  const applyBtn = document.querySelector('[data-action="apply-update"]');
  const dismissBtn = document.querySelector('[data-action="dismiss-update"]');

  if (applyBtn) {
    applyBtn.addEventListener('click', applyUpdate);
  }
  if (dismissBtn) {
    dismissBtn.addEventListener('click', dismissUpdateBanner);
  }
});

function applyUpdate() {
  const banner = document.getElementById('update-banner');
  const downloadUrl = banner?.dataset?.downloadUrl;

  if (!downloadUrl) {
    console.error('No download URL available for update');
    return;
  }

  const metaCsrf = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = metaCsrf ? metaCsrf.getAttribute('content') : '';
  fetch('/settings/apply-update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({ download_url: downloadUrl })
  }).then(r => {
    if (r.ok) {
      dismissUpdateBanner();
      document.body.innerHTML = '<div class="container text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Applying update...</span></div><p class="mt-3">Applying update, please wait...</p></div>';
    } else {
      console.error('Update failed:', r.status);
    }
  }).catch(e => {
    console.error('Update error:', e);
  });
}

function dismissUpdateBanner() {
  const banner = document.getElementById('update-banner');
  if (banner) banner.style.display = 'none';
}

// Expose for inline use in templates that need it
window.applyUpdate = applyUpdate;
window.dismissUpdateBanner = dismissUpdateBanner;
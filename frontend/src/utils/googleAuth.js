/**
 * Google Identity Services (GIS) helper.
 * Requires GOOGLE_CLIENT_ID on the backend (exposed via GET /auth/config).
 */

import { apiGet, apiPost } from './api';
import { setToken } from './auth';

const GIS_SRC = 'https://accounts.google.com/gsi/client';

let gisScriptPromise = null;

function loadGisScript() {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (gisScriptPromise) return gisScriptPromise;
  gisScriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GIS_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', () => reject(new Error('Failed to load Google Sign-In.')));
      return;
    }
    const script = document.createElement('script');
    script.src = GIS_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Sign-In.'));
    document.head.appendChild(script);
  });
  return gisScriptPromise;
}

/**
 * Open the Google One Tap / account chooser and exchange the ID token with our API.
 * @returns {Promise<{ access_token: string, user_id: string, email: string, name?: string }>}
 */
export async function signInWithGoogle() {
  const config = await apiGet('/auth/config');
  if (!config.google_enabled || !config.google_client_id) {
    throw new Error(
      'Google Sign-In is not configured. Set GOOGLE_CLIENT_ID on the backend (and rebuild/restart).',
    );
  }

  await loadGisScript();

  const credential = await new Promise((resolve, reject) => {
    try {
      window.google.accounts.id.initialize({
        client_id: config.google_client_id,
        callback: (response) => {
          if (response?.credential) resolve(response.credential);
          else reject(new Error('Google Sign-In was cancelled or failed.'));
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      // Prompt the account chooser; fall back to a button render if One Tap is blocked.
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          // Invisible temporary button click as GIS fallback.
          const host = document.createElement('div');
          host.style.position = 'fixed';
          host.style.left = '-9999px';
          document.body.appendChild(host);
          window.google.accounts.id.renderButton(host, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
          });
          const btn = host.querySelector('div[role="button"]');
          if (btn) btn.click();
          else reject(new Error('Google Sign-In popup was blocked. Allow popups and try again.'));
          setTimeout(() => host.remove(), 5000);
        }
      });
    } catch (err) {
      reject(err instanceof Error ? err : new Error(String(err)));
    }
  });

  const data = await apiPost('/auth/google', { id_token: credential });
  setToken(data.access_token, data.user_id, data.email, data.name || '');
  return data;
}

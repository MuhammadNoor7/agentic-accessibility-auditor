const TOKEN_KEY = 'axion_token';
const USER_ID_KEY = 'axion_user_id';
const EMAIL_KEY = 'axion_email';
const NAME_KEY = 'axion_name';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getEmail() {
  return localStorage.getItem(EMAIL_KEY) || '';
}

export function getName() {
  return localStorage.getItem(NAME_KEY) || '';
}

export function setToken(token, user_id, email, name = '') {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_ID_KEY, user_id);
  localStorage.setItem(EMAIL_KEY, email || '');
  localStorage.setItem(NAME_KEY, (name || '').trim());
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(EMAIL_KEY);
  localStorage.removeItem(NAME_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export function getAuthHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Display label for avatar tooltip / aria — prefer full name, else email. */
export function getDisplayName() {
  const name = getName().trim();
  if (name) return name;
  const email = getEmail().trim();
  return email || 'Account';
}

/**
 * Initials for the top-right avatar.
 * "Muhammad Noor" → "MN", "jane.doe@x.com" → "JD", "ayesha@x.com" → "AY"
 */
export function getInitials() {
  const name = getName().trim();
  const email = getEmail().trim();
  const source = name || (email.includes('@') ? email.split('@')[0] : email) || '?';
  const parts = source
    .replace(/[._+\-]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  const single = parts[0] || '?';
  const letters = single.replace(/[^a-zA-Z0-9]/g, '');
  if (letters.length >= 2) return letters.slice(0, 2).toUpperCase();
  return (letters[0] || '?').toUpperCase();
}

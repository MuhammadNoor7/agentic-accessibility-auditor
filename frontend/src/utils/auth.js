const TOKEN_KEY = 'axion_token';
const USER_ID_KEY = 'axion_user_id';
const EMAIL_KEY = 'axion_email';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token, user_id, email) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_ID_KEY, user_id);
  localStorage.setItem(EMAIL_KEY, email);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export function getAuthHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

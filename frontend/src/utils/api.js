import { getAuthHeaders } from './auth';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002';

async function handleResponse(response) {
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) || `Request failed with status ${response.status}`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return data;
}

export async function apiPost(path, body, requiresAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(requiresAuth ? getAuthHeaders() : {}),
    },
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiGet(path, requiresAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: {
      ...(requiresAuth ? getAuthHeaders() : {}),
    },
  });
  return handleResponse(response);
}

export async function apiDelete(path, requiresAuth = false) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: {
      ...(requiresAuth ? getAuthHeaders() : {}),
    },
  });
  return handleResponse(response);
}

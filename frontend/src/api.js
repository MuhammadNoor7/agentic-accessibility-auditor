// Central place for all backend API calls.
// Relative by default so requests go through the Vite dev-server proxy
// (see vite.config.js) instead of a hardcoded host — set VITE_API_BASE
// to override with an absolute URL if you're not using the proxy.
import { getAuthHeaders } from './utils/auth';

const API_BASE = import.meta.env.VITE_API_BASE || '';

// Step 1: upload screenshot + XML pair, kicks off parse -> rules -> agent explain.
// Returns { audit_id, status }
export async function createAudit(screenshotFile, xmlFile) {
  const formData = new FormData();
  formData.append('screenshot', screenshotFile);
  if (xmlFile) {
    formData.append('xml', xmlFile);
  }

  const res = await fetch(`${API_BASE}/api/v1/audit`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Audit upload failed (${res.status})`);
  }
  return res.json();
}

// Step 2: check progress. Returns { audit_id, status, message }
// status is one of: pending | parsing | checking | explaining | complete | error
export async function getAuditStatus(auditId) {
  const res = await fetch(`${API_BASE}/api/v1/audit/${auditId}/status`);
  if (!res.ok) throw new Error(`Status check failed (${res.status})`);
  return res.json();
}

// Step 3: once complete, fetch the full report (score, summary, violations[])
export async function getAuditReport(auditId) {
  const res = await fetch(`${API_BASE}/api/v1/audit/${auditId}/report`);
  if (!res.ok) throw new Error(`Report fetch failed (${res.status})`);
  return res.json();
}

// Raw violations doc for a just-completed audit — used to build the summary
// (screen_id, total_violations, per-severity counts) persisted via POST /records.
export async function getAuditViolations(auditId) {
  const res = await fetch(`${API_BASE}/api/v1/audit/${auditId}/violations`);
  if (!res.ok) throw new Error(`Violations fetch failed (${res.status})`);
  return res.json();
}

// Persist a completed audit into the logged-in user's Audit History.
// Called once per audit, right after its report loads (see Dashboard.jsx).
export async function createRecord(payload) {
  const res = await fetch(`${API_BASE}/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Record creation failed (${res.status})`);
  }
  return res.json();
}

// Re-open the full report for a past record from Audit History (Records page).
// Unlike getAuditReport, this reads the persisted report off disk by record_id,
// so it works even after the backend has restarted since the audit ran.
export async function getRecordReport(recordId) {
  const res = await fetch(`${API_BASE}/records/${recordId}/report`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Report fetch failed (${res.status})`);
  }
  return res.json();
}

// Step 4: download HTML or PDF export from the Week 5 report generator.
export async function downloadAuditReport(auditId, format) {
  const res = await fetch(`${API_BASE}/api/v1/audit/${auditId}/report/download?format=${format}`);
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Download failed (${res.status})`);
  }

  const blob = await res.blob();
  const disposition = res.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] || `axion-report.${format}`;

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

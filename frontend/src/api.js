// Central place for all backend API calls.
// Base URL of your local FastAPI server (started with `uvicorn backend.main:app`).
const API_BASE = 'http://127.0.0.1:8000';

// Step 1: upload the XML file, kicks off parse -> rules -> agent explain.
// Returns { audit_id, status }
export async function createAudit(xmlFile) {
  const formData = new FormData();
  formData.append('xml', xmlFile);

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
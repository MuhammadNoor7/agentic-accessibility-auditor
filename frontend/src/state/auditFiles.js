// Simple in-memory store for the currently uploaded screenshot/XML and audit ID.
// Survives SPA navigation (module stays loaded) regardless of which
// link/button the user clicks — unlike react-router's navigate() state,
// which only persists if every single link explicitly passes it along.
let currentFiles = { screenshot: null, xml: null };
let currentAuditId = null;
// audit_ids already POSTed to /records this session — survives Dashboard
// unmounting/remounting on SPA navigation (unlike a component-local ref),
// so revisiting Dashboard for the same audit never creates a duplicate record.
const recordedAuditIds = new Set();

export function setAuditFiles(screenshot, xml) {
  currentFiles = { screenshot, xml };
}

export function getAuditFiles() {
  return currentFiles;
}

export function setAuditId(id) {
  currentAuditId = id;
}

export function getAuditId() {
  return currentAuditId;
}

export function hasRecordedAudit(auditId) {
  return recordedAuditIds.has(auditId);
}

export function markAuditRecorded(auditId) {
  recordedAuditIds.add(auditId);
}
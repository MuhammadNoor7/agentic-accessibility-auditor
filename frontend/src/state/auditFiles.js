// Simple in-memory store for the currently uploaded screenshot/XML.
// Survives SPA navigation (module stays loaded) regardless of which
// link/button the user clicks — unlike react-router's navigate() state,
// which only persists if every single link explicitly passes it along.
let currentFiles = { screenshot: null, xml: null };

export function setAuditFiles(screenshot, xml) {
  currentFiles = { screenshot, xml };
}

export function getAuditFiles() {
  return currentFiles;
}
import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { setAuditFiles, setAuditId } from '../state/auditFiles';
import { createAudit, getAuditViolations } from '../api';
import { apiPost } from '../utils/api';
import { isLoggedIn } from '../utils/auth';

// ── Responsive rules (inline styles can't do @media, so inject CSS) ───────────
const injectResponsiveStyles = (() => {
  let injected = false;
  return () => {
    if (injected) return;
    injected = true;
    const style = document.createElement('style');
    style.textContent = `
    @media (max-width: 767px) {
      .axion-topbar { padding: 14px 16px 14px 64px !important; flex-wrap: wrap; gap: 10px; }
      .axion-search { display: none !important; }
      .axion-content { padding: 16px !important; }
      .axion-upload-zone { padding: 28px 18px 22px !important; }
      .axion-cta-bar { flex-direction: column !important; align-items: stretch !important; }
      .axion-cta-button { width: 100%; justify-content: center; }
      .axion-heading { font-size: 22px !important; }
      .axion-audit-steps { grid-template-columns: 1fr !important; }
    }
  `;
    document.head.appendChild(style);
  };
})();

// ── Keyframe injection (once) ─────────────────────────────────────────────────
const injectKeyframes = (() => {
  let injected = false;
  return () => {
    if (injected) return;
    injected = true;
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulseIn {
        0%   { transform: scale(0.85); opacity: 0; }
        60%  { transform: scale(1.04); }
        100% { transform: scale(1);    opacity: 1; }
      }
      @keyframes shake {
        0%,100% { transform: translateX(0); }
        20%     { transform: translateX(-8px); }
        40%     { transform: translateX(8px); }
        60%     { transform: translateX(-5px); }
        80%     { transform: translateX(5px); }
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      @keyframes stepSlideIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes checkPop {
        0%   { transform: scale(0); }
        60%  { transform: scale(1.2); }
        100% { transform: scale(1); }
      }
    `;
    document.head.appendChild(style);
  };
})();

// ── Inline SVG Icons ──────────────────────────────────────────────────────────
const Icon = {
  folder: (color = '#00c896', size = 28) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
    </svg>
  ),
  photo: (color = '#fff', size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <circle cx="8.5" cy="9.5" r="1.5" />
      <path d="M21 16l-5-5-4 4-2-2-5 5" />
    </svg>
  ),
  xml: (color = '#fff', size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 3v4a1 1 0 0 0 1 1h4" />
      <path d="M5 12V5a2 2 0 0 1 2-2h7l5 5v4" />
      <path d="M5 18h14" />
      <path d="M7 21l-2-3 2-3" />
      <path d="M17 21l2-3-2-3" />
      <path d="M11 15l2 6" />
    </svg>
  ),
  check: (color = '#00c896', size = 26) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  ),
  alert: (color = '#ef4444', size = 26) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  xIcon: (color = '#888', size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  refresh: (color = '#fff', size = 15) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  ),
  arrow: (color = '#64748b', size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  ),
  eye: (color = '#00c896', size = 14) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  fileSearch: (color = '#1D9E75', size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2.5H7a2 2 0 00-2 2v15a2 2 0 002 2h10a2 2 0 002-2V8.5L14 2.5z" />
      <path d="M13.5 2.5V8H19" />
      <circle cx="11" cy="14" r="2.5" />
      <path d="M15 17.5l-1.5-1.5" />
    </svg>
  ),
};

// ── Helpers ───────────────────────────────────────────────────────────────────
// Filename without its extension, e.g. "chat_1054.png" -> "chat_1054"
function getStem(filename) {
  return filename.replace(/\.[^/.]+$/, '');
}

// Last run of digits in a filename, e.g. "chat_1054.png" -> "1054"
function extractNumber(filename) {
  const matches = filename.match(/\d+/g);
  return matches ? matches[matches.length - 1] : null;
}

// Strong pair match: exact stem match first (safe for any naming), falling
// back to shared trailing numeric ID ONLY when both files share the same
// prefix before that number (e.g. chat_1054.png + chat_1054.xml).
// This fixes the false-positive bug: photo1.jpg no longer matches data1.xml,
// since "photo" !== "data" even though both contain "1".
function filesMatch(screenshotName, xmlName) {
  const stem1 = getStem(screenshotName);
  const stem2 = getStem(xmlName);
  if (stem1 === stem2) return true;

  const n1 = extractNumber(screenshotName);
  const n2 = extractNumber(xmlName);
  if (n1 === null || n2 === null || n1 !== n2) return false;

  const prefix1 = stem1.replace(/\d+$/, '');
  const prefix2 = stem2.replace(/\d+$/, '');
  return prefix1 === prefix2;
}

function Spinner({ size = 14, color = '#94a3b8' }) {
  return (
    <div style={{
      width: size, height: size,
      border: `2px solid ${color}`,
      borderTopColor: 'transparent',
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite',
      flexShrink: 0,
    }} />
  );
}

// ── File Preview Popup ────────────────────────────────────────────────────────
function FilePreviewPopup({ screenshot, xml, onClose }) {
  const [tab, setTab] = useState('screenshot');
  const [imgUrl, setImgUrl] = useState(null);
  const [xmlText, setXmlText] = useState('');
  const [loadingXml, setLoadingXml] = useState(false);

  useEffect(() => {
    if (!screenshot) return;
    const url = URL.createObjectURL(screenshot);
    setImgUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [screenshot]);

  useEffect(() => {
    if (!xml) return;
    setLoadingXml(true);
    const reader = new FileReader();
    reader.onload = e => {
      setXmlText(e.target.result);
      setLoadingXml(false);
    };
    reader.readAsText(xml);
  }, [xml]);

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(15,27,45,0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, animation: 'fadeIn 0.2s ease',
        padding: '24px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff',
          borderRadius: 18,
          width: '100%',
          maxWidth: 780,
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 24px 64px rgba(0,0,0,0.28)',
          animation: 'pulseIn 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards',
        }}
      >
        <div style={{
          background: '#0f1422',
          padding: '18px 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {Icon.fileSearch('#1D9E75', 18)}
            <div>
              <p style={{ color: '#fff', fontSize: 16, fontWeight: 700, margin: 0 }}>
                File Preview
              </p>
              <p style={{ color: '#a8bbd4', fontSize: 12, margin: '3px 0 0' }}>
                {screenshot?.name} + {xml?.name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close preview"
            style={{
              background: '#7f1d1d', border: 'none', borderRadius: 8,
              width: 32, height: 32,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', color: '#fff', fontSize: 17, lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e2e8f0',
          padding: '0 24px',
          flexShrink: 0,
          background: '#f8fafc',
        }}>
          {[
            { key: 'screenshot', label: 'Screenshot', icon: '🖼' },
            { key: 'xml',        label: 'XML source',  icon: '📄' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: tab === t.key ? '2px solid #1D9E75' : '2px solid transparent',
                padding: '14px 20px 12px',
                fontSize: 14,
                fontWeight: tab === t.key ? 700 : 500,
                color: tab === t.key ? '#1D9E75' : '#64748b',
                cursor: 'pointer',
                fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', gap: 7,
                transition: 'color 0.15s',
              }}
            >
              <span aria-hidden="true">{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>

          {tab === 'screenshot' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: '100%', background: '#f8fafc',
                border: '1px solid #e2e8f0', borderRadius: 10,
                padding: '10px 16px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                flexWrap: 'wrap', gap: 6,
              }}>
                <span style={{ fontSize: 13, color: '#0f1422', fontWeight: 600 }}>{screenshot?.name}</span>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {screenshot ? (screenshot.size / 1024).toFixed(1) + ' KB' : ''}
                  {' · '}{screenshot?.type}
                </span>
              </div>
              {imgUrl && (
                <img
                  src={imgUrl}
                  alt={`Preview of ${screenshot?.name}`}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '52vh',
                    borderRadius: 10,
                    border: '1px solid #e2e8f0',
                    objectFit: 'contain',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  }}
                />
              )}
            </div>
          )}

          {tab === 'xml' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0', borderRadius: 10,
                padding: '10px 16px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                flexWrap: 'wrap', gap: 6,
              }}>
                <span style={{ fontSize: 13, color: '#0f1422', fontWeight: 600 }}>{xml?.name}</span>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {xml ? (xml.size / 1024).toFixed(1) + ' KB' : ''}
                  {' · XML'}
                </span>
              </div>
              {loadingXml ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
                  <Spinner size={24} color="#1D9E75" />
                </div>
              ) : (
                <pre style={{
                  background: '#0f1422',
                  color: '#a8bbd4',
                  borderRadius: 10,
                  padding: '20px',
                  fontSize: 12.5,
                  lineHeight: 1.7,
                  overflowX: 'auto',
                  margin: 0,
                  fontFamily: "'Roboto Mono', 'Fira Code', 'Courier New', monospace",
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  maxHeight: '52vh',
                  overflowY: 'auto',
                }}>
                  {xmlText || 'No content found.'}
                </pre>
              )}
            </div>
          )}
        </div>

        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexShrink: 0,
          background: '#f8fafc',
          flexWrap: 'wrap', gap: 10,
        }}>
          <span style={{ fontSize: 13, color: '#64748b' }}>
            Both files look correct? Close this and click <strong>Start Audit</strong>.
          </span>
          <button
            onClick={onClose}
            style={{
              background: '#1a2240', color: '#fff', border: 'none',
              borderRadius: 8, padding: '9px 20px',
              fontSize: 13, fontWeight: 700, cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Close preview
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Validation Popup ──────────────────────────────────────────────────────────
function ValidationPopup({ result, screenshotName, xmlName, onClose }) {
  const ok = result === 'matched';
  const missingScreenshot = result === 'missing_screenshot';
  const title = ok ? 'Files Matched!' : missingScreenshot ? 'Screenshot Required' : 'File Mismatch';
  const message = ok
    ? 'Your screenshot and XML are a validated pair. You can now start the audit.'
    : missingScreenshot
    ? 'Please upload a screenshot (PNG or JPG) before selecting the XML file.'
    : "The files don't share the same identifier. Upload a matching pair.";

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(15,27,45,0.55)',
        backdropFilter: 'blur(3px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, animation: 'fadeIn 0.2s ease',
        padding: '16px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff',
          borderRadius: 18,
          borderTop: `4px solid ${ok ? '#00c896' : '#ef4444'}`,
          padding: '36px 32px 28px',
          maxWidth: 420, width: '92%',
          position: 'relative',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0,0,0,0.18)',
          animation: ok
            ? 'pulseIn 0.4s cubic-bezier(0.34,1.56,0.64,1) forwards'
            : 'shake 0.45s ease forwards',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 14, right: 14,
            background: '#f1f5f9', border: 'none', borderRadius: 8,
            width: 30, height: 30,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          {Icon.xIcon()}
        </button>

        <div style={{
          width: 60, height: 60, borderRadius: '50%', marginBottom: 16,
          background: ok ? '#e6faf4' : '#fee2e2',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {ok ? Icon.check('#00c896', 28) : Icon.alert('#ef4444', 28)}
        </div>

        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0f1b2d', margin: '0 0 10px' }}>
          {title}
        </h3>
        <p style={{ fontSize: 13.5, color: '#64748b', lineHeight: 1.6, margin: '0 0 24px' }}>
          {message}
        </p>

        {!missingScreenshot && (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[screenshotName, xmlName].map(name => (
            <div key={name} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: '#f8fafc', borderRadius: 8, padding: '10px 14px',
            }}>
              <span style={{ flex: 1, fontSize: 12.5, color: '#334155', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {name}
              </span>
              <span style={{
                fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                background: ok ? '#dcfce7' : '#fee2e2',
                color: ok ? '#16a34a' : '#ef4444',
              }}>
                {ok ? '✓' : '✗ ID mismatch'}
              </span>
            </div>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}

// ── Audit Steps Config (cosmetic progress shown while real API call runs) ────
const AUDIT_STEPS = [
  { label: 'Parsing screenshot and XML',      detail: 'Extracting UI component tree from UIAutomator dump',           pct: 15 },
  { label: 'Mapping components to bounds',    detail: 'Resolving components with spatial coordinates from XML',        pct: 32 },
  { label: 'Running WCAG 2.2 AA rule engine', detail: 'Checking 18 rules: labels, contrast, touch targets and more',  pct: 55 },
  { label: 'Detecting violations',            detail: 'Cross-referencing components against accessibility guidelines',  pct: 74 },
  { label: 'Scoring and ranking issues',      detail: 'Classifying by severity: critical, serious, moderate, minor',   pct: 90 },
  { label: 'Generating report',               detail: 'Compiling all findings into a structured accessibility report',  pct: 100 },
];

// ── Audit Processing Popup ────────────────────────────────────────────────────
// Now actually calls the backend (createAudit) instead of just faking progress.
// The step animation below still runs so the UI doesn't feel instant/jumpy,
// but "done" only becomes true once BOTH the animation AND the real API call finish.
function AuditPopup({ screenshotFile, xmlFile, onViewDashboard }) {
  const [completedSteps, setCompletedSteps] = useState([]);
  const [activeStep,     setActiveStep]     = useState(0);
  const [progress,       setProgress]       = useState(0);
  const [done,           setDone]           = useState(false);
  const [error,          setError]          = useState(null);
  const [auditId,        setAuditIdState]   = useState(null);

  // Real backend call — fires once, independent of the cosmetic animation below.
  useEffect(() => {
    let cancelled = false;
    createAudit(screenshotFile, xmlFile)
      .then(result => {
        if (cancelled) return;
        if (result.status === 'error') {
          setError(result.message || 'Audit pipeline failed.');
          return;
        }
        setAuditIdState(result.audit_id);
        setAuditId(result.audit_id); // persist so Dashboard/Report can read it later

        // Best-effort: save this audit to the user's Records history. Skipped
        // entirely for guests (no JWT) and never blocks the audit flow itself.
        if (isLoggedIn()) {
          getAuditViolations(result.audit_id)
            .then(violationsDoc => {
              const bySeverity = { High: 0, Medium: 0, Low: 0 };
              (violationsDoc.violations || []).forEach(v => {
                bySeverity[v.severity] = (bySeverity[v.severity] || 0) + 1;
              });
              return apiPost('/records', {
                screen_id: violationsDoc.screen_id,
                total_violations: violationsDoc.total_violations,
                violations_by_severity: bySeverity,
                components_path: '',
                violations_path: `outputs/violations/${violationsDoc.screen_id}_violations.json`,
              }, true);
            })
            .catch(() => {});
        }
      })
      .catch(err => {
        if (!cancelled) setError(err.message || 'Could not reach the audit server.');
      });
    return () => { cancelled = true; };
  }, [screenshotFile, xmlFile]);

  // Cosmetic step animation — purely visual, runs regardless of API timing.
  useEffect(() => {
    let stepIdx = 0;
    function runStep() {
      if (stepIdx >= AUDIT_STEPS.length) return;
      setActiveStep(stepIdx);
      const targetPct = AUDIT_STEPS[stepIdx].pct;
      const fromPct   = stepIdx === 0 ? 0 : AUDIT_STEPS[stepIdx - 1].pct;
      const duration  = 800 + stepIdx * 120;
      const startTs   = performance.now();
      function animate(ts) {
        const p = Math.min((ts - startTs) / duration, 1);
        setProgress(Math.round(fromPct + (targetPct - fromPct) * p));
        if (p < 1) {
          requestAnimationFrame(animate);
        } else {
          const finished = stepIdx;
          stepIdx++;
          setCompletedSteps(prev => [...prev, finished]);
          if (stepIdx >= AUDIT_STEPS.length) {
            setTimeout(() => setAnimationDone(true), 350);
          } else {
            setTimeout(runStep, 350);
          }
        }
      }
      requestAnimationFrame(animate);
    }
    const t = setTimeout(runStep, 400);
    return () => clearTimeout(t);
  }, []);

  // Tracks whether the cosmetic animation has finished its steps.
  const [animationDone, setAnimationDone] = useState(false);

  // Only show the "done" success card once animation AND real API call both finish.
  useEffect(() => {
    if (animationDone && auditId && !error) {
      setDone(true);
    }
  }, [animationDone, auditId, error]);

  if (error) {
    return (
      <div style={{
        position: 'fixed', inset: 0, background: 'rgba(15,27,45,0.65)',
        backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 1000, animation: 'fadeIn 0.2s ease', padding: '20px',
      }}>
        <div style={{
          background: '#fff', borderRadius: 18, width: '100%', maxWidth: 480,
          padding: '32px', textAlign: 'center', boxShadow: '0 24px 64px rgba(0,0,0,0.22)',
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%', background: '#fee2e2',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
          }}>
            {Icon.alert('#ef4444', 26)}
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0f1422', margin: '0 0 10px' }}>
            Audit failed
          </h3>
          <p style={{ fontSize: 14, color: '#64748b', margin: '0 0 24px', lineHeight: 1.6 }}>
            {error}
          </p>
          <p style={{ fontSize: 12, color: '#94a3b8', margin: '0 0 20px' }}>
            Check that the backend server is running at http://127.0.0.1:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(15,27,45,0.65)',
      backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center',
      justifyContent: 'center', zIndex: 1000, animation: 'fadeIn 0.2s ease', padding: '20px',
    }}>
      <div style={{
        background: '#fff', borderRadius: 18, width: '100%', maxWidth: 760,
        overflow: 'hidden', boxShadow: '0 24px 64px rgba(0,0,0,0.22)',
        animation: 'pulseIn 0.35s cubic-bezier(0.34,1.56,0.64,1) forwards',
      }}>
        <div style={{ background: '#0f1422', padding: '22px 24px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 40, height: 40, borderRadius: '50%', background: '#1D9E75',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              animation: done ? 'checkPop 0.4s ease forwards' : 'none',
            }}>
              {done ? Icon.check('#fff', 20) : <Spinner size={18} color="#fff" />}
            </div>
            <div>
              <p style={{ color: '#ffffff', fontSize: 18, fontWeight: 700, margin: 0 }}>
                {done ? 'Audit complete' : 'Running accessibility audit'}
              </p>
              <p style={{ color: '#a8bbd4', fontSize: 14, margin: '5px 0 0', fontWeight: 500 }}>
                {done ? 'Your report is ready to review' : 'Analyzing against WCAG 2.2 AA rules…'}
              </p>
            </div>
          </div>
          <div style={{ marginTop: 16, height: 4, background: '#1e2d42', borderRadius: 99, overflow: 'hidden' }}>
            <div style={{ height: '100%', borderRadius: 99, background: '#1D9E75', width: `${progress}%`, transition: 'width 0.5s cubic-bezier(0.4,0,0.2,1)' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
            <span style={{ fontSize: 13, color: '#a8bbd4', fontWeight: 500 }}>
              {done ? 'All steps complete' : `${AUDIT_STEPS[activeStep]?.label}…`}
            </span>
            <span style={{ fontSize: 14, color: '#1D9E75', fontWeight: 700 }}>{progress}%</span>
          </div>
        </div>

        <div style={{ padding: '20px 24px 0' }}>
          <p style={{ fontSize: 13, color: '#0f1422', fontWeight: 700, letterSpacing: '0.8px', margin: '0 0 14px', textTransform: 'uppercase' }}>
            Audit steps
          </p>
          <div className="axion-audit-steps" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {AUDIT_STEPS.map((s, i) => {
              const isComplete = completedSteps.includes(i);
              const isActive   = activeStep === i && !isComplete && !done;
              const isPending  = i > activeStep && !isComplete;
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 14px', borderRadius: 8,
                  background: isComplete ? '#f0fdf8' : isActive ? '#fafafa' : '#f8fafc',
                  border: `1px solid ${isComplete ? '#6ee7b7' : isActive ? '#cbd5e1' : '#e2e8f0'}`,
                  opacity: isPending ? 0.45 : 1,
                  transition: 'background 0.3s, border-color 0.3s, opacity 0.3s',
                }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: '50%',
                    background: isComplete ? '#1D9E75' : '#e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1,
                  }}>
                    {isComplete ? Icon.check('#fff', 15) : isActive ? <Spinner size={14} color="#475569" /> : null}
                  </div>
                  <div>
                    <p style={{ fontSize: 15, fontWeight: 600, color: isComplete ? '#065f46' : isPending ? '#94a3b8' : '#0f1422', margin: 0 }}>{s.label}</p>
                    <p style={{ fontSize: 13, color: isPending ? '#b0bec5' : '#475569', margin: '3px 0 0', lineHeight: 1.5 }}>{s.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {done ? (
  <div style={{ padding: '20px 24px 24px' }}>
    <div style={{
      background: '#f0fdf8', border: '1px solid #6ee7b7', borderRadius: 10,
      padding: '20px 16px', display: 'flex', flexDirection: 'column', alignItems: 'center',
      textAlign: 'center', gap: 10, marginBottom: 16,
    }}>
      <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#1D9E75', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, animation: 'checkPop 0.4s ease forwards' }}>
        {Icon.check('#fff', 22)}
      </div>
      <div>
        <p style={{ fontSize: 16, fontWeight: 700, color: '#0f1422', margin: 0 }}>Audit finished</p>
        <p style={{ fontSize: 13.5, color: '#065f46', margin: '5px 0 0', fontWeight: 500 }}>Violations detected — ranked by severity and ready to review</p>
      </div>
    </div>
    <button
      onClick={() => onViewDashboard(auditId)}
      style={{
        width: '100%', background: '#1D9E75', color: '#fff', border: 'none',
        borderRadius: 10, padding: '15px', fontSize: 16, fontWeight: 700, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontFamily: 'inherit',
      }}
      onMouseEnter={e => e.currentTarget.style.background = '#17876a'}
      onMouseLeave={e => e.currentTarget.style.background = '#1D9E75'}
    >
      View issues dashboard {Icon.arrow('#fff', 17)}
    </button>
  </div>
) : (
  <div style={{ height: 20 }} />
)}
      </div>
    </div>
  );
}

// ── Main Upload Page ──────────────────────────────────────────────────────────
export default function Upload() {
  injectKeyframes();
  injectResponsiveStyles();
  const navigate = useNavigate();

  const [screenshot,       setScreenshot]       = useState(null);
  const [xml,              setXml]              = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [showPopup,        setShowPopup]        = useState(false);
  const [showAuditPopup,   setShowAuditPopup]   = useState(false);
  const [showPreview,      setShowPreview]      = useState(false);
  const [searchQuery,      setSearchQuery]      = useState('');

   useEffect(() => {
    setAuditFiles(screenshot, xml);
  }, [screenshot, xml]);
  
  const screenshotRef = useRef(null);
  const xmlRef        = useRef(null);

  const step =
    !screenshot              ? 'empty'
    : !xml                   ? 'waiting'
    : validationResult === 'matched' ? 'matched'
    : 'mismatched';

  const progress =
    step === 'empty' ? 0 : step === 'waiting' ? 50 : step === 'matched' ? 100 : 75;

  const progressColor =
    step === 'matched'      ? '#1D9E75'
    : step === 'mismatched' ? '#ef4444'
    : '#f59e0b';

  const zoneBorder =
    step === 'empty'        ? '1.5px dashed #dde2f0'
    : step === 'mismatched' ? '1.5px solid #ef4444'
    : '1.5px solid #1D9E75';

  const zoneBg =
    step === 'matched'      ? '#f0fdf8'
    : step === 'mismatched' ? '#fff5f5'
    : '#fff';

  const canAudit = validationResult === 'matched';

  const handleMainClick = () => {
    if (validationResult) {
      setScreenshot(null); setXml(null); setValidationResult(null); setShowPopup(false);
      setTimeout(() => screenshotRef.current?.click(), 0);
    } else if (!screenshot) {
      screenshotRef.current?.click();
    } else {
      xmlRef.current?.click();
    }
  };

  const handleScreenshotChange = useCallback(e => {
    const file = e.target.files[0];
    if (!file) return;
    setScreenshot(file); setXml(null); setValidationResult(null);
    e.target.value = '';
  }, []);

  const handleXmlChange = useCallback(e => {
    const file = e.target.files[0];
    if (!file) return;
    if (!screenshot) {
      setValidationResult('missing_screenshot');
      setShowPopup(true);
      e.target.value = '';
      return;
    }
    const matched = filesMatch(screenshot.name, file.name);
    setXml(file);
    setValidationResult(matched ? 'matched' : 'mismatched');
    setShowPopup(true);
    e.target.value = '';
  }, [screenshot]);

  const btnLabel = validationResult ? 'Replace files' : screenshot && !xml ? 'Select XML file' : 'Select screenshot';
  const btnIcon  = validationResult ? Icon.refresh() : screenshot && !xml ? Icon.xml() : Icon.photo();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
      <Sidebar activePage="upload" />

      <input ref={screenshotRef} type="file" accept=".png,.jpg,.jpeg" style={{ display: 'none' }} onChange={handleScreenshotChange} />
      <input ref={xmlRef}        type="file" accept=".xml"            style={{ display: 'none' }} onChange={handleXmlChange} />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }} aria-label="Upload Audit Assets">

        {/* Topbar */}
        <div className="axion-topbar" style={{
          background: '#fff', padding: '16px 32px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '0.5px solid #e2e6f0',
        }}>
          <div>
            <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>Workspace</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: '#1a2240', margin: 0 }}>New Audit</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <input type="search" placeholder="Search past audits…" aria-label="Search past audits" className="axion-search"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && searchQuery.trim()) {
                  navigate(`/audit-history?q=${encodeURIComponent(searchQuery.trim())}`);
                }
              }}
              style={{ background: '#f4f6fb', border: '0.5px solid #dde2f0', borderRadius: 6, padding: '9px 16px', fontSize: 15, color: '#1a2240', width: 210 }}
            />
            <div role="img" aria-label="User: Ayesha Naveed" title="Ayesha Naveed"
              style={{ width: 42, height: 42, borderRadius: '50%', background: '#1D9E75', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 15, fontWeight: 700, flexShrink: 0 }}>
              <span aria-hidden="true">AN</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="axion-content" style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: 24, justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

            <div>
              <span style={{ background: '#e8f5f0', color: '#0f6e56', fontSize: 13, fontWeight: 700, padding: '4px 12px', borderRadius: 4, letterSpacing: '0.5px' }}>
                AI-POWERED AUDIT
              </span>
              <h1 className="axion-heading" style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: '10px 0 4px' }}>Upload Audit Assets</h1>
              <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>
                Upload your Android screenshot and UIAutomator XML separately. We'll validate them as a matching pair.
              </p>
            </div>

            {/* Upload Zone */}
            <div className="axion-upload-zone" style={{
              background: zoneBg, border: zoneBorder, borderRadius: 14,
              padding: '44px 32px 32px',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              transition: 'all 0.25s',
            }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%',
                background: step === 'mismatched' ? '#fee2e2' : '#e8f5f0',
                display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 18,
              }}>
                {step === 'empty'      && Icon.folder('#1D9E75', 26)}
                {step === 'waiting'    && Icon.xml('#1D9E75', 26)}
                {step === 'matched'    && Icon.check('#1D9E75', 26)}
                {step === 'mismatched' && Icon.alert('#ef4444', 26)}
              </div>

              <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 6px', textAlign: 'center', wordBreak: 'break-word' }}>
                {step === 'empty'      && 'Upload files'}
                {step === 'waiting'    && screenshot?.name}
                {step === 'matched'    && 'Files matched'}
                {step === 'mismatched' && 'File mismatch'}
              </p>

              <p style={{ fontSize: 14, color: '#5a6a8a', margin: '0 0 24px', textAlign: 'center', maxWidth: 440, lineHeight: 1.6 }}>
                {step === 'empty'      && 'Select your PNG or JPG screenshot first, then the matching XML file'}
                {step === 'waiting'    && 'Screenshot uploaded — now select the matching XML file'}
                {step === 'matched'    && `"${screenshot?.name}" and "${xml?.name}" are a validated pair`}
                {step === 'mismatched' && `"${screenshot?.name}" and "${xml?.name}" don't share the same identifier`}
              </p>

              <button
                onClick={handleMainClick}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: validationResult ? '#475569' : '#1a2240',
                  color: '#fff', border: 'none', borderRadius: 8,
                  fontSize: 15, fontWeight: 600, padding: '12px 28px',
                  cursor: 'pointer', fontFamily: 'inherit', marginBottom: 24,
                }}
              >
                {btnIcon}{btnLabel}
              </button>

              <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: 8 }}>
                <span style={{ fontSize: 14, color: step === 'empty' ? '#5a6a8a' : progressColor, fontWeight: 500 }}>
                  {step === 'empty'      && 'No files uploaded'}
                  {step === 'waiting'    && 'Screenshot uploaded'}
                  {step === 'matched'    && 'Files validated successfully'}
                  {step === 'mismatched' && 'Mismatch detected'}
                </span>
                <span style={{ fontSize: 14, fontWeight: 700, color: step === 'empty' ? '#5a6a8a' : progressColor }}>{progress}%</span>
              </div>

              <div style={{ width: '100%', height: 5, background: '#e2e6f0', borderRadius: 99, overflow: 'hidden', marginBottom: 14 }}>
                <div style={{
                  height: '100%', borderRadius: 99,
                  width: `${progress}%`,
                  background: step === 'empty' ? '#e2e6f0' : progressColor,
                  transition: 'width 0.5s cubic-bezier(0.4,0,0.2,1), background 0.3s',
                }} />
              </div>

              {step === 'empty' && (
                <span style={{ fontSize: 14, color: '#f59e0b', fontWeight: 500 }}>Upload your screenshot to begin</span>
              )}
              {step === 'waiting' && (
                <span style={{ fontSize: 14, color: '#f59e0b', fontWeight: 500 }}>Now select the matching XML file</span>
              )}

              {/* Action pills row — shown only when both files uploaded */}
              {validationResult && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', justifyContent: 'center' }}>
                  <button
                    onClick={() => setShowPopup(true)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      border: '1px solid #1a2240',
                      borderRadius: 99, fontSize: 13, fontWeight: 600,
                      padding: '5px 14px', cursor: 'pointer',
                      background: '#f1f5f9',
                      color: '#1a2240',
                      fontFamily: 'inherit',
                    }}
                  >
                    {Icon.eye('#1a2240', 14)}
                    View validation status
                  </button>

                  {canAudit && (
                    <button
                      onClick={() => setShowPreview(true)}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 6,
                        border: '1px solid #1a2240',
                        borderRadius: 99, fontSize: 13, fontWeight: 600,
                        padding: '5px 14px', cursor: 'pointer',
                        background: '#f1f5f9',
                        color: '#1a2240',
                        fontFamily: 'inherit',
                      }}
                    >
                      {Icon.fileSearch('#1a2240', 14)}
                      Preview files
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* CTA bar */}
          <div className="axion-cta-bar" style={{
            background: '#0f1422', borderRadius: 14, padding: '18px 28px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20,
          }}>
            <div>
              <p style={{ color: '#e2e6f0', fontSize: 18, fontWeight: 700, margin: 0 }}>Ready to Generate Accessibility Report?</p>
              <p style={{ color: '#4a5a7a', fontSize: 14, margin: '5px 0 0' }}>
                {canAudit ? 'Files validated. Click "Start Audit" to run the WCAG 2.2 AA check.' : 'Upload a matching screenshot and XML file to enable the audit.'}
              </p>
            </div>
            <button
              className="axion-cta-button"
              disabled={!canAudit}
              aria-label="Start accessibility audit"
              onClick={() => canAudit && setShowAuditPopup(true)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: canAudit ? '#1D9E75' : '#2d3f52',
                color: canAudit ? '#fff' : '#4a5a7a',
                border: 'none', borderRadius: 10,
                fontSize: 17, fontWeight: 700, padding: '14px 30px',
                cursor: canAudit ? 'pointer' : 'not-allowed',
                fontFamily: 'inherit', whiteSpace: 'nowrap', flexShrink: 0,
                transition: 'background 0.25s',
              }}
            >
              Start Audit {Icon.arrow(canAudit ? '#fff' : '#4a5a7a', 16)}
            </button>
          </div>
        </div>
      </main>

      {showPopup && validationResult && (
        <ValidationPopup
          result={validationResult}
          screenshotName={screenshot?.name}
          xmlName={xml?.name}
          onClose={() => setShowPopup(false)}
        />
      )}

      {showAuditPopup && (
        <AuditPopup
          screenshotFile={screenshot}
          xmlFile={xml}
          onViewDashboard={(auditId) => {
            setShowAuditPopup(false);
            navigate('/dashboard', { state: { auditId, screenshot, xml } });
          }}
        />
      )}

      {showPreview && (
        <FilePreviewPopup
          screenshot={screenshot}
          xml={xml}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}
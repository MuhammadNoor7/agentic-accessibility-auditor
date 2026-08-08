import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { getAuditFiles, getAuditId, hasRecordedAudit, markAuditRecorded } from '../state/auditFiles'
import { getAuditReport, createRecord } from '../api'
import Sidebar from '../components/Sidebar'
import UserAvatar from '../components/ui/UserAvatar'

/* ────────────────────────────────────────────────────────────────────────────
   RULE REFERENCE — sourced from Accessibility_Guidelines_Rules_v2.docx
   30 guidelines (G01–G30) × 30 detection rules (R01–R30).
   Severity in the source doc is High / Medium / Low — mapped here to
   Critical / Serious / Minor to match the dashboard's 3-tier visual language.
   ──────────────────────────────────────────────────────────────────────────── */
const SEVERITY_MAP = { High: 'Critical', Medium: 'Serious', 'Low/Med': 'Serious', Low: 'Minor' }

const RULES = {
  R01: { guideline: 'G01', label: 'Missing accessible label',      wcag: 'WCAG 4.1.2', docSeverity: 'High' },
  R02: { guideline: 'G02', label: 'No image description',          wcag: 'WCAG 1.1.1', docSeverity: 'High' },
  R03: { guideline: 'G03', label: 'Duplicate labels',               wcag: 'WCAG 4.1.2', docSeverity: 'Medium' },
  R04: { guideline: 'G04', label: 'Small touch target',             wcag: 'WCAG 2.5.5', docSeverity: 'High' },
  R05: { guideline: 'G05', label: 'Unlabeled input field',          wcag: 'WCAG 1.3.1', docSeverity: 'High' },
  R06: { guideline: 'G06', label: 'Disabled important control',     wcag: 'WCAG 2.1.1', docSeverity: 'Medium' },
  R07: { guideline: 'G07', label: 'Invisible / zero-size element',  wcag: 'WCAG 1.3.1', docSeverity: 'Medium' },
  R08: { guideline: 'G08', label: 'Layout overlap',                 wcag: 'WCAG 1.3.2', docSeverity: 'Medium' },
  R09: { guideline: 'G09', label: 'Low contrast',                   wcag: 'WCAG 1.4.3', docSeverity: 'Medium' },
  R10: { guideline: 'G10', label: 'Text overflow',                  wcag: 'WCAG 1.4.4', docSeverity: 'Low/Med' },
  R11: { guideline: 'G11', label: 'Color-only information',         wcag: 'WCAG 1.4.1', docSeverity: 'High' },
  R12: { guideline: 'G12', label: 'Missing captions',                wcag: 'WCAG 1.2.2', docSeverity: 'High' },
  R13: { guideline: 'G13', label: 'No transcript',                   wcag: 'WCAG 1.2.1', docSeverity: 'High' },
  R14: { guideline: 'G14', label: 'Audio-only notification',        wcag: 'WCAG 1.3.3', docSeverity: 'Medium' },
  R15: { guideline: 'G15', label: 'Bad focus order',                 wcag: 'WCAG 1.3.2', docSeverity: 'Medium' },
  R16: { guideline: 'G16', label: 'Decorative element in focus tree',wcag: 'WCAG 1.3.1', docSeverity: 'Low' },
  R17: { guideline: 'G17', label: 'Insufficient touch spacing',      wcag: 'WCAG 2.5.5', docSeverity: 'Medium' },
  R18: { guideline: 'G18', label: 'Multi-gesture only',              wcag: 'WCAG 2.1.1', docSeverity: 'High' },
  R19: { guideline: 'G19', label: 'No confirmation for destructive action', wcag: 'WCAG 3.3.4', docSeverity: 'Medium' },
  R20: { guideline: 'G20', label: 'Hint-only label',                 wcag: 'WCAG 3.3.2', docSeverity: 'Medium' },
  R21: { guideline: 'G21', label: 'Vague error message',             wcag: 'WCAG 3.3.1', docSeverity: 'High' },
  R22: { guideline: 'G22', label: 'No password show/hide toggle',    wcag: 'WCAG 3.3.1', docSeverity: 'Medium' },
  R23: { guideline: 'G23', label: 'Unlabeled navigation control',    wcag: 'WCAG 2.4.6', docSeverity: 'High' },
  R24: { guideline: 'G24', label: 'Missing screen title',            wcag: 'WCAG 2.4.2', docSeverity: 'Medium' },
  R25: { guideline: 'G25', label: 'Uncontrolled animation',          wcag: 'WCAG 2.2.2', docSeverity: 'Medium' },
  R26: { guideline: 'G26', label: 'No session timeout warning',      wcag: 'WCAG 2.2.1', docSeverity: 'Medium' },
  R27: { guideline: 'G27', label: 'Complex label language',          wcag: 'WCAG 3.1.5', docSeverity: 'Low' },
  R28: { guideline: 'G28', label: 'Font scale overflow',             wcag: 'WCAG 1.4.4', docSeverity: 'Medium' },
  R29: { guideline: 'G29', label: 'All-caps body text',              wcag: 'WCAG 3.1.5', docSeverity: 'Low' },
  R30: { guideline: 'G30', label: 'Icon-only button, no label',      wcag: 'WCAG 1.1.1', docSeverity: 'High' },
}

/* ── Severity visual tokens ─────────────────────────────────────────────── */
const SEV = {
  Critical: { bg: '#fdf0ef', color: '#7A1C1C', dot: '#ef4444', cardBg: '#fff5f5', cardBorder: '#fecaca', desc: 'Must fix — blocks assistive tech' },
  Serious:  { bg: '#fef6ed', color: '#7A4000', dot: '#f97316', cardBg: '#fff7ed', cardBorder: '#fed7aa', desc: 'High impact on usability' },
  Minor:    { bg: '#f4f6fb', color: '#3D4043', dot: '#94a3b8', cardBg: '#f8fafc', cardBorder: '#e2e8f0', desc: 'Low impact, good to fix' },
}

const severityOrder = ['Critical', 'Serious', 'Minor']

/* ── Shared icons / spinner (same visual language as Upload's audit popup) ─ */
const Icon = {
  check: (color = '#00c896', size = 26) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  ),
  arrow: (color = '#64748b', size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  ),
  alert: (color = '#ef4444', size = 26) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
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
  )
}

/* ── Audit Steps Config (mirrors Upload.jsx's Start Audit flow) ──────────── */
const AUDIT_STEPS = [
  { label: 'Parsing screenshot and XML', detail: 'Extracting UI component tree from UIAutomator dump', pct: 15 },
  { label: 'Mapping components to bounds', detail: 'Resolving components with spatial coordinates from XML', pct: 32 },
  { label: 'Running WCAG 2.2 AA rule engine', detail: 'Checking 18 rules: labels, contrast, touch targets and more', pct: 55 },
  { label: 'Detecting violations', detail: 'Cross-referencing components against accessibility guidelines', pct: 74 },
  { label: 'Scoring and ranking issues', detail: 'Classifying by severity: critical, serious, moderate, minor', pct: 90 },
  { label: 'Generating report', detail: 'Compiling all findings into a structured accessibility report', pct: 100 },
]

/* ── Re-run Audit Processing Popup — now re-fetches the real report ──────── */
function AuditPopup({ auditId, onClose, onRefreshed }) {
  const [completedSteps, setCompletedSteps] = useState([])
  const [activeStep, setActiveStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)
  const [error, setError] = useState(null)

  // Real re-fetch of the report for this same audit_id
  useEffect(() => {
    let cancelled = false
    if (!auditId) {
      setError('No audit ID available to refresh.')
      return
    }
    getAuditReport(auditId)
      .then(report => {
        if (!cancelled) onRefreshed(report)
      })
      .catch(err => {
        if (!cancelled) setError(err.message || 'Could not refresh the report.')
      })
    return () => { cancelled = true }
  }, [auditId])

  useEffect(() => {
    let stepIdx = 0
    function runStep() {
      if (stepIdx >= AUDIT_STEPS.length) return
      setActiveStep(stepIdx)
      const targetPct = AUDIT_STEPS[stepIdx].pct
      const fromPct = stepIdx === 0 ? 0 : AUDIT_STEPS[stepIdx - 1].pct
      const duration = 700 + stepIdx * 100
      const startTs = performance.now()
      function animate(ts) {
        const p = Math.min((ts - startTs) / duration, 1)
        setProgress(Math.round(fromPct + (targetPct - fromPct) * p))
        if (p < 1) {
          requestAnimationFrame(animate)
        } else {
          const finished = stepIdx
          stepIdx++
          setCompletedSteps(prev => [...prev, finished])
          if (stepIdx >= AUDIT_STEPS.length) {
            setTimeout(() => setDone(true), 300)
          } else {
            setTimeout(runStep, 300)
          }
        }
      }
      requestAnimationFrame(animate)
    }
    const t = setTimeout(runStep, 350)
    return () => clearTimeout(t)
  }, [])

  if (error) {
    return (
      <div style={{
        position: 'fixed', inset: 0, background: 'rgba(15,27,45,0.65)',
        backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 1000, padding: '20px',
      }}>
        <div style={{ background: '#fff', borderRadius: 18, width: '100%', maxWidth: 440, padding: '28px', textAlign: 'center' }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
            {Icon.alert('#ef4444', 24)}
          </div>
          <p style={{ fontSize: 16, fontWeight: 700, color: '#0f1422', margin: '0 0 8px' }}>Refresh failed</p>
          <p style={{ fontSize: 13.5, color: '#64748b', margin: '0 0 20px' }}>{error}</p>
          <button onClick={onClose} style={{ background: '#1a2240', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontWeight: 700, cursor: 'pointer' }}>
            Close
          </button>
        </div>
      </div>
    )
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
            }}>
              {done ? Icon.check('#fff', 20) : <Spinner size={18} color="#fff" />}
            </div>
            <div>
              <p style={{ color: '#ffffff', fontSize: 18, fontWeight: 700, margin: 0 }}>
                {done ? 'Audit complete' : 'Re-running accessibility audit'}
              </p>
              <p style={{ color: '#a8bbd4', fontSize: 14, margin: '5px 0 0', fontWeight: 500 }}>
                {done ? 'Your report has been refreshed' : 'Analyzing against WCAG 2.2 AA rules…'}
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
              const isComplete = completedSteps.includes(i)
              const isActive = activeStep === i && !isComplete && !done
              const isPending = i > activeStep && !isComplete
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 14px', borderRadius: 8,
                  background: isComplete ? '#f0fdf8' : isActive ? '#fafafa' : '#f8fafc',
                  border: `1px solid ${isComplete ? '#6ee7b7' : isActive ? '#cbd5e1' : '#e2e8f0'}`,
                  opacity: isPending ? 0.45 : 1, transition: 'background 0.3s, border-color 0.3s, opacity 0.3s',
                }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: '50%', background: isComplete ? '#1D9E75' : '#e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1,
                  }}>
                    {isComplete ? Icon.check('#fff', 15) : isActive ? <Spinner size={14} color="#475569" /> : null}
                  </div>
                  <div>
                    <p style={{ fontSize: 15, fontWeight: 600, color: isComplete ? '#065f46' : isPending ? '#94a3b8' : '#0f1422', margin: 0 }}>
                      {s.label}
                    </p>
                    <p style={{ fontSize: 13, color: isPending ? '#b0bec5' : '#475569', margin: '3px 0 0', lineHeight: 1.5 }}>
                      {s.detail}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {done ? (
          <div style={{ padding: '20px 24px 24px' }}>
            <div style={{
              background: '#f0fdf8', border: '1px solid #6ee7b7', borderRadius: 10, padding: '14px 16px',
              display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16,
            }}>
              <div style={{
                width: 34, height: 34, borderRadius: '50%', background: '#1D9E75',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                {Icon.check('#fff', 17)}
              </div>
              <div>
                <p style={{ fontSize: 15, fontWeight: 700, color: '#0f1422', margin: 0 }}>Audit finished</p>
                <p style={{ fontSize: 13, color: '#065f46', margin: '4px 0 0', fontWeight: 500 }}>
                  Violations refreshed — ranked by severity and ready to review
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                width: '100%', background: '#1D9E75', color: '#fff', border: 'none', borderRadius: 10,
                padding: '15px', fontSize: 16, fontWeight: 700, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontFamily: 'inherit',
              }}
            >
              Back to dashboard {Icon.arrow('#fff', 17)}
            </button>
          </div>
        ) : (
          <div style={{ height: 20 }} />
        )}
      </div>
    </div>
  )
}

/* ── Issue Detail Drawer ───────────────────────────────────────────────── */
function IssueDrawer({ issue, onClose }) {
  const s = SEV[issue.severity]
  const rule = RULES[issue.rule_id]
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(15,27,45,0.45)',
        backdropFilter: 'blur(2px)',
        zIndex: 200,
        display: 'flex', justifyContent: 'flex-end',
        animation: 'fadeIn 0.2s ease',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        className="axion-drawer"
        style={{
          height: '100%', background: '#fff',
          display: 'flex', flexDirection: 'column',
          boxShadow: '-8px 0 32px rgba(0,0,0,0.12)',
          animation: 'slideIn 0.25s ease',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          background: '#0f1422', padding: '20px 24px',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
              <span style={{
                background: s.bg, color: s.color, fontSize: 12, fontWeight: 700,
                padding: '3px 10px', borderRadius: 99,
                display: 'inline-flex', alignItems: 'center', gap: 5,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot, display: 'inline-block' }} />
                {issue.severity}
              </span>
              <span style={{ fontSize: 12, color: '#a8bbd4', fontWeight: 600 }}>{issue.guideline}</span>
              <span style={{ fontSize: 11, color: '#1D9E75', background: '#1e2d42', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
                {issue.rule_id} · {rule?.guideline}
              </span>
              {issue.cv_confidence != null && (
                <span style={{ fontSize: 11, color: '#0f1422', background: '#1D9E75', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
                  👁 CV-confirmed {Math.round(issue.cv_confidence * 100)}%
                </span>
              )}
            </div>
            <p style={{ color: '#fff', fontSize: 17, fontWeight: 700, margin: 0, lineHeight: 1.4 }}>
              {issue.issue}
            </p>
            <p style={{ color: '#a8bbd4', fontSize: 13, margin: '6px 0 0' }}>
              {issue.class} · {issue.component_id}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close detail panel"
            style={{
              background: '#7f1d1d', border: 'none', borderRadius: 8,
              width: 32, height: 32, display: 'flex', alignItems: 'center',
              justifyContent: 'center', cursor: 'pointer', flexShrink: 0,
              color: '#fff', fontSize: 18, lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              background: '#f1f5f9', color: '#1a2240', fontSize: 12, fontWeight: 700,
              padding: '4px 12px', borderRadius: 6,
            }}>
              Rule {issue.rule_id}
            </span>
            <span style={{
              background: '#f1f5f9', color: '#475569', fontSize: 12, fontWeight: 600,
              padding: '4px 12px', borderRadius: 6,
            }}>
              Component {issue.component_id}
            </span>
          </div>

          {[
            { label: 'What the issue is', icon: '⚠', text: issue.agent_explanation,      iconBg: '#fef3c7', borderColor: '#1a2240' },
            { label: 'Why it matters',     icon: '👁', text: issue.agent_why_it_matters, iconBg: '#dbeafe', borderColor: '#1a2240' },
            { label: 'How to fix it',      icon: '🔧', text: issue.agent_developer_fix,  iconBg: '#dcfce7', borderColor: '#1a2240' },
          ].map(({ label, icon, text, iconBg, borderColor }) => (
            <div key={label} style={{
              background: '#f8fafc', border: `1px solid ${borderColor}`,
              borderRadius: 10, padding: '14px 16px',
            }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: '#1a2240', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ background: iconBg, borderRadius: 4, padding: '2px 5px', fontSize: 13 }} aria-hidden="true">{icon}</span>
                {label}
              </p>
              <p style={{ fontSize: 14, color: '#0f1422', margin: 0, lineHeight: 1.6 }}>
                {text}
              </p>
            </div>
          ))}

          <div style={{
            background: '#f0fdf8', border: '1px solid #059669',
            borderRadius: 10, padding: '14px 16px',
          }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: '#0f6e56', textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 6px' }}>
              📄 Recommendation
            </p>
            <p style={{ fontSize: 14, color: '#065f46', margin: 0, lineHeight: 1.6 }}>
              {issue.recommendation}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Main Dashboard ────────────────────────────────────────────────────── */
export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const { screenshot, xml } = getAuditFiles()

  // audit_id can arrive via route state (fresh navigation from Upload)
  // or the shared store (getAuditId) if the page was refreshed / reached another way.
  const auditId = location.state?.auditId || getAuditId()

  const [report, setReport]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)

  const [severityFilter, setSeverityFilter] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [showAuditPopup, setShowAuditPopup] = useState(false)

  useEffect(() => {
    if (!auditId) {
      setLoadError('No audit found. Please run a new audit from the Upload page.')
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    getAuditReport(auditId)
      .then(data => {
        if (cancelled) return
        setReport(data)
        setLoading(false)

        if (!hasRecordedAudit(auditId)) {
          markAuditRecorded(auditId)
          createRecord({
            screen_id: data.screen_id,
            total_violations: data.summary?.total_issues ?? (data.violations || []).length,
            violations_by_severity: {
              critical: data.summary?.critical ?? 0,
              high: data.summary?.high ?? 0,
              medium: data.summary?.medium ?? 0,
              low: data.summary?.low ?? 0,
            },
            components_path: '',
            violations_path: `outputs/violations/${data.screen_id}_violations.json`,
            accessibility_score: data.accessibility_score ?? null,
            screenshot_name: screenshot?.name || null,
            xml_name: xml?.name || null,
          }).catch(err => {
            // History logging is best-effort — never break the report the
            // user is already looking at over this.
            console.error('Could not save this audit to history:', err.message)
          })
        }
      })
      .catch(err => {
        if (!cancelled) { setLoadError(err.message || 'Could not load report.'); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [auditId])

  // Map real backend violations -> UI shape (severity label + drawer fields)
  const violations = (report?.violations || []).map(v => ({
    ...v,
    severity: SEVERITY_MAP[v.severity] || v.severity,
  }))

  const total = violations.length
  const counts = severityOrder.reduce((acc, s) => {
    acc[s] = violations.filter(v => v.severity === s).length
    return acc
  }, {})
  const pct = s => total ? Math.round((counts[s] / total) * 100) : 0

  const filtered = violations
    .filter(v => severityFilter === 'All' || v.severity === severityFilter)
    .filter(v => {
      const q = searchQuery.trim().toLowerCase()
      if (!q) return true
      return [v.rule_id, v.issue, v.class, v.component_id, v.guideline]
        .some(field => field?.toLowerCase().includes(q))
    })

  // ── Loading state ──────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
        <Sidebar activePage="dashboard" />
        <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ textAlign: 'center' }}>
            <Spinner size={32} color="#1D9E75" />
            <p style={{ marginTop: 16, color: '#5a6a8a', fontSize: 15 }}>Loading your audit report…</p>
          </div>
        </main>
      </div>
    )
  }

  // ── Error / no audit state ─────────────────────────────────────────────
  if (loadError) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
        <Sidebar activePage="dashboard" />
        <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
          <div style={{ textAlign: 'center', maxWidth: 420 }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              {Icon.alert('#ef4444', 26)}
            </div>
            <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 8px' }}>Couldn't load dashboard</p>
            <p style={{ fontSize: 14, color: '#64748b', margin: '0 0 20px' }}>{loadError}</p>
            <button
              onClick={() => navigate('/upload')}
              style={{ background: '#1a2240', color: '#fff', border: 'none', borderRadius: 8, padding: '12px 24px', fontWeight: 700, cursor: 'pointer' }}
            >
              Go to Upload
            </button>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
      <Sidebar activePage="dashboard" />

      <style>{`
        @keyframes fadeIn  { from { opacity:0 } to { opacity:1 } }
        @keyframes slideIn { from { transform:translateX(40px); opacity:0 } to { transform:translateX(0); opacity:1 } }
        @keyframes pulseIn { 0% { transform: scale(0.85); opacity: 0; } 60% { transform: scale(1.04); } 100% { transform: scale(1); opacity: 1; } }
        @keyframes spin { to { transform: rotate(360deg); } }

        .axion-topbar {
          padding: 16px 32px;
        }
        .axion-heading-row {
          flex-wrap: wrap;
          gap: 16px;
        }
        .axion-stat-grid {
          grid-template-columns: 220px 1fr 1fr 1fr;
        }
        .axion-search-input {
          width: 210px;
        }
        .axion-table-scroll {
          overflow-x: auto;
        }
        .axion-drawer {
          width: 440px;
        }

        @media (max-width: 900px) {
          .axion-stat-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        @media (max-width: 640px) {
          .axion-audit-steps {
            grid-template-columns: 1fr;
          }
          .axion-topbar {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            padding: 16px 20px;
          }
          .axion-heading-row {
            flex-direction: column;
            align-items: stretch;
          }
          .axion-topbar-actions {
            width: 100%;
          }
          .axion-stat-grid {
            grid-template-columns: 1fr;
          }
          .axion-search-input {
            width: 100%;
          }
          .axion-drawer {
            width: 100vw;
            max-width: 100vw;
          }
        }
      `}</style>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }} aria-label="Issues Dashboard">

        {/* TOPBAR */}
        <div className="axion-topbar" style={{
          background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '0.5px solid #e2e6f0',
        }}>
          <div>
            <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>Workspace</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: '#1a2240', margin: 0 }}>Issues Dashboard</p>
          </div>
          <div className="axion-topbar-actions" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <input
              type="search" placeholder="Search issues, rule ID…" aria-label="Search detected issues"
              className="axion-search-input"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                background: '#f4f6fb', border: '0.5px solid #dde2f0',
                borderRadius: 6, padding: '9px 16px', fontSize: 15,
                color: '#1a2240',
              }}
            />
            <UserAvatar />
          </div>
        </div>

        {/* CONTENT */}
        <div style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Heading row */}
          <div className="axion-heading-row" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <span style={{
                background: '#e8f5f0', color: '#0f6e56', fontSize: 13,
                fontWeight: 700, padding: '4px 12px', borderRadius: 4, letterSpacing: '0.5px',
              }}>
                AI-POWERED AUDIT
              </span>
              <h1 style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: '10px 0 4px' }}>
                Issues Dashboard
              </h1>
              <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>
                {report?.screen_id || screenshot?.name || 'screen'} &nbsp;·&nbsp; {total} issue{total === 1 ? '' : 's'} found &nbsp;·&nbsp; {report?.enrichment_mode === 'llm' ? 'AI-explained' : 'Rule-based'}
              </p>
            </div>
           <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4 }}>
  <button
  aria-label="Start a new audit"
  onClick={() => navigate('/upload')}
  style={{
    background: '#1a2240', color: '#fff', border: 'none',
    borderRadius: 8, padding: '12px 22px', fontSize: 15,
    fontWeight: 600, cursor: 'pointer',
    display: 'flex', alignItems: 'center', gap: 6,
  }}
>
  <span aria-hidden="true" style={{ fontSize: 16 }}>+</span> New Audit
</button>

  <button
    aria-label="Re-run accessibility audit"
    onClick={() => setShowAuditPopup(true)}
    style={{
      background: '#1a2240', color: '#fff', border: 'none',
      borderRadius: 8, padding: '12px 22px', fontSize: 15,
      fontWeight: 600, cursor: 'pointer',
      display: 'flex', alignItems: 'center', gap: 6,
    }}
  >
    <span aria-hidden="true" style={{ fontSize: 16 }}>↺</span> Re-run Audit
  </button>
</div>
          </div>

          {/* STAT CARDS */}
          <div className="axion-stat-grid" style={{ display: 'grid', gap: 14 }}>

            <div
              role="img"
              aria-label={`Accessibility score: ${report?.accessibility_score ?? '—'} out of 100. Based on ${total} detected issues.`}
              style={{
                background: '#0f1422', borderRadius: 14,
                padding: '20px 20px', display: 'flex', alignItems: 'center', gap: 16,
              }}
            >
              <div style={{ position: 'relative', width: 72, height: 72, flexShrink: 0 }} aria-hidden="true">
                <svg width="72" height="72" viewBox="0 0 72 72">
                  <circle cx="36" cy="36" r="30" fill="none" stroke="#1e2d42" strokeWidth="6" />
                  <circle cx="36" cy="36" r="30" fill="none" stroke="#1D9E75" strokeWidth="6"
                    strokeDasharray="188.5"
                    strokeDashoffset={188.5 - (188.5 * (report?.accessibility_score ?? 0)) / 100}
                    strokeLinecap="round" transform="rotate(-90 36 36)" />
                </svg>
                <div style={{
                  position: 'absolute', inset: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, fontWeight: 700, color: '#fff',
                }}>
                  {report?.accessibility_score ?? '—'}
                </div>
              </div>
              <div aria-hidden="true">
                <p style={{ fontSize: 11, color: '#4a5a7a', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px', margin: '0 0 4px' }}>
                  Score
                </p>
                <p style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5, margin: 0 }}>
                  Based on {total} detected issues
                </p>
              </div>
            </div>

            {severityOrder.map(sev => {
              const s = SEV[sev]
              return (
                <div key={sev} style={{
                  background: s.cardBg, border: `1px solid ${s.cardBorder}`,
                  borderRadius: 14, padding: '18px 20px',
                  cursor: 'pointer',
                  outline: severityFilter === sev ? `2px solid ${s.dot}` : 'none',
                  transition: 'outline 0.15s',
                }}
                  onClick={() => setSeverityFilter(severityFilter === sev ? 'All' : sev)}
                  title={`Filter by ${sev}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.dot, display: 'inline-block' }} aria-hidden="true" />
                    <span style={{ fontSize: 11, color: s.color, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {sev}
                    </span>
                  </div>
                  <p style={{ fontSize: 32, fontWeight: 700, color: s.color, margin: '0 0 4px', lineHeight: 1 }}>
                    {counts[sev]}
                  </p>
                  <p style={{ fontSize: 11, color: s.dot, margin: 0 }}>
                    {s.desc}
                  </p>
                </div>
              )
            })}
          </div>

          {/* PRIORITY BAR */}
          <div style={{
            background: '#fff', borderRadius: 14,
            border: '0.5px solid #e2e6f0', padding: '20px 24px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: 0 }}>Issues by priority</p>
              <p style={{ fontSize: 14, color: '#5a6a8a', margin: 0 }}>{total} total issues</p>
            </div>
            <div
              style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', height: 12, gap: 2 }}
              role="img"
              aria-label={`Issues by priority: Critical ${pct('Critical')}% (${counts.Critical}), Serious ${pct('Serious')}% (${counts.Serious}), Minor ${pct('Minor')}% (${counts.Minor})`}
            >
              <div style={{ width: `${pct('Critical')}%`, background: '#A32D2D', borderRadius: '99px 0 0 99px' }} aria-hidden="true" />
              <div style={{ width: `${pct('Serious')}%`,  background: '#854F0B' }} aria-hidden="true" />
              <div style={{ width: `${pct('Minor')}%`,    background: '#5F5E5A', borderRadius: '0 99px 99px 0' }} aria-hidden="true" />
            </div>
            <div style={{ display: 'flex', gap: 20, marginTop: 10, flexWrap: 'wrap' }}>
              {severityOrder.map(sev => (
                <span key={sev} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: SEV[sev].color }}>
                  <span style={{ width: 9, height: 9, borderRadius: '50%', background: SEV[sev].dot, display: 'inline-block' }} aria-hidden="true" />
                  {sev} {pct(sev)}%
                </span>
              ))}
            </div>
          </div>

          {/* ISSUES TABLE */}
          <div style={{
            background: '#fff', borderRadius: 14,
            border: '0.5px solid #e2e6f0', overflow: 'hidden',
          }}>
            <div style={{
              padding: '14px 20px', borderBottom: '0.5px solid #e2e6f0',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: 0 }}>
                Detected issues
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <select
                  value={severityFilter}
                  onChange={e => setSeverityFilter(e.target.value)}
                  aria-label="Filter by severity"
                  style={{
                    fontSize: 13, padding: '7px 14px',
                    border: '1.5px solid #94a3b8', borderRadius: 6,
                    color: '#1a2240', background: '#fff', cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  <option value="All">All severities</option>
                  <option value="Critical">Critical</option>
                  <option value="Serious">Serious</option>
                  <option value="Minor">Minor</option>
                </select>
                <span style={{ fontSize: 13, color: '#94a3b8' }}>
                  {filtered.length} of {total} shown
                </span>
              </div>
            </div>

            <div className="axion-table-scroll">
            <table style={{ width: '100%', borderCollapse: 'collapse' }} aria-label="Detected accessibility issues">
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  {['Rule', 'Issue & component', 'Severity', 'Guideline', ''].map(h => (
                    <th key={h} scope="col" style={{
                      padding: '10px 16px', textAlign: 'left',
                      fontSize: 11, fontWeight: 700, color: '#64748b',
                      textTransform: 'uppercase', letterSpacing: '0.6px',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((v, i) => {
                  const s = SEV[v.severity]
                  return (
                    <tr key={i} style={{ borderTop: '0.5px solid #f0f2f8', transition: 'background 0.15s' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#fafbff'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '13px 16px', fontSize: 14, fontWeight: 700, color: '#1a2240', width: 70 }}>
                        {v.rule_id}
                      </td>
                      <td style={{ padding: '13px 16px' }}>
                        <p style={{ fontSize: 15, fontWeight: 600, color: '#0f1422', margin: 0 }}>{v.issue}</p>
                        <p style={{ fontSize: 12, color: '#94a3b8', margin: '3px 0 0' }}>{v.class} · {v.component_id}</p>
                        {v.cv_confidence != null && (
                          <p style={{ fontSize: 11, color: '#1D9E75', margin: '3px 0 0', fontWeight: 600 }}>
                            👁 CV-confirmed {Math.round(v.cv_confidence * 100)}%
                          </p>
                        )}
                      </td>
                      <td style={{ padding: '13px 16px', width: 120 }}>
                        <span style={{
                          background: s.bg, color: s.color, padding: '4px 12px', borderRadius: 99,
                          fontSize: 12, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 5,
                        }}>
                          <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot, display: 'inline-block' }} aria-hidden="true" />
                          {v.severity}
                        </span>
                      </td>
                      <td style={{ padding: '13px 16px', fontSize: 13, color: '#475569', fontWeight: 500, width: 160 }}>
                        {v.guideline}
                      </td>
                      <td style={{ padding: '13px 16px', width: 80, textAlign: 'right' }}>
                        <button
                          onClick={() => setSelectedIssue(v)}
                          aria-label={`View details for ${v.issue}`}
                          style={{
                            background: '#1a2240', border: 'none', borderRadius: 6, padding: '6px 14px',
                            fontSize: 12, color: '#fff', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                            transition: 'background 0.15s',
                          }}
                          onMouseEnter={e => e.currentTarget.style.background = '#2a3660'}
                          onMouseLeave={e => e.currentTarget.style.background = '#1a2240'}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  )
                })}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: 14 }}>
                      {searchQuery.trim()
                        ? `No issues match "${searchQuery}"`
                        : `No issues found for "${severityFilter}"`}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
          </div>
        </div>

        {/* BOTTOM BAR */}
        <div style={{ padding: '0 32px 32px' }}>
          <div style={{
            background: '#0f1422', borderRadius: 14, padding: '18px 28px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20,
          }}>
            <div>
              <p style={{ color: '#e2e6f0', fontSize: 18, fontWeight: 700, margin: 0 }}>
                All critical issues reviewed?
              </p>
              <p style={{ color: '#4a5a7a', fontSize: 14, margin: '5px 0 0' }}>
                Compile this audit into a shareable accessibility report.
              </p>
            </div>
            <button
              aria-label="Generate accessibility report"
              onClick={() => navigate('/report', { state: { auditId } })}
              style={{
                background: '#1D9E75', color: '#fff', border: 'none',
                borderRadius: 10, padding: '14px 30px',
                fontSize: 17, fontWeight: 700, cursor: 'pointer',
                whiteSpace: 'nowrap', flexShrink: 0, transition: 'background 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#17876a'}
              onMouseLeave={e => e.currentTarget.style.background = '#1D9E75'}
            >
              Generate Report →
            </button>
          </div>
        </div>
      </main>

      {selectedIssue && (
        <IssueDrawer issue={selectedIssue} onClose={() => setSelectedIssue(null)} />
      )}

      {showAuditPopup && (
        <AuditPopup
          auditId={auditId}
          onRefreshed={(freshReport) => setReport(freshReport)}
          onClose={() => setShowAuditPopup(false)}
        />
      )}
    </div>
  )
}
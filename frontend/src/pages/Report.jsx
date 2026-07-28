import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { getAuditFiles, getAuditId } from '../state/auditFiles'
import { getAuditReport } from '../api'
import Sidebar from '../components/Sidebar'
import UserAvatar from '../components/ui/UserAvatar'

/* ────────────────────────────────────────────────────────────────────────────
   RULE REFERENCE — same lookup used in Dashboard.jsx, sourced from
   Accessibility_Guidelines_Rules_v2.docx. Kept in sync so Rule IDs resolve
   to the same WCAG citation everywhere in the app.
   ──────────────────────────────────────────────────────────────────────────── */
const RULES = {
  R01: { guideline: 'G01', wcag: 'WCAG 4.1.2' }, R02: { guideline: 'G02', wcag: 'WCAG 1.1.1' },
  R03: { guideline: 'G03', wcag: 'WCAG 4.1.2' },  R04: { guideline: 'G04', wcag: 'WCAG 2.5.5' },
  R05: { guideline: 'G05', wcag: 'WCAG 1.3.1' },  R06: { guideline: 'G06', wcag: 'WCAG 2.1.1' },
  R07: { guideline: 'G07', wcag: 'WCAG 1.3.1' },  R08: { guideline: 'G08', wcag: 'WCAG 1.3.2' },
  R09: { guideline: 'G09', wcag: 'WCAG 1.4.3' },  R10: { guideline: 'G10', wcag: 'WCAG 1.4.4' },
  R11: { guideline: 'G11', wcag: 'WCAG 1.4.1' },  R12: { guideline: 'G12', wcag: 'WCAG 1.2.2' },
  R13: { guideline: 'G13', wcag: 'WCAG 1.2.1' },  R14: { guideline: 'G14', wcag: 'WCAG 1.3.3' },
  R15: { guideline: 'G15', wcag: 'WCAG 1.3.2' },  R16: { guideline: 'G16', wcag: 'WCAG 1.3.1' },
  R17: { guideline: 'G17', wcag: 'WCAG 2.5.5' },  R18: { guideline: 'G18', wcag: 'WCAG 2.1.1' },
  R19: { guideline: 'G19', wcag: 'WCAG 3.3.4' },  R20: { guideline: 'G20', wcag: 'WCAG 3.3.2' },
  R21: { guideline: 'G21', wcag: 'WCAG 3.3.1' },  R22: { guideline: 'G22', wcag: 'WCAG 3.3.1' },
  R23: { guideline: 'G23', wcag: 'WCAG 2.4.6' },  R24: { guideline: 'G24', wcag: 'WCAG 2.4.2' },
  R25: { guideline: 'G25', wcag: 'WCAG 2.2.2' },  R26: { guideline: 'G26', wcag: 'WCAG 2.2.1' },
  R27: { guideline: 'G27', wcag: 'WCAG 3.1.5' },  R28: { guideline: 'G28', wcag: 'WCAG 1.4.4' },
  R29: { guideline: 'G29', wcag: 'WCAG 3.1.5' },  R30: { guideline: 'G30', wcag: 'WCAG 1.1.1' },
}

// JSON severity (High/Medium/Low) → UI severity (Critical/Serious/Minor)
const SEVERITY_MAP = { High: 'Critical', Medium: 'Serious', Low: 'Minor' }

/* ── Severity visual tokens (shared language with Dashboard.jsx) ─────────── */
const SEV = {
  Critical: { color: '#7A1C1C', bg: '#fdf0ef' },
  Serious:  { color: '#7A4000', bg: '#fef6ed' },
  Minor:    { color: '#3D4043', bg: '#f4f6fb' },
}

function uiSeverity(jsonSeverity) {
  return SEVERITY_MAP[jsonSeverity] || 'Minor'
}

function severityColor(s) { return SEV[uiSeverity(s)].color }
function severityBg(s)    { return SEV[uiSeverity(s)].bg }

// Builds the three summary pills (Critical/Serious/Minor) from a violations[] array.
function buildSummaryPills(violations) {
  const counts = { Critical: 0, Serious: 0, Minor: 0 }
  violations.forEach(v => { counts[uiSeverity(v.severity)]++ })
  return [
    { label: `${counts.Critical} Critical`, color: SEV.Critical.color, bg: SEV.Critical.bg, count: counts.Critical },
    { label: `${counts.Serious} Serious`,   color: SEV.Serious.color,  bg: SEV.Serious.bg,  count: counts.Serious },
    { label: `${counts.Minor} Minor`,       color: SEV.Minor.color,    bg: SEV.Minor.bg,    count: counts.Minor },
  ]
}

// Guideline category breakdown, computed from violations[] by grouping on the guideline label.
function buildGuidelineCategories(violations) {
  const categoryMap = {}
  violations.forEach(v => {
    const label = v.guideline?.split(' — ')[1] || v.guideline || 'Uncategorized'
    categoryMap[label] = (categoryMap[label] || 0) + 1
  })
  const maxCount = Math.max(...Object.values(categoryMap), 1)
  return Object.entries(categoryMap).map(([label, count]) => ({
    label, count, pct: Math.round((count / maxCount) * 100),
  }))
}

/* ── Shared icons / spinner (same visual language as Upload/Dashboard) ───── */
const Icon = {
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
}
function Spinner({ size = 14, color = '#94a3b8' }) {
  return (
    <div style={{
      width: size, height: size, border: `2px solid ${color}`, borderTopColor: 'transparent',
      borderRadius: '50%', animation: 'spin 0.8s linear infinite', flexShrink: 0,
    }} />
  )
}

/* ── Report generation steps (mirrors the audit-processing visual language) ── */
const REPORT_STEPS = [
  { label: 'Compiling violations', pct: 35 },
  { label: 'Formatting document', pct: 70 },
  { label: 'Finalizing file', pct: 100 },
]

/* ── Processing popup shown after choosing PDF / HTML ─────────────────────── */
function GeneratingPopup({ format, onDone }) {
  const [stepIdx, setStepIdx] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
  let i = 0
  let tickTimer
  const tick = () => {
    if (i >= REPORT_STEPS.length) {
      setTimeout(onDone, 350)
      return
    }
    setStepIdx(i)
    setProgress(REPORT_STEPS[i].pct)
    i++
    tickTimer = setTimeout(tick, 550)
  }
  const t = setTimeout(tick, 300)
  return () => {
    clearTimeout(t)
    clearTimeout(tickTimer)
  }
}, [])

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(15,27,45,0.65)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20,
    }}>
      <div style={{
        background: '#fff', borderRadius: 18, width: '100%', maxWidth: 380,
        padding: '30px 28px', boxShadow: '0 24px 64px rgba(0,0,0,0.22)', textAlign: 'center',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: '50%', background: '#0f1422',
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px',
        }}>
          <Spinner size={20} color="#fff" />
        </div>
        <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 6px' }}>
          Generating {format?.toUpperCase()}&hellip;
        </p>
        <p style={{ fontSize: 14, color: '#5a6a8a', margin: '0 0 20px' }}>
          {REPORT_STEPS[stepIdx]?.label}
        </p>
        <div style={{ height: 6, background: '#f4f6fb', borderRadius: 99, overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: 99, background: '#1D9E75',
            width: `${progress}%`, transition: 'width 0.4s ease',
          }} />
        </div>
      </div>
    </div>
  )
}

/* ── Shared document body — used by both PDF and HTML previews ─────────── */
function PreviewDocument({ imgUrl, xmlText, screenshotName, xmlName, screenId, isHtml, violations, totalIssues, severityCounts, schemaVersion, xmlPath }) {
  return (
    <div style={{ padding: isHtml ? '0' : '36px 40px' }}>

      {/* Header */}
      {!isHtml && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: '#0f1422', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {Icon.check('#fff', 16)}
            </div>
            <span style={{ fontSize: 19, fontWeight: 700, color: '#0f1422' }}>Axion</span>
          </div>
          <span style={{ fontSize: 13, color: '#94a3b8' }}>Generated by Axion accessibility auditor</span>
        </div>
      )}

      <h2 style={{ fontSize: isHtml ? 28 : 26, fontWeight: 700, color: '#0f1422', margin: `0 0 ${isHtml ? 24 : 20}px` }}>
        Accessibility audit report
      </h2>

      {/* Stat tiles */}
      <div className="axion-doc-stats" style={{ display: 'grid', gap: 12, marginBottom: 26 }}>
        {[['SCREEN ID', screenId], ['TOTAL ISSUES', totalIssues], ['SCHEMA', `v${schemaVersion}`]].map(([label, value]) => (
          <div key={label} style={{ background: isHtml ? '#f0fdf8' : '#f4f6fb', border: isHtml ? '1px solid #bbf7e0' : 'none', borderRadius: 8, padding: '12px 14px' }}>
            <p style={{ fontSize: 11, color: isHtml ? '#0f6e56' : '#5a6a8a', fontWeight: 700, letterSpacing: '0.5px', margin: '0 0 4px' }}>{label}</p>
            <p style={{ fontSize: 15, fontWeight: 700, color: '#0f1422', margin: 0 }}>{value}</p>
          </div>
        ))}
        <div style={{ background: isHtml ? '#fff7ed' : '#f4f6fb', border: isHtml ? '1px solid #fed7aa' : 'none', borderRadius: 8, padding: '12px 14px' }}>
          <p style={{ fontSize: 11, color: isHtml ? '#9a3412' : '#5a6a8a', fontWeight: 700, letterSpacing: '0.5px', margin: '0 0 4px' }}>SEVERITY</p>
          <p style={{ fontSize: 13, fontWeight: 700, margin: 0, display: 'flex', gap: 8 }}>
            <span style={{ color: '#7A1C1C' }}>{severityCounts?.Critical ?? 0} crit</span>
            <span style={{ color: '#7A4000' }}>{severityCounts?.Serious ?? 0} serious</span>
            <span style={{ color: '#3D4043' }}>{severityCounts?.Minor ?? 0} minor</span>
          </p>
        </div>
      </div>

      {/* Screenshot + XML */}
      <div className="axion-doc-columns" style={{ display: 'grid', gap: 20, marginBottom: 28 }}>
        <div>
          <p style={{ fontSize: 12, fontWeight: 700, color: '#5a6a8a', letterSpacing: '0.5px', margin: '0 0 8px' }}>SCREENSHOT</p>
          <div style={{
            background: '#f4f6fb', borderRadius: 8, border: '1px solid #e2e6f0',
            minHeight: 120, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', overflow: 'hidden', padding: 8,
          }}>
            {imgUrl
              ? <img src={imgUrl} alt="Uploaded screenshot" style={{ maxWidth: '100%', maxHeight: 180, borderRadius: 6, objectFit: 'contain' }} />
              : <><span style={{ fontSize: 28 }}>🖼️</span><p style={{ fontSize: 12, color: '#5a6a8a', margin: '8px 0 0' }}>{screenshotName || 'No screenshot'}</p></>
            }
            {imgUrl && <p style={{ fontSize: 11, color: '#94a3b8', margin: '6px 0 0' }}>{screenshotName}</p>}
          </div>
        </div>
        <div>
          <p style={{ fontSize: 12, fontWeight: 700, color: '#5a6a8a', letterSpacing: '0.5px', margin: '0 0 8px' }}>UIAUTOMATOR XML</p>
          <div style={{
            background: '#0f1422', borderRadius: 8, padding: '14px 16px',
            fontFamily: 'monospace', fontSize: 11.5, color: '#a8bbd4', lineHeight: 1.7,
            maxHeight: 200, overflowY: 'auto',
          }}>
            {xmlText
              ? <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#7dd3fc', fontSize: 11 }}>{xmlText.slice(0, 800)}{xmlText.length > 800 ? '\n…' : ''}</pre>
              : <>
                  <div style={{ color: '#7dd3fc' }}>&lt;EditText id="username"<br />&nbsp;&nbsp;bounds="[32,120][400,168]" /&gt;</div>
                  <div style={{ color: '#7dd3fc', marginTop: 6 }}>&lt;ImageButton id="back"<br />&nbsp;&nbsp;bounds="[32,50][80,98]" /&gt;</div>
                </>
            }
            <p style={{ color: '#5a6a8a', margin: '8px 0 0', fontSize: 11 }}>{xmlName || xmlPath?.split('/').pop() || 'window.xml'}</p>
          </div>
        </div>
      </div>

      {/* Violations */}
      <p style={{ fontSize: 12, fontWeight: 700, color: '#5a6a8a', letterSpacing: '0.5px', margin: '0 0 12px' }}>DETECTED VIOLATIONS</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 8 }}>
        {violations.map((v, i) => (
          <div key={i} style={{
            border: `1px solid ${isHtml ? '#e2e8f0' : '#e2e6f0'}`,
            borderLeft: isHtml ? `4px solid ${v.severity === 'High' ? '#ef4444' : v.severity === 'Medium' ? '#f97316' : '#94a3b8'}` : `1px solid #e2e6f0`,
            borderRadius: 10, padding: '16px 18px',
            background: isHtml ? '#fafbff' : '#fff',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ background: severityBg(v.severity), color: severityColor(v.severity), padding: '2px 10px', borderRadius: 6, fontSize: 12, fontWeight: 700 }}>
                  {v.rule_id} · {v.severity}
                </span>
                <span style={{ fontSize: 12.5, color: '#94a3b8' }}>{v.guideline}</span>
              </div>
              <span style={{ fontSize: 12, color: '#94a3b8' }}>{v.component_id}</span>
            </div>
            <p style={{ fontSize: 15.5, fontWeight: 700, color: '#0f1422', margin: '0 0 4px' }}>{v.issue}</p>
            <p style={{ fontSize: 13.5, color: '#5a6a8a', margin: '0 0 10px', lineHeight: 1.5 }}>{v.agent_why_it_matters}</p>
            {isHtml && (
              <p style={{ fontSize: 13, color: '#475569', margin: '0 0 10px', lineHeight: 1.5 }}>
                <strong style={{ color: '#0f1422' }}>Explanation:</strong> {v.agent_explanation}
              </p>
            )}
            <div style={{ background: '#f0fdf8', borderRadius: 6, padding: '8px 12px', fontFamily: 'monospace', fontSize: 12.5, color: '#085041' }}>
              <strong>FIX</strong><br />{isHtml ? v.agent_developer_fix : v.recommendation}
            </div>
          </div>
        ))}
      </div>

      <p style={{ textAlign: 'center', fontSize: 12, color: '#94a3b8', marginTop: 24 }}>
        {isHtml ? '🌐 HTML Report' : 'Page 1 of 1'} · Generated by Axion · WCAG 2.2 AA
      </p>
    </div>
  )
}

/* ── Preview modal ─────────────────────────────────────────────────────── */
function ReportPreview({ format, screenshotFile, xmlFile, screenId, onClose, violations, totalIssues, severityCounts, schemaVersion, xmlPath }) {
  const isHtml = format === 'html'
  const [imgUrl,  setImgUrl]  = useState(null)
  const [xmlText, setXmlText] = useState('')

  useEffect(() => {
    if (!screenshotFile) return
    const url = URL.createObjectURL(screenshotFile)
    setImgUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [screenshotFile])

  useEffect(() => {
    if (!xmlFile) return
    const reader = new FileReader()
    reader.onload = e => setXmlText(e.target.result)
    reader.readAsText(xmlFile)
  }, [xmlFile])

  return (
    <div
      role="dialog" aria-modal="true" aria-labelledby="preview-title"
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: isHtml ? 'rgba(15,27,45,0.5)' : 'rgba(15,27,45,0.6)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        zIndex: 1000, padding: '32px 20px', overflowY: 'auto',
      }}
    >
      <div
        id="preview-title"
        onClick={e => e.stopPropagation()}
        style={{
          background: isHtml ? '#f4f6fb' : '#fff',
          borderRadius: 14, width: '100%', maxWidth: 760,
          boxShadow: '0 24px 64px rgba(0,0,0,0.3)', overflow: 'hidden',
        }}
      >
        {/* Toolbar */}
        <div style={{
          background: isHtml ? '#1a2240' : '#0f1422',
          padding: '12px 20px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {isHtml && (
              <div style={{ display: 'flex', gap: 6 }}>
                <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
                <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
                <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
              </div>
            )}
            <span style={{ color: isHtml ? '#94a3b8' : '#fff', fontSize: 13, fontFamily: isHtml ? 'monospace' : 'inherit' }}>
              {isHtml ? `axion-report-${screenId}.html` : `Preview · PDF`}
            </span>
          </div>
          <button onClick={onClose} aria-label="Close preview" style={{
            background: '#1e2d42', color: '#fff', border: 'none', borderRadius: 6,
            padding: '6px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>
            Close
          </button>
        </div>

        {/* HTML browser address bar */}
        {isHtml && (
          <div style={{ background: '#e8edf5', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 8, borderBottom: '1px solid #dde2f0' }}>
            <div style={{ flex: 1, background: '#fff', borderRadius: 6, padding: '5px 14px', fontSize: 12, color: '#475569', fontFamily: 'monospace', border: '1px solid #e2e8f0' }}>
              axion://report/{screenId}
            </div>
          </div>
        )}

        {/* Document body */}
        <div style={{ padding: isHtml ? '32px 40px' : '36px 40px', background: isHtml ? '#fff' : '#fff' }}>
          {isHtml && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, paddingBottom: 16, borderBottom: '2px solid #1a2240' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: '#1a2240', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {Icon.check('#1D9E75', 16)}
                </div>
                <span style={{ fontSize: 19, fontWeight: 700, color: '#0f1422' }}>Axion</span>
              </div>
              <span style={{ fontSize: 13, color: '#94a3b8' }}>Accessibility audit report · HTML</span>
            </div>
          )}
          <PreviewDocument
            imgUrl={imgUrl}
            xmlText={xmlText}
            screenshotName={screenshotFile?.name}
            xmlName={xmlFile?.name}
            screenId={screenId}
            isHtml={isHtml}
            violations={violations}
            totalIssues={totalIssues}
            severityCounts={severityCounts}
            schemaVersion={schemaVersion}
            xmlPath={xmlPath}
          />
        </div>
      </div>
    </div>
  )
}

export default function Report() {
  const navigate = useNavigate()
  const location = useLocation()
  const { screenshot: screenshotFile, xml: xmlFile } = getAuditFiles()

  // audit_id can arrive via route state (fresh navigation from Dashboard)
  // or the shared store (getAuditId) if the page was refreshed / reached another way.
  const auditId = location.state?.auditId || getAuditId()

  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)

  const [showConfirm, setShowConfirm] = useState(false)
  const [flowStep, setFlowStep] = useState('idle') // idle | processing | preview
  const [format, setFormat] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

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
        if (!cancelled) { setReport(data); setLoading(false) }
      })
      .catch(err => {
        if (!cancelled) { setLoadError(err.message || 'Could not load report.'); setLoading(false) }
      })
    return () => { cancelled = true }
  }, [auditId])

  const violations = report?.violations || []
  const totalIssues = violations.length

  // Use the actual backend screen_id first, then the uploaded screenshot's
  // filename, falling back to a generic label if neither is available.
  const screenId = report?.screen_id
    || (screenshotFile?.name ? screenshotFile.name.replace(/\.[^/.]+$/, '') : 'screen')

  const summaryPills = buildSummaryPills(violations)
  const severityCounts = summaryPills.reduce((acc, p) => {
    acc[p.label.split(' ')[1]] = p.count
    return acc
  }, {})
  const guidelineCategories = buildGuidelineCategories(violations)

  const filteredViolations = violations.filter(v => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return true
    return [v.rule_id, v.issue, v.class, v.component_id, v.guideline]
      .some(field => field?.toLowerCase().includes(q))
  })

  function handleDownloadClick() {
    setShowConfirm(true)
  }

  function handleChooseFormat(fmt) {
    setFormat(fmt)
    setShowConfirm(false)
    setFlowStep('processing')
  }

  function handleProcessingDone() {
    setFlowStep('preview')
  }

  function handleClosePreview() {
    setFlowStep('idle')
    setFormat(null)
  }

  // ── Loading state ──────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
        <Sidebar activePage="report" />
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
        <Sidebar activePage="report" />
        <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
          <div style={{ textAlign: 'center', maxWidth: 420 }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              {Icon.alert('#ef4444', 26)}
            </div>
            <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 8px' }}>Couldn't load report</p>
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
      <Sidebar activePage="report" />

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }

        .axion-topbar {
          padding: 16px 32px;
        }
        .axion-topbar-actions {
          display: flex; align-items: center; gap: 14px;
        }
        .axion-search-input {
          width: 210px;
        }
        .axion-heading-row {
          flex-wrap: wrap;
          gap: 16px;
        }
        .axion-score-card {
          flex-wrap: wrap;
        }
        .axion-doc-stats {
          grid-template-columns: repeat(4, 1fr);
        }
        .axion-doc-columns {
          grid-template-columns: 1fr 1.4fr;
        }
        .axion-format-modal {
          width: 420px;
        }

        @media (max-width: 640px) {
          .axion-topbar {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            padding: 16px 20px;
          }
          .axion-topbar-actions {
            width: 100%;
          }
          .axion-search-input {
            width: 100%;
          }
          .axion-doc-stats {
            grid-template-columns: 1fr 1fr;
          }
          .axion-doc-columns {
            grid-template-columns: 1fr;
          }
          .axion-format-modal {
            width: 100%;
            max-width: 420px;
          }
        }
      `}</style>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        aria-label="Accessibility Audit Report">

        {/* ── TOPBAR ── */}
        <div className="axion-topbar" style={{
          background: '#fff', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '0.5px solid #e2e6f0',
        }}>
          <div>
            <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>Workspace</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: '#1a2240', margin: 0 }}>Audit Report</p>
          </div>
          <div className="axion-topbar-actions">
            <input
              type="search" placeholder="Search issues, rule ID…" aria-label="Search violations in this report"
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

        {/* ── CONTENT ── */}
        <div style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Report header */}
          <div className="axion-heading-row" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <span style={{
                background: '#e8f5f0', color: '#0f6e56', fontSize: 13,
                fontWeight: 700, padding: '4px 12px', borderRadius: 4, letterSpacing: '0.5px',
              }}>
                AUDIT REPORT
              </span>
              <h1 style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: '10px 0 10px' }}>
                Accessibility Audit Report
              </h1>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 14, color: '#5a6a8a' }}>
                  <span aria-hidden="true">📋 </span>Screen ID: {screenId}
                </span>
                <span style={{ fontSize: 14, color: '#5a6a8a' }}>
                  <span aria-hidden="true">🖥 </span>Total issues: {totalIssues}
                </span>
              </div>
            </div>

            <button
              aria-label="Start a new audit"
              onClick={() => navigate('/upload')}
              style={{
                background: '#1a2240', color: '#fff', border: 'none',
                borderRadius: 8, padding: '12px 22px', fontSize: 15,
                fontWeight: 700, cursor: 'pointer', marginTop: 4,
                display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
              }}
            >
              <span aria-hidden="true" style={{ fontSize: 16 }}>+</span> New Audit
            </button>
          </div>

          {/* ── SCORE + SUMMARY CARD ── */}
          <div className="axion-score-card" style={{
            background: '#fff', borderRadius: 14, border: '0.5px solid #e2e6f0',
            padding: '28px 32px', display: 'flex', alignItems: 'center', gap: 32,
          }}>
            <div
              role="img"
              aria-label={`Total issues detected: ${totalIssues}`}
              style={{ position: 'relative', width: 90, height: 90, flexShrink: 0 }}
            >
              <svg width="90" height="90" viewBox="0 0 90 90" aria-hidden="true">
                <circle cx="45" cy="45" r="38" fill="none" stroke="#e2e6f0" strokeWidth="8" />
                <circle cx="45" cy="45" r="38" fill="none" stroke="#1D9E75" strokeWidth="8"
                  strokeDasharray="238.8"
                  strokeDashoffset={238.8 - (238.8 * Math.min(totalIssues, 10)) / 10}
                  strokeLinecap="round" transform="rotate(-90 45 45)" />
              </svg>
              <div aria-hidden="true" style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ fontSize: 24, fontWeight: 700, color: '#0f1422' }}>{totalIssues}</span>
                <span style={{ fontSize: 10, color: '#5a6a8a', fontWeight: 600 }}>ISSUES</span>
              </div>
            </div>

            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 6px' }}>
                This audit reviewed {screenId} and surfaced {totalIssues} issue{totalIssues !== 1 ? 's' : ''}
              </p>
              <p style={{ fontSize: 15, color: '#5a6a8a', margin: '0 0 14px', lineHeight: 1.6 }}>
                Most findings relate to missing accessible labels and unlabeled input fields.
                Resolving the High and Medium severity issues below moves this app closer to WCAG 2.2 AA conformance.
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {summaryPills.map(({ label, color, bg }) => (
                  <span key={label} style={{
                    background: bg, color,
                    padding: '5px 14px', borderRadius: 20,
                    fontSize: 14, fontWeight: 700,
                  }}>
                    <span aria-hidden="true">● </span>{label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* ── ISSUES BY GUIDELINE CATEGORY ── */}
          <div style={{
            background: '#fff', borderRadius: 14,
            border: '0.5px solid #e2e6f0', padding: 24,
          }}>
            <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 20px' }}>
              Issues by Guideline Category
            </p>
            {guidelineCategories.map(({ label, count, pct }) => (
              <div key={label} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 15, color: '#0f1422', fontWeight: 500 }}>{label}</span>
                  <span style={{ fontSize: 15, color: '#5a6a8a', fontWeight: 600 }}>{count}</span>
                </div>
                <div
                  role="progressbar"
                  aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
                  aria-label={`${label}: ${count} issues (${pct}%)`}
                  style={{ background: '#f4f6fb', borderRadius: 4, height: 8 }}
                >
                  <div style={{ width: `${pct}%`, background: '#1a2240', borderRadius: 4, height: 8 }} />
                </div>
              </div>
            ))}
          </div>

          {/* ── TOP PRIORITY ISSUES ── */}
          <div style={{
            background: '#fff', borderRadius: 14,
            border: '0.5px solid #e2e6f0', padding: 24,
          }}>
            <p style={{ fontSize: 17, fontWeight: 700, color: '#0f1422', margin: '0 0 20px' }}>
              Top Priority Issues
            </p>
            {filteredViolations.length === 0 && (
              <p style={{ padding: '24px 0', textAlign: 'center', color: '#94a3b8', fontSize: 14 }}>
                {totalIssues === 0
                  ? 'No issues found — this screen looks clean! 🎉'
                  : `No issues match "${searchQuery}"`}
              </p>
            )}
            {filteredViolations.map((v, i) => {
              const rule = RULES[v.rule_id]
              const sev = uiSeverity(v.severity)
              return (
                <div key={i} style={{
                  padding: '18px 0',
                  borderBottom: i < filteredViolations.length - 1 ? '0.5px solid #f0f2f8' : 'none',
                }}>
                  <div style={{
                    display: 'flex', alignItems: 'flex-start',
                    justifyContent: 'space-between', gap: 16,
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
                        <span style={{
                          background: severityBg(v.severity),
                          color: severityColor(v.severity),
                          padding: '3px 12px', borderRadius: 20,
                          fontSize: 13, fontWeight: 700,
                        }}>
                          {v.rule_id} · {sev}
                        </span>
                        <span style={{ fontSize: 13, color: '#5a6a8a' }}>
                          {screenId}.png · {v.class.split('.').pop()} · {v.component_id}
                        </span>
                      </div>
                      <p style={{ fontSize: 16, fontWeight: 700, color: '#0f1422', margin: '0 0 4px' }}>
                        {v.issue}
                      </p>
                      <p style={{ fontSize: 13.5, color: '#5a6a8a', margin: '0 0 8px', lineHeight: 1.5 }}>
                        {v.agent_explanation}
                      </p>
                      <p style={{
                        fontSize: 14, color: '#085041', margin: 0,
                        background: '#f0fdf8', padding: '8px 14px', borderRadius: 6,
                        fontFamily: 'monospace',
                      }}>
                        Fix: {v.agent_developer_fix}
                      </p>
                    </div>
                    <span style={{ fontSize: 13, color: '#5a6a8a', flexShrink: 0 }}>
                      {rule?.wcag || ''}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ── BOTTOM BAR ── */}
        <div style={{ padding: '18px 32px', backgroundColor: '#f4f6fb' }}>
          <div style={{
            background: '#0f1422', borderRadius: 14, padding: '18px 28px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div>
              <p style={{ color: '#e2e6f0', fontSize: 18, fontWeight: 700, margin: 0 }}>
                Ready to share this report?
              </p>
              <p style={{ color: '#4a5a7a', fontSize: 14, margin: '5px 0 0' }}>
                Export as PDF or HTML and send to your development team.
              </p>
            </div>
            <button
              aria-label="Download accessibility report"
              onClick={handleDownloadClick}
              style={{
                background: '#1D9E75', color: '#fff', border: 'none',
                borderRadius: 10, padding: '14px 30px', fontSize: 17,
                fontWeight: 700, cursor: 'pointer',
              }}
            >
              Download Report →
            </button>
          </div>
        </div>
      </main>

      {/* ── DOWNLOAD REPORT — FORMAT CHOICE POPUP ── */}
      {showConfirm && (
        <div
          role="dialog" aria-modal="true"
          aria-labelledby="confirm-title" aria-describedby="confirm-desc"
          onClick={() => setShowConfirm(false)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            className="axion-format-modal"
            style={{
              background: '#fff', borderRadius: 16, padding: '28px 32px',
              boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
              display: 'flex', flexDirection: 'column', gap: 18,
            }}
          >
            <div>
              <p id="confirm-title" style={{ fontSize: 20, fontWeight: 700, color: '#0f1422', margin: '0 0 6px' }}>
                Download Report
              </p>
              <p id="confirm-desc" style={{ fontSize: 14, color: '#5a6a8a', margin: 0, lineHeight: 1.6 }}>
                Choose a format to download the full accessibility audit report for {screenId}.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                onClick={() => handleChooseFormat('pdf')}
                aria-label="Download report as PDF"
                style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  background: '#f8fafc', border: '1.5px solid #e2e6f0', borderRadius: 10,
                  padding: '14px 16px', cursor: 'pointer', textAlign: 'left',
                  fontFamily: 'inherit', transition: 'border-color 0.15s, background 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = '#1a2240'; e.currentTarget.style.background = '#f1f5f9' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = '#e2e6f0'; e.currentTarget.style.background = '#f8fafc' }}
              >
                <span style={{
                  width: 38, height: 38, borderRadius: 8, background: '#1a2240',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0,
                }}>
                  PDF
                </span>
                <span>
                  <p style={{ fontSize: 14.5, fontWeight: 700, color: '#0f1422', margin: 0 }}>
                    Download as PDF
                  </p>
                  <p style={{ fontSize: 12.5, color: '#5a6a8a', margin: '2px 0 0' }}>
                    Best for printing or sharing as-is
                  </p>
                </span>
              </button>

              <button
                onClick={() => handleChooseFormat('html')}
                aria-label="Download report as HTML"
                style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  background: '#f8fafc', border: '1.5px solid #e2e6f0', borderRadius: 10,
                  padding: '14px 16px', cursor: 'pointer', textAlign: 'left',
                  fontFamily: 'inherit', transition: 'border-color 0.15s, background 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = '#1D9E75'; e.currentTarget.style.background = '#f0fdf8' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = '#e2e6f0'; e.currentTarget.style.background = '#f8fafc' }}
              >
                <span style={{
                  width: 38, height: 38, borderRadius: 8, background: '#1D9E75',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0,
                }}>
                  HTML
                </span>
                <span>
                  <p style={{ fontSize: 14.5, fontWeight: 700, color: '#0f1422', margin: 0 }}>
                    Download as HTML
                  </p>
                  <p style={{ fontSize: 12.5, color: '#5a6a8a', margin: '2px 0 0' }}>
                    Best for sending to your dev team to browse
                  </p>
                </span>
              </button>
            </div>

            <button
              onClick={() => setShowConfirm(false)}
              style={{
                background: 'transparent', color: '#5a6a8a', border: 'none',
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
                padding: '4px 0', textAlign: 'center', fontFamily: 'inherit',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* ── PROCESSING STEPS ── */}
      {flowStep === 'processing' && (
        <GeneratingPopup format={format} onDone={handleProcessingDone} />
      )}

      {/* ── PREVIEW ── */}
      {flowStep === 'preview' && (
        <ReportPreview
          format={format}
          screenshotFile={screenshotFile}
          xmlFile={xmlFile}
          screenId={screenId}
          onClose={handleClosePreview}
          violations={violations}
          totalIssues={totalIssues}
          severityCounts={severityCounts}
          schemaVersion={report?.schema_version || '1.0'}
          xmlPath={report?.xml_path}
        />
      )}
    </div>
  )
}
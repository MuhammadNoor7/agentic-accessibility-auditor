import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

/* ────────────────────────────────────────────────────────────────────────────
   MOCK audit history — replace with a real fetch('/api/audits') once the
   backend persists past runs. Shape mirrors what the Upload/Dashboard flow
   would produce per screen.
   ──────────────────────────────────────────────────────────────────────────── */
const AUDITS = [
  { id: 'screen_008', high: 2, med: 0, low: 0, date: 'Today' },
  { id: 'screen_007', high: 3, med: 2, low: 1, date: 'Jun 30' },
  { id: 'screen_006', high: 4, med: 0, low: 0, date: 'Jun 29' },
  { id: 'screen_005', high: 2, med: 4, low: 2, date: 'Jun 28' },
  { id: 'screen_004', high: 1, med: 1, low: 1, date: 'Jun 27' },
  { id: 'screen_003', high: 3, med: 2, low: 0, date: 'Jun 26' },
  { id: 'screen_002', high: 2, med: 1, low: 1, date: 'Jun 25' },
  { id: 'screen_001', high: 2, med: 0, low: 0, date: 'Jun 14' },
].map(a => ({ ...a, total: a.high + a.med + a.low }))

const totalIssuesFound = AUDITS.reduce((sum, a) => sum + a.total, 0)
const mostRecent = AUDITS[0]

const SEV_DOT = { high: '#f97316', med: '#94a3b8', low: '#cbd5e1' }
const SEV_LABEL = { high: 'high', med: 'med', low: 'low' }

export default function AuditHistory() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [severityFilter, setSeverityFilter] = useState('All')
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '')

  useEffect(() => {
    const q = searchParams.get('q')
    if (q) setSearchQuery(q)
  }, [searchParams])

  const filtered = AUDITS
    .filter(a => severityFilter === 'All' || a[severityFilter.toLowerCase()] > 0)
    .filter(a => a.id.toLowerCase().includes(searchQuery.trim().toLowerCase()))

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f6fb' }}>
      <Sidebar activePage="records" />

      <style>{`
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
        .axion-stat-grid {
          grid-template-columns: repeat(4, 1fr);
        }
        .axion-filter-row {
          flex-wrap: wrap;
          gap: 10px;
        }
        .axion-table-scroll {
          overflow-x: auto;
        }
        .axion-bottom-bar {
          flex-wrap: wrap;
        }

        @media (max-width: 900px) {
          .axion-stat-grid {
            grid-template-columns: 1fr 1fr;
          }
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
          .axion-heading-row {
            flex-direction: column;
            align-items: stretch;
          }
          .axion-stat-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }} aria-label="Audit History">

        {/* ── TOPBAR ── */}
        <div className="axion-topbar" style={{
          background: '#fff', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '0.5px solid #e2e6f0',
        }}>
          <div>
            <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>Workspace</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: '#1a2240', margin: 0 }}>Audit History</p>
          </div>
          <div className="axion-topbar-actions">
            <input
              type="search" placeholder="Search by screen ID…" aria-label="Search audits by screen ID"
              className="axion-search-input"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                background: '#f4f6fb', border: '0.5px solid #dde2f0',
                borderRadius: 6, padding: '9px 16px', fontSize: 15,
                color: '#1a2240',
              }}
            />
            <div
              role="img" aria-label="User: Ayesha Naveed" title="Ayesha Naveed"
              style={{
                width: 42, height: 42, borderRadius: '50%',
                background: '#1D9E75', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: '#fff', fontSize: 15, fontWeight: 700,
              }}
            >
              <span aria-hidden="true">AN</span>
            </div>
          </div>
        </div>

        {/* ── CONTENT ── */}
        <div style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Heading row */}
          <div className="axion-heading-row" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <span style={{
                background: '#e8f5f0', color: '#0f6e56', fontSize: 13,
                fontWeight: 700, padding: '4px 12px', borderRadius: 4, letterSpacing: '0.5px',
              }}>
                AUDIT RECORDS
              </span>
              <h1 style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: '10px 0 4px' }}>
                Audit History
              </h1>
              <p style={{ fontSize: 15, color: '#5a6a8a', margin: 0 }}>
                All past accessibility audits linked to your account.
              </p>
            </div>
            <button
              onClick={() => navigate('/upload')}
              aria-label="Start a new audit"
              style={{
                background: '#1a2240', color: '#fff', border: 'none',
                borderRadius: 8, padding: '12px 22px', fontSize: 15,
                fontWeight: 600, cursor: 'pointer', marginTop: 4,
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              + New Audit
            </button>
          </div>

          {/* STAT CARDS */}
          <div className="axion-stat-grid" style={{ display: 'grid', gap: 14 }}>
            <div style={{ background: '#fff', border: '0.5px solid #e2e6f0', borderRadius: 14, padding: '18px 20px' }}>
              <p style={{ fontSize: 11, color: '#5a6a8a', fontWeight: 700, letterSpacing: '0.6px', textTransform: 'uppercase', margin: '0 0 8px' }}>Total audits</p>
              <p style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: 0 }}>{AUDITS.length}</p>
            </div>
            <div style={{ background: '#fff', border: '0.5px solid #e2e6f0', borderRadius: 14, padding: '18px 20px' }}>
              <p style={{ fontSize: 11, color: '#5a6a8a', fontWeight: 700, letterSpacing: '0.6px', textTransform: 'uppercase', margin: '0 0 8px' }}>Screens audited</p>
              <p style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: 0 }}>{AUDITS.length}</p>
            </div>
            <div style={{ background: '#fff', border: '0.5px solid #e2e6f0', borderRadius: 14, padding: '18px 20px' }}>
              <p style={{ fontSize: 11, color: '#5a6a8a', fontWeight: 700, letterSpacing: '0.6px', textTransform: 'uppercase', margin: '0 0 8px' }}>Issues found</p>
              <p style={{ fontSize: 30, fontWeight: 700, color: '#0f1422', margin: 0 }}>{totalIssuesFound}</p>
            </div>
            <div style={{ background: '#f0fdf8', border: '1px solid #6ee7b7', borderRadius: 14, padding: '18px 20px' }}>
              <p style={{ fontSize: 11, color: '#0f6e56', fontWeight: 700, letterSpacing: '0.6px', textTransform: 'uppercase', margin: '0 0 8px' }}>Most recent</p>
              <p style={{ fontSize: 18, fontWeight: 700, color: '#0f1422', margin: '0 0 2px' }}>{mostRecent.id}</p>
              <p style={{ fontSize: 12.5, color: '#0f6e56', margin: 0 }}>Audited {mostRecent.date === 'Today' ? 'today' : mostRecent.date}</p>
            </div>
          </div>

          {/* Filter row */}
          <div className="axion-filter-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <select
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
              aria-label="Filter by severity"
              style={{
                fontSize: 13, padding: '9px 16px', border: '1.5px solid #94a3b8',
                borderRadius: 8, color: '#1a2240', background: '#fff', cursor: 'pointer', fontWeight: 600,
              }}
            >
              <option value="All">All severities</option>
              <option value="High">Has high severity</option>
              <option value="Med">Has medium severity</option>
              <option value="Low">Has low severity</option>
            </select>
            <span style={{ fontSize: 13, color: '#94a3b8' }}>{filtered.length} records</span>
          </div>

          {/* TABLE */}
          <div style={{ background: '#fff', borderRadius: 14, border: '0.5px solid #e2e6f0', overflow: 'hidden' }}>
            <div className="axion-table-scroll">
            <table style={{ width: '100%', borderCollapse: 'collapse' }} aria-label="Audit history records">
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  {['#', 'Screen ID', 'File paths', 'Severity', 'Issues', 'Date', ''].map(h => (
                    <th key={h} scope="col" style={{
                      padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700,
                      color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.6px',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((a, i) => (
                  <tr key={a.id} style={{ borderTop: '0.5px solid #f0f2f8' }}>
                    <td style={{ padding: '13px 16px', fontSize: 13, color: '#94a3b8' }}>{i + 1}</td>
                    <td style={{ padding: '13px 16px', fontSize: 15, fontWeight: 700, color: '#0f1422' }}>{a.id}</td>
                    <td style={{ padding: '13px 16px', fontSize: 12.5, color: '#94a3b8', lineHeight: 1.6 }}>
                      data/screenshots/{a.id}.png<br />
                      data/xml/window_{a.id.split('_')[1]}.xml
                    </td>
                    <td style={{ padding: '13px 16px' }}>
                      <div style={{ display: 'flex', gap: 10, fontSize: 12.5, fontWeight: 600 }}>
                        {a.high > 0 && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#7A4000' }}>
                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: SEV_DOT.high }} aria-hidden="true" />
                            {a.high} high
                          </span>
                        )}
                        {a.med > 0 && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#475569' }}>
                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: SEV_DOT.med }} aria-hidden="true" />
                            {a.med} med
                          </span>
                        )}
                        {a.low > 0 && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#94a3b8' }}>
                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: SEV_DOT.low }} aria-hidden="true" />
                            {a.low} low
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '13px 16px', fontSize: 14, fontWeight: 600, color: '#0f1422' }}>{a.total} issues</td>
                    <td style={{ padding: '13px 16px', fontSize: 13, color: '#5a6a8a' }}>{a.date}</td>
                    <td style={{ padding: '13px 16px', textAlign: 'right' }}>
                      <button
                        onClick={() => navigate('/report')}
                        aria-label={`View report for ${a.id}`}
                        style={{
                          background: '#1a2240', border: 'none', borderRadius: 6, padding: '6px 16px',
                          fontSize: 12, color: '#fff', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: 14 }}>
                      {searchQuery.trim()
                        ? `No audits match "${searchQuery}".`
                        : 'No audits match this filter.'}
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
          <div className="axion-bottom-bar" style={{
            background: '#0f1422', borderRadius: 14, padding: '18px 28px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20,
          }}>
            <div>
              <p style={{ color: '#e2e6f0', fontSize: 18, fontWeight: 700, margin: 0 }}>
                Ready to start a new audit?
              </p>
              <p style={{ color: '#4a5a7a', fontSize: 14, margin: '5px 0 0' }}>
                Upload a new screenshot and XML pair to begin.
              </p>
            </div>
            <button
              onClick={() => navigate('/upload')}
              aria-label="Start a new audit"
              style={{
                background: '#1D9E75', color: '#fff', border: 'none',
                borderRadius: 10, padding: '14px 30px',
                fontSize: 17, fontWeight: 700, cursor: 'pointer',
                whiteSpace: 'nowrap', flexShrink: 0,
              }}
            >
              New Audit →
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
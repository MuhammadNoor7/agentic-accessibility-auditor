import { NavLink } from 'react-router-dom'

const navItems = [
  {
    key: 'upload',
    label: 'Upload',
    to: '/upload',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8fa3c4" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 15V4M12 4L8.5 7.5M12 4l3.5 3.5" />
        <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
      </svg>
    ),
  },
  {
    key: 'dashboard',
    label: 'Dashboard',
    to: '/dashboard',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="13" width="4.5" height="8" rx="1" fill="#ef4444" />
        <rect x="9.5" y="8" width="4.5" height="13" rx="1" fill="#1D9E75" />
        <rect x="16" y="4" width="4.5" height="17" rx="1" fill="#3b82f6" />
      </svg>
    ),
  },
  {
    key: 'report',
    label: 'Reports',
    to: '/report',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2.5H7a2 2 0 00-2 2v15a2 2 0 002 2h10a2 2 0 002-2V8.5L14 2.5z" />
        <path d="M13.5 2.5V8H19" />
        <path d="M8.5 13h7M8.5 16.5h7M8.5 9.5h3" />
      </svg>
    ),
  },
  {
    key: 'records',
    label: 'Records',
    to: '/audit-history',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8fa3c4" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7.5V12l2.5 1.5" />
      </svg>
    ),
  },
]

export default function Sidebar({ activePage }) {
  return (
    <aside style={{
      width: 240, flexShrink: 0, background: '#0f1422',
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      padding: '24px 0', minHeight: '100vh',
    }}>
      <div>
        <div style={{ padding: '0 20px', marginBottom: 36 }}>
          <p style={{ color: '#ffffff', fontSize: 20, fontWeight: 700, margin: 0 }}>Axion</p>
          <p style={{ color: '#5a6a8a', fontSize: 13, margin: '2px 0 0' }}>Accessibility Auditor</p>
        </div>

        <nav aria-label="Main navigation" style={{ padding: '0 12px' }}>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {navItems.map(({ key, label, to, icon }) => {
              const isActive = activePage === key
              return (
                <li key={key}>
                  <NavLink to={to} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    minHeight: 44, padding: '0 12px', borderRadius: 8,
                    fontSize: 14, fontWeight: isActive ? 600 : 400,
                    textDecoration: 'none',
                    color: isActive ? '#ffffff' : '#8fa3c4',
                    background: isActive ? '#1a2240' : 'transparent',
                    borderLeft: isActive ? '3px solid #1D9E75' : '3px solid transparent',
                    transition: 'background 0.15s, color 0.15s',
                  }}>
                    {icon}
                    {label}
                  </NavLink>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>

      <div style={{
        margin: '0 16px', background: '#122a22',
        border: '1px solid #1D9E75', borderRadius: 10, padding: '14px 16px',
      }}>
        <p style={{ color: '#1D9E75', fontSize: 13, fontWeight: 700, margin: 0 }}>WCAG AA Engine</p>
        <p style={{ color: '#8fa3c4', fontSize: 12, margin: '5px 0 0', lineHeight: 1.5 }}>
          Audits run against WCAG 2.2 AA criteria.
        </p>
      </div>
    </aside>
  )
}
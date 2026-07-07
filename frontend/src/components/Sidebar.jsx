import { useState, useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import logoMark from '../assets/axion-logo-mark.png'

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
        <rect x="3" y="13" width="4.5" height="8" rx="1" fill="#8fa3c4" />
        <rect x="9.5" y="8" width="4.5" height="13" rx="1" fill="#8fa3c4" opacity="0.75" />
        <rect x="16" y="4" width="4.5" height="17" rx="1" fill="#8fa3c4" opacity="0.5" />
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
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  // Lock background scroll while the mobile drawer is open
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  // Close the drawer automatically if the viewport grows back to desktop size
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) setOpen(false)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <>
      <style>{`
        .axion-sidebar {
          width: 240px;
          flex-shrink: 0;
        }
        .axion-hamburger {
          display: none;
        }
        .axion-sidebar-backdrop {
          display: none;
        }

        @media (max-width: 767px) {
          .axion-sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            z-index: 1100;
            transform: translateX(-100%);
            transition: transform 0.25s ease;
          }
          .axion-sidebar.is-open {
            transform: translateX(0);
          }
          .axion-hamburger {
            display: flex;
          }
          .axion-sidebar-backdrop.is-open {
            display: block;
          }
        }
      `}</style>

      {/* Hamburger toggle — visible only below 768px, fixed so it overlays any page's topbar */}
      <button
        className="axion-hamburger"
        onClick={() => setOpen(true)}
        aria-label="Open navigation menu"
        aria-expanded={open}
        style={{
          position: 'fixed', top: 14, left: 14, zIndex: 1050,
          width: 42, height: 42, borderRadius: 10,
          background: '#0f1422', border: 'none',
          alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Backdrop — closes the drawer when tapped */}
      <div
        className={`axion-sidebar-backdrop ${open ? 'is-open' : ''}`}
        onClick={() => setOpen(false)}
        aria-hidden="true"
        style={{
          position: 'fixed', inset: 0, background: 'rgba(15,20,34,0.55)', zIndex: 1090,
        }}
      />

      <aside
        className={`axion-sidebar ${open ? 'is-open' : ''}`}
        style={{
          background: '#0f1422',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          padding: '24px 0', minHeight: '100vh',
        }}
      >
        <div>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 16px 20px', gap: 10,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <img src={logoMark} alt="" aria-hidden="true" width={50} height={50} style={{ width: 50, height: 50, flexShrink: 0 }} />
              <div>
                <p style={{ color: '#ffffff', fontSize: 20, fontWeight: 700, margin: 0 }}>Axion</p>
                <p style={{ color: '#5a6a8a', fontSize: 13, margin: '2px 0 0' }}>Accessibility Auditor</p>
              </div>
            </div>
            {/* Close button — only rendered inside the mobile drawer */}
            <button
              className="axion-hamburger"
              onClick={() => setOpen(false)}
              aria-label="Close navigation menu"
              style={{
                width: 32, height: 32, borderRadius: 8, background: '#1a2240',
                border: 'none', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8fa3c4" strokeWidth="2" strokeLinecap="round">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <nav aria-label="Main navigation" style={{ padding: '0 12px' }}>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {navItems.map(({ key, label, to, icon }) => {
                const isActive = activePage === key
                return (
                  <li key={key}>
                    <NavLink
                      to={to}
                      onClick={() => setOpen(false)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        minHeight: 44, padding: '0 12px', borderRadius: 8,
                        fontSize: 14, fontWeight: isActive ? 600 : 400,
                        textDecoration: 'none',
                        color: isActive ? '#ffffff' : '#8fa3c4',
                        background: isActive ? '#1a2240' : 'transparent',
                        borderLeft: isActive ? '3px solid #1D9E75' : '3px solid transparent',
                        transition: 'background 0.15s, color 0.15s',
                      }}
                    >
                      {icon}
                      {label}
                    </NavLink>
                  </li>
                )
              })}
            </ul>
          </nav>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <button
            onClick={() => navigate('/login')}
            aria-label="Log out"
            style={{
              margin: '0 16px', display: 'flex', alignItems: 'center', gap: 10,
              background: 'transparent', border: '1px solid #2a3a52', borderRadius: 8,
              padding: '10px 14px', color: '#8fa3c4', fontSize: 14, fontWeight: 500,
              cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.15s, color 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = '#1a2240'; e.currentTarget.style.color = '#fff' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#8fa3c4' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Log out
          </button>

          <div style={{
            margin: '0 16px', background: '#122a22',
            border: '1px solid #1D9E75', borderRadius: 10, padding: '14px 16px',
          }}>
            <p style={{ color: '#1D9E75', fontSize: 13, fontWeight: 700, margin: 0 }}>WCAG AA Engine</p>
            <p style={{ color: '#8fa3c4', fontSize: 12, margin: '5px 0 0', lineHeight: 1.5 }}>
              Audits run against WCAG 2.2 AA criteria.
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}
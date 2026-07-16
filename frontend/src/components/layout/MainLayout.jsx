import { NavLink } from 'react-router-dom';
import Logo from '../ui/Logo';
import UserAvatar from '../ui/UserAvatar';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/upload', label: 'Upload', icon: UploadIcon },
  { to: '/audit-history', label: 'Audit History', icon: HistoryIcon },
];

function DashboardIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" {...props}>
      <rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="11" y="2.5" width="6.5" height="6.5" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="2.5" y="11" width="6.5" height="6.5" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="11" y="11" width="6.5" height="6.5" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
function UploadIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" {...props}>
      <path d="M10 13V3M10 3l-4 4M10 3l4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 13v2.5A1.5 1.5 0 004.5 17h11a1.5 1.5 0 001.5-1.5V13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function HistoryIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" {...props}>
      <circle cx="10" cy="10.5" r="7" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 6.5V10.5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6.5 2.5L4 4.8M13.5 2.5L16 4.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export default function MainLayout({ title, subtitle, actions, children }) {
  return (
    <div className="min-h-screen flex bg-[var(--color-page-bg)]">
      {/* Sidebar */}
      <aside className="hidden md:flex md:w-64 shrink-0 bg-[var(--color-navy)] flex-col justify-between px-5 py-6">
        <div>
          <div className="mb-9 px-1">
            <Logo light size="sm" align="left" showTagline={false} />
          </div>
          <nav aria-label="Main navigation">
            <ul className="space-y-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 min-h-[48px] px-3.5 rounded-lg text-[15px] font-medium transition-colors
                       focus-visible:outline-3 focus-visible:outline-[var(--color-green)]
                       ${isActive
                         ? 'bg-[var(--color-navy-button)] text-white'
                         : 'text-[var(--color-light-gray-text)] hover:bg-[var(--color-navy-button)] hover:text-white'}`
                    }
                  >
                    <Icon aria-hidden="true" />
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <NavLink
          to="/login"
          className="flex items-center gap-3 min-h-[48px] px-3.5 rounded-lg text-[15px] font-medium text-[var(--color-light-gray-text)] hover:bg-[var(--color-navy-button)] hover:text-white focus-visible:outline-3 focus-visible:outline-[var(--color-green)]"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M7.5 17.5H4.5a1.5 1.5 0 01-1.5-1.5v-12A1.5 1.5 0 014.5 2.5h3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M13 14l4.5-4-4.5-4M17.3 10H7.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Log out
        </NavLink>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-[var(--color-border)] px-6 md:px-8 py-5 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-[var(--color-navy)] truncate">{title}</h1>
            {subtitle && <p className="text-sm text-[var(--color-gray-text)] mt-0.5">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-4 shrink-0">
            {actions}
            <UserAvatar size={40} fontSize={14} />
          </div>
        </header>

        <main className="flex-1 px-6 md:px-8 py-7">{children}</main>
      </div>
    </div>
  );
}

import { Link } from 'react-router-dom';
import Logo from '../ui/Logo';

const features = [
  'Parses Android UI XML with pixel-level precision',
  'Flags WCAG 2.2 AA violations automatically',
  'Generates developer-ready fix recommendations',
];

export default function AuthLayout({ title, subtitle, children, backTo, backLabel, icon }) {
  return (
    <div className="min-h-screen w-full flex bg-white">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-[42%] bg-[var(--color-navy)] flex-col justify-between px-12 py-12">
        <Logo light size="lg" align="left" />
        <div className="max-w-sm">
          <h2 className="text-white text-[28px] leading-snug font-semibold mb-6">
            Accessibility auditing, built for real Android teams.
          </h2>
          <ul className="space-y-4">
            {features.map((f) => (
              <li key={f} className="flex items-start gap-3 text-[var(--color-light-gray-text)] text-[15px]">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" className="mt-0.5 shrink-0">
                  <circle cx="10" cy="10" r="9" stroke="var(--color-green)" strokeWidth="1.5" />
                  <path d="M6 10.3l2.6 2.6L14.3 7" stroke="var(--color-green)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-[var(--color-muted-text)] text-sm">&copy; 2026 Axion. All rights reserved.</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 lg:hidden flex justify-center">
            <Logo align="center" />
          </div>

          {backTo && (
            <Link
              to={backTo}
              aria-label={backLabel || 'Go back'}
              className="inline-flex items-center gap-1.5 text-sm text-[var(--color-gray-text)] hover:text-[var(--color-navy)] mb-6 min-h-[44px] focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M10 12.5L5.5 8l4.5-4.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {backLabel || 'Back'}
            </Link>
          )}

          {icon && <div className="flex justify-center mb-5">{icon}</div>}

          {/* Visible, descriptive screen title (G24) */}
          <h1 className="text-[26px] font-bold text-[var(--color-navy)] mb-2">{title}</h1>
          {subtitle && <p className="text-[var(--color-gray-text)] text-[15px] mb-8">{subtitle}</p>}

          {children}
        </div>
      </div>
    </div>
  );
}

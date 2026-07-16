import { getDisplayName, getInitials } from '../../utils/auth';

/**
 * Top-right profile chip: shows the logged-in user's initials.
 * Reads name/email from localStorage (set at signup/login).
 */
export default function UserAvatar({ size = 42, fontSize = 15, className = '' }) {
  const initials = getInitials();
  const label = getDisplayName();

  return (
    <div
      role="img"
      aria-label={`User: ${label}`}
      title={label}
      className={className}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: '#1D9E75',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize,
        fontWeight: 700,
        flexShrink: 0,
        letterSpacing: '0.02em',
      }}
    >
      <span aria-hidden="true">{initials}</span>
    </div>
  );
}

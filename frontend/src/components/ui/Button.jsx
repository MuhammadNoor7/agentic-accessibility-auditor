import { Link } from 'react-router-dom';

export default function Button({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  fullWidth = true,
  disabled = false,
  to,
  ...rest
}) {
  const base = 'inline-flex items-center justify-center min-h-[48px] px-6 rounded-lg text-[15px] font-semibold transition-colors duration-150 focus-visible:outline-3 focus-visible:outline-[var(--color-green)] disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-[var(--color-navy-button)] text-white hover:bg-[var(--color-navy)]',
    secondary: 'bg-white text-[var(--color-navy)] border border-[var(--color-border)] hover:bg-[var(--color-page-bg)]',
    green: 'bg-[var(--color-green)] text-white hover:bg-[var(--color-green-dark)]',
  };
  const className = `${base} ${variants[variant]} ${fullWidth ? 'w-full' : ''}`;

  if (to) {
    return (
      <Link to={to} className={className} {...rest}>
        {children}
      </Link>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Badge({ children, tone = 'minor', className = '' }) {
  const tones = {
    critical: 'text-[var(--color-critical-text)] bg-[var(--color-critical-bg)]',
    serious: 'text-[var(--color-serious-text)] bg-[var(--color-serious-bg)]',
    minor: 'text-[var(--color-minor-text)] bg-[var(--color-minor-bg)]',
    green: 'text-[var(--color-green-dark)] bg-[var(--color-green-bg)]',
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function Card({ children, className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag
      className={`bg-white border border-[var(--color-border)] rounded-xl ${className}`}
      {...rest}
    >
      {children}
    </Tag>
  );
}

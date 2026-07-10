export default function TextField({
  id,
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  autoComplete,
  required = false,
}) {
  const errorId = `${id}-error`;

  return (
    <div className="text-left mb-5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-[var(--color-navy)] mb-1.5"
      >
        {label}
        {required && <span aria-hidden="true" className="text-[var(--color-critical-text)]"> *</span>}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={`w-full min-h-[48px] rounded-lg border px-4 text-[15px] text-[var(--color-navy)]
          bg-white placeholder:text-[var(--color-gray-text)]
          focus-visible:outline-3 focus-visible:outline-[var(--color-green)]
          ${error ? 'border-[var(--color-critical-text)]' : 'border-[var(--color-border)]'}`}
      />
      {error && (
        <p
          id={errorId}
          role="alert"
          className="mt-1.5 text-sm text-[var(--color-critical-text)] flex items-center gap-1.5"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 4.5v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="11" r="0.75" fill="currentColor" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}

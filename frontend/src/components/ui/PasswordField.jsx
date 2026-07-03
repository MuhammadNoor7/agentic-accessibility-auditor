import { useState } from 'react';

export default function PasswordField({
  id,
  label,
  value,
  onChange,
  placeholder,
  error,
  autoComplete = 'current-password',
  required = false,
  hint,
}) {
  const [visible, setVisible] = useState(false);
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  return (
    <div className="text-left mb-5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-[var(--color-navy)] mb-1.5"
      >
        {label}
        {required && <span aria-hidden="true" className="text-[var(--color-critical-text)]"> *</span>}
      </label>
      <div className="relative">
        <input
          id={id}
          name={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={[error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined}
          className={`w-full min-h-[48px] rounded-lg border pl-4 pr-12 text-[15px] text-[var(--color-navy)]
            bg-white placeholder:text-[var(--color-gray-text)]
            focus-visible:outline-3 focus-visible:outline-[var(--color-green)]
            ${error ? 'border-[var(--color-critical-text)]' : 'border-[var(--color-border)]'}`}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          aria-pressed={visible}
          className="absolute right-0 top-0 h-full w-12 min-w-[48px] flex items-center justify-center
            text-[var(--color-gray-text)] hover:text-[var(--color-navy)] focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded-lg"
        >
          {visible ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M2 12c1.6-4.4 6-7.5 10-7.5s8.4 3.1 10 7.5c-1.6 4.4-6 7.5-10 7.5S3.6 16.4 2 12z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
              <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M6.5 6.7C4.3 8.1 2.7 10 2 12c1.6 4.4 6 7.5 10 7.5 1.7 0 3.4-.5 4.9-1.4M9.9 4.7c.7-.1 1.4-.2 2.1-.2 4 0 8.4 3.1 10 7.5-.5 1.4-1.3 2.7-2.3 3.9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>
      </div>
      {hint && !error && (
        <p id={hintId} className="mt-1.5 text-sm text-[var(--color-gray-text)]">{hint}</p>
      )}
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

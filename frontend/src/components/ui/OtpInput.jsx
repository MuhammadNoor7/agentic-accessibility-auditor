import { useRef } from 'react';

export default function OtpInput({ length = 6, value, onChange, error }) {
  const inputsRef = useRef([]);
  const digits = value.split('').concat(Array(length).fill('')).slice(0, length);
  const errorId = 'otp-error';

  const setDigit = (index, digit) => {
    const next = [...digits];
    next[index] = digit;
    onChange(next.join(''));
  };

  const handleChange = (index) => (e) => {
    const digit = e.target.value.replace(/\D/g, '').slice(-1);
    setDigit(index, digit);
    if (digit && index < length - 1) inputsRef.current[index + 1]?.focus();
  };

  const handleKeyDown = (index) => (e) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
    if (pasted) {
      e.preventDefault();
      onChange(pasted.padEnd(length, ''));
      inputsRef.current[Math.min(pasted.length, length - 1)]?.focus();
    }
  };

  return (
    <fieldset className="mb-5 border-0 p-0 m-0">
      <legend className="block text-sm font-medium text-[var(--color-navy)] mb-2">
        6-digit verification code
      </legend>
      <div className="flex gap-3" role="group" aria-describedby={error ? errorId : undefined}>
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => (inputsRef.current[i] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={handleChange(i)}
            onKeyDown={handleKeyDown(i)}
            onPaste={handlePaste}
            aria-label={`Digit ${i + 1} of ${length}`}
            aria-invalid={Boolean(error)}
            className={`w-12 h-14 min-w-[48px] text-center text-xl font-semibold rounded-lg border
              text-[var(--color-navy)] bg-white
              focus-visible:outline-3 focus-visible:outline-[var(--color-green)]
              ${error ? 'border-[var(--color-critical-text)]' : 'border-[var(--color-border)]'}`}
          />
        ))}
      </div>
      {error && (
        <p id={errorId} role="alert" className="mt-2 text-sm text-[var(--color-critical-text)] flex items-center gap-1.5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 4.5v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="11" r="0.75" fill="currentColor" />
          </svg>
          {error}
        </p>
      )}
    </fieldset>
  );
}

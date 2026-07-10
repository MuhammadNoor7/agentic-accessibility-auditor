import { useEffect, useRef } from 'react';

export default function Modal({ open, onClose, titleId, children, labelledBy }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const prevFocused = document.activeElement;
    dialogRef.current?.focus();

    const handleKey = (e) => {
      if (e.key === 'Escape' && onClose) onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('keydown', handleKey);
      prevFocused?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-navy)]/60 px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className="w-full max-w-[420px] bg-white rounded-2xl shadow-2xl p-8 outline-none"
      >
        {children}
      </div>
    </div>
  );
}

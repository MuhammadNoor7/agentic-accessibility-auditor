import { useRef, useState, useId } from 'react';

export default function FileDropzone({ label, hint, accept, file, onChange, icon }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const inputId = useId();

  const handleFiles = (files) => {
    if (files && files[0]) onChange(files[0]);
  };

  return (
    <div>
      <label htmlFor={inputId} className="block text-sm font-medium text-[var(--color-navy)] mb-2">
        {label}
      </label>

      {!file ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors
            ${dragging ? 'border-[var(--color-green)] bg-[var(--color-green-fix-bg)]' : 'border-[var(--color-border-alt)] bg-white'}`}
        >
          <div className="mx-auto mb-3 w-12 h-12 rounded-full bg-[var(--color-page-bg)] flex items-center justify-center text-[var(--color-gray-text)]">
            {icon}
          </div>
          <p className="text-[15px] text-[var(--color-navy)] mb-1">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="font-semibold text-[var(--color-green-dark)] hover:underline focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
            >
              Click to upload
            </button>{' '}
            or drag and drop
          </p>
          {hint && <p className="text-sm text-[var(--color-gray-text)]">{hint}</p>}
          <input
            ref={inputRef}
            id={inputId}
            type="file"
            accept={accept}
            className="sr-only"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      ) : (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] bg-white px-4 py-3.5">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-green-bg)] flex items-center justify-center text-[var(--color-green-dark)] shrink-0">
              {icon}
            </div>
            <div className="min-w-0">
              <p className="text-[15px] font-medium text-[var(--color-navy)] truncate">{file.name}</p>
              <p className="text-sm text-[var(--color-gray-text)]">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onChange(null)}
            aria-label={`Remove ${file.name}`}
            className="w-11 h-11 shrink-0 flex items-center justify-center rounded-lg text-[var(--color-gray-text)] hover:text-[var(--color-critical-text)] hover:bg-[var(--color-critical-bg)] focus-visible:outline-3 focus-visible:outline-[var(--color-green)]"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

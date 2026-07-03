import { Link } from 'react-router-dom';

export default function FooterLink({ text, linkText, to }) {
  return (
    <p className="text-center text-[15px] text-[var(--color-gray-text)] mt-6">
      {text}{' '}
      <Link
        to={to}
        className="font-semibold text-[var(--color-green-dark)] hover:underline focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
      >
        {linkText}
      </Link>
    </p>
  );
}

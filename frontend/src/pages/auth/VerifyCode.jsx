import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import OtpInput from '../../components/ui/OtpInput';
import Button from '../../components/ui/Button';
import { apiPost } from '../../utils/api';
import { setToken } from '../../utils/auth';

export default function VerifyCode() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const purpose = location.state?.purpose || 'password_reset';
  const [debugCode, setDebugCode] = useState(location.state?.debugCode || null);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(30);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!email) {
      navigate(purpose === 'email_verify' ? '/signup' : '/forgot-password', { replace: true });
    }
  }, [email, purpose, navigate]);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const digits = code.replace(/\s/g, '');
    if (digits.length < 6) {
      setError('Enter all 6 digits of the code we sent you.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const data = await apiPost('/auth/verify-otp', {
        email,
        code: digits,
        purpose,
      });
      if (purpose === 'email_verify') {
        setToken(data.access_token, data.user_id, data.email, data.name || '');
        navigate('/upload');
        return;
      }
      navigate('/set-password', {
        state: { email, resetToken: data.reset_token },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    setError('');
    try {
      const data = await apiPost('/auth/resend-otp', { email, purpose });
      setDebugCode(data.debug_code || null);
      setSecondsLeft(30);
      setCode('');
    } catch (err) {
      setError(err.message);
    }
  };

  const subtitleEmail = email || 'your email';

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={`We sent a 6-digit code to ${subtitleEmail}.`}
      backTo={purpose === 'email_verify' ? '/signup' : '/forgot-password'}
      backLabel="Back"
      icon={
        <div className="w-14 h-14 rounded-full bg-[var(--color-green-bg)] flex items-center justify-center" aria-hidden="true">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="5" width="18" height="14" rx="2" stroke="var(--color-green-dark)" strokeWidth="1.8" />
            <path d="M4 7l8 6 8-6" stroke="var(--color-green-dark)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      }
    >
      <form onSubmit={handleSubmit} noValidate>
        <OtpInput value={code} onChange={setCode} error={error} />
        {debugCode ? (
          <p className="text-sm text-[var(--color-gray-text)] mb-4" aria-live="polite">
            Dev code (SMTP not configured): <strong>{debugCode}</strong>
          </p>
        ) : null}
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Verifying…' : 'Verify code'}
        </Button>
      </form>

      <div className="text-center mt-6 text-[15px]">
        {secondsLeft > 0 ? (
          <p className="text-[var(--color-gray-text)]" aria-live="polite">
            Resend code in 0:{String(secondsLeft).padStart(2, '0')}
          </p>
        ) : (
          <button
            type="button"
            onClick={handleResend}
            className="font-semibold text-[var(--color-green-dark)] hover:underline min-h-[44px] focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
          >
            Resend code
          </button>
        )}
      </div>
    </AuthLayout>
  );
}

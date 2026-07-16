import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import TextField from '../../components/ui/TextField';
import Button from '../../components/ui/Button';
import { apiPost } from '../../utils/api';
import { emailError } from '../../utils/validation';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const eMsg = emailError(email);
    if (eMsg) {
      setError(eMsg);
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const data = await apiPost('/auth/forgot-password', { email: email.trim() });
      navigate('/verify-code', {
        state: {
          email: email.trim(),
          purpose: 'password_reset',
          debugCode: data.debug_code || null,
          emailSent: Boolean(data.email_sent),
          mailHint: data.message || '',
        },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Forgot your password?"
      subtitle="Enter your email and we'll send you a 6-digit code to reset it."
      backTo="/login"
      backLabel="Back to log in"
    >
      <form onSubmit={handleSubmit} noValidate>
        <TextField
          id="email"
          label="Email address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
          error={error}
        />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Sending…' : 'Send reset code'}
        </Button>
      </form>
    </AuthLayout>
  );
}

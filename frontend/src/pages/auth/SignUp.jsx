import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import TextField from '../../components/ui/TextField';
import PasswordField from '../../components/ui/PasswordField';
import Button from '../../components/ui/Button';
import GoogleButton from '../../components/ui/GoogleButton';
import FooterLink from '../../components/ui/FooterLink';
import { apiPost } from '../../utils/api';
import { signInWithGoogle } from '../../utils/googleAuth';
import { emailError, passwordError } from '../../utils/validation';

export default function SignUp() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    if (!form.name.trim()) next.name = 'Please enter your full name.';
    const e = emailError(form.email);
    if (e) next.email = e;
    const p = passwordError(form.password, { requiredMessage: 'Please create a password.' });
    if (p) next.password = p;
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      // Creates the account and emails a verification OTP (debug_code when SMTP is off).
      await apiPost('/auth/register', {
        email: form.email,
        password: form.password,
        name: form.name.trim(),
      });
      const resent = await apiPost('/auth/resend-otp', {
        email: form.email.trim(),
        purpose: 'email_verify',
      });
      navigate('/verify-code', {
        state: {
          email: form.email.trim(),
          purpose: 'email_verify',
          debugCode: resent.debug_code || null,
          emailSent: Boolean(resent.email_sent),
          mailHint: resent.message || '',
        },
      });
    } catch (err) {
      setErrors((prev) => ({ ...prev, email: err.message }));
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleClick = async () => {
    setErrors({});
    setSubmitting(true);
    try {
      await signInWithGoogle();
      navigate('/upload');
    } catch (err) {
      setErrors((prev) => ({ ...prev, password: err.message }));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start auditing Android UIs for accessibility in minutes."
    >
      <form onSubmit={handleSubmit} noValidate>
        <TextField
          id="name"
          label="Full name"
          value={form.name}
          onChange={handleChange('name')}
          placeholder="Jane Doe"
          autoComplete="name"
          required
          error={errors.name}
        />
        <TextField
          id="email"
          label="Email address"
          type="email"
          value={form.email}
          onChange={handleChange('email')}
          placeholder="you@example.com"
          autoComplete="email"
          required
          error={errors.email}
        />
        <PasswordField
          id="password"
          label="Password"
          value={form.password}
          onChange={handleChange('password')}
          placeholder="Create a password"
          autoComplete="new-password"
          required
          hint="Must be at least 8 characters and include a letter and a number."
          error={errors.password}
        />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create account'}
        </Button>
      </form>

      <div className="flex items-center gap-3 my-6" role="presentation">
        <div className="h-px flex-1 bg-[var(--color-border)]" />
        <span className="text-sm text-[var(--color-gray-text)]">or</span>
        <div className="h-px flex-1 bg-[var(--color-border)]" />
      </div>

      <GoogleButton onClick={handleGoogleClick} />

      <FooterLink text="Already have an account?" linkText="Log in" to="/login" />
    </AuthLayout>
  );
}

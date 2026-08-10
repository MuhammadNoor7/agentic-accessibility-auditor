import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import TextField from '../../components/ui/TextField';
import PasswordField from '../../components/ui/PasswordField';
import Button from '../../components/ui/Button';
import GoogleButton from '../../components/ui/GoogleButton';
import FooterLink from '../../components/ui/FooterLink';
import { apiPost } from '../../utils/api';
import { setToken } from '../../utils/auth';
import { signInWithGoogle } from '../../utils/googleAuth';
import { emailError, passwordError } from '../../utils/validation';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    const e = emailError(form.email);
    if (e) next.email = e;
    const p = passwordError(form.password, { requiredMessage: 'Please enter your password.' });
    if (p) next.password = p;
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const data = await apiPost('/auth/login', { email: form.email, password: form.password });
      setToken(data.access_token, data.user_id, data.email, data.name || '');
      navigate('/upload');
    } catch (err) {
      setErrors((prev) => ({ ...prev, password: err.message }));
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
    <AuthLayout title="Log in to Axion" subtitle="Welcome back. Enter your details to continue.">
      <form onSubmit={handleSubmit} noValidate>
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
          placeholder="Enter your password"
          autoComplete="current-password"
          required
          error={errors.password}
        />
        <div className="flex justify-end mb-4 -mt-2">
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-[var(--color-green-dark)] hover:underline min-h-[44px] flex items-center focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
          >
            Forgot password?
          </Link>
        </div>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Log in'}
        </Button>
      </form>

      <div className="flex items-center gap-3 my-4" role="presentation">
        <div className="h-px flex-1 bg-[var(--color-border)]" />
        <span className="text-sm text-[var(--color-gray-text)]">or</span>
        <div className="h-px flex-1 bg-[var(--color-border)]" />
      </div>

      <GoogleButton onClick={handleGoogleClick} />

      <FooterLink text="Don't have an account?" linkText="Sign up" to="/signup" />
    </AuthLayout>
  );
}
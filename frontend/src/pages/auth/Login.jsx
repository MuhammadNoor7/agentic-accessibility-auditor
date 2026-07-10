import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import TextField from '../../components/ui/TextField';
import PasswordField from '../../components/ui/PasswordField';
import Button from '../../components/ui/Button';
import GoogleButton from '../../components/ui/GoogleButton';
import FooterLink from '../../components/ui/FooterLink';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    // Specific, field-identifying error messages (G21 / R21)
    const next = {};
    if (!form.email.trim()) {
      next.email = 'Please enter your email address.';
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      next.email = 'Enter a valid email address, e.g. name@example.com.';
    }
    if (!form.password) {
      next.password = 'Please enter your password.';
    } else if (form.password.length < 8) {
      next.password = 'Password must be at least 8 characters.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) navigate('/upload');
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
        <div className="flex justify-end mb-5 -mt-2">
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-[var(--color-green-dark)] hover:underline min-h-[44px] flex items-center focus-visible:outline-3 focus-visible:outline-[var(--color-green)] rounded"
          >
            Forgot password?
          </Link>
        </div>
        <Button type="submit">Log in</Button>
      </form>

      <div className="flex items-center gap-3 my-6" role="presentation">
        <div className="h-px flex-1 bg-[var(--color-border)]" />
        <span className="text-sm text-[var(--color-gray-text)]">or</span>
        <div className="h-px flex-1 bg-[var(--color-border)]" />
      </div>

      <GoogleButton onClick={() => navigate('/upload')} />

      <FooterLink text="Don't have an account?" linkText="Sign up" to="/signup" />
    </AuthLayout>
  );
}

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import PasswordField from '../../components/ui/PasswordField';
import Button from '../../components/ui/Button';
import { apiPost } from '../../utils/api';
import { passwordError } from '../../utils/validation';

export default function SetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const resetToken = location.state?.resetToken || '';
  const [form, setForm] = useState({ password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!resetToken) {
      navigate('/forgot-password', { replace: true });
    }
  }, [resetToken, navigate]);

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    const p = passwordError(form.password, { requiredMessage: 'Please enter a new password.' });
    if (p) next.password = p;
    if (!form.confirm) {
      next.confirm = 'Please confirm your new password.';
    } else if (form.confirm !== form.password) {
      next.confirm = 'Passwords do not match. Please try again.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      await apiPost('/auth/reset-password', {
        reset_token: resetToken,
        password: form.password,
      });
      navigate('/reset-success');
    } catch (err) {
      setErrors((prev) => ({ ...prev, password: err.message }));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Set a new password"
      subtitle="Choose a strong password you haven't used before."
    >
      <form onSubmit={handleSubmit} noValidate>
        <PasswordField
          id="password"
          label="New password"
          value={form.password}
          onChange={handleChange('password')}
          placeholder="Enter new password"
          autoComplete="new-password"
          required
          hint="Must be at least 8 characters and include a letter and a number."
          error={errors.password}
        />
        <PasswordField
          id="confirm"
          label="Confirm new password"
          value={form.confirm}
          onChange={handleChange('confirm')}
          placeholder="Re-enter new password"
          autoComplete="new-password"
          required
          error={errors.confirm}
        />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : 'Reset password'}
        </Button>
      </form>
    </AuthLayout>
  );
}

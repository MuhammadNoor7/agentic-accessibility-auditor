import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/layout/AuthLayout';
import PasswordField from '../../components/ui/PasswordField';
import Button from '../../components/ui/Button';

export default function SetPassword() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ password: '', confirm: '' });
  const [errors, setErrors] = useState({});

  const handleChange = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const next = {};
    if (!form.password) {
      next.password = 'Please enter a new password.';
    } else if (form.password.length < 8) {
      next.password = 'Password must be at least 8 characters.';
    }
    if (!form.confirm) {
      next.confirm = 'Please confirm your new password.';
    } else if (form.confirm !== form.password) {
      next.confirm = 'Passwords do not match. Please try again.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) navigate('/reset-success');
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
          hint="Must be at least 8 characters."
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
        <Button type="submit">Reset password</Button>
      </form>
    </AuthLayout>
  );
}

import AuthLayout from '../../components/layout/AuthLayout';
import Button from '../../components/ui/Button';

export default function ResetSuccess() {
  return (
    <AuthLayout
      title="Password reset successful"
      icon={
        <div className="w-16 h-16 rounded-full bg-[var(--color-green-bg)] flex items-center justify-center" aria-hidden="true">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M9 16.5l4.5 4.5L23 11" stroke="var(--color-green-dark)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      }
    >
      <p className="text-[var(--color-gray-text)] text-[15px] mb-8 text-center -mt-2">
        Your password has been updated. You can now log in with your new password.
      </p>
      <Button to="/login" fullWidth>
        Continue to log in
      </Button>
    </AuthLayout>
  );
}

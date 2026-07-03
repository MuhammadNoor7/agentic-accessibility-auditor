import { Routes, Route, Navigate } from 'react-router-dom';
import SignUp from './pages/auth/SignUp';
import Login from './pages/auth/Login';
import ForgotPassword from './pages/auth/ForgotPassword';
import VerifyCode from './pages/auth/VerifyCode';
import SetPassword from './pages/auth/SetPassword';
import ResetSuccess from './pages/auth/ResetSuccess';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import Report from './pages/Report';
import Records from './pages/Records';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Auth flow */}
      <Route path="/signup" element={<SignUp />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/verify-code" element={<VerifyCode />} />
      <Route path="/set-password" element={<SetPassword />} />
      <Route path="/reset-success" element={<ResetSuccess />} />

      {/* Main app */}
      <Route path="/upload" element={<Upload />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/report" element={<Report />} />
      <Route path="/audit-history" element={<Records />} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
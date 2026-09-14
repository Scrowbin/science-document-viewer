import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { HomePage, LoginPage, RegisterPage, ForgotPasswordPage } from './pages';

/**
 * App Root Component: Orchestrates top-level Authentication Provider
 * and Client-Side Routing between Pages.
 */
export function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Main Scientific Document Manager Library */}
          <Route path="/" element={<HomePage />} />

          {/* Authentication & User Onboarding Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

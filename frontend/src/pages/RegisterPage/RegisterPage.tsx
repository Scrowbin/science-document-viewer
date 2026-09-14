import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from './RegisterPage.module.css';
import {
  FaUserPlus,
  FaUser,
  FaEnvelope,
  FaLock,
  FaEye,
  FaEyeSlash,
  FaBuildingColumns,
  FaArrowRight,
  FaCircleExclamation,
  FaCheck,
} from 'react-icons/fa6';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, error, isLoading, clearError, isAuthenticated, user } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [institution, setInstitution] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(true);
  const [localError, setLocalError] = useState<string | null>(null);

  // Clear context error on unmount
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  // Calculate password strength score (0 to 4)
  const passwordStrength = useMemo(() => {
    if (!password) return { score: 0, label: 'None', color: '#9ca3af', width: '0%' };
    let s = 0;
    if (password.length >= 8) s += 1;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) s += 1;
    if (/\d/.test(password)) s += 1;
    if (/[^A-Za-z0-9]/.test(password)) s += 1;

    switch (s) {
      case 1:
        return { score: 1, label: 'Weak', color: '#ef4444', width: '25%' };
      case 2:
        return { score: 2, label: 'Fair', color: '#f59e0b', width: '50%' };
      case 3:
        return { score: 3, label: 'Good', color: '#3b82f6', width: '75%' };
      case 4:
        return { score: 4, label: 'Strong', color: '#10b981', width: '100%' };
      default:
        return { score: 0, label: 'Too short', color: '#ef4444', width: '15%' };
    }
  }, [password]);

  const passwordsMatch = useMemo(() => {
    if (!confirmPassword) return true;
    return password === confirmPassword;
  }, [password, confirmPassword]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!name.trim()) {
      setLocalError('Please enter your full name.');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setLocalError('Please provide a valid email address.');
      return;
    }
    if (password.length < 8) {
      setLocalError('Password must contain at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match. Please re-check.');
      return;
    }
    if (!acceptTerms) {
      setLocalError('You must agree to the Terms of Service to register.');
      return;
    }

    const success = await register({
      name: name.trim(),
      email: email.trim(),
      institution: institution.trim(),
      password,
      confirmPassword,
      acceptTerms,
    });

    if (success) {
      navigate('/');
    }
  };

  const displayedError = localError || error;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.authCard}>
        {/* Brand Header */}
        <div className={styles.brandHeader}>
          <div className={styles.brandLogoCircle}>
            <FaUserPlus />
          </div>
          <h1 className={styles.brandTitle}>Create Account</h1>
          <p className={styles.brandSubtitle}>
            Join SciDocs to manage and analyze your research papers
          </p>
        </div>

        {/* Active Session Notice */}
        {isAuthenticated && user && (
          <div className={styles.signedInNotice}>
            <span>
              Currently signed in as <strong>{user.name}</strong> ({user.email}). Registering a new account will switch to that account.
            </span>
          </div>
        )}

        {/* Error Alert */}
        {displayedError && (
          <div className={styles.errorAlert} role="alert">
            <FaCircleExclamation />
            <span>{displayedError}</span>
          </div>
        )}

        {/* Form */}
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="name">
              Full Name
            </label>
            <div className={styles.inputWrapper}>
              <FaUser className={styles.inputIcon} />
              <input
                id="name"
                type="text"
                className={styles.inputField}
                placeholder="Dr. Alexander Wright"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor="email">
                Academic Email
              </label>
              <div className={styles.inputWrapper}>
                <FaEnvelope className={styles.inputIcon} />
                <input
                  id="email"
                  type="email"
                  className={styles.inputField}
                  placeholder="alex@stanford.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor="institution">
                Institution (Optional)
              </label>
              <div className={styles.inputWrapper}>
                <FaBuildingColumns className={styles.inputIcon} />
                <input
                  id="institution"
                  type="text"
                  className={styles.inputField}
                  placeholder="University / Institute"
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="password">
              Password
            </label>
            <div className={styles.inputWrapper}>
              <FaLock className={styles.inputIcon} />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className={styles.inputField}
                placeholder="Minimum 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                className={styles.togglePasswordBtn}
                onClick={() => setShowPassword((prev) => !prev)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>

            {/* Dynamic Password Strength Indicator */}
            {password && (
              <div className={styles.strengthMeterContainer}>
                <div className={styles.strengthBarWrapper}>
                  <div
                    className={styles.strengthBarFill}
                    style={{
                      width: passwordStrength.width,
                      backgroundColor: passwordStrength.color,
                    }}
                  />
                </div>
                <div className={styles.strengthLabel}>
                  <span style={{ color: 'var(--text-muted)' }}>Strength</span>
                  <span style={{ color: passwordStrength.color, fontWeight: 600 }}>
                    {passwordStrength.label}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="confirmPassword">
              Confirm Password
            </label>
            <div className={styles.inputWrapper}>
              <FaLock className={styles.inputIcon} />
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                className={styles.inputField}
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
              {confirmPassword && passwordsMatch && (
                <span style={{ position: 'absolute', right: 14, color: '#10b981', fontSize: 13 }}>
                  <FaCheck />
                </span>
              )}
            </div>
            {confirmPassword && !passwordsMatch && (
              <span style={{ fontSize: 11, color: '#ef4444', marginTop: 2 }}>
                Passwords do not match
              </span>
            )}
          </div>

          {/* Terms checkbox */}
          <div className={styles.termsRow}>
            <input
              id="terms"
              type="checkbox"
              className={styles.checkbox}
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              required
            />
            <label htmlFor="terms" className={styles.termsText}>
              I agree to the{' '}
              <button type="button" className={styles.linkButton}>
                Terms of Service
              </button>{' '}
              and{' '}
              <button type="button" className={styles.linkButton}>
                Academic Data Privacy Policy
              </button>
            </label>
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            className={styles.submitBtn}
            disabled={isLoading || !passwordsMatch}
          >
            {isLoading ? (
              <span>Creating your account...</span>
            ) : (
              <>
                <span>Register & Access Library</span>
                <FaArrowRight />
              </>
            )}
          </button>
        </form>

        {/* Footer Navigation */}
        <div className={styles.footerText}>
          Already have an account?{' '}
          <button
            type="button"
            className={styles.linkButton}
            onClick={() => navigate('/login')}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;

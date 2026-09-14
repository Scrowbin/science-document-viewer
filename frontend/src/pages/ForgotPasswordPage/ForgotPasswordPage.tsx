import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import styles from './ForgotPasswordPage.module.css';
import {
  FaKey,
  FaEnvelope,
  FaLock,
  FaEye,
  FaEyeSlash,
  FaArrowRight,
  FaArrowLeft,
  FaCheck,
  FaCircleExclamation,
  FaShieldHalved,
} from 'react-icons/fa6';

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const { requestPasswordReset, confirmPasswordReset } = useAuth();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  // Step 1: Send reset request
  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please provide a valid email address.');
      return;
    }

    setIsLoading(true);
    const res = await requestPasswordReset(email);
    setIsLoading(false);

    if (res.success) {
      setInfoMessage(res.message);
      // Advance to step 2 after short delay or immediately
      setCode('123456'); // pre-fill test verification code for convenience
      setStep(2);
    } else {
      setErrorMessage(res.message);
    }
  };

  // Step 2: Confirm reset with code
  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!code.trim() || code.trim().length !== 6) {
      setErrorMessage('Please enter a valid 6-digit verification code.');
      return;
    }
    if (newPassword.length < 8) {
      setErrorMessage('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    const res = await confirmPasswordReset(email, code.trim(), newPassword);
    setIsLoading(false);

    if (res.success) {
      setStep(3);
    } else {
      setErrorMessage(res.message);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.authCard}>
        {/* Step Indicator */}
        <div className={styles.stepIndicator}>
          <div
            className={`${styles.stepDot} ${
              step >= 1 ? styles.stepDotActive : ''
            } ${step > 1 ? styles.stepDotCompleted : ''}`}
          />
          <div
            className={`${styles.stepDot} ${
              step >= 2 ? styles.stepDotActive : ''
            } ${step > 2 ? styles.stepDotCompleted : ''}`}
          />
          <div
            className={`${styles.stepDot} ${
              step === 3 ? styles.stepDotActive : ''
            }`}
          />
        </div>

        {/* STEP 1: Enter Email */}
        {step === 1 && (
          <>
            <div className={styles.brandHeader}>
              <div className={styles.brandLogoCircle}>
                <FaKey />
              </div>
              <h1 className={styles.brandTitle}>Reset Password</h1>
              <p className={styles.brandSubtitle}>
                Enter the email associated with your account and we will send you a verification code.
              </p>
            </div>

            {errorMessage && (
              <div className={styles.errorAlert} role="alert">
                <FaCircleExclamation />
                <span>{errorMessage}</span>
              </div>
            )}

            <form className={styles.form} onSubmit={handleRequestReset} noValidate>
              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="email">
                  Registered Email Address
                </label>
                <div className={styles.inputWrapper}>
                  <FaEnvelope className={styles.inputIcon} />
                  <input
                    id="email"
                    type="email"
                    className={styles.inputField}
                    placeholder="sarah.jenkins@stanford.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className={styles.submitBtn}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span>Sending code...</span>
                ) : (
                  <>
                    <span>Send Verification Code</span>
                    <FaArrowRight />
                  </>
                )}
              </button>
            </form>
          </>
        )}

        {/* STEP 2: Verification Code & New Password */}
        {step === 2 && (
          <>
            <div className={styles.brandHeader}>
              <div className={styles.brandLogoCircle}>
                <FaShieldHalved />
              </div>
              <h1 className={styles.brandTitle}>New Password</h1>
              <p className={styles.brandSubtitle}>
                We sent a 6-digit code to <strong>{email}</strong>. Enter the code and your new password below.
              </p>
            </div>

            {infoMessage && (
              <div className={styles.infoAlert}>
                <FaCheck />
                <span>{infoMessage} (Hint: use <strong>123456</strong> for testing)</span>
              </div>
            )}

            {errorMessage && (
              <div className={styles.errorAlert} role="alert">
                <FaCircleExclamation />
                <span>{errorMessage}</span>
              </div>
            )}

            <form className={styles.form} onSubmit={handleConfirmReset} noValidate>
              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="code">
                  6-Digit Verification Code
                </label>
                <div className={styles.inputWrapper}>
                  <input
                    id="code"
                    type="text"
                    maxLength={6}
                    className={`${styles.inputField} ${styles.codeField}`}
                    placeholder="123456"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                    required
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="newPassword">
                  New Password
                </label>
                <div className={styles.inputWrapper}>
                  <FaLock className={styles.inputIcon} />
                  <input
                    id="newPassword"
                    type={showPassword ? 'text' : 'password'}
                    className={styles.inputField}
                    placeholder="Minimum 8 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
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
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="confirmPassword">
                  Confirm New Password
                </label>
                <div className={styles.inputWrapper}>
                  <FaLock className={styles.inputIcon} />
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    className={styles.inputField}
                    placeholder="Re-enter your new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className={styles.submitBtn}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span>Resetting password...</span>
                ) : (
                  <>
                    <span>Confirm & Reset Password</span>
                    <FaCheck />
                  </>
                )}
              </button>

              <button
                type="button"
                className={styles.resendBtn}
                onClick={handleRequestReset}
              >
                Didn't receive the code? Resend
              </button>
            </form>
          </>
        )}

        {/* STEP 3: Password Successfully Reset */}
        {step === 3 && (
          <div style={{ textAlign: 'center' }}>
            <div className={styles.brandHeader}>
              <div
                className={`${styles.brandLogoCircle} ${styles.brandLogoCircleSuccess}`}
              >
                <FaCheck />
              </div>
              <h1 className={styles.brandTitle}>Password Updated!</h1>
              <p className={styles.brandSubtitle}>
                Your password has been reset successfully. You can now sign in with your new credentials.
              </p>
            </div>

            <button
              type="button"
              className={`${styles.submitBtn} ${styles.successBtn}`}
              onClick={() => navigate('/login')}
            >
              <span>Back to Sign In</span>
              <FaArrowRight />
            </button>
          </div>
        )}

        {/* Footer Navigation */}
        <div className={styles.footerNav}>
          <button
            type="button"
            className={styles.backLink}
            onClick={() => navigate('/login')}
          >
            <FaArrowLeft /> Back to Sign In
          </button>
        </div>
      </div>
    </div>
  );
}

export default ForgotPasswordPage;

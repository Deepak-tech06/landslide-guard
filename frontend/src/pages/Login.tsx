import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabase';
import { useAuth } from '../AuthContext';
import { ShieldAlert, Loader2, Eye, EyeOff, ArrowLeft } from 'lucide-react';

const FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');";

const MONITORED_ZONES = [
  { name: 'Shillong Sector', status: 'active' },
  { name: 'NH6 (Jorabat)', status: 'monitoring' },
  { name: 'Cherrapunji', status: 'standby' },
];

const STATUS_COLOR: Record<string, string> = {
  active: '#4F9D69',
  monitoring: '#C2811F',
  standby: '#8B94A0',
  critical: '#C1432A',
};

function getFriendlyError(message: string) {
  if (/invalid login credentials/i.test(message)) {
    return "That email or password doesn't look right.";
  }
  return message;
}

function ContourBackground() {
  return (
    <div className="login-bg-overlay" aria-hidden="true">
      <svg viewBox="0 0 600 900" className="login-bg-svg" preserveAspectRatio="xMidYMid slice">
        <path d="M-20 120 C 120 60, 220 180, 340 110 S 560 90, 620 150" stroke="#B8621B" strokeWidth="2" fill="none" />
        <path d="M-20 220 C 100 170, 260 280, 380 200 S 540 210, 620 260" stroke="#8B94A0" strokeWidth="1.5" fill="none" />
        <path d="M-20 330 C 140 260, 250 380, 400 300 S 560 320, 620 370" stroke="#8B94A0" strokeWidth="1.5" fill="none" />
        <path d="M-20 460 C 120 400, 280 500, 420 420 S 560 440, 620 490" stroke="#B8621B" strokeWidth="2" fill="none" />
        <path d="M-20 580 C 140 520, 260 620, 400 550 S 560 560, 620 610" stroke="#8B94A0" strokeWidth="1.5" fill="none" />
        <path d="M-20 700 C 120 650, 280 740, 420 670 S 560 690, 620 730" stroke="#8B94A0" strokeWidth="1.5" fill="none" />
        <path d="M-20 810 C 140 760, 260 850, 400 790 S 560 800, 620 840" stroke="#B8621B" strokeWidth="2" fill="none" />
      </svg>
    </div>
  );
}

function Wordmark({ small = false }: { small?: boolean }) {
  return (
    <div className={`wordmark-container ${small ? 'small' : ''}`}>
      <div className="wordmark-icon">
        <ShieldAlert className="lucide-icon text-accent" />
      </div>
      <span className="wordmark-text">
        LandslideGuard
      </span>
    </div>
  );
}

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSendingReset, setIsSendingReset] = useState(false);
  
  const navigate = useNavigate();
  const { session } = useAuth();

  // Redirect if already logged in
  if (session) {
    navigate('/dashboard');
    return null;
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setIsSubmitting(true);

    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (authError) {
        setError(getFriendlyError(authError.message));
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during login.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async () => {
    setError('');
    setInfo('');
    if (!email.trim()) {
      setError('Enter your email above, then request a reset link.');
      return;
    }
    setIsSendingReset(true);
    
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/login`,
      });
      if (resetError) {
        setError(resetError.message);
      } else {
        setInfo(`Reset link sent to ${email.trim()}.`);
      }
    } catch (err: any) {
      setError('Failed to send reset link.');
    } finally {
      setIsSendingReset(false);
    }
  };

  return (
    <div className="login-layout">
      <style>{FONT_IMPORT}</style>
      <style>{`
        .login-layout {
          min-height: 100vh;
          background-color: #12151A;
          color: #E8EAED;
          display: flex;
          flex-direction: row;
          font-family: 'Inter', ui-sans-serif, system-ui;
        }

        .login-left-panel {
          display: none;
          position: relative;
          overflow: hidden;
          border-right: 1px solid #262C35;
          flex-direction: column;
          justify-content: space-between;
          padding: 40px;
          background-color: #12151A;
        }

        @media (min-width: 768px) {
          .login-left-panel {
            display: flex;
            width: 42%;
          }
        }

        @media (min-width: 1024px) {
          .login-left-panel {
            width: 38%;
          }
        }

        .login-bg-overlay {
          position: absolute;
          inset: 0;
          opacity: 0.16;
          pointer-events: none;
        }

        .login-bg-svg {
          width: 100%;
          height: 100%;
        }

        .z-10 {
          position: relative;
          z-index: 10;
        }

        .demo-badge {
          margin-top: 16px;
          padding: 4px 10px;
          display: inline-flex;
          background-color: rgba(184, 98, 27, 0.1);
          border: 1px solid rgba(184, 98, 27, 0.2);
          color: #E9A05E;
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1px;
          border-radius: 4px;
        }

        .login-info-section {
          font-family: 'IBM Plex Mono', monospace;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          font-size: 14px;
        }

        .info-title {
          font-size: 20px;
          color: #E8EAED;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .info-subtitle {
          color: #8B94A0;
          margin-top: 4px;
          font-size: 12px;
          font-family: 'Inter', sans-serif;
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: #4F9D69;
          animation: pulse-op 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        .sim-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: #3b82f6;
        }

        @keyframes pulse-op {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        .divider {
          height: 1px;
          background-color: #262C35;
        }

        .module-title {
          font-size: 12px;
          color: #8B94A0;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 12px;
          font-weight: 600;
          font-family: 'Inter', sans-serif;
        }

        .module-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .module-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 14px;
        }

        .module-name {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #C7CCD3;
          font-family: 'Inter', sans-serif;
        }

        .module-status {
          font-size: 12px;
          color: #8B94A0;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }

        .login-right-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          padding: 24px;
          position: relative;
          z-index: 10;
          background-color: #12151A;
        }

        @media (min-width: 640px) {
          .login-right-panel {
            padding: 40px;
          }
        }

        .login-form-container {
          width: 100%;
          max-width: 384px;
        }

        .mobile-wordmark {
          margin-bottom: 40px;
          display: flex;
          justify-content: center;
        }

        @media (min-width: 768px) {
          .mobile-wordmark {
            display: none;
          }
        }

        .wordmark-container {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .wordmark-container.small {
          gap: 8px;
        }

        .wordmark-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background-color: rgba(184, 98, 27, 0.15);
          border: 1px solid rgba(184, 98, 27, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .wordmark-container.small .wordmark-icon {
          width: 28px;
          height: 28px;
          border-radius: 6px;
        }

        .lucide-icon {
          width: 18px;
          height: 18px;
        }
        
        .wordmark-container.small .lucide-icon {
          width: 14px;
          height: 14px;
        }

        .text-accent {
          color: #D9853E;
        }

        .wordmark-text {
          font-size: 18px;
          font-weight: 600;
          color: #E8EAED;
          font-family: 'Space Grotesk', sans-serif;
        }

        .wordmark-container.small .wordmark-text {
          font-size: 14px;
          font-weight: 500;
        }

        .login-header {
          margin-bottom: 32px;
        }

        .login-title {
          font-size: 24px;
          font-weight: 700;
          color: #E8EAED;
          font-family: 'Space Grotesk', sans-serif;
        }

        .login-desc {
          font-size: 14px;
          color: #8B94A0;
          margin-top: 8px;
          line-height: 1.5;
        }

        .highlight-text {
          font-weight: 600;
          color: #D9853E;
        }

        .alert-box {
          margin-bottom: 24px;
          padding: 16px;
          border-radius: 8px;
          font-size: 14px;
          display: flex;
          align-items: flex-start;
          gap: 8px;
        }

        .alert-error {
          background-color: rgba(193, 67, 42, 0.1);
          border: 1px solid rgba(193, 67, 42, 0.3);
          color: #E5876F;
        }

        .alert-info-box {
          background-color: rgba(79, 157, 105, 0.1);
          border: 1px solid rgba(79, 157, 105, 0.3);
          color: #8FCBA3;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .input-group {
          display: flex;
          flex-direction: column;
        }

        .input-label-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 6px;
        }

        .input-label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: #C7CCD3;
        }

        .forgot-link {
          font-size: 12px;
          color: #D9853E;
          font-weight: 500;
          background: none;
          border: none;
          cursor: pointer;
          transition: color 0.2s;
        }

        .forgot-link:hover {
          color: #E9A05E;
        }
        
        .forgot-link:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .input-wrapper {
          position: relative;
        }

        .login-input {
          width: 100%;
          background-color: #1A1E24;
          border: 1px solid #2A313C;
          border-radius: 8px;
          padding: 12px 16px;
          color: #E8EAED;
          font-size: 14px;
          transition: all 0.2s;
          box-sizing: border-box;
        }
        
        .login-input.has-icon {
          padding-right: 44px;
        }

        .login-input::placeholder {
          color: #5C6470;
        }

        .login-input:focus {
          outline: none;
          border-color: rgba(184, 98, 27, 0.7);
          box-shadow: 0 0 0 2px rgba(184, 98, 27, 0.5);
        }

        .login-input:disabled {
          opacity: 0.5;
        }

        .icon-btn {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: #5C6470;
          background: none;
          border: none;
          cursor: pointer;
          padding: 4px;
          transition: color 0.2s;
          display: flex;
        }

        .icon-btn:hover {
          color: #C7CCD3;
        }

        .submit-btn {
          width: 100%;
          background-color: #B8621B;
          color: white;
          font-weight: 500;
          border-radius: 8px;
          padding: 12px 16px;
          border: none;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 8px;
          font-size: 14px;
          box-shadow: 0 4px 12px rgba(184, 98, 27, 0.2);
        }

        .submit-btn:hover:not(:disabled) {
          background-color: #A35515;
        }

        .submit-btn:active:not(:disabled) {
          background-color: #8F4810;
        }

        .submit-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .spin-icon {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .login-footer {
          margin-top: 32px;
          padding-top: 32px;
          border-top: 1px solid #262C35;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .return-link {
          color: #8B94A0;
          font-size: 14px;
          font-weight: 500;
          background: none;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: color 0.2s;
        }

        .return-link:hover {
          color: #E8EAED;
        }
      `}</style>

      {/* Left panel: network context */}
      <div className="login-left-panel">
        <ContourBackground />
        
        <div className="z-10">
          <Wordmark />
          <div className="demo-badge">
            DEMO MODEL / UNVALIDATED PROTOTYPE
          </div>
        </div>

        <div className="z-10 login-info-section">
          
          <div className="info-grid">
            <div>
              <div className="info-title">
                <span className="pulse-dot"></span>
                LIVE
              </div>
              <div className="info-subtitle">Open-Meteo Rainfall</div>
            </div>
            <div>
              <div className="info-title" style={{ color: '#8B94A0' }}>
                <span className="sim-dot"></span>
                SIMULATED
              </div>
              <div className="info-subtitle">Soil Moisture Data</div>
            </div>
          </div>

          <div className="divider" />

          <div>
            <h3 className="module-title">System Modules</h3>
            <ul className="module-list">
              {MONITORED_ZONES.map((zone) => (
                <li key={zone.name} className="module-item">
                  <span className="module-name">
                    <span className="status-dot" style={{ backgroundColor: STATUS_COLOR[zone.status] }} />
                    {zone.name}
                  </span>
                  <span className="module-status">{zone.status}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Right panel: authentication */}
      <div className="login-right-panel">
        <div className="login-form-container">
          <div className="mobile-wordmark">
            <Wordmark />
          </div>

          <div className="login-header">
            <h1 className="login-title">
              Sign in to continue
            </h1>
            <p className="login-desc">
              <span className="highlight-text">Authorized access only.</span> Authentication is required to generate warnings, verify incidents, and submit field reports.
            </p>
          </div>

          {error && (
            <div role="alert" className="alert-box alert-error">
              <ShieldAlert style={{ width: '16px', height: '16px', marginTop: '2px', flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}
          
          {info && !error && (
            <div role="status" className="alert-box alert-info-box">
              {info}
            </div>
          )}

          <form onSubmit={handleLogin} className="login-form" noValidate>
            <div className="input-group">
              <label className="input-label" htmlFor="email" style={{ marginBottom: '6px' }}>
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                autoFocus
                disabled={isSubmitting}
                aria-invalid={!!error}
                className="login-input"
                placeholder="you@example.com"
              />
            </div>

            <div className="input-group">
              <div className="input-label-row">
                <label className="input-label" htmlFor="password">
                  Password
                </label>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  disabled={isSendingReset}
                  className="forgot-link"
                >
                  {isSendingReset ? 'Sending...' : 'Forgot password?'}
                </button>
              </div>
              <div className="input-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  disabled={isSubmitting}
                  aria-invalid={!!error}
                  className="login-input has-icon"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="icon-btn"
                >
                  {showPassword ? <EyeOff style={{ width: '18px', height: '18px' }} /> : <Eye style={{ width: '18px', height: '18px' }} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
              className="submit-btn"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="spin-icon" style={{ width: '18px', height: '18px' }} />
                  <span>Signing in...</span>
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className="login-footer">
            <button
              onClick={() => navigate('/dashboard')}
              className="return-link"
            >
              <ArrowLeft style={{ width: '16px', height: '16px' }} />
              Return to public dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
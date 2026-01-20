import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginRequest } from '../api/client.js';
import loginImage from '../../assets/image/login.png';

function EyeIcon({ slashed }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      {slashed && (
        <path
          d="M4 20L20 4"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await loginRequest({ email, password });

      if (data?.tokens) {
        window.localStorage.setItem('access_token', data.tokens.access_token);
        window.localStorage.setItem('refresh_token', data.tokens.refresh_token);
      }

      navigate('/detection');
    } catch (err) {
      setError(err.message || 'Failed to log in');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth auth--login">
      <div className="auth__panel auth__panel--left">
        <div className="auth__overlay">
          <p className="auth__tagline">Know Whats Real</p>
          <p className="auth__brand">VerifAI</p>
        </div>
        <img src={loginImage} alt="Login illustration" className="auth__image" />
      </div>

      <div className="auth__panel auth__panel--right">
        <div className="auth__header-row">
          <button
            type="button"
            className="auth__logo-link"
            onClick={() => navigate('/')}
          >
            VerifAI
          </button>
        </div>

        <h1 className="auth__title">Log in</h1>
        <p className="auth__subtitle">
          If you don&apos;t have an account register
          <br />
          You can{' '}
          <Link to="/signup" className="auth__link">
            Register here !
          </Link>
        </p>

        <form
          className="auth__form"
          onSubmit={handleSubmit}
        >
          <label className="auth__field">
            <span>Email</span>
            <input
              type="email"
              placeholder="Enter your email address"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>

          <label className="auth__field">
            <span>Password</span>
            <div className="auth__password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your Password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="auth__password-toggle"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                <span className="auth__password-icon">
                  <EyeIcon slashed={!showPassword} />
                </span>
              </button>
            </div>
          </label>

          <div className="auth__row auth__row--between">
            <label className="auth__checkbox">
              <input type="checkbox" />
              <span>Remember me</span>
            </label>
            <button type="button" className="auth__link auth__link--button">
              Forgot Password ?
            </button>
          </div>

          {error && <p className="auth__error">{error}</p>}

          <button type="submit" className="auth__primary">
            {loading ? 'Logging in…' : 'Login'}
          </button>

          <p className="auth__or">or continue with</p>
          <div className="auth__socials">
            <button type="button" className="auth__social">
              f
            </button>
            <button type="button" className="auth__social">
              
            </button>
            <button type="button" className="auth__social">
              G
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;


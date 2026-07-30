import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const TERMS = [
  {
    number: '01',
    title: 'Acceptance of Terms',
    content:
      'By creating an account or using VerifAI, you agree to be bound by these Terms and Conditions. If you do not agree, please discontinue use of the service immediately.',
  },
  {
    number: '02',
    title: 'Eligibility',
    content:
      'You must be at least 13 years old to use VerifAI. By using the service, you represent that you meet this requirement.',
  },
  {
    number: '03',
    title: 'User Responsibilities',
    content:
      'You agree to use VerifAI for lawful purposes only. You must not misuse the service, attempt to reverse-engineer any component, or use the platform to facilitate harmful or fraudulent activity. You are responsible for maintaining the confidentiality of your account credentials.',
  },
  {
    number: '04',
    title: 'Privacy & Data Practices',
    content:
      'We are committed to protecting your privacy. VerifAI collects only the information necessary to provide and improve our services, including your email address, password (hashed), and analysis data. Raw messages and images for scam analysis are processed securely; images for OCR are processed on your device and not stored. We avoid retaining unnecessary personal data and keep security and audit logs for compliance, which may include user IDs and emails. For more details, please review our Privacy Policy (coming soon).',
  },
  {
    number: '05',
    title: 'Data Retention, Deletion & Model Improvement',
    content:
      'Audit logs are retained for 90 days. You may request account deletion at any time; your account and analysis history will be deleted or redacted as required. Some metadata may be retained for security and compliance purposes. For ongoing improvement of our detection models, anonymized and aggregated analysis data may be exported and used by administrators, even after deletion. Once data has been used for model training or improvement, it cannot be removed from those processes, but it will never be linked to your identity or used for any other purpose.',
  },
  {
    number: '06',
    title: 'Data Integrity',
    content:
      'Analysis records may be retained to support audits, investigations, and service quality. Where data is stored, it is handled according to our retention and access control policies.',
  },
  {
    number: '07',
    title: 'Disclaimer',
    content:
      'VerifAI provides AI-powered guidance and scam prevention tools, but does not guarantee outcomes. Results are advisory and do not constitute legal, financial, or professional advice. Use of the service is at your own risk.',
  },
  {
    number: '08',
    title: 'Limitation of Liability',
    content:
      'To the fullest extent permitted by law, VerifAI and its operators are not liable for any damages or losses resulting from your use of the service, including but not limited to direct, indirect, incidental, or consequential damages.',
  },
  {
    number: '09',
    title: 'Changes to Terms',
    content:
      'We may update these Terms and Conditions from time to time. Continued use of VerifAI after changes are posted constitutes your acceptance of the revised terms. Material changes will be communicated via the platform.',
  },
  {
    number: '10',
    title: 'Governing Law',
    content:
      'These Terms and Conditions are governed by the laws of the Republic of the Philippines. Any disputes arising from or relating to these terms shall be resolved in the courts of the Philippines.',
  },
  {
    number: '11',
    title: 'Contact',
    content:
      'For questions or concerns regarding these terms or your data, please contact us at support@verifai.com. We aim to respond within 2–3 business days. (placeholder for now)',
  },
];

function TermsAndConditions() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const dark = theme === 'dark';

  return (
    <div className={`page page--terms page-enter${dark ? ' terms--dark' : ' terms--light'}`}>
      <style>{`
        .page--terms {
          min-height: 100vh;
          font-family: 'Segoe UI', system-ui, sans-serif;
          transition: background 0.25s, color 0.25s;
        }

        /* DARK */
        .terms--dark {
          background: #0f0f17;
          color: #e2e2f0;
          --tc-border: rgba(255,255,255,0.07);
          --tc-muted: #55556e;
          --tc-body: #8888a8;
          --tc-card-hover: rgba(255,255,255,0.02);
          --tc-nav-bg: rgba(15,15,23,0.92);
          --tc-num: #2e2e48;
          --tc-num-hover: #6ee7f7;
          --tc-title: #ffffff;
          --tc-accent-a: #6ee7f7;
          --tc-accent-b: #a78bfa;
          --tc-btn-border: rgba(255,255,255,0.13);
          --tc-btn-color: #9090b0;
          --tc-btn-hover-border: #6ee7f7;
          --tc-btn-hover-color: #6ee7f7;
          --tc-tag-bg: rgba(110,231,247,0.08);
          --tc-tag-color: #6ee7f7;
          --tc-link: #6ee7f7;
        }

        /* LIGHT */
        .terms--light {
          background: #f5f5fa;
          color: #1a1a2e;
          --tc-border: rgba(0,0,0,0.08);
          --tc-muted: #9090aa;
          --tc-body: #4a4a6a;
          --tc-card-hover: rgba(0,0,0,0.02);
          --tc-nav-bg: rgba(245,245,250,0.92);
          --tc-num: #d0d0e0;
          --tc-num-hover: #2563eb;
          --tc-title: #0f0f1a;
          --tc-accent-a: #2563eb;
          --tc-accent-b: #7c3aed;
          --tc-btn-border: rgba(0,0,0,0.15);
          --tc-btn-color: #5a5a7a;
          --tc-btn-hover-border: #2563eb;
          --tc-btn-hover-color: #2563eb;
          --tc-tag-bg: rgba(37,99,235,0.08);
          --tc-tag-color: #2563eb;
          --tc-link: #2563eb;
        }

        /* NAV */
        .terms-nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 48px;
          border-bottom: 1px solid var(--tc-border);
          position: sticky;
          top: 0;
          background: var(--tc-nav-bg);
          backdrop-filter: blur(14px);
          z-index: 100;
        }
        .terms-nav__brand {
          font-size: 1.25rem;
          font-weight: 800;
          letter-spacing: -0.5px;
          cursor: pointer;
          background: linear-gradient(135deg, var(--tc-accent-a), var(--tc-accent-b));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          border: none;
          padding: 0;
          background-color: transparent;
        }
        .terms-nav__right {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .terms-nav__theme {
          background: none;
          border: 1px solid var(--tc-btn-border);
          color: var(--tc-btn-color);
          width: 36px;
          height: 36px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }
        .terms-nav__theme:hover {
          border-color: var(--tc-btn-hover-border);
        }
        .terms-nav__close {
          background: none;
          border: 1px solid var(--tc-btn-border);
          color: var(--tc-btn-color);
          padding: 8px 18px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.82rem;
          font-weight: 500;
          transition: all 0.2s;
        }
        .terms-nav__close:hover {
          border-color: var(--tc-btn-hover-border);
          color: var(--tc-btn-hover-color);
        }

        /* HERO */
        .terms-hero {
          padding: 64px 48px 40px;
          max-width: 820px;
          margin: 0 auto;
        }
        .terms-hero__tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: var(--tc-tag-bg);
          color: var(--tc-tag-color);
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 2.5px;
          text-transform: uppercase;
          padding: 5px 12px;
          border-radius: 20px;
          margin-bottom: 20px;
        }
        .terms-hero__title {
          font-size: clamp(2rem, 5vw, 3.2rem);
          font-weight: 800;
          line-height: 1.1;
          letter-spacing: -1.5px;
          color: var(--tc-title);
          margin: 0 0 18px;
        }
        .terms-hero__title span {
          background: linear-gradient(135deg, var(--tc-accent-a), var(--tc-accent-b));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .terms-hero__meta {
          display: flex;
          flex-wrap: wrap;
          gap: 20px;
          font-size: 0.8rem;
          color: var(--tc-muted);
        }
        .terms-hero__meta-item {
          display: flex;
          align-items: center;
          gap: 7px;
        }
        .terms-hero__meta-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--tc-accent-a);
          opacity: 0.7;
          flex-shrink: 0;
        }

        /* DIVIDER */
        .terms-divider {
          max-width: 820px;
          margin: 0 auto;
          padding: 0 48px;
          border: none;
          border-top: 1px solid var(--tc-border);
        }

        /* CLOSE TIP */
        .terms-close-tip {
          text-align: center;
          padding: 18px 48px 4px;
          font-size: 0.78rem;
          color: var(--tc-muted);
        }
        .terms-close-tip a {
          color: var(--tc-link);
          text-decoration: none;
        }
        .terms-close-tip a:hover { text-decoration: underline; }

        /* CONTENT */
        .terms-content {
          max-width: 820px;
          margin: 0 auto;
          padding: 8px 48px 80px;
        }
        .terms-section {
          display: grid;
          grid-template-columns: 52px 1fr;
          gap: 20px;
          padding: 30px 8px;
          border-bottom: 1px solid var(--tc-border);
          border-radius: 6px;
          transition: background 0.15s;
        }
        .terms-section:last-child { border-bottom: none; }
        .terms-section:hover { background: var(--tc-card-hover); }
        .terms-section:hover .terms-section__number { color: var(--tc-num-hover); }

        .terms-section__number {
          font-size: 0.68rem;
          font-weight: 700;
          letter-spacing: 1.5px;
          color: var(--tc-num);
          padding-top: 3px;
          transition: color 0.2s;
          user-select: none;
        }
        .terms-section__title {
          font-size: 1rem;
          font-weight: 700;
          color: var(--tc-title);
          margin: 0 0 8px;
          letter-spacing: -0.2px;
        }
        .terms-section__text {
          font-size: 0.875rem;
          line-height: 1.8;
          color: var(--tc-body);
          margin: 0;
        }

        /* FOOTER */
        .terms-footer {
          border-top: 1px solid var(--tc-border);
          padding: 24px 48px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .terms-footer__tagline {
          font-size: 0.78rem;
          color: var(--tc-muted);
          font-style: italic;
        }
        .terms-footer__copy {
          font-size: 0.75rem;
          color: var(--tc-muted);
        }

        /* RESPONSIVE */
        @media (max-width: 600px) {
          .terms-nav { padding: 14px 20px; }
          .terms-hero { padding: 40px 20px 28px; }
          .terms-divider { padding: 0 20px; }
          .terms-close-tip { padding: 14px 20px 0; }
          .terms-content { padding: 8px 20px 60px; }
          .terms-section { grid-template-columns: 1fr; gap: 6px; }
          .terms-section__number { display: none; }
          .terms-footer { padding: 20px; flex-direction: column; gap: 6px; text-align: center; }
        }
      `}</style>

      {/* NAV */}
      <header className="terms-nav">
        <button className="terms-nav__brand" type="button" onClick={() => navigate('/')}>
          VerifAI
        </button>
        <div className="terms-nav__right">
          <button
            className="terms-nav__theme"
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? '☀️' : '🌙'}
          </button>
          <button
            className="terms-nav__close"
            type="button"
            onClick={() => window.close()}
          >
            Close ✕
          </button>
        </div>
      </header>

      {/* HERO */}
      <section className="terms-hero">
        <div className="terms-hero__tag">Legal</div>
        <h1 className="terms-hero__title">
          Terms &amp; <span>Conditions</span>
        </h1>
        <div className="terms-hero__meta">
          <span className="terms-hero__meta-item">
            <span className="terms-hero__meta-dot" />
            Effective January 2025
          </span>
          <span className="terms-hero__meta-item">
            <span className="terms-hero__meta-dot" />
            Last updated March 2025
          </span>
          <span className="terms-hero__meta-item">
            <span className="terms-hero__meta-dot" />
            7 sections
          </span>
        </div>
      </section>

      <hr className="terms-divider" />

      {/* CLOSE TIP */}
      <p className="terms-close-tip">
        Opened from signup? Read through and{' '}
        <a href="#" onClick={(e) => { e.preventDefault(); window.close(); }}>
          close this tab
        </a>{' '}
        to return to registration.
      </p>

      {/* SECTIONS */}
      <main className="terms-content">
        {TERMS.map((term) => (
          <div className="terms-section" key={term.number}>
            <span className="terms-section__number">{term.number}</span>
            <div className="terms-section__body">
              <h2 className="terms-section__title">{term.title}</h2>
              <p className="terms-section__text">{term.content}</p>
            </div>
          </div>
        ))}
      </main>

      {/* FOOTER */}
      <footer className="terms-footer">
        <span className="terms-footer__tagline">Know what's real. VerifAI.</span>
        <span className="terms-footer__copy">© {new Date().getFullYear()} VerifAI. All rights reserved.</span>
      </footer>
    </div>
  );
}

export default TermsAndConditions;
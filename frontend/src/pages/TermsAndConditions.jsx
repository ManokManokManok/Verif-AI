import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const TERMS = [
  {
    number: '01',
    title: 'Acceptance of Terms',
    content: [
      'These Terms explain the rules for using VerifAI. By accessing the service, you agree to these Terms. If you do not agree, do not use the service.',
      'If you use VerifAI on behalf of another person or organization, you confirm that you are authorized to accept these Terms for them.',
    ],
  },
  {
    number: '02',
    title: 'Eligibility',
    content: [
      'You must be at least 13 years old, or the minimum age required to use an online service where you live if that age is higher. If you are below the age of majority where you live, use the service only with a parent or legal guardian’s permission and supervision.',
      'VerifAI is not designed for children under 13. Do not create an account or submit a child’s personal information if you do not have authority to do so.',
    ],
  },
  {
    number: '03',
    title: 'Accounts and Acceptable Use',
    content: [
      'Provide accurate account information and keep your sign-in credentials confidential. You are responsible for activity carried out through your account; tell us promptly if you believe it has been accessed without permission.',
      'Use VerifAI lawfully and do not interfere with its operation, probe or bypass its security, overload it, extract or reverse-engineer it except where the law permits, or use it to facilitate fraud, harassment, or other harm.',
      'Only submit content that you have the right to use. Do not submit information that you are not comfortable sharing with the service and, where applicable, its AI providers.',
    ],
  },
  {
    number: '04',
    title: 'Information We Collect',
    content: [
      'Account information: your email address, username, password hash, and information needed to authenticate and secure your account. We do not store your password in plain text.',
      'Submitted content and results: text or images you submit for detection, the resulting verdict, scores, category, explanation, warning signs, and timestamps. For signed-in users, detection results are saved to the account history. Some image-analysis results also retain an image preview.',
      'Chats: signed-in chatbot conversations and their messages are stored in conversation history. Guest chat is not saved to a signed-in account, but messages are processed to provide a response and may be held temporarily in server memory.',
      'Service and security data: the service may record request paths, timestamps, HTTP methods, response status and timing, device type, browser user-agent, referrer, session identifiers, account identifiers, and a hashed IP address for usage analytics. Security or audit events may also record an IP address, account identifier, email address, user-agent, and the event details.',
      'Browser storage: the app stores authentication tokens and preferences such as your selected theme in browser local storage. Some temporary flows use session storage. Do not use a shared or public device without signing out.',
    ],
  },
  {
    number: '05',
    title: 'How We Use and Process Information',
    content: [
      'We use submitted content to perform the requested scam analysis or answer a chatbot message; account and history data to provide sign-in, saved history, analytics, and data export features; and technical and security data to operate, troubleshoot, protect, and measure the service.',
      'AI processing depends on the feature and deployment. Image analysis sends the submitted image and analysis prompt to Google Gemini. Chat and some text-generation features may use Google Gemini; chatbot generation can fall back to Gemma running with the service. Other detection may use VerifAI software or models. Do not submit passwords, payment credentials, government identifiers, or unrelated sensitive information.',
      'When an external AI provider processes content, that provider receives the content needed for the request and processes it under its own terms and privacy practices. VerifAI does not control the provider’s retention or handling. Review the provider’s current terms before submitting sensitive content.',
    ],
  },
  {
    number: '06',
    title: 'Storage, Retention, and Deletion',
    content: [
      'VerifAI stores account, analysis, and signed-in conversation records in its configured database. The current service does not apply one published automatic expiry period to all of these records. They may remain in active or archive storage until removed through an available feature or handled by an operational process.',
      'Deleting an individual detection or clearing detection history removes it from your visible history and clears the submitted message text, but associated metadata (such as the result, scores, timestamp, and account association) is retained. The feature does not permanently erase every related record.',
      'Deleting a conversation removes it from active conversation history but the current implementation archives a copy. Deleting your account removes the account from active accounts but archives a copy of the account record. Account deletion does not currently erase all associated analysis records, archived conversations, archived account data, or operational/security logs.',
      'We have not verified a fixed retention period for archived records or operational logs. We will retain information only as long as needed for the purposes described here and as required or permitted by law, but exact deletion timing is not currently guaranteed. This description reflects current product behavior and may change as retention controls are implemented.',
    ],
  },
  {
    number: '07',
    title: 'Sharing and Service Providers',
    content: [
      'We do not publish your account data or make your submitted content public through the service. We share information with providers only as needed to operate features you use, including database hosting, AI processing, and account or security email delivery; to protect the service; or to comply with legal obligations.',
      'The current AI integration may send content to Google Gemini as described above. Database and email providers depend on the deployment configuration. Providers may process data in locations different from yours and under their own terms. This page does not identify every provider or promise a particular hosting region.',
      'The service may display aggregate scam-pattern analytics. These are derived from analysis records; aggregation does not by itself guarantee that information can never be re-identified.',
    ],
  },
  {
    number: '08',
    title: 'Your Choices and Data Requests',
    content: [
      'You can review saved detection history and use the available data-export and deletion controls in the app. The export currently includes personal analytics and saved detection results, including retained message text; it does not include chats or uploaded image files.',
      'You may have additional rights under the privacy laws that apply to you, such as requesting access, correction, deletion, or restriction of certain information. Those rights may have legal exceptions. The app does not currently provide a complete self-service process for every request, and deleted data may remain in the archives described above.',
    ],
  },
  {
    number: '09',
    title: 'Security and Privacy Limitations',
    content: [
      'We use technical and organizational measures intended to protect information, but no online service, transmission, or storage system can be guaranteed completely secure. We cannot promise that unauthorized access, loss, or disclosure will never occur.',
      'If you believe your account or information has been compromised, stop using the affected session and contact verifaisupportacc@gmail.com. Do not send passwords or authentication codes in a support request.',
    ],
  },
  {
    number: '10',
    title: 'Service Results and Availability',
    content: [
      'VerifAI provides automated scam-detection information and general educational guidance. Results can be incomplete, inaccurate, outdated, or wrong, and a “not scam” result does not establish that a message, person, link, or transaction is safe.',
      'Do not rely on VerifAI as the sole basis for sending money, sharing credentials, making a legal or financial decision, or responding to an emergency. Verify requests through an independent, trusted channel and seek qualified professional advice where appropriate.',
      'We may change, suspend, or discontinue features, including AI features, to maintain or improve the service. We do not guarantee uninterrupted availability or that every feature will remain available.',
    ],
  },
  {
    number: '11',
    title: 'Intellectual Property',
    content: [
      'VerifAI and its software, branding, and service materials are owned by their respective owners and protected by applicable intellectual-property laws. These Terms grant you a limited, revocable right to use the service for its intended purpose.',
      'You retain rights you have in content you submit. You give VerifAI permission to process that content only as needed to provide, secure, and operate the features you request, subject to these Terms and applicable law.',
    ],
  },
  {
    number: '12',
    title: 'Disclaimers and Liability',
    content: [
      'To the extent permitted by law, the service is provided “as is” and “as available,” without warranties that cannot lawfully be excluded. Nothing in these Terms limits rights or remedies that applicable law does not allow us to limit.',
      'To the fullest extent permitted by law, VerifAI and its operators are not liable for indirect, incidental, special, consequential, or punitive loss arising from use of the service. This does not exclude liability that cannot be excluded or limited by law.',
    ],
  },
  {
    number: '13',
    title: 'Changes to These Terms',
    content: [
      'We may revise these Terms as the service or legal requirements change. We will update the “Last updated” date when we publish a revision. Where the law requires notice or renewed consent for a material change, we will provide it.',
      'The revised Terms apply from their stated effective date. Continuing to use the service after that date may constitute acceptance only to the extent permitted by applicable law.',
    ],
  },
  {
    number: '14',
    title: 'Governing Law',
    content: [
      'These Terms are intended to be governed by the laws of the Republic of the Philippines, without displacing any mandatory consumer or privacy protections that apply where you live. Any forum or venue for a dispute is subject to those mandatory rights and applicable law.',
    ],
  },
  {
    number: '15',
    title: 'Contact and Legal Review',
    content: [
      'For customer support, account verification, privacy questions, or data requests, email verifaisupportacc@gmail.com. Verif-AI is intended to use this mailbox as the sender for account emails; delivery depends on the email settings of the running deployment.',
      'Do not email passwords, one-time codes, or other authentication secrets. Include only the information needed to explain your request.',
      'This page describes current product behavior but is not a substitute for a jurisdiction-specific privacy notice or legal review. The service operator should have qualified counsel review these Terms and confirm the described data practices, retention periods, and provider details.',
    ],
    contactEmail: 'verifaisupportacc@gmail.com',
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
        .terms-nav__home {
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
        .terms-nav__home:hover {
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
        .terms-section__text + .terms-section__text { margin-top: 8px; }
        .terms-section__text a { color: var(--tc-link); }

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
            className="terms-nav__home"
            type="button"
            onClick={() => navigate('/')}
          >
            Back to Home
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
            Effective October 11, 2026
          </span>
          <span className="terms-hero__meta-item">
            <span className="terms-hero__meta-dot" />
            Last updated October 11, 2026
          </span>
          <span className="terms-hero__meta-item">
            <span className="terms-hero__meta-dot" />
            {TERMS.length} sections
          </span>
        </div>
      </section>

      <hr className="terms-divider" />

      {/* SECTIONS */}
      <main className="terms-content">
        {TERMS.map((term) => (
          <div className="terms-section" key={term.number}>
            <span className="terms-section__number">{term.number}</span>
            <div className="terms-section__body">
              <h2 className="terms-section__title">{term.title}</h2>
              {term.content.map((paragraph) => (
                <p className="terms-section__text" key={paragraph}>{paragraph}</p>
              ))}
              {term.contactEmail && (
                <p className="terms-section__text">
                  <a href={`mailto:${term.contactEmail}`}>{term.contactEmail}</a>
                </p>
              )}
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
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';

const FEATURES = [
  {
    title: 'AI scam detection',
    description: 'Multi-head BERT plus LLM analysis for accurate scam vs. legitimate classification and scam-type labels.',
    icon: '🛡️',
  },
  {
    title: 'Trust indicators',
    description: 'Review metadata, confidence, and result history to understand how each decision was made.',
    icon: '✅',
  },
  {
    title: 'Real-time analysis',
    description: 'Paste and analyze in seconds. No batch uploads—instant feedback for messages and links.',
    icon: '⚡',
  },
  {
    title: 'Chat history',
    description: 'Logged-in users get saved analysis history so you can revisit past checks and share results.',
    icon: '📋',
  },
];

const HOW_IT_WORKS = [
  { step: 1, title: 'Paste your message', detail: 'Copy the suspicious text, email, or promo into the detection box.' },
  { step: 2, title: 'AI analyzes', detail: 'Our model classifies scam likelihood and extracts key red flags.' },
  { step: 3, title: 'Get your result', detail: 'See verdict, scores, scam type, and a short summary with markers.' },
];

const WORKFLOW_STAGES = [
  {
    number: '01',
    label: 'Submit',
    title: 'Bring the suspicious message',
    detail: 'Paste a text, email, offer, or link. Remove passwords and payment details first.',
    content: <div className="workflow__message"><span>SMS</span><p>“Pay a small delivery fee to reschedule: bit.ly/...”</p></div>,
  },
  {
    number: '02',
    label: 'Scan',
    title: 'Signals are checked',
    detail: 'The analysis looks for pressure, impersonation, payment requests, and suspicious links.',
    content: <div className="workflow__scan"><span className="workflow__scan-line" /><i>Urgency language</i><i>Shortened link</i><i>Payment request</i></div>,
  },
  {
    number: '03',
    label: 'Assess',
    title: 'Risk is explained',
    detail: 'You get a risk assessment plus the specific signals that shaped the result.',
    content: <div className="workflow__assessment"><span>Risk assessment</span><strong>Likely scam</strong><b>High risk</b></div>,
  },
  {
    number: '04',
    label: 'Act',
    title: 'Take the safer next step',
    detail: 'Pause, avoid the suspicious request, and verify through an official channel you trust.',
    content: <div className="workflow__action"><strong>Do not click or pay.</strong><span>Verify through the official delivery app.</span></div>,
  },
];

const FAQS = [
  {
    question: 'What can I check?',
    answer: 'You can check suspicious messages, emails, links, promotions, and screenshots. Remove passwords, payment details, and verification codes before submitting anything.',
  },
  {
    question: 'Can VerifAI guarantee a result?',
    answer: 'No. A result is guidance, not proof. We explain the signals we found and tell you when the model is uncertain so you can verify through an official channel.',
  },
  {
    question: 'What if I already paid or shared information?',
    answer: 'Contact your bank, card provider, or account provider through a trusted official number immediately. Do not use contact details from the suspicious message. VerifAI cannot recover funds or replace emergency support.',
  },
  {
    question: 'Do I need an account?',
    answer: 'You can start a detection without signing in. An account lets you revisit your analysis history and use additional features.',
  },
];



function Landing() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [workflowStage, setWorkflowStage] = useState(0);

  // Handle logout button click - show confirmation modal
  const handleLogout = () => {
    setShowLogoutModal(true);
  };

  // Handle logout confirmation
  const confirmLogout = async () => {
    setShowLogoutModal(false);
    setShowUserMenu(false);
    await logout();
    navigate('/');
  };

  // Handle logout cancellation
  const cancelLogout = () => {
    setShowLogoutModal(false);
  };

  // Handle admin button click
  const handleAdminClick = () => {
    if (!isLoggedIn) {
      // Redirect to login if not logged in
      navigate('/login');
      return;
    }

    if (!isAdmin) {
      // Show error or redirect if not admin
      alert('Admin access required. Please log in with an admin account.');
      return;
    }

    // Navigate to admin page
    navigate('/admin');
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setShowUserMenu(false);
    if (showUserMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showUserMenu]);

  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return undefined;
    const interval = window.setInterval(() => {
      setWorkflowStage((current) => (current + 1) % WORKFLOW_STAGES.length);
    }, 4200);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return undefined;
    const revealItems = document.querySelectorAll('.landing-reveal');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('landing-reveal--visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    revealItems.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="page page--landing page-enter">
      <header className="nav">
        <div className="brand">VerifAI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>How it works</button>
          {isLoggedIn && <button className="nav__link nav__btn" type="button" onClick={() => navigate('/analytics')}>Your Verif-AI Journey</button>}
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/detection')}>Check a message</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/chatbot')}>Get guidance</button>
        </nav>

        {isLoggedIn ? (
          <div className="nav__user-menu" onClick={(e) => e.stopPropagation()}>
            <button
              className="nav__login"
              type="button"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              {user?.username || user?.email || 'Profile'}
            </button>
            {showUserMenu && (
              <div className="nav__dropdown">
                <button
                  className="nav__dropdown-item"
                  type="button"
                  onClick={() => { navigate('/settings'); setShowUserMenu(false); }}
                >
                  Settings
                </button>
                {isAdmin && (
                  <button
                    className="nav__dropdown-item nav__dropdown-item--admin"
                    type="button"
                    onClick={() => { navigate('/admin'); setShowUserMenu(false); }}
                  >
                    Admin Panel
                  </button>
                )}
                <button
                  className="nav__dropdown-item nav__dropdown-item--logout"
                  type="button"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="nav__login"
            type="button"
            onClick={() => navigate('/login')}
          >
            Login/Signup
          </button>
        )}
      </header>

      <main className="landing">
        <section className="landing__hero landing__hero--trust">
          <div className="landing__hero-copy">
            <p className="landing__eyebrow"><span aria-hidden="true">●</span> A calmer second opinion</p>
            <h1 className="landing__title">Know before you click, pay, or reply.</h1>
            <p className="landing__body">VerifAI checks suspicious messages, links, and offers for common scam signals, then explains what it found in plain language.</p>
            <div className="landing__actions">
              <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>Check something now <span aria-hidden="true">→</span></button>
              <button type="button" className="landing__cta landing__cta--quiet" onClick={() => navigate('/chatbot')}>I think I’ve been scammed</button>
            </div>
            <p className="landing__fine-print">No account required to start. Never share passwords, bank details, or verification codes.</p>
          </div>
          <div className="landing__hero-panel" aria-label="What happens when you check a message">
            <div className="landing__panel-top"><span className="landing__status-dot" aria-hidden="true" /> VerifAI safety check <span>Just now</span></div>
            <div className="landing__message-preview"><span>SMS</span><p>“Your delivery is waiting. Pay a small fee to reschedule: bit.ly/...”</p></div>
            <div className="landing__result"><div><span className="landing__result-label">Risk assessment</span><strong>Likely scam</strong></div><span className="landing__risk">High risk</span></div>
            <ul className="landing__signals"><li><span aria-hidden="true">!</span> Shortened link hides the destination</li><li><span aria-hidden="true">!</span> Urgent payment request</li><li><span aria-hidden="true">!</span> Delivery company is not named</li></ul>
            <p className="landing__panel-note">We show the signals behind every result so you can decide what to do next.</p>
          </div>
        </section>

        <div className="landing__trust-strip" aria-label="VerifAI trust commitments">
          <span><b aria-hidden="true">✓</b> Plain-language explanations</span>
          <span><b aria-hidden="true">✓</b> Privacy-conscious analysis</span>
          <span><b aria-hidden="true">✓</b> Honest about uncertainty</span>
        </div>

        <section className="landing__proof landing-reveal" aria-labelledby="proof-title">
          <div>
            <p className="landing__eyebrow">Built for the moment you hesitate</p>
            <h2 id="proof-title" className="landing__section-title">A clear second opinion beats a rushed decision.</h2>
          </div>
          <div className="landing__proof-list">
            <article><strong>01</strong><h3>See the reason</h3><p>Every result points to concrete signals such as pressure, impersonation, or suspicious links.</p></article>
            <article><strong>02</strong><h3>Keep control</h3><p>Start without an account and decide what to do after you understand the risk.</p></article>
            <article><strong>03</strong><h3>Know the limit</h3><p>Uncertain results are called out clearly. Verification through a trusted channel still matters.</p></article>
          </div>
        </section>

        <section className="landing__how landing__workflow landing-reveal" id="how-it-works" aria-labelledby="workflow-title">
          <div className="workflow__heading">
            <p className="landing__eyebrow">Watch the process</p>
            <h2 id="workflow-title" className="landing__section-title">From hesitation to a safer decision.</h2>
            <p>Each stage is visible, explainable, and designed to keep you in control.</p>
          </div>
          <div className="workflow__stage-panel" aria-live="polite">
            <div className="workflow__stage-top">
              <span>Stage {workflowStage + 1} of {WORKFLOW_STAGES.length}</span>
              <div className="workflow__progress" aria-hidden="true"><span style={{ width: `${((workflowStage + 1) / WORKFLOW_STAGES.length) * 100}%` }} /></div>
            </div>
            <div className="workflow__stage-content" key={workflowStage}>
              <div>
                <p className="workflow__stage-label">{WORKFLOW_STAGES[workflowStage].label}</p>
                <h3>{WORKFLOW_STAGES[workflowStage].title}</h3>
                <p>{WORKFLOW_STAGES[workflowStage].detail}</p>
              </div>
              {WORKFLOW_STAGES[workflowStage].content}
            </div>
          </div>
          <div className="workflow__controls" role="tablist" aria-label="Detection workflow stages">
            {WORKFLOW_STAGES.map((stage, index) => (
              <button key={stage.number} type="button" role="tab" aria-selected={workflowStage === index} className={workflowStage === index ? 'is-active' : ''} onClick={() => setWorkflowStage(index)}>
                <span>{stage.number}</span>{stage.label}
              </button>
            ))}
          </div>
          <button type="button" className="landing__cta landing__cta--secondary" onClick={() => navigate('/detection')}>
            Start a free check
          </button>
        </section>

        <section className="landing__features landing-reveal" id="features">
          <p className="landing__eyebrow">Useful by design</p>
          <h2 className="landing__section-title">Protection that explains itself.</h2>
          <div className="landing__feature-grid">
            {FEATURES.map((feature, idx) => (
              <div key={idx} className="landing__feature-card">
                <span className="landing__feature-icon" aria-hidden="true">{feature.icon}</span>
                <h3 className="landing__feature-title">{feature.title}</h3>
                <p className="landing__feature-desc">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="landing__transparency landing-reveal" aria-labelledby="transparency-title">
          <div className="landing__transparency-copy">
            <p className="landing__eyebrow">Transparent by default</p>
            <h2 id="transparency-title" className="landing__section-title">No mystery score. No inflated promise.</h2>
            <p>VerifAI combines classification with readable indicators. It is designed to help you pause and verify, not to make decisions for you.</p>
          </div>
          <div className="landing__metric-list">
            <div><strong>15+</strong><span>scam categories supported</span></div>
            <div><strong>10 KB</strong><span>maximum message size</span></div>
            <div><strong>2 ways</strong><span>to get help: detection or guidance</span></div>
          </div>
        </section>

        <section className="landing__faq landing-reveal" aria-labelledby="faq-title">
          <div className="landing__faq-heading">
            <p className="landing__eyebrow">Before you begin</p>
            <h2 id="faq-title" className="landing__section-title">Straight answers to common concerns.</h2>
          </div>
          <div className="landing__faq-list">
            {FAQS.map((faq) => (
              <details key={faq.question}>
                <summary>{faq.question}<span aria-hidden="true">+</span></summary>
                <p>{faq.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="landing__final-cta landing-reveal" aria-labelledby="final-cta-title">
          <p className="landing__eyebrow">Pause. Check. Then decide.</p>
          <h2 id="final-cta-title">You are targeted, but you are not alone.</h2>
          <p>Get a plain-language second opinion before you click, pay, or reply.</p>
          <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>Start a free check <span aria-hidden="true">→</span></button>
          <small>VerifAI provides guidance and does not replace your bank, service provider, or emergency support.</small>
        </section>
      </main>

      <footer className="landing__footer">
        <div className="landing__footer-inner">
          <nav className="landing__footer-links">
            <button type="button" className="landing__footer-link" onClick={() => navigate('/detection')}>
              Detection
            </button>
            <button type="button" className="landing__footer-link" onClick={() => navigate('/chatbot')}>
              AI Chatbot
            </button>
            {!isLoggedIn && (
              <button type="button" className="landing__footer-link" onClick={() => navigate('/login')}>
                Login
              </button>
            )}
          </nav>
          <p className="landing__footer-tagline">Know what’s real. VerifAI.</p>
          <p className="landing__footer-copy">
            © {new Date().getFullYear()} VerifAI. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Logout Confirmation Modal */}
      <LogoutConfirmModal
        isOpen={showLogoutModal}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />
    </div>
  );
}

export default Landing;


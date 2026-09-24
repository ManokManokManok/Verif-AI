import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';
import LandingHeroMobile from '../components/LandingHeroMobile';

// Automatically import all images from the carousel folder
const imageModules = import.meta.glob('../assets/carousel/*.{jpg,jpeg,png,gif,webp}', { eager: true });
const imageFiles = Object.values(imageModules).map((mod) => mod.default).sort();

// Narrative intro sequence: what VerifAI is, who it's for, how it feels to use, and privacy.
const CAROUSEL_SLIDES = [
  {
    src: imageFiles[0],
    title: 'What is VerifAI?',
    description: 'VerifAI checks messages, emails, and links for you — and tells you in plain terms if something looks like a scam.',
  },
  {
    src: imageFiles[1],
    title: 'Built for real people, not tech experts',
    description: 'Scams increasingly target people through texts and calls. VerifAI gives you a clear second opinion before you trust anything.',
  },
  {
    src: imageFiles[2],
    title: 'Paste a message, get a clear answer',
    description: 'You\u2019ll see a simple verdict — Likely Scam or Looks Safe — with an easy explanation, not confusing tech jargon.',
  },
  {
    src: imageFiles[3],
    title: 'Your privacy comes first',
    description: 'Your messages aren\u2019t stored or shared. We only look at what\u2019s needed to give you an answer.',
  },
];

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



function Landing() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const [activeIndex, setActiveIndex] = useState(0);
  const [imgAnimClass, setImgAnimClass] = useState('anim-in anim-right');
  const [textAnimClass, setTextAnimClass] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const textRef = useRef(null);
  const [isMobile, setIsMobile] = useState(false);

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

  // Advance to a slide, restarting the image/text animations (skipped for reduced motion)
  const goToSlide = (nextIndex, direction) => {
    setActiveIndex(nextIndex);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setImgAnimClass('');
    setTextAnimClass('');
    if (reduceMotion) return;
    requestAnimationFrame(() => {
      setImgAnimClass(`anim-in anim-${direction}`);
      setTextAnimClass('carousel-text-anim');
    });
  };

  const handlePrevSlide = () => {
    const nextIndex = (activeIndex - 1 + CAROUSEL_SLIDES.length) % CAROUSEL_SLIDES.length;
    goToSlide(nextIndex, 'left');
  };

  const handleNextSlide = () => {
    const nextIndex = (activeIndex + 1) % CAROUSEL_SLIDES.length;
    goToSlide(nextIndex, 'right');
  };

  const handleDotClick = (idx) => {
    if (idx === activeIndex) return;
    goToSlide(idx, idx > activeIndex ? 'right' : 'left');
  };

  // Play animation on first mount
  useEffect(() => {
    setTextAnimClass('carousel-text-anim');
  }, []);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setShowUserMenu(false);
    if (showUserMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showUserMenu]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 600px)');
    const update = () => setIsMobile(!!mq.matches);
    update();
    mq.addEventListener?.('change', update);
    return () => mq.removeEventListener?.('change', update);
  }, []);

  return (
    <div className="page page--landing page-enter">
      <header className="nav">
        <div className="brand">VerifAI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button">About us</button>
          {isLoggedIn && <button className="nav__link nav__btn" type="button" onClick={() => navigate('/analytics')}>Your Verif-AI Journey</button>}
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/detection')}>Detection</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/chatbot')}>AI Chatbot</button>
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
        {isMobile ? (
          <LandingHeroMobile slides={CAROUSEL_SLIDES} />
        ) : (
          <section className="landing__hero">
            <div className="landing__left">
              <div
                className="carousel"
                role="region"
                aria-roledescription="carousel"
                aria-label="Introduction to VerifAI"
              >
                <img
                  key={activeIndex}
                  src={CAROUSEL_SLIDES[activeIndex].src}
                  alt={CAROUSEL_SLIDES[activeIndex].title}
                  className={`carousel-img ${imgAnimClass}`}
                />

                <button
                  type="button"
                  className="carousel__arrow carousel__arrow--prev"
                  aria-label="Previous slide"
                  onClick={handlePrevSlide}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                <button
                  type="button"
                  className="carousel__arrow carousel__arrow--next"
                  aria-label="Next slide"
                  onClick={handleNextSlide}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>

                <div className="carousel__dots" role="tablist" aria-label="Slide navigation">
                  {CAROUSEL_SLIDES.map((_, idx) => (
                    <button
                      key={idx}
                      type="button"
                      role="tab"
                      aria-selected={idx === activeIndex}
                      aria-label={`Go to slide ${idx + 1}`}
                      className={`carousel__dot ${idx === activeIndex ? 'carousel__dot--active' : ''}`}
                      onClick={() => handleDotClick(idx)}
                    />
                  ))}
                </div>
              </div>
            </div>

          <section className="landing__right">
            <div ref={textRef} className={textAnimClass}>
              <h1 className="landing__title">
                {CAROUSEL_SLIDES[activeIndex]?.title}
              </h1>
              <p className="landing__body">
                {CAROUSEL_SLIDES[activeIndex]?.description}
              </p>
              <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>
                Get Started
              </button>
            </div>
          </section>
        </section>
        )}

        <section className="landing__features" id="features">
          <h2 className="landing__section-title">What VerifAI offers</h2>
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

        <section className="landing__how" id="how-it-works">
          <h2 className="landing__section-title">How it works</h2>
          <div className="landing__steps">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step} className="landing__step">
                <span className="landing__step-num">{item.step}</span>
                <div className="landing__step-content">
                  <h3 className="landing__step-title">{item.title}</h3>
                  <p className="landing__step-detail">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
          <button type="button" className="landing__cta landing__cta--secondary" onClick={() => navigate('/detection')}>
            Try Detection
          </button>
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


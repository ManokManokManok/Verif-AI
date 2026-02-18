import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, Pagination } from 'swiper/modules';
import { useAuth } from '../context/AuthContext';

import 'swiper/css';
import 'swiper/css/pagination';

// Automatically import all images from the carousel folder
const imageModules = import.meta.glob('../assets/carousel/*.{jpg,jpeg,png,gif,webp}', { eager: true });
const imageFiles = Object.values(imageModules).map((mod) => mod.default).sort();

const CAROUSEL_SLIDES = [
  {
    src: imageFiles[0],
    title: 'AI-powered scam detection',
    description: 'Paste any message, email, or promo—our AI analyzes it in seconds and tells you if it’s a scam. Built on BERT and LLM models for accuracy you can trust.',
  },
  {
    src: imageFiles[1],
    title: 'Clear verdicts and explanations',
    description: 'Get a scam vs. legit score, scam type classification, and key linguistic markers. Understand why something was flagged, not just that it was.',
  },
  {
    src: imageFiles[2],
    title: 'Blockchain-verified results',
    description: 'Important analyses can be anchored on-chain for tamper-proof verification. Admins can anchor; anyone can verify integrity.',
  },
  {
    src: imageFiles[3],
    title: 'Privacy-first and secure',
    description: 'We don’t store raw messages on the blockchain—only hashes and classifications. Your data stays under your control.',
  },
];

const FEATURES = [
  {
    title: 'AI scam detection',
    description: 'Multi-head BERT plus LLM analysis for accurate scam vs. legitimate classification and scam-type labels.',
    icon: '🛡️',
  },
  {
    title: 'Blockchain anchoring',
    description: 'Anchor analysis results on-chain for immutable proof. Verify integrity anytime.',
    icon: '⛓️',
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
  const swiperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [textAnimClass, setTextAnimClass] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const textRef = useRef(null);

  // Handle logout
  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
    navigate('/');
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

    // Navigate to blockchain/admin page
    navigate('/blockchain');
  };

  // Click left/right overlay to navigate
  const handleSideClick = (e) => {
    if (!swiperRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if (x < rect.width / 2) {
      swiperRef.current.slidePrev();
    } else {
      swiperRef.current.slideNext();
    }
  };

  // Sync text with Swiper's active index
  const handleSlideChange = (swiper) => {
    setActiveIndex(swiper.realIndex);
    // Remove and re-add animation class to restart animation
    if (textRef.current) {
      setTextAnimClass('');
      // Force reflow
      void textRef.current.offsetWidth;
      setTextAnimClass('carousel-text-anim');
    }
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

  return (
    <div className="page page--landing">
      <header className="nav">
        <div className="brand">VerifAI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button">About us</button>
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
                  onClick={() => { navigate('/detection'); setShowUserMenu(false); }}
                >
                  Dashboard
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
        <section className="landing__hero">
          <div className="landing__left">
            <div className="carousel" style={{ overflow: 'hidden', position: 'relative', height: '100%' }}>
              <Swiper
                modules={[Autoplay, Pagination]}
                slidesPerView={1}
                loop={true}
                autoplay={{ delay: 4000, disableOnInteraction: false }}
                pagination={{ clickable: true }}
                style={{ width: '100%', height: '100%' }}
                onSwiper={(swiper) => { swiperRef.current = swiper; }}
                onSlideChange={handleSlideChange}
              >
                {CAROUSEL_SLIDES.map((slide, idx) => (
                  <SwiperSlide key={idx}>
                    <img
                      src={slide.src}
                      alt={slide.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                    />
                  </SwiperSlide>
                ))}
              </Swiper>
              <div
                style={{ position: 'absolute', top: 0, left: 0, width: '50%', height: '100%', zIndex: 5, cursor: 'pointer' }}
                onClick={() => swiperRef.current && swiperRef.current.slidePrev()}
              />
              <div
                style={{ position: 'absolute', top: 0, right: 0, width: '50%', height: '100%', zIndex: 5, cursor: 'pointer' }}
                onClick={() => swiperRef.current && swiperRef.current.slideNext()}
              />
            </div>
            <button className="landing__admin-btn" type="button" onClick={handleAdminClick}>
              Admin Panel
            </button>
          </div>

          <section className="landing__right">
            <div ref={textRef} className={textAnimClass}>
              <h1 className="landing__title">
                {CAROUSEL_SLIDES[activeIndex]?.title}
              </h1>
              <p className="landing__body">
                {CAROUSEL_SLIDES[activeIndex]?.description}
              </p>
              <button type="button" className="landing__cta" onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}>
                Get Started
              </button>
            </div>
          </section>
        </section>

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
            <button type="button" className="landing__footer-link" onClick={() => navigate('/login')}>
              Login
            </button>
          </nav>
          <p className="landing__footer-tagline">Know what’s real. VerifAI.</p>
          <p className="landing__footer-copy">
            © {new Date().getFullYear()} VerifAI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Landing;


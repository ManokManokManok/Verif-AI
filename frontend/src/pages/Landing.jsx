import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, Pagination } from 'swiper/modules';
import { useAuth } from '../context/AuthContext';
import LogoutConfirmModal from '../components/auth/LogoutConfirmModal';
import LandingHeroMobile from '../components/LandingHeroMobile';

import 'swiper/css';
import 'swiper/css/pagination';

// Automatically import all images from the carousel folder
const imageModules = import.meta.glob('../assets/carousel/*.{jpg,jpeg,png,gif,webp}', { eager: true });
const imageFiles = Object.values(imageModules).map((mod) => mod.default).sort();

const CAROUSEL_SLIDES = [
  {
    src: imageFiles[0],
    title: 'Is that message real or a scam?',
    description: 'Received a suspicious text, email, or website link? VerifAI instantly checks it for you so you can stay safe from online fraud.',
  },
  {
    src: imageFiles[1],
    title: 'Clear advice in plain English',
    description: 'No confusing technical jargon. Get straightforward guidance explaining whether a message is safe or suspicious, and what to do next.',
  },
  {
    src: imageFiles[2],
    title: 'Your privacy is always our priority',
    description: 'We protect your data with strict security. We only scan the text you manually submit, and we never share or sell your personal details.',
  },
  {
    src: imageFiles[3],
    title: 'Friendly help whenever you need it',
    description: 'Use our instant scam checker or chat with our friendly AI assistant anytime you have questions about suspicious emails or calls.',
  },
];

const WHAT_VERIFAI_DOES = [
  {
    title: 'Instant Scam Detection',
    description: 'Paste any suspicious email, text message, or website link to immediately check if scammers are trying to trick you or take your money.',
  },
  {
    title: 'Plain-English Explanations',
    description: 'Receive a clear verdict with easy-to-read explanations that point out specific warning signs, so you never have to guess.',
  },
  {
    title: 'Friendly AI Helper',
    description: 'Ask questions or double-check confusing emails in real time with our easy-to-use AI Chatbot.',
  },
  {
    title: 'Saved History (Optional)',
    description: 'Log in to keep a record of your past checks so you can revisit results or share safety warnings with family members.',
  },
];

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Copy the message',
    detail: 'Highlight and copy the suspicious text message, email, or website link from your phone or computer.',
  },
  {
    step: '02',
    title: 'Paste into VerifAI',
    detail: 'Open our Detection page and paste your copied text directly into the simple check box.',
  },
  {
    step: '03',
    title: 'Get instant safety advice',
    detail: 'Click "Check Message" to immediately see if it is safe or a scam, along with clear recommendations.',
  },
];

const EXPECTATIONS = [
  {
    title: '100% Free to Use',
    description: 'Check as many messages as you need without paying any money or entering a credit card.',
  },
  {
    title: 'Immediate Results',
    description: 'Get a clear safety verdict within 2 to 3 seconds. No waiting around or uploading files.',
  },
  {
    title: 'No Sign-Up Required',
    description: 'Check messages immediately without an account. Sign up only if you wish to save your history.',
  },
  {
    title: 'Designed for Clarity',
    description: 'Built with large readable text, high contrast, and simple language for users of all technical backgrounds.',
  },
];

const DATA_PRIVACY_ITEMS = [
  {
    title: 'What information we collect',
    description: 'Only the specific text message, email snippet, or website link that you manually copy and paste into our check box.',
  },
  {
    title: 'Why we need this data',
    description: 'To scan the message for dangerous links, fake urgency tactics, and known fraud patterns.',
  },
  {
    title: 'How your data is protected',
    description: 'All text checks are transmitted using encrypted secure connections. We never sell or share your messages with advertisers or third parties.',
  },
  {
    title: 'You remain in full control',
    description: 'You decide what to check. You can use VerifAI completely anonymously, or delete your saved check history at any time.',
  },
];

const TRUST_REASONS = [
  {
    title: 'Transparent & Honest',
    description: 'We explain the exact red flags found in a message so you understand why it is suspicious and can decide with confidence.',
  },
  {
    title: 'Privacy By Design',
    description: 'We never automatically monitor your phone calls, personal text messages, or email inbox. We only analyze what you ask us to check.',
  },
  {
    title: 'Built for Real People',
    description: 'Designed specifically to protect senior citizens, families, and everyday internet users from increasingly convincing online scams.',
  },
];

const FAQ_ITEMS = [
  {
    question: 'Is VerifAI free to use?',
    answer: 'Yes, VerifAI is completely free. You can check suspicious messages, emails, and links without paying any money or providing payment details.',
  },
  {
    question: 'Do I need to create an account or sign up?',
    answer: 'No. You can start checking messages immediately without signing up. Creating a free account is optional if you want to save your check history.',
  },
  {
    question: 'Does VerifAI read my private text messages or emails automatically?',
    answer: 'No, absolutely not. VerifAI never accesses your phone, email inbox, or private messages automatically. We only process the specific text or link that you manually copy and paste into our detection box.',
  },
  {
    question: 'How fast will I get my results?',
    answer: 'Results are virtually instant. It usually takes 2 to 3 seconds for VerifAI to analyze your text and display a clear verdict with easy-to-read advice.',
  },
  {
    question: 'How does VerifAI decide if a message is a scam?',
    answer: 'VerifAI scans the text for common scam signs—such as high-pressure demands for money, fake bank warnings, suspicious web addresses, and requests for private codes.',
  },
  {
    question: 'What should I do if a message is flagged as a scam?',
    answer: 'If VerifAI flags a message as a scam: 1) Do not click any links in the message. 2) Do not reply or send money. 3) Delete or block the sender right away. You can also ask our AI Chatbot for further guidance.',
  },
  {
    question: 'Can I check suspicious website links as well as text messages?',
    answer: 'Yes. You can copy and paste web links, promotional text, emails, or text messages. VerifAI will check them all for potential security threats.',
  },
];

function Landing() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin, logout, user } = useAuth();
  const swiperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [textAnimClass, setTextAnimClass] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [openFaqIndex, setOpenFaqIndex] = useState(0); // First FAQ open by default
  const textRef = useRef(null);
  const [isMobile, setIsMobile] = useState(false);

  // Smooth scroll helper
  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Handle logout button click
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

  // Sync text with Swiper's active index
  const handleSlideChange = (swiper) => {
    setActiveIndex(swiper.realIndex);
    if (textRef.current) {
      setTextAnimClass('');
      void textRef.current.offsetWidth;
      setTextAnimClass('carousel-text-anim');
    }
  };

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
    const mq = window.matchMedia('(max-width: 768px)');
    const update = () => setIsMobile(!!mq.matches);
    update();
    mq.addEventListener?.('change', update);
    return () => mq.removeEventListener?.('change', update);
  }, []);

  const toggleFaq = (index) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  return (
    <div className="page page--landing page-enter">
      <header className="nav">
        <div className="brand" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          Verif-AI
        </div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button" onClick={() => scrollToSection('about')}>
            What is VerifAI?
          </button>
          <button className="nav__link nav__btn" type="button" onClick={() => scrollToSection('how-it-works')}>
            How it works
          </button>
          <button className="nav__link nav__btn" type="button" onClick={() => scrollToSection('data-privacy')}>
            Data Privacy
          </button>
          <button className="nav__link nav__btn" type="button" onClick={() => scrollToSection('faq')}>
            FAQs
          </button>
          {isLoggedIn && (
            <button className="nav__link nav__btn" type="button" onClick={() => navigate('/analytics')}>
              Your Verif-AI Journey
            </button>
          )}
          <button className="nav__link nav__btn nav__btn--highlight" type="button" onClick={() => navigate('/detection')}>
            Detection
          </button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/chatbot')}>
            AI Chatbot
          </button>
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
            Login / Signup
          </button>
        )}
      </header>

      <main className="landing">
        {/* HERO SECTION */}
        {isMobile ? (
          <LandingHeroMobile slides={CAROUSEL_SLIDES} />
        ) : (
          <section className="landing__hero">
            <div className="landing__left">
              <div className="carousel" style={{ overflow: 'hidden', position: 'relative', height: '100%' }}>
                <Swiper
                  modules={[Autoplay, Pagination]}
                  slidesPerView={1}
                  loop={true}
                  autoplay={{ delay: 5000, disableOnInteraction: false }}
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
            </div>

            <section className="landing__right">
              <div ref={textRef} className={textAnimClass}>
                <h1 className="landing__title">
                  {CAROUSEL_SLIDES[activeIndex]?.title}
                </h1>
                <p className="landing__body">
                  {CAROUSEL_SLIDES[activeIndex]?.description}
                </p>
                <div className="landing__hero-actions">
                  <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>
                    Check a Message Now
                  </button>
                  <button type="button" className="landing__cta landing__cta--secondary" onClick={() => scrollToSection('how-it-works')}>
                    See How It Works
                  </button>
                </div>
              </div>
            </section>
          </section>
        )}

        {/* SECTION 1: WHAT VERIFAI IS & DOES */}
        <section className="landing__section" id="about">
          <div className="landing__section-header">
            <h2 className="landing__section-title">What is VerifAI?</h2>
            <p className="landing__section-subtitle">
              VerifAI is a straightforward tool designed to protect you from online scams, fraudulent text messages, fake bank alerts, and suspicious email links.
            </p>
          </div>

          <div className="landing__info-grid">
            {WHAT_VERIFAI_DOES.map((feature, idx) => (
              <div key={idx} className="landing__info-item">
                <h3 className="landing__info-title">{feature.title}</h3>
                <p className="landing__info-desc">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 2: HOW IT WORKS */}
        <section className="landing__section landing__section--alt" id="how-it-works">
          <div className="landing__section-header">
            <h2 className="landing__section-title">How to check a message in 3 steps</h2>
            <p className="landing__section-subtitle">
              You do not need any technical background to use VerifAI.
            </p>
          </div>

          <div className="landing__steps-list">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step} className="landing__step-row">
                <div className="landing__step-number">{item.step}</div>
                <div className="landing__step-text">
                  <h3 className="landing__step-heading">{item.title}</h3>
                  <p className="landing__step-body">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="landing__center-action">
            <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>
              Try Detection Now
            </button>
          </div>
        </section>

        {/* SECTION 3: WHAT TO EXPECT */}
        <section className="landing__section" id="expectations">
          <div className="landing__section-header">
            <h2 className="landing__section-title">What you need to know</h2>
            <p className="landing__section-subtitle">
              Key facts to keep in mind when using our service.
            </p>
          </div>

          <div className="landing__info-grid">
            {EXPECTATIONS.map((item, idx) => (
              <div key={idx} className="landing__info-item">
                <h3 className="landing__info-title">{item.title}</h3>
                <p className="landing__info-desc">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 4: DATA PRIVACY & SAFETY */}
        <section className="landing__section landing__section--alt" id="data-privacy">
          <div className="landing__section-header">
            <h2 className="landing__section-title">How we handle your data</h2>
            <p className="landing__section-subtitle">
              Your trust and personal privacy are essential to us.
            </p>
          </div>

          <div className="landing__info-grid">
            {DATA_PRIVACY_ITEMS.map((item, idx) => (
              <div key={idx} className="landing__info-item">
                <h3 className="landing__info-title">{item.title}</h3>
                <p className="landing__info-desc">{item.description}</p>
              </div>
            ))}
          </div>

          <div className="landing__privacy-statement">
            <h3 className="landing__privacy-statement-title">Our Privacy Promise</h3>
            <p className="landing__privacy-statement-text">
              VerifAI will <strong>never sell your personal data</strong>, share message contents with third-party advertisers, or access private messages on your device without your explicit input.
            </p>
          </div>
        </section>

        {/* SECTION 5: WHY YOU CAN TRUST VERIFAI */}
        <section className="landing__section" id="why-trust">
          <div className="landing__section-header">
            <h2 className="landing__section-title">Why you can trust VerifAI</h2>
            <p className="landing__section-subtitle">
              Built on transparency, privacy, and clarity.
            </p>
          </div>

          <div className="landing__info-grid landing__info-grid--3col">
            {TRUST_REASONS.map((item, idx) => (
              <div key={idx} className="landing__info-item">
                <h3 className="landing__info-title">{item.title}</h3>
                <p className="landing__info-desc">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 6: FREQUENTLY ASKED QUESTIONS */}
        <section className="landing__section landing__section--alt" id="faq">
          <div className="landing__section-header">
            <h2 className="landing__section-title">Frequently Asked Questions</h2>
            <p className="landing__section-subtitle">
              Common questions about using VerifAI.
            </p>
          </div>

          <div className="landing__faq-list">
            {FAQ_ITEMS.map((faq, idx) => {
              const isOpen = openFaqIndex === idx;
              return (
                <div key={idx} className={`landing__faq-row ${isOpen ? 'landing__faq-row--open' : ''}`}>
                  <button
                    type="button"
                    className="landing__faq-trigger"
                    onClick={() => toggleFaq(idx)}
                    aria-expanded={isOpen}
                  >
                    <span>{faq.question}</span>
                    <span className="landing__faq-icon">{isOpen ? '−' : '+'}</span>
                  </button>
                  {isOpen && (
                    <div className="landing__faq-content">
                      <p>{faq.answer}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* FINAL CALL TO ACTION */}
        <section className="landing__cta-section">
          <div className="landing__cta-inner">
            <h2 className="landing__cta-heading">Received a message that looks suspicious?</h2>
            <p className="landing__cta-subtext">
              Check it right now for free. It takes less than 10 seconds to verify.
            </p>
            <div className="landing__cta-buttons">
              <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>
                Check a Message Now
              </button>
              <button type="button" className="landing__cta landing__cta--secondary" onClick={() => navigate('/chatbot')}>
                Talk to AI Assistant
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing__footer">
        <div className="landing__footer-inner">
          <div className="landing__footer-brand">
            <strong>VerifAI</strong> — Scam Protection Helper
          </div>
          <nav className="landing__footer-links">
            <button type="button" className="landing__footer-link" onClick={() => scrollToSection('about')}>
              What is VerifAI?
            </button>
            <button type="button" className="landing__footer-link" onClick={() => scrollToSection('how-it-works')}>
              How it works
            </button>
            <button type="button" className="landing__footer-link" onClick={() => scrollToSection('data-privacy')}>
              Data Privacy
            </button>
            <button type="button" className="landing__footer-link" onClick={() => scrollToSection('faq')}>
              FAQs
            </button>
            <button type="button" className="landing__footer-link" onClick={() => navigate('/detection')}>
              Detection
            </button>
            <button type="button" className="landing__footer-link" onClick={() => navigate('/chatbot')}>
              AI Chatbot
            </button>
          </nav>
          <p className="landing__footer-copy">
            © {new Date().getFullYear()} VerifAI. All rights reserved. Designed for privacy and peace of mind.
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

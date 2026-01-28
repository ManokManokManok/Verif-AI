
import { useMemo, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, Pagination } from 'swiper/modules';

import 'swiper/css';
import 'swiper/css/pagination';

// Automatically import all images from the carousel folder
const imageModules = import.meta.glob('../assets/carousel/*.{jpg,jpeg,png,gif,webp}', { eager: true });
const imageFiles = Object.values(imageModules).map((mod) => mod.default).sort();

// Define your carousel slides with image, title, and description
const CAROUSEL_SLIDES = [
  {
    src: imageFiles[0],
    title: 'The leading platform in AI fraud detection',
    description: 'Detect and prevent AI-generated fraud with our advanced platform. Protect your users and your business with real-time monitoring and enterprise-grade security.',
  },
  {
    src: imageFiles[1],
    title: 'Seamless integration for your workflow',
    description: 'Integrate our solution into your existing systems with ease. Our APIs and dashboards are designed for security and risk teams to streamline operations.',
  },
  {
    src: imageFiles[2],
    title: 'Built for trust & safety',
    description: 'Keep users safe while scaling AI across your product. Our platform is built with trust and safety at its core.',
  },
  {
    src: imageFiles[3],
    title: 'Real-time insights and analytics',
    description: 'Gain actionable insights with real-time analytics and reporting. Stay ahead of threats and make informed decisions.',
  },
];



function Landing() {
  const navigate = useNavigate();
  const swiperRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [textAnimClass, setTextAnimClass] = useState('');
  const textRef = useRef(null);
  const isLoggedIn = useMemo(
    () => Boolean(window.localStorage.getItem('access_token')),
    [],
  );

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

  return (
    <div className="page page--landing">
      <header className="nav">
        <div className="brand">Verif-AI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button">About us</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/detection')}>Detection</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/chatbot')}>AI Chatbot</button>
          <button className="nav__link nav__btn" type="button">Membership</button>
        </nav>
        <button className="nav__login" type="button" onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}>
          {isLoggedIn ? 'Profile' : 'Login / Signup'}
        </button>
      </header>

      <main className="landing">
        <section className="landing__left">
          <div className="carousel" style={{ overflow: 'hidden', position: 'relative', height: '100%' }}>
            <Swiper
              modules={[Autoplay, Pagination]}
              slidesPerView={1}
              loop={true}
              autoplay={{ delay: 3500, disableOnInteraction: false }}
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
            {/* Left/right click overlays for manual navigation, allow drag/swipe on image */}
            <div
              style={{ position: 'absolute', top: 0, left: 0, width: '50%', height: '100%', zIndex: 5, cursor: 'pointer' }}
              onClick={() => swiperRef.current && swiperRef.current.slidePrev()}
            />
            <div
              style={{ position: 'absolute', top: 0, right: 0, width: '50%', height: '100%', zIndex: 5, cursor: 'pointer' }}
              onClick={() => swiperRef.current && swiperRef.current.slideNext()}
            />
          </div>
          <button className="admin-btn" type="button">ADMIN</button>
        </section>

        <section className="landing__right">
          <div ref={textRef} className={textAnimClass}>
            <h1 className="landing__title">
              {CAROUSEL_SLIDES[activeIndex]?.title}
            </h1>
            <p className="landing__body">
              {CAROUSEL_SLIDES[activeIndex]?.description}
            </p>
            <button type="button" className="cta" onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}>
              Get Started
            </button>
          </div>
        </section>
      </main>

      <footer className="footer">
        INSERT FOOTER HERE ( ALL RIGHTS RESERVED? MAYBE CUSTOMER SUPPORT? ) SCROLL DOWN
      </footer>
    </div>
  );
}

export default Landing;


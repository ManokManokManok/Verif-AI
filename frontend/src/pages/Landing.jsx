import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const CAROUSEL_ITEMS = [
  {
    title: 'Enterprise-grade protection',
    subtitle: 'Detect AI-generated fraud before it hurts your customers.',
  },
  {
    title: 'Real-time monitoring',
    subtitle: 'Streamlined dashboards for security and risk teams.',
  },
  {
    title: 'Built for trust & safety',
    subtitle: 'Keep users safe while scaling AI across your product.',
  },
];

function Landing() {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);
  const isLoggedIn = useMemo(
    () => Boolean(window.localStorage.getItem('access_token')),
    [],
  );

  useEffect(() => {
    const id = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % CAROUSEL_ITEMS.length);
    }, 3500);
    return () => clearInterval(id);
  }, []);

  const active = CAROUSEL_ITEMS[activeIndex];

  return (
    <div className="page page--landing">
      <header className="nav">
        <div className="brand">VerifAI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button">
            About us
          </button>
          <button
            className="nav__link nav__btn"
            type="button"
            onClick={() => navigate('/detection')}
          >
            Detection
          </button>
          <button
            className="nav__link nav__btn"
            type="button"
            onClick={() => navigate('/chatbot')}
          >
            AI Chatbot
          </button>
          <button className="nav__link nav__btn" type="button">
            Membership
          </button>
        </nav>
        <button
          className="nav__login"
          type="button"
          onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}
        >
          {isLoggedIn ? 'Profile' : 'Login/Signup'}
        </button>
      </header>

      <main className="landing">
        <section className="landing__left">
          <div className="carousel">
            <div className="carousel__panel">
              <p className="carousel__hint">Image carousel / video here</p>
              <h3 className="carousel__title">{active.title}</h3>
              <p className="carousel__subtitle">{active.subtitle}</p>
              <div className="carousel__dots">
                {CAROUSEL_ITEMS.map((_, idx) => (
                  <span
                    key={idx}
                    className={
                      idx === activeIndex
                        ? 'carousel__dot carousel__dot--active'
                        : 'carousel__dot'
                    }
                  />
                ))}
              </div>
            </div>
          </div>

          <button className="admin-btn" type="button">
            ADMIN
          </button>
        </section>

        <section className="landing__right">
          <h1 className="landing__title">
            The leading platform
            <br />
            in AI fraud detection
          </h1>
          <p className="landing__body">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin
            fringilla, arcu id faucibus pulvinar, nulla nisl finibus mauris, eu
            condimentum neque metus nec metus. Phasellus vel lectus eu augue
            gravida luctus non eget neque.
          </p>
          <button
            type="button"
            className="cta"
            onClick={() => navigate(isLoggedIn ? '/detection' : '/login')}
          >
            Get Started
          </button>
        </section>
      </main>

      <footer className="footer">
        INSERT FOOTER HERE ( ALL RIGHTS RESERVED? MAYBE CUSTOMER SUPPORT? ) SCROLL
        DOWN
      </footer>
    </div>
  );
}

export default Landing;


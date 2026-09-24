import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LandingHeroMobile = ({ slides = [] }) => {
  const navigate = useNavigate();
  const [active, setActive] = useState(0);
  const [animClass, setAnimClass] = useState('anim-in anim-right');

  // Advance to a slide, restarting the image animation (skipped for reduced motion)
  const goToSlide = (nextIndex, direction) => {
    setActive(nextIndex);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setAnimClass('');
    if (reduceMotion) return;
    requestAnimationFrame(() => setAnimClass(`anim-in anim-${direction}`));
  };

  const handlePrev = () => {
    const nextIndex = (active - 1 + slides.length) % slides.length;
    goToSlide(nextIndex, 'left');
  };

  const handleNext = () => {
    const nextIndex = (active + 1) % slides.length;
    goToSlide(nextIndex, 'right');
  };

  const slide = slides[active];

  return (
    <section className="landing__hero landing__hero--mobile">
      <div
        className="landing__mobile-carousel carousel"
        role="region"
        aria-roledescription="carousel"
        aria-label="Introduction to VerifAI"
      >
        {slide && (
          <img
            key={active}
            src={slide.src}
            alt={slide.title}
            className={`landing__mobile-image carousel-img ${animClass}`}
          />
        )}

        <button type="button" className="carousel__arrow carousel__arrow--prev" aria-label="Previous slide" onClick={handlePrev}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <button type="button" className="carousel__arrow carousel__arrow--next" aria-label="Next slide" onClick={handleNext}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>

        <div className="carousel__dots" role="tablist" aria-label="Slide navigation">
          {slides.map((_, idx) => (
            <button
              key={idx}
              type="button"
              role="tab"
              aria-selected={idx === active}
              aria-label={`Go to slide ${idx + 1}`}
              className={`carousel__dot ${idx === active ? 'carousel__dot--active' : ''}`}
              onClick={() => goToSlide(idx, idx > active ? 'right' : 'left')}
            />
          ))}
        </div>
      </div>

      <div className="landing__mobile-text">
        <h2 className="landing__mobile-title">{slide?.title}</h2>
        <p className="landing__mobile-body">{slide?.description}</p>
        <div className="landing__mobile-actions">
          <button type="button" className="landing__cta" onClick={() => navigate('/detection')}>
            Get Started
          </button>
        </div>
      </div>
    </section>
  );
};

export default LandingHeroMobile;

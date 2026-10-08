import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Autoplay, Pagination } from 'swiper/modules';
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/pagination';

const LandingHeroMobile = ({ slides = [] }) => {
  const navigate = useNavigate();
  const swiperRef = useRef(null);
  const [active, setActive] = useState(0);
  const [animClass, setAnimClass] = useState('anim-in anim-right');

  const handlePrev = () => {
    swiperRef.current?.slidePrev();
  };

  const handleNext = () => {
    swiperRef.current?.slideNext();
  };

  const handleSlideChange = (swiper) => {
    setActive(swiper.realIndex);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setAnimClass('');
    if (reduceMotion) return;
    requestAnimationFrame(() => setAnimClass('anim-in anim-right'));
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
        <Swiper
          modules={[Autoplay, Pagination]}
          slidesPerView={1}
          loop={slides.length > 1}
          autoplay={{ delay: 5000, disableOnInteraction: false }}
          pagination={{ clickable: true }}
          onSwiper={(swiper) => { swiperRef.current = swiper; }}
          onSlideChange={handleSlideChange}
          style={{ width: '100%', height: '100%' }}
        >
          {slides.map((item, index) => (
            <SwiperSlide key={`${item.src}-${index}`}>
              <img
                src={item.src}
                alt={item.title}
                className={`landing__mobile-image carousel-img ${index === active ? animClass : ''}`}
              />
            </SwiperSlide>
          ))}
        </Swiper>

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

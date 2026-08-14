import { useEffect, useRef, useState } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, Pagination } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';

const LandingHeroMobile = ({ slides = [] }) => {
  const swiperRef = useRef(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    // start simple autoplay sync
    const interval = setInterval(() => {
      if (swiperRef.current) {
        try {
          swiperRef.current.slideNext();
        } catch (e) {}
      }
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="landing__hero landing__hero--mobile">
      <div className="landing__mobile-carousel">
        <Swiper
          modules={[Autoplay, Pagination]}
          slidesPerView={1}
          loop
          pagination={{ clickable: true }}
          onSwiper={(s) => { swiperRef.current = s; }}
          onSlideChange={(s) => setActive(s.realIndex)}
        >
          {slides.map((s, idx) => (
            <SwiperSlide key={idx}>
              <img src={s.src} alt={s.title} className="landing__mobile-image" />
            </SwiperSlide>
          ))}
        </Swiper>
      </div>

      <div className="landing__mobile-text">
        <h2 className="landing__mobile-title">{slides[active]?.title}</h2>
        <p className="landing__mobile-body">{slides[active]?.description}</p>
        <div className="landing__mobile-actions">
          <button type="button" className="landing__cta">Get Started</button>
        </div>
      </div>
    </section>
  );
};

export default LandingHeroMobile;

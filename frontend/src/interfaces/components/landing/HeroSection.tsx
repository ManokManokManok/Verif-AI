import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';

/**
 * Hero Section component
 * Main hero section for the landing page
 */
export const HeroSection: React.FC = () => {
  const { user } = useAuth();
  const [currentSlide, setCurrentSlide] = useState(0);

  const securityImages = [
    {
      url: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&h=600&fit=crop&auto=format",
      title: "Cybersecurity Protection",
      description: "Advanced threat detection systems"
    },
    {
      url: "https://images.unsplash.com/photo-1550745165-9bc0b252726a?w=800&h=600&fit=crop&auto=format",
      title: "Digital Security",
      description: "Comprehensive fraud prevention"
    },
    {
      url: "https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=600&fit=crop&auto=format",
      title: "AI Security Analysis",
      description: "Intelligent threat monitoring"
    },
    {
      url: "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=600&fit=crop&auto=format",
      title: "Security Analytics",
      description: "Real-time fraud detection"
    },
    {
      url: "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=800&h=600&fit=crop&auto=format",
      title: "Network Protection",
      description: "Advanced security infrastructure"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % securityImages.length);
    }, 5000); // Change slide every 5 seconds

    return () => clearInterval(timer);
  }, [securityImages.length]);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % securityImages.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + securityImages.length) % securityImages.length);
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center `bg-linear-to-br` from-slate-900 via-slate-800 to-slate-900 pt-16">
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Image Carousel */}
          <div className="order-2 lg:order-1">
            <div className="relative rounded-xl aspect-video overflow-hidden shadow-2xl border border-slate-600">
              {/* Main Image */}
              <div className="relative w-full h-full">
                <img
                  src={securityImages[currentSlide].url}
                  alt={securityImages[currentSlide].title}
                  className="w-full h-full object-cover transition-opacity duration-500"
                />
                
                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-linear-to-t from-slate-900/80 via-slate-900/40 to-transparent"></div>
                
                {/* Image Info */}
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <h4 className="text-white font-semibold text-lg mb-1">
                    {securityImages[currentSlide].title}
                  </h4>
                  <p className="text-slate-300 text-sm">
                    {securityImages[currentSlide].description}
                  </p>
                </div>
              </div>

              {/* Navigation Arrows */}
              <button
                onClick={prevSlide}
                className="absolute left-4 top-1/2 -translate-y-1/2 bg-slate-800/80 hover:bg-slate-700/80 text-white p-2 rounded-full transition-colors duration-200 backdrop-blur-sm"
                aria-label="Previous slide"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button
                onClick={nextSlide}
                className="absolute right-4 top-1/2 -translate-y-1/2 bg-slate-800/80 hover:bg-slate-700/80 text-white p-2 rounded-full transition-colors duration-200 backdrop-blur-sm"
                aria-label="Next slide"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>

              {/* Slide Indicators */}
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                {securityImages.map((_: any, index: number) => (
                  <button
                    key={index}
                    onClick={() => goToSlide(index)}
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      index === currentSlide 
                        ? 'bg-white w-8' 
                        : 'bg-slate-400 hover:bg-slate-300'
                    }`}
                    aria-label={`Go to slide ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Content */}
          <div className="order-1 lg:order-2 text-left lg:text-right">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
              The leading platform
              <br />
              in AI fraud detection
            </h1>

            <p className="text-base md:text-lg text-slate-300 mb-8 leading-relaxed">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin fringilla, arcu id faucibus pulvinar, nulla nisl finibus mauris, eu condimentum neque metus nec metus. Phasellus vel lectus eu augue gravida luctus non eget neque.
            </p>

            <div className="flex justify-start lg:justify-end">
              {!user ? (
                <Link to="/register">
                  <Button size="lg" className="bg-white hover:bg-gray-100 text-slate-900 px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all">
                    Get Started
                  </Button>
                </Link>
              ) : (
                <Link to="/dashboard">
                  <Button size="lg" className="bg-white hover:bg-gray-100 text-slate-900 px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all">
                    Go to Dashboard
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

import React from 'react';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import {
  HeroSection,
  FeaturesSection,
  TestimonialsSection,
} from '../components/landing';

/**
 * Landing page component
 * Main entry point for unauthenticated users
 */
export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900">
      <Header />
      <HeroSection />
      <FeaturesSection />
      <TestimonialsSection />
      <Footer/>
    </div>
  );
};

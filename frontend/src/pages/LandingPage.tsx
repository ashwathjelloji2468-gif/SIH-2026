import { useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import LandingNavbar from '../components/Landing/LandingNavbar';
import HeroSection from '../components/Landing/HeroSection';
import FeaturesSection from '../components/Landing/FeaturesSection';
import ProductShowcase from '../components/Landing/ProductShowcase';
import TrustSection from '../components/Landing/TrustSection';
import TestimonialsSection from '../components/Landing/TestimonialsSection';
import CTASection from '../components/Landing/CTASection';
import ContactSection from '../components/Landing/ContactSection';
import LandingFooter from '../components/Landing/LandingFooter';

gsap.registerPlugin(ScrollTrigger);

export default function LandingPage() {
  useEffect(() => {
    // Refresh ScrollTrigger after all sections mount
    const timeout = setTimeout(() => {
      ScrollTrigger.refresh();
    }, 500);

    return () => {
      clearTimeout(timeout);
      // Clean up all ScrollTrigger instances on unmount
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0B1120] bg-hex-pattern bg-radial-subtle text-slate-100 overflow-x-hidden">
      <LandingNavbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <ProductShowcase />
        <TrustSection />
        <TestimonialsSection />
        <CTASection />
        <ContactSection />
      </main>
      <LandingFooter />
    </div>
  );
}

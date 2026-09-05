import React, { useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ThreeShield } from './ThreeShield';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../../context/ProjectContext';

gsap.registerPlugin(ScrollTrigger);

export const HeroSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const pillRef = useRef<HTMLDivElement>(null);
  const h1Ref = useRef<HTMLHeadingElement>(null);
  const pRef = useRef<HTMLParagraphElement>(null);
  const buttonsRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { setIsScanModalOpen } = useProject();

  useEffect(() => {
    const tl = gsap.timeline();
    
    tl.fromTo(
      [pillRef.current, h1Ref.current, pRef.current, buttonsRef.current],
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.8, stagger: 0.2, ease: 'power3.out', delay: 0.2 }
    );

    return () => {
      tl.kill();
    };
  }, []);

  const handleBookDemo = () => {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section id="hero" ref={containerRef} className="relative min-h-screen overflow-hidden flex items-center justify-center bg-[#06080F]">
      {/* Background Layers */}
      <div className="absolute inset-0 bg-grid-cyber opacity-20 pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#06080F_100%)] pointer-events-none z-0" />
      
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-60 pointer-events-none">
        <ThreeShield />
      </div>

      {/* Content Layer */}
      <div className="relative z-10 text-center max-w-4xl mx-auto px-6 flex flex-col items-center">
        {/* Top Pill */}
        <div 
          ref={pillRef}
          className="px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs md:text-sm font-semibold tracking-wide mb-8 backdrop-blur-sm shadow-[0_0_10px_rgba(6,182,212,0.15)]"
        >
          NIST PQC Standards · FIPS 203/204/205 Compliant
        </div>

        {/* H1 Title */}
        <h1 
          ref={h1Ref}
          className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent pb-2"
        >
          Securing the Future of Digital Trust
        </h1>

        {/* Paragraph */}
        <p 
          ref={pRef}
          className="text-lg text-slate-400 max-w-2xl mx-auto mt-6"
        >
          Enterprise-grade quantum cryptographic discovery, risk intelligence, and automated post-quantum migration — powered by deterministic AST analysis and NIST PQC standards.
        </p>

        {/* CTA Buttons */}
        <div ref={buttonsRef} className="flex flex-col sm:flex-row items-center gap-4 mt-8">
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/dashboard')}
            className="w-full sm:w-auto px-8 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-semibold rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-colors cursor-pointer"
          >
            Get Started
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleBookDemo}
            className="w-full sm:w-auto px-8 py-3 border border-white/20 bg-white/[0.04] backdrop-blur-sm hover:bg-white/[0.08] text-white font-medium rounded-lg transition-colors cursor-pointer"
          >
            Book a Demo
          </motion.button>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 text-slate-500 z-10">
        <ChevronDown className="w-8 h-8 animate-bounce opacity-70" />
      </div>
    </section>
  );
};

export default HeroSection;

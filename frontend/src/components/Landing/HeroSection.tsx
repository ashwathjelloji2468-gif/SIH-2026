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
    <section 
      id="hero" 
      ref={containerRef} 
      className="relative min-h-screen overflow-hidden flex items-center justify-center bg-[#0B1120] pt-20"
    >
      {/* 1. Background Patterns & Dark Contrast Overlays */}
      <div className="absolute inset-0 bg-grid-cyber bg-hex-pattern opacity-25 pointer-events-none z-0" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#0B1120]/80 via-transparent to-[#0B1120] pointer-events-none z-0" />
      
      {/* 2. Soft Cyan Radial Glow Centered Behind Sphere */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] md:w-[700px] md:h-[700px] rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.22)_0%,rgba(6,182,212,0.07)_50%,transparent_70%)] blur-3xl pointer-events-none z-0" />

      {/* 3. Geometric Sphere 3D Layer */}
      <div className="absolute inset-0 z-0 opacity-70 pointer-events-none">
        <ThreeShield />
      </div>

      {/* 4. Content Layer with High Contrast Typography */}
      <div className="relative z-10 text-center max-w-4xl mx-auto px-6 flex flex-col items-center">
        {/* Top Cyan Badge */}
        <div 
          ref={pillRef}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#22D3EE]/40 bg-[#0B1120]/80 text-[#22D3EE] text-xs md:text-sm font-semibold font-mono tracking-wide mb-8 backdrop-blur-md shadow-[0_0_15px_rgba(34,211,238,0.25)]"
        >
          <span className="w-2 h-2 rounded-full bg-[#22D3EE] animate-pulse" />
          <span>NIST PQC Standards · FIPS 203/204/205 Compliant</span>
        </div>

        {/* Pure White High-Contrast Headline */}
        <h1 
          ref={h1Ref}
          className="text-5xl md:text-7xl font-extrabold text-[#F8FAFC] tracking-tight leading-none pb-2 drop-shadow-[0_4px_20px_rgba(0,0,0,0.8)]"
        >
          Securing the Future of{' '}
          <span className="bg-gradient-to-r from-white via-[#67E8F9] to-[#22D3EE] bg-clip-text text-transparent">
            Digital Trust
          </span>
        </h1>

        {/* Soft Gray Supporting Body Text */}
        <p 
          ref={pRef}
          className="text-base md:text-lg text-[#94A3B8] max-w-2xl mx-auto mt-6 leading-relaxed font-normal"
        >
          Enterprise-grade quantum cryptographic discovery, risk intelligence, and automated post-quantum migration — powered by deterministic AST analysis and NIST PQC standards.
        </p>

        {/* CTA Buttons */}
        <div ref={buttonsRef} className="flex flex-col sm:flex-row items-center gap-4 mt-10">
          <motion.button 
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => navigate('/dashboard')}
            className="w-full sm:w-auto px-8 py-3.5 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#0B1120] font-bold rounded-xl shadow-[0_0_25px_rgba(34,211,238,0.45)] transition-all cursor-pointer text-base"
          >
            Get Started →
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.96 }}
            onClick={handleBookDemo}
            className="w-full sm:w-auto px-8 py-3.5 border border-[#22D3EE]/40 bg-[#22D3EE]/5 hover:bg-[#22D3EE]/15 text-[#22D3EE] font-semibold rounded-xl backdrop-blur-md transition-all cursor-pointer text-base shadow-[0_0_15px_rgba(34,211,238,0.15)]"
          >
            Book a Demo
          </motion.button>
        </div>
      </div>

      {/* Scroll Down Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-slate-400 z-10 pointer-events-none">
        <ChevronDown className="w-7 h-7 animate-bounce opacity-70" />
      </div>
    </section>
  );
};

export default HeroSection;

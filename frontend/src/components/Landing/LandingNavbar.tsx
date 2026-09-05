import React, { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sentriq3DLogo } from '../Three/Sentriq3DLogo';

export const LandingNavbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Auto-hide logic
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setIsVisible(false); // scrolling down & past header
      } else {
        setIsVisible(true); // scrolling up
      }
      
      setIsScrolled(currentScrollY > 20);
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const scrollToSection = (id: string) => {
    setIsMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const navLinks = [
    { name: 'Features', id: 'features' },
    { name: 'Product', id: 'product' },
    { name: 'Security', id: 'security' },
    { name: 'Contact', id: 'contact' },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-transform duration-300 ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      } ${
        isScrolled 
          ? 'bg-[#06080F]/60 backdrop-blur-xl border-b border-white/[0.06]' 
          : 'bg-transparent border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* 3D Moving Logo Left */}
        <div className="flex items-center gap-3">
          <Sentriq3DLogo size="sm" showText={true} />
          <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-widest bg-cyan-950/40 text-cyan-400 border border-cyan-800/50 ml-2">
            QUANTUM INTELLIGENCE
          </span>
        </div>

        {/* Center Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <button
              key={link.name}
              onClick={() => scrollToSection(link.id)}
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              {link.name}
            </button>
          ))}
        </nav>

        {/* Right CTA (Desktop) */}
        <div className="hidden md:flex items-center">
          <Link
            to="/dashboard"
            className="group relative px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-black font-semibold rounded-lg transition-all duration-300 shadow-[0_0_15px_rgba(6,182,212,0.4)] hover:shadow-[0_0_25px_rgba(34,211,238,0.6)] flex items-center gap-2"
          >
            Launch Console
            <span className="transition-transform group-hover:translate-x-1">→</span>
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden p-2 text-slate-300 hover:text-white"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-full left-0 right-0 bg-[#070A12] border-b border-white/[0.06] shadow-2xl py-4 md:hidden flex flex-col"
          >
            {navLinks.map((link) => (
              <button
                key={link.name}
                onClick={() => scrollToSection(link.id)}
                className="px-6 py-4 text-left text-base font-medium text-slate-300 hover:text-white hover:bg-white/[0.03] transition-colors"
              >
                {link.name}
              </button>
            ))}
            <div className="px-6 pt-4 pb-2">
              <Link
                to="/dashboard"
                className="flex justify-center items-center gap-2 w-full px-5 py-3 bg-cyan-500 text-black font-semibold rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.4)]"
              >
                Launch Console →
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default LandingNavbar;

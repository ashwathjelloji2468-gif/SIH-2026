import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

export const ScrollNavControl: React.FC = () => {
  const [isAtTop, setIsAtTop] = useState<boolean>(true);
  const [isAtBottom, setIsAtBottom] = useState<boolean>(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;

      setIsAtTop(scrollY <= 50);
      setIsAtBottom(scrollY + windowHeight >= documentHeight - 50);
    };

    // Initial check
    handleScroll();

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth',
    });
  };

  return (
    <div
      aria-label="Page scroll navigation"
      className="fixed right-4 md:right-8 bottom-6 md:bottom-10 z-40 flex flex-col items-center bg-[#0B0F19]/80 backdrop-blur-xl border border-slate-800/90 rounded-2xl p-1.5 shadow-[0_0_25px_rgba(0,0,0,0.6)] transition-all duration-300 hover:border-cyan-500/40"
    >
      {/* Scroll to Top Button */}
      <button
        type="button"
        onClick={scrollToTop}
        disabled={isAtTop}
        aria-label="Scroll to top"
        title="Scroll to top"
        className={`p-2.5 rounded-xl border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 ${
          isAtTop
            ? 'opacity-35 cursor-not-allowed border-transparent text-slate-600'
            : 'opacity-100 cursor-pointer border-slate-800/80 bg-slate-900/60 text-slate-300 hover:text-cyan-300 hover:bg-cyan-950/60 hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(34,211,238,0.25)] active:scale-95'
        }`}
      >
        <ChevronUp className="w-4 h-4 md:w-5 md:h-5 stroke-[2.5]" />
      </button>

      {/* Subtle Separator Line */}
      <div className="w-4 h-[1px] bg-slate-800/80 my-1" />

      {/* Scroll to Bottom Button */}
      <button
        type="button"
        onClick={scrollToBottom}
        disabled={isAtBottom}
        aria-label="Scroll to bottom"
        title="Scroll to bottom"
        className={`p-2.5 rounded-xl border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 ${
          isAtBottom
            ? 'opacity-35 cursor-not-allowed border-transparent text-slate-600'
            : 'opacity-100 cursor-pointer border-slate-800/80 bg-slate-900/60 text-slate-300 hover:text-cyan-300 hover:bg-cyan-950/60 hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(34,211,238,0.25)] active:scale-95'
        }`}
      >
        <ChevronDown className="w-4 h-4 md:w-5 md:h-5 stroke-[2.5]" />
      </button>
    </div>
  );
};

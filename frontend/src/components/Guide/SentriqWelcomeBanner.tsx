import React, { useState, useEffect } from 'react';
import { Compass, Sparkles, X, ShieldCheck, ArrowRight } from 'lucide-react';

interface SentriqWelcomeBannerProps {
  onStartTour: () => void;
}

export const SentriqWelcomeBanner: React.FC<SentriqWelcomeBannerProps> = ({ onStartTour }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem('sentriq_welcome_dismissed');
    const tourCompleted = localStorage.getItem('sentriq_tour_completed');
    if (!dismissed && !tourCompleted) {
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    localStorage.setItem('sentriq_welcome_dismissed', 'true');
    setIsVisible(false);
  };

  const handleStartTourClick = () => {
    handleDismiss();
    onStartTour();
  };

  if (!isVisible) return null;

  return (
    <div className="mb-6 rounded-3xl border border-cyan-500/40 bg-gradient-to-r from-[#06080F] via-cyan-950/40 to-[#0B1120] p-6 shadow-2xl relative overflow-hidden font-sans">
      {/* Background visual glow */}
      <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
        <div className="space-y-2 max-w-2xl text-left">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/80 font-mono text-[10px] font-bold tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>WELCOME TO SENTRIQ</span>
            </span>
            <span className="text-slate-500 text-xs font-mono">Quantum Intelligence Platform</span>
          </div>

          <h2 className="text-xl font-bold font-mono text-slate-100">
            Discover Cryptographic Risk. Understand Quantum Exposure. Plan and Validate Migration.
          </h2>

          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            SENTRIQ quantifies post-quantum vulnerability using Mosca analysis, explainable QARS scoring, NIST FIPS 203/204 candidate mapping, and AST-driven refactoring.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleStartTourClick}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/80 font-mono text-xs font-bold transition-all shadow-lg hover:scale-105 cursor-pointer"
          >
            <Compass className="w-4 h-4 text-cyan-400 animate-spin-slow" />
            <span>Start Guided Tour</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={handleDismiss}
            className="px-3.5 py-2.5 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 font-mono text-xs font-medium transition-colors cursor-pointer"
          >
            Explore on my own
          </button>

          <button
            onClick={handleDismiss}
            className="p-2 text-slate-500 hover:text-slate-300 transition-colors"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

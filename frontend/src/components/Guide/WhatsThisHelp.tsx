import React, { useState } from 'react';
import { HelpCircle, X, ExternalLink, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface WhatsThisHelpProps {
  term: string;
  title?: string;
  what: string;
  why: string;
  next: string;
  nextRoute?: string;
  className?: string;
}

export const WhatsThisHelp: React.FC<WhatsThisHelpProps> = ({
  term,
  title,
  what,
  why,
  next,
  nextRoute,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className={`inline-flex items-center relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="p-1 text-slate-400 hover:text-cyan-400 hover:bg-cyan-950/40 rounded-full transition-colors cursor-pointer"
        title={`What's this? (${term})`}
        aria-label={`Help for ${term}`}
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop overlay for mobile/popover focus */}
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-xs"
            onClick={() => setIsOpen(false)}
          />

          {/* Contextual Popover Card */}
          <div className="absolute left-0 top-full mt-2 w-80 sm:w-96 rounded-2xl border border-cyan-800/80 bg-[#0B1120] p-4 shadow-2xl z-50 space-y-3 font-sans text-left text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono text-[10px] font-bold">
                  EXPLAINER
                </span>
                <h4 className="font-mono font-bold text-slate-100 text-sm">
                  {title || term}
                </h4>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* WHAT */}
            <div className="space-y-1">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400">
                WHAT
              </span>
              <p className="text-slate-300 leading-relaxed text-xs">{what}</p>
            </div>

            {/* WHY */}
            <div className="space-y-1">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
                WHY IT MATTERS
              </span>
              <p className="text-slate-300 leading-relaxed text-xs">{why}</p>
            </div>

            {/* NEXT */}
            <div className="space-y-1 bg-slate-900/70 p-2.5 rounded-xl border border-slate-800">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
                WHAT SHOULD I DO NEXT?
              </span>
              <p className="text-slate-300 leading-relaxed text-xs mb-2">{next}</p>

              {nextRoute && (
                <button
                  onClick={() => {
                    setIsOpen(false);
                    navigate(nextRoute);
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-800/60 text-[11px] font-mono hover:bg-cyan-900/60 transition-colors cursor-pointer"
                >
                  <span>Go to Route</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Bottom link to full guide */}
            <div className="pt-1 flex items-center justify-between text-[11px] font-mono border-t border-slate-800/60">
              <span className="text-slate-500">Need full details?</span>
              <button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/guide');
                }}
                className="text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>Open Guide</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

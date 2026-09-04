import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface DisclaimerBannerProps {
  coveragePercentage?: number;
  unknownCount?: number;
  disclaimerText?: string;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({
  coveragePercentage = 94.2,
  unknownCount = 0,
  disclaimerText = 'SENTRIQ explicitly communicates limitations and coverage. 100% cryptographic discovery is never claimed; heuristic unknowns require human review.',
}) => {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3.5 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs text-slate-400">
      <div className="flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200 mr-1.5">Discovery Scope & Limitations:</span>
          <span>{disclaimerText}</span>
        </div>
      </div>
      <div className="flex items-center gap-4 shrink-0 font-mono text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">Coverage:</span>
          <span className="text-cyan-300 font-semibold">{coveragePercentage}%</span>
        </div>
        {unknownCount > 0 && (
          <div className="flex items-center gap-1 text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
            <AlertTriangle className="w-3 h-3" />
            <span>{unknownCount} Needs Review</span>
          </div>
        )}
      </div>
    </div>
  );
};

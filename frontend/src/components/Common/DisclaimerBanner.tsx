import React from 'react';
import { AlertTriangle, ShieldCheck, Info } from 'lucide-react';

interface DisclaimerBannerProps {
  coveragePercentage?: number;
  unknownCount?: number;
  disclaimerText?: string;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({
  coveragePercentage = 94.2,
  unknownCount = 0,
  disclaimerText = 'SENTRIQ explicitly communicates discovery limitations. 100% cryptographic coverage is never claimed. Binary-only, vendor-managed, and dynamically loaded crypto require human review.',
}) => {
  return (
    <div className="rounded-xl border border-[#1E293B] bg-[#0B1120] p-4 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs text-[#94A3B8]">
      <div className="flex items-start gap-2.5">
        <Info className="w-4 h-4 text-[#22D3EE] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#F8FAFC] mr-1.5">Discovery Scope & Honest Disclosure:</span>
          <span>{disclaimerText}</span>
        </div>
      </div>
      <div className="flex items-center gap-4 shrink-0 font-mono text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="text-[#94A3B8]">Coverage:</span>
          <span className="text-[#22D3EE] font-semibold">≤{coveragePercentage}%</span>
        </div>
        {unknownCount > 0 && (
          <div className="flex items-center gap-1 text-amber-400 bg-amber-950/40 px-2.5 py-0.5 rounded-full border border-amber-800/40">
            <AlertTriangle className="w-3 h-3" />
            <span>{unknownCount} Needs Review</span>
          </div>
        )}
      </div>
    </div>
  );
};

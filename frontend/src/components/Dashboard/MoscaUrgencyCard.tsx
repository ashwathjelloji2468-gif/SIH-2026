import React from 'react';
import { AlertTriangle, ArrowRight, ShieldCheck, HelpCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface MoscaUrgencyCardProps {
  xLifetime?: number; // e.g. 10 years
  yMigration?: number; // e.g. 3 years
  zHorizonYear?: number; // e.g. 2033
}

export const MoscaUrgencyCard: React.FC<MoscaUrgencyCardProps> = ({
  xLifetime = 10,
  yMigration = 3,
  zHorizonYear = 2033,
}) => {
  const currentYear = new Date().getFullYear();
  const yearsUntilZ = Math.max(0, zHorizonYear - currentYear);
  const totalRequiredTime = xLifetime + yMigration;
  const isBreached = totalRequiredTime > yearsUntilZ;
  const gapYears = totalRequiredTime - yearsUntilZ;

  return (
    <div
      className={`rounded-xl border p-6 shadow-xl transition-all ${
        isBreached
          ? 'border-rose-800/80 bg-gradient-to-br from-rose-950/40 via-[#0B0F19] to-[#0B0F19]'
          : 'border-emerald-800/60 bg-gradient-to-br from-emerald-950/20 via-[#0B0F19] to-[#0B0F19]'
      }`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          {isBreached ? (
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          )}
          <h3 className="text-sm font-semibold text-slate-100">Mosca Theorem Exposure Condition</h3>
        </div>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full border font-mono font-bold uppercase ${
            isBreached
              ? 'bg-rose-950 text-rose-300 border-rose-700 animate-pulse'
              : 'bg-emerald-950 text-emerald-300 border-emerald-700'
          }`}
        >
          {isBreached ? 'Deadline Breach' : 'Within Safety Window'}
        </span>
      </div>

      <div className="space-y-4">
        {/* The Equation */}
        <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 font-mono text-center">
          <div className="text-xs text-slate-400 mb-1">Fundamental Mosca Inequality:</div>
          <div className="text-base sm:text-lg font-extrabold tracking-wide">
            <span className="text-cyan-400">X ({xLifetime}y)</span> +{' '}
            <span className="text-blue-400">Y ({yMigration}y)</span>{' '}
            <span className={isBreached ? 'text-rose-400 font-black' : 'text-emerald-400'}>
              {isBreached ? '>' : '≤'}
            </span>{' '}
            <span className="text-purple-400">Z ({yearsUntilZ}y until {zHorizonYear})</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {totalRequiredTime} years required vs {yearsUntilZ} years available until Cryptanalytically Relevant Quantum Computer (CRQC)
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          {isBreached ? (
            <>
              <strong className="text-rose-300 font-semibold">Immediate Action Required:</strong> Your cryptographic data security lifetime plus migration duration exceeds the quantum threat horizon by{' '}
              <span className="text-rose-300 font-mono font-bold">{gapYears} year(s)</span>. Adversaries executing <em>Harvest Now, Decrypt Later (HNDL)</em> attacks can intercept and store this data today to decrypt retroactively.
            </>
          ) : (
            <>
              Your data protection lifespan and migration buffer are currently within the projected threat window. Continue planning PQC hybrid migration to prevent future exposure.
            </>
          )}
        </p>

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Assumptions derived from Michele Mosca & NIST PQC Guidelines</span>
          </div>
          <Link
            to="/risk"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <span>Configure Mosca Sliders</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};

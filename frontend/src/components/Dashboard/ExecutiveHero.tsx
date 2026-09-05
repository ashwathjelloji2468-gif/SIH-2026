import React from 'react';
import { ArrowRight, Cpu, Binary, Sparkles, ShieldCheck, ChevronRight } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { CyberVisual } from '../Common/CyberVisual';
import { Globe3D } from '../Three/Globe3D';

export const ExecutiveHero: React.FC = () => {
  const { currentProject, setIsScanModalOpen } = useProject();
  const navigate = useNavigate();

  const journeyStages = [
    'Discover',
    'Understand',
    'Prove',
    'Assess',
    'Prioritize',
    'Recommend',
    'Simulate',
    'Validate',
    'Plan',
    'Monitor',
  ];

  return (
    <div className="relative overflow-hidden rounded-3xl border border-slate-800/90 bg-gradient-to-r from-[#0B0F19] via-[#0D1322] to-[#0B0F19] p-6 sm:p-8 lg:p-10 shadow-2xl mb-8">
      {/* Background Cyber Lattice Particle Visual */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        <CyberVisual className="w-full h-full" />
      </div>

      {/* Cyber Subtle Glow Accents */}
      <div className="absolute top-0 right-1/4 w-96 h-48 bg-cyan-500/10 blur-[110px] pointer-events-none" />
      <div className="absolute -bottom-10 left-10 w-72 h-40 bg-indigo-500/10 blur-[90px] pointer-events-none" />

      <div className="relative z-10 space-y-6">
        {/* Top Product Tagline & NIST Status */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/50 px-3.5 py-1 text-xs font-mono text-cyan-300 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>NIST PQC Standards (FIPS 203 / 204 / 205) Enterprise Intelligence</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            <span>Deterministic AST Analysis Active</span>
          </div>
        </div>

        {/* Split Grid: Title & 3D Globe */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          <div className="lg:col-span-8 space-y-4">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
              Quantum Cryptographic Discovery & <br />
              <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
                Post-Quantum Migration Architecture
              </span>
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
              Continuous discovery, Mosca exposure modeling, and automated PQC upgrade simulation across code repositories, TLS sessions, and cryptographic dependencies.
            </p>
          </div>

          <div className="lg:col-span-4 h-48 lg:h-56 relative rounded-2xl bg-[#06080F]/60 border border-slate-800/80 overflow-hidden hidden sm:block">
            <Globe3D className="w-full h-full" />
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            onClick={() => setIsScanModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-5 py-2.5 text-xs font-bold text-slate-950 transition-all shadow-lg shadow-cyan-950/60 hover:shadow-cyan-500/25 cursor-pointer active:scale-95"
          >
            <span>Scan Source Code</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => navigate('/risk')}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700/80 bg-slate-900/80 hover:bg-slate-800 px-4 py-2.5 text-xs font-medium text-slate-200 transition-colors cursor-pointer"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Simulate Mosca Risk</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/80 px-4 py-2.5 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <Binary className="w-4 h-4 text-slate-400" />
            <span>CycloneDX 1.6 CBOM</span>
          </button>
        </div>

        {/* 10-Stage Product Lifecycle Journey Bar */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-2">
            Continuous Transition Journey
          </div>
          <div className="flex items-center overflow-x-auto pb-1 text-[11px] font-mono text-slate-400 scrollbar-none">
            {journeyStages.map((stage, idx) => (
              <React.Fragment key={stage}>
                <div
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-colors shrink-0 ${
                    idx === 0
                      ? 'bg-cyan-950/70 text-cyan-300 font-bold border border-cyan-800/60'
                      : idx < 4
                      ? 'text-slate-300'
                      : 'text-slate-500'
                  }`}
                >
                  <span className="text-[9px] opacity-60">0{idx + 1}</span>
                  <span>{stage}</span>
                </div>
                {idx < journeyStages.length - 1 && (
                  <ChevronRight className="w-3 h-3 text-slate-700 shrink-0 mx-0.5" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

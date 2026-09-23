import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Compass,
  ArrowRight,
  ArrowLeft,
  X,
  CheckCircle2,
  FolderGit2,
  ScanSearch,
  Binary,
  ShieldAlert,
  ShieldCheck,
  GitFork,
  FileSpreadsheet,
} from 'lucide-react';

export interface TourStep {
  id: number;
  title: string;
  route: string;
  targetName: string;
  icon: React.ComponentType<{ className?: string }>;
  what: string;
  why: string;
  nextAction: string;
}

export const TOUR_STEPS: TourStep[] = [
  {
    id: 1,
    title: 'Project Selection & Ingestion',
    route: '/projects',
    targetName: 'Repositories Page',
    icon: FolderGit2,
    what: 'Ingest Git repositories and set domain criticality context.',
    why: 'Establishing clear project context ensures QARS risk calculations mirror real enterprise impact.',
    nextAction: 'Select a repository to begin discovery.',
  },
  {
    id: 2,
    title: 'Automated Scan Console',
    route: '/scan',
    targetName: 'Scan Orchestrator',
    icon: ScanSearch,
    what: 'Run multi-engine static discovery across source code, AST, certificates, and dependencies.',
    why: 'Generates a fresh Cryptographic Bill of Materials (CBOM) with exact source line locations.',
    nextAction: 'Trigger a scan to extract cryptographic primitives automatically.',
  },
  {
    id: 3,
    title: 'Cryptographic Asset Inventory (CBOM)',
    route: '/inventory',
    targetName: 'Inventory & CBOM',
    icon: Binary,
    what: 'Inspect detected algorithms, key sizes, evidence snippets, and unknown routines.',
    why: 'Provides full auditability for every public key, cipher suite, and hash function in your codebase.',
    nextAction: 'Filter by "Needs Review" to classify unknown cryptographic primitives.',
  },
  {
    id: 4,
    title: 'Mosca Theorem & Threat Scenarios',
    route: '/risk',
    targetName: 'Risk & Mosca Theorem',
    icon: ShieldAlert,
    what: 'Evaluates Harvest-Now-Decrypt-Later (HNDL) exposure: X (Shelf-Life) + Y (Migration Time) > Z (Threat Horizon).',
    why: 'Identifies which sensitive data will be compromised by quantum cryptanalysis before migration finishes.',
    nextAction: 'Review critical threat scenarios like Quantum Signature Forgery and HNDL.',
  },
  {
    id: 5,
    title: 'Quantum-Aware Risk Score (QARS)',
    route: '/qars',
    targetName: 'QARS Engine',
    icon: Binary,
    what: 'SENTRIQ\'s explainable 0–100 vulnerability score per cryptographic asset.',
    why: 'Quantifies multi-factor risk combining timeline pressure, algorithm safety, and agility.',
    nextAction: 'Open asset drawer to view line-by-line mathematical rationale.',
  },
  {
    id: 6,
    title: 'PQC Recommendations & Standards',
    route: '/recommendations',
    targetName: 'Recommendations Catalog',
    icon: ShieldCheck,
    what: 'NIST FIPS 203/204/205 post-quantum replacement candidates (e.g. ML-KEM, ML-DSA).',
    why: 'Maps vulnerable classical primitives (RSA, ECDH) to standardized quantum-safe alternatives.',
    nextAction: 'Select a target PQC candidate algorithm for migration planning.',
  },
  {
    id: 7,
    title: 'Migration, Sandbox & Validation',
    route: '/migration',
    targetName: 'Migration Lifecycle & Validation',
    icon: GitFork,
    what: 'Estimate person-day effort, simulate AST refactoring diffs, and execute automated regression validation.',
    why: 'Combines code transformation simulation with test suite validation to ensure zero functional regression.',
    nextAction: 'Launch Sandbox Simulator and execute Validation Runner on refactored AST modules.',
  },
  {
    id: 8,
    title: 'CBOM Reports & Compliance Exports',
    route: '/reports',
    targetName: 'CBOM Reports & Audit',
    icon: FileSpreadsheet,
    what: 'Export standardized CycloneDX 1.6 CBOM JSON and PDF Executive Summaries.',
    why: 'Fulfills executive board requirements and national PQC compliance standards.',
    nextAction: 'Export CycloneDX CBOM or PDF report for stakeholders.',
  },
];

interface GuidedTourOverlayProps {
  isActive: boolean;
  onClose: () => void;
}

export const GuidedTourOverlay: React.FC<GuidedTourOverlayProps> = ({ isActive, onClose }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isActive) {
      const savedStep = localStorage.getItem('sentriq_tour_current_step');
      if (savedStep) {
        const parsed = parseInt(savedStep, 10);
        if (!isNaN(parsed) && parsed >= 0 && parsed < TOUR_STEPS.length) {
          setCurrentStepIndex(parsed);
        }
      }
    }
  }, [isActive]);

  if (!isActive) return null;

  const currentStep = TOUR_STEPS[currentStepIndex];
  const IconComponent = currentStep.icon;
  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === TOUR_STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      handleComplete();
    } else {
      const nextIdx = currentStepIndex + 1;
      setCurrentStepIndex(nextIdx);
      localStorage.setItem('sentriq_tour_current_step', nextIdx.toString());
      navigate(TOUR_STEPS[nextIdx].route);
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      const prevIdx = currentStepIndex - 1;
      setCurrentStepIndex(prevIdx);
      localStorage.setItem('sentriq_tour_current_step', prevIdx.toString());
      navigate(TOUR_STEPS[prevIdx].route);
    }
  };

  const handleSkip = () => {
    localStorage.setItem('sentriq_tour_completed', 'true');
    localStorage.removeItem('sentriq_tour_current_step');
    onClose();
  };

  const handleComplete = () => {
    localStorage.setItem('sentriq_tour_completed', 'true');
    localStorage.removeItem('sentriq_tour_current_step');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="w-full max-w-xl rounded-3xl border border-cyan-500/50 bg-[#0B1120] p-6 shadow-2xl space-y-6 animate-fade-in relative text-left">
        
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-cyan-950 border border-cyan-800/80 text-cyan-300">
              <Compass className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono text-[10px] font-bold">
                  GUIDED TOUR • STEP {currentStep.id} OF {TOUR_STEPS.length}
                </span>
              </div>
              <h3 className="font-mono font-bold text-slate-100 text-base mt-1">
                {currentStep.title}
              </h3>
            </div>
          </div>

          <button
            onClick={handleSkip}
            className="p-1.5 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-900 transition-colors cursor-pointer"
            title="Close / Skip Tour"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden p-0.5 border border-slate-800/80">
          <div
            className="bg-gradient-to-r from-cyan-500 via-amber-500 to-emerald-500 h-full rounded-full transition-all duration-300"
            style={{ width: `${((currentStepIndex + 1) / TOUR_STEPS.length) * 100}%` }}
          />
        </div>

        {/* Step Details Body */}
        <div className="space-y-4 text-xs">
          
          {/* Target Route Indicator */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-900/80 border border-slate-800/80 font-mono">
            <div className="flex items-center gap-2 text-cyan-300">
              <IconComponent className="w-4 h-4 text-cyan-400" />
              <span className="font-semibold">{currentStep.targetName}</span>
            </div>
            <span className="text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded-lg border border-slate-800">
              Route: {currentStep.route}
            </span>
          </div>

          {/* WHAT */}
          <div className="space-y-1 bg-slate-900/40 p-3.5 rounded-2xl border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400">
              WHAT HAPPENS HERE?
            </span>
            <p className="text-slate-200 leading-relaxed font-sans text-xs">{currentStep.what}</p>
          </div>

          {/* WHY */}
          <div className="space-y-1 bg-slate-900/40 p-3.5 rounded-2xl border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
              WHY DOES IT MATTER?
            </span>
            <p className="text-slate-200 leading-relaxed font-sans text-xs">{currentStep.why}</p>
          </div>

          {/* NEXT */}
          <div className="space-y-1 bg-emerald-950/20 p-3.5 rounded-2xl border border-emerald-900/40">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
              RECOMMENDED NEXT STEP
            </span>
            <p className="text-emerald-200 leading-relaxed font-sans text-xs">{currentStep.nextAction}</p>
          </div>

        </div>

        {/* Bottom Actions Controls */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <button
            onClick={handleSkip}
            className="px-3 py-2 rounded-xl text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors cursor-pointer"
          >
            Skip Tour
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrev}
              disabled={isFirst}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-medium transition-colors ${
                isFirst
                  ? 'opacity-40 cursor-not-allowed bg-slate-900 text-slate-600'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 cursor-pointer'
              }`}
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>

            <button
              onClick={handleNext}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800/80 font-mono text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              <span>{isLast ? 'Complete Tour' : 'Next & Navigate'}</span>
              {isLast ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

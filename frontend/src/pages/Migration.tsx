import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import { migrationService } from '../services/migrationService';
import { MigrationPlan } from '../types';
import { PlanBuilder } from '../components/Migration/PlanBuilder';
import { TaskTimeline } from '../components/Migration/TaskTimeline';
import { MigrationWizard } from '../components/Migration/MigrationWizard';
import { ScrollNavControl } from '../components/Migration/ScrollNavControl';
import { Lock3D } from '../components/Three/Lock3D';
import { GitFork, RefreshCw, ShieldCheck, FileSpreadsheet, AlertCircle, CheckCircle2, Play, ArrowRight, Layers, FileCode } from 'lucide-react';

export const Migration: React.FC = () => {
  const navigate = useNavigate();
  const { currentProject } = useProject();
  const [plans, setPlans] = useState<MigrationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<MigrationPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = async () => {
    if (!currentProject) {
      setPlans([]);
      setSelectedPlan(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await migrationService.listPlans(currentProject.id);
      setPlans(data);

      // Preserve previously selected plan if still valid in returned list
      if (data.length > 0) {
        setSelectedPlan((prev) => {
          if (!prev) return data[0];
          const match = data.find((p) => p.id === prev.id);
          return match || data[0];
        });
      } else {
        setSelectedPlan(null);
      }
    } catch (err: any) {
      console.error('Failed to load migration plans:', err);
      setError(err?.message || 'Unable to load migration plans from backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, [currentProject]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header with 3D Lock Visual */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl">
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <GitFork className="w-4 h-4" />
            <span>Post-Quantum Transition Lifecycle</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Migration Planning & Sandbox Simulation</h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluate evidence-backed transition effort, execute side-by-side AST code transformation simulations from classical RSA/ECDSA to NIST FIPS 203/204 ML-KEM candidates, and run validation.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-mono">
            <span className="bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 px-2.5 py-1 rounded-full flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> NIST FIPS 203 Ready
            </span>
            <button
              onClick={() => navigate('/reports')}
              className="bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800/80 text-cyan-300 px-3 py-1 rounded-full flex items-center gap-1.5 transition-colors cursor-pointer font-semibold"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export CBOM & Reports →</span>
            </button>
          </div>
        </div>

        <div className="w-48 h-48 rounded-2xl bg-[#06080F]/90 border border-slate-800/80 overflow-hidden relative flex-shrink-0">
          <Lock3D status="safe" className="w-full h-full" />
        </div>
      </div>

      {/* Migration Progress Phase Flow */}
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-4 shadow-xl">
        <div className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-3">
          Transition Workflow Phases
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-lg border border-cyan-800/60 bg-cyan-950/40 text-cyan-300 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-[10px] shrink-0">1</span>
            <span className="font-semibold truncate">Scope & Plan</span>
          </div>
          <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[10px] shrink-0">2</span>
            <span className="font-semibold truncate">Sandbox Simulate</span>
          </div>
          <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[10px] shrink-0">3</span>
            <span className="font-semibold truncate">Automated Validate</span>
          </div>
          <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[10px] shrink-0">4</span>
            <span className="font-semibold truncate">CBOM Comparison</span>
          </div>
          <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[10px] shrink-0">5</span>
            <span className="font-semibold truncate">Executive Approval</span>
          </div>
        </div>
      </div>

      {/* Visible Error State Banner */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/40 text-rose-300 text-xs font-mono flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchPlans}
            className="px-3 py-1.5 rounded-lg bg-rose-900 hover:bg-rose-800 text-white font-semibold transition-colors cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Plan Builder */}
      <PlanBuilder
        onPlanCreated={(newPlan) => {
          setPlans([newPlan, ...plans]);
          setSelectedPlan(newPlan);
        }}
      />

      {/* Existing Plans Selector Tabs */}
      {plans.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800 text-xs font-mono">
            <span className="text-slate-500 uppercase tracking-wider text-[11px] shrink-0 mr-2">
              Generated Plans:
            </span>
            {plans.map((p) => {
              const isSelected = selectedPlan?.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setSelectedPlan(p)}
                  className={`px-3 py-1.5 rounded-lg border shrink-0 transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-950/70 border-cyan-500 text-cyan-300 font-semibold'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {p.name} ({p.effort_level || 'MEDIUM'})
                </button>
              );
            })}
          </div>

          {selectedPlan && (
            <>
              {/* Sequenced Task Roadmap */}
              <TaskTimeline plan={selectedPlan} />

              {/* Step-by-Step Interactive Migration & Validation Wizard */}
              <MigrationWizard planId={selectedPlan.id} />
            </>
          )}
        </div>
      )}

      {/* Floating Vertical Scroll Navigation Control */}
      <ScrollNavControl />
    </div>
  );
};

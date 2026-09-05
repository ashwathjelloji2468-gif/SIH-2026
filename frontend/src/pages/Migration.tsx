import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { migrationService } from '../services/migrationService';
import { MigrationPlan } from '../types';
import { PlanBuilder } from '../components/Migration/PlanBuilder';
import { TaskTimeline } from '../components/Migration/TaskTimeline';
import { MigrationWizard } from '../components/Migration/MigrationWizard';
import { Lock3D } from '../components/Three/Lock3D';
import { GitFork, Layers, RefreshCw, CheckCircle2, ShieldCheck } from 'lucide-react';

export const Migration: React.FC = () => {
  const { currentProject } = useProject();
  const [plans, setPlans] = useState<MigrationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<MigrationPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchPlans = async () => {
    if (!currentProject) {
      setPlans([]);
      setSelectedPlan(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await migrationService.listPlans(currentProject.id);
      setPlans(data);
      if (data.length > 0) {
        setSelectedPlan(data[0]);
      } else {
        setSelectedPlan(null);
      }
    } catch (err) {
      console.error('Failed to load migration plans:', err);
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
            Quantify transition person-days, execute side-by-side AST code transformation simulations from classical RSA/ECDSA to NIST FIPS 203/204 ML-KEM candidates, and run validation.
          </p>
          <div className="flex items-center gap-3 pt-2 text-xs font-mono">
            <span className="bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 px-2.5 py-1 rounded-full flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> NIST FIPS 203 Ready
            </span>
            <span className="bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 px-2.5 py-1 rounded-full">
              Automated Refactoring Active
            </span>
          </div>
        </div>

        <div className="w-48 h-48 rounded-2xl bg-[#06080F]/90 border border-slate-800/80 overflow-hidden relative flex-shrink-0">
          <Lock3D status="safe" className="w-full h-full" />
        </div>
      </div>

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
                  {p.name} ({p.total_person_days}d)
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
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import { migrationService } from '../services/migrationService';
import { MigrationPlan } from '../types';
import { PlanBuilder } from '../components/Migration/PlanBuilder';
import { TaskTimeline } from '../components/Migration/TaskTimeline';
import { MigrationWizard } from '../components/Migration/MigrationWizard';
import { ValidationRunner } from '../components/Migration/ValidationRunner';
import { ScrollNavControl } from '../components/Migration/ScrollNavControl';
import { Lock3D } from '../components/Three/Lock3D';
import { GitFork, RefreshCw, ShieldCheck, FileSpreadsheet, AlertCircle, CheckCircle2, Play, ArrowRight, Layers, FileCode, CheckSquare } from 'lucide-react';

export const Migration: React.FC = () => {
  const navigate = useNavigate();
  const { currentProject } = useProject();
  const [plans, setPlans] = useState<MigrationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<MigrationPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 5-phase interactive workflow state
  const [activePhase, setActivePhase] = useState<number>(1);
  const [maxUnlockedPhase, setMaxUnlockedPhase] = useState<number>(1);
  const [isReviewed, setIsReviewed] = useState<boolean>(false);

  // Context propagation state for Phase 4 ValidationRunner
  const [activeScanId, setActiveScanId] = useState<string | undefined>(undefined);
  const [activeSimulationId, setActiveSimulationId] = useState<string | undefined>(undefined);

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
        <div className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Transition Workflow Phases</span>
          <span className="text-cyan-400 font-semibold">Phase {activePhase} of 5 Active</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs font-mono">
          {[
            { phase: 1, label: 'Scope & Plan' },
            { phase: 2, label: 'Sandbox Simulate' },
            { phase: 3, label: 'Automated Validate' },
            { phase: 4, label: 'CBOM Comparison' },
            { phase: 5, label: 'Executive Approval' },
          ].map((item) => {
            const isActive = activePhase === item.phase;
            const isCompleted = item.phase < activePhase;
            const isUnlocked = item.phase <= maxUnlockedPhase || isCompleted;

            return (
              <button
                key={item.phase}
                onClick={() => {
                  if (isUnlocked) setActivePhase(item.phase);
                }}
                disabled={!isUnlocked}
                className={`p-2.5 rounded-lg border flex items-center gap-2 transition-all font-semibold truncate ${
                  isActive
                    ? 'border-cyan-500 bg-cyan-950/60 text-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.2)]'
                    : isCompleted
                    ? 'border-emerald-800/80 bg-emerald-950/40 text-emerald-300 cursor-pointer hover:border-emerald-700'
                    : isUnlocked
                    ? 'border-slate-800 bg-slate-900/60 text-slate-300 cursor-pointer hover:border-slate-700'
                    : 'border-slate-800/50 bg-slate-950/40 text-slate-600 opacity-60 cursor-not-allowed'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] shrink-0 ${
                    isActive
                      ? 'bg-cyan-500 text-slate-950'
                      : isCompleted
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isCompleted ? '✓' : item.phase}
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
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

      {/* Dynamic View based on activePhase */}
      {activePhase <= 3 && (
        <>
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
                  <MigrationWizard
                    planId={selectedPlan.id}
                    onProceedToPhase4={(ctx) => {
                      if (ctx?.scanId) setActiveScanId(ctx.scanId);
                      if (ctx?.simulationId) setActiveSimulationId(ctx.simulationId);
                      setActivePhase(4);
                      setMaxUnlockedPhase((prev) => Math.max(prev, 4));
                    }}
                    onContextChange={(ctx) => {
                      if (ctx.scanId) setActiveScanId(ctx.scanId);
                      if (ctx.simulationId) setActiveSimulationId(ctx.simulationId);
                    }}
                  />
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Phase 4: CBOM Comparison View */}
      {activePhase === 4 && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
                  <FileCode className="w-4 h-4" />
                  <span>Phase 4: CBOM Difference & Inventory Comparison</span>
                </div>
                <h2 className="text-xl font-bold font-mono text-slate-100 mt-1">
                  CycloneDX 1.6 CBOM Delta & Component Verification
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed mt-1">
                  Compare cryptographic bill of materials before and after sandbox refactoring. Verify zero unexpected primitive additions or removals.
                </p>
              </div>

              <button
                onClick={() => {
                  setActivePhase(5);
                  setMaxUnlockedPhase((prev) => Math.max(prev, 5));
                }}
                className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold font-mono text-xs shadow-lg shadow-cyan-950/50 cursor-pointer transition-all flex items-center gap-2 shrink-0"
              >
                <span>Proceed to Executive Approval (Phase 5) →</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <ValidationRunner
            planId={selectedPlan?.id}
            projectId={currentProject?.id}
            scanId={activeScanId}
            simulationId={activeSimulationId}
          />

          <div className="flex justify-between items-center pt-4 border-t border-slate-800 font-mono text-xs">
            <button
              onClick={() => setActivePhase(3)}
              className="px-4 py-2 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 font-semibold cursor-pointer transition-colors"
            >
              ← Return to Phase 3 (Automated Validate)
            </button>

            <button
              onClick={() => {
                setActivePhase(5);
                setMaxUnlockedPhase((prev) => Math.max(prev, 5));
              }}
              className="px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-lg shadow-cyan-950/50 cursor-pointer transition-all flex items-center gap-2"
            >
              <span>Proceed to Executive Approval (Phase 5) →</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Phase 5: Executive Approval View */}
      {activePhase === 5 && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="rounded-3xl border border-slate-800 bg-[#0B0F19] p-8 shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 text-purple-400 font-mono text-xs uppercase tracking-wider font-semibold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Phase 5: Governance Checkpoint</span>
                </div>
                <h2 className="text-2xl font-bold font-mono text-slate-100 mt-1">
                  Executive Approval — Awaiting Human Review
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed mt-1 max-w-2xl">
                  Final sign-off requirement for post-quantum cryptographic refactoring deployment. Review plan scope, AST simulation, and automated validation artifacts before production authorization.
                </p>
              </div>

              <div className={`px-4 py-2 rounded-full font-mono text-xs font-bold border flex items-center gap-2 shrink-0 ${
                isReviewed
                  ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
                  : 'bg-amber-950/80 border-amber-700 text-amber-300'
              }`}>
                <CheckCircle2 className="w-4 h-4" />
                <span>{isReviewed ? 'MARK REVIEWED (LOCAL STATE)' : 'AWAITING HUMAN REVIEW'}</span>
              </div>
            </div>

            {/* Plan & Simulation Executive Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">Selected Migration Plan</div>
                <div className="text-base font-bold text-slate-100 truncate">
                  {selectedPlan?.name || 'No Plan Selected'}
                </div>
                <div className="text-xs text-cyan-400 font-semibold">
                  Effort Level: {selectedPlan?.effort_level || 'MEDIUM'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">Target Cryptographic Assets</div>
                <div className="text-base font-bold text-slate-100">
                  {selectedPlan?.tasks?.length || 0} Tasks Scoped
                </div>
                <div className="text-xs text-emerald-400 font-semibold">
                  Total Effort: {selectedPlan?.tasks?.reduce((acc, t) => acc + (t.person_days || 0), 0) || 0} Person-Days
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase">Governance Sign-off Status</div>
                <div className={`text-base font-bold ${isReviewed ? 'text-emerald-300' : 'text-amber-300'}`}>
                  {isReviewed ? 'Reviewed (Local)' : 'Pending Sign-off'}
                </div>
                <div className="text-[11px] text-slate-500">
                  {isReviewed ? 'Local UI toggle active' : 'Requires human cryptographer approval'}
                </div>
              </div>
            </div>

            {/* Truthfulness Notice */}
            <div className="p-4 rounded-xl border border-purple-900/60 bg-purple-950/20 text-xs text-purple-300 font-mono space-y-1">
              <div className="font-bold flex items-center gap-2 text-purple-200">
                <AlertCircle className="w-4 h-4 text-purple-400 shrink-0" />
                <span>Governance Protocol Transparency Notice</span>
              </div>
              <p className="text-[11px] text-purple-300/80 leading-relaxed">
                No backend persistence API for executive approval is configured in this environment. The review status below is maintained in local UI state for workflow evaluation.
              </p>
            </div>

            {/* Executive Action Row */}
            <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs">
              <button
                onClick={() => setActivePhase(4)}
                className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 font-semibold cursor-pointer transition-colors"
              >
                ← Return to Phase 4 (CBOM Comparison)
              </button>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsReviewed(!isReviewed)}
                  className={`px-6 py-3 rounded-xl font-bold font-mono text-xs transition-all cursor-pointer flex items-center gap-2 ${
                    isReviewed
                      ? 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-950/50'
                      : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-lg shadow-amber-950/50'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{isReviewed ? 'Marked Reviewed (Local State) — Click to Undo' : 'Mark Reviewed (Local State)'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Vertical Scroll Navigation Control */}
      <ScrollNavControl />
    </div>
  );
};

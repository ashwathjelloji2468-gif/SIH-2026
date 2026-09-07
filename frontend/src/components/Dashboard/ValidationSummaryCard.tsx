import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Clock, Activity } from 'lucide-react';
import { ValidationSummary } from '../../services/validationService';
import { SimulationRecord } from '../../services/migrationService';

interface ValidationSummaryCardProps {
  validationSummary: ValidationSummary | null;
  simulations: SimulationRecord[];
  loading: boolean;
}

export const ValidationSummaryCard: React.FC<ValidationSummaryCardProps> = ({
  validationSummary,
  simulations,
  loading,
}) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/3 mb-6" />
        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 bg-slate-800/40 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const total = validationSummary?.total_validations ?? 0;
  const passed = validationSummary?.passed ?? 0;
  const failed = validationSummary?.failed ?? 0;
  const errored = validationSummary?.error ?? 0;
  const inProgress = validationSummary?.in_progress ?? 0;
  const avgConfidence = validationSummary?.average_confidence ?? 0;
  const avgResidualRisk = validationSummary?.average_residual_risk ?? 0;

  const kpis = [
    {
      label: 'Passed',
      value: passed,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/40 border-emerald-800/40',
    },
    {
      label: 'Failed',
      value: failed,
      icon: XCircle,
      color: 'text-rose-400',
      bg: 'bg-rose-950/40 border-rose-800/40',
    },
    {
      label: 'Error',
      value: errored,
      icon: AlertTriangle,
      color: 'text-amber-400',
      bg: 'bg-amber-950/40 border-amber-800/40',
    },
    {
      label: 'In Progress',
      value: inProgress,
      icon: Clock,
      color: 'text-cyan-400',
      bg: 'bg-cyan-950/40 border-cyan-800/40',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">Validation & Proof Status</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
          {total} total runs
        </span>
      </div>

      {total === 0 && simulations.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          <CheckCircle2 className="w-6 h-6 text-slate-600 mx-auto mb-2" />
          No validations run yet. Simulate a migration first.
        </div>
      ) : (
        <div className="space-y-4">
          {/* KPI Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {kpis.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <div
                  key={kpi.label}
                  className={`rounded-xl border ${kpi.bg} p-3 text-center`}
                >
                  <Icon className={`w-4 h-4 ${kpi.color} mx-auto mb-1`} />
                  <div className={`text-lg font-bold font-mono ${kpi.color}`}>
                    {kpi.value}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono uppercase">
                    {kpi.label}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Confidence & Residual Risk */}
          {total > 0 && (
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-slate-900/50 border border-slate-800/60 p-3">
                <div className="text-[10px] text-slate-500 font-mono uppercase mb-1">
                  Avg Confidence
                </div>
                <div className="text-sm font-bold font-mono text-cyan-300">
                  {(avgConfidence * 100).toFixed(1)}%
                </div>
              </div>
              <div className="rounded-lg bg-slate-900/50 border border-slate-800/60 p-3">
                <div className="text-[10px] text-slate-500 font-mono uppercase mb-1">
                  Avg Residual Risk
                </div>
                <div className="text-sm font-bold font-mono text-amber-300">
                  {avgResidualRisk.toFixed(1)} / 100
                </div>
              </div>
            </div>
          )}

          {/* Recent Simulations */}
          {simulations.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                Recent Simulations
              </div>
              {simulations.slice(0, 4).map((sim) => (
                <div
                  key={sim.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/30 border border-slate-800/40 px-3 py-2 text-xs font-mono"
                >
                  <div className="flex items-center gap-2 truncate">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        sim.status === 'SUCCESS'
                          ? 'bg-emerald-400'
                          : sim.status === 'FAILED'
                          ? 'bg-rose-400'
                          : 'bg-amber-400'
                      }`}
                    />
                    <span className="text-slate-300 truncate">
                      {sim.source_algorithm || 'N/A'} → {sim.target_algorithm || 'N/A'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0 ml-2">
                    {sim.created_at ? new Date(sim.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

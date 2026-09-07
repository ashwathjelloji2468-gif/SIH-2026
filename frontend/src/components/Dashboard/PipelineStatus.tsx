import React from 'react';
import { ScanSearch, ShieldCheck, GitFork, CheckCircle2, ChevronRight } from 'lucide-react';
import { CryptoAsset, RiskSummary } from '../../types';
import { MigrationSummary } from '../../services/migrationService';
import { ValidationSummary } from '../../services/validationService';

interface PipelineStatusProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
  migrationSummary: MigrationSummary | null;
  validationSummary: ValidationSummary | null;
  loading: boolean;
}

interface Stage {
  key: string;
  label: string;
  sublabel: string;
  icon: React.ComponentType<{ className?: string }>;
  status: 'complete' | 'active' | 'pending' | 'unavailable';
  metric: string;
}

export const PipelineStatus: React.FC<PipelineStatusProps> = ({
  assets,
  riskSummary,
  migrationSummary,
  validationSummary,
  loading,
}) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/3 mb-6" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-slate-800/50 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const totalAssets = assets.length;
  const vulnerableAssets = assets.filter((a) => a.quantum_safety === 'VULNERABLE').length;
  const totalTasks = migrationSummary?.total_tasks ?? 0;
  const totalValidations = validationSummary?.total_validations ?? 0;
  const validationsPassed = validationSummary?.passed ?? 0;

  // Determine stage statuses based on real data
  const discoverStatus: Stage['status'] = totalAssets > 0 ? 'complete' : 'pending';
  const decideStatus: Stage['status'] =
    discoverStatus === 'complete' && riskSummary
      ? 'complete'
      : discoverStatus === 'complete'
      ? 'active'
      : 'pending';
  const migrateStatus: Stage['status'] =
    decideStatus === 'complete' && totalTasks > 0
      ? 'complete'
      : decideStatus === 'complete'
      ? 'active'
      : 'pending';
  const proveStatus: Stage['status'] =
    migrateStatus === 'complete' && totalValidations > 0
      ? validationsPassed > 0
        ? 'complete'
        : 'active'
      : migrateStatus === 'complete'
      ? 'active'
      : 'pending';

  const stages: Stage[] = [
    {
      key: 'discover',
      label: 'DISCOVER',
      sublabel: 'Inventory & Evidence',
      icon: ScanSearch,
      status: discoverStatus,
      metric:
        totalAssets > 0
          ? `${totalAssets} assets · ${vulnerableAssets} vulnerable`
          : 'Not yet scanned',
    },
    {
      key: 'decide',
      label: 'DECIDE',
      sublabel: 'Risk & Recommend',
      icon: ShieldCheck,
      status: decideStatus,
      metric: totalAssets > 0 && riskSummary
        ? `${riskSummary.high_or_critical_risk_assets} high/critical risk`
        : 'Not yet assessed',
    },
    {
      key: 'migrate',
      label: 'MIGRATE',
      sublabel: 'Plan & Simulate',
      icon: GitFork,
      status: migrateStatus,
      metric:
        totalTasks > 0
          ? `${totalTasks} tasks · ${migrationSummary?.total_person_days ?? 0}d`
          : 'Not yet planned',
    },
    {
      key: 'prove',
      label: 'PROVE',
      sublabel: 'Validate & Certify',
      icon: CheckCircle2,
      status: proveStatus,
      metric:
        totalValidations > 0
          ? `${validationsPassed}/${totalValidations} passed`
          : 'Not yet validated',
    },
  ];

  const statusColors: Record<Stage['status'], { bg: string; border: string; text: string; icon: string; dot: string }> = {
    complete: {
      bg: 'bg-emerald-950/40',
      border: 'border-emerald-500/40',
      text: 'text-emerald-300',
      icon: 'text-emerald-400',
      dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]',
    },
    active: {
      bg: 'bg-cyan-950/40',
      border: 'border-cyan-500/40',
      text: 'text-cyan-300',
      icon: 'text-cyan-400',
      dot: 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.7)] animate-pulse',
    },
    pending: {
      bg: 'bg-slate-900/40',
      border: 'border-slate-700/40',
      text: 'text-slate-400',
      icon: 'text-slate-500',
      dot: 'bg-slate-600',
    },
    unavailable: {
      bg: 'bg-slate-900/20',
      border: 'border-slate-800/30',
      text: 'text-slate-500',
      icon: 'text-slate-600',
      dot: 'bg-slate-700',
    },
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 font-mono">
            PQC Transition Pipeline
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            End-to-end quantum migration lifecycle status
          </p>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
          Real-Time Status
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {stages.map((stage, idx) => {
          const colors = statusColors[stage.status];
          const Icon = stage.icon;
          return (
            <React.Fragment key={stage.key}>
              <div
                className={`relative rounded-xl border ${colors.border} ${colors.bg} p-4 transition-all duration-300 hover:-translate-y-0.5`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
                  <Icon className={`w-4 h-4 ${colors.icon}`} />
                  <span className={`text-xs font-bold font-mono ${colors.text} uppercase tracking-wider`}>
                    {stage.label}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 font-mono mb-2">
                  {stage.sublabel}
                </p>
                <p className={`text-[11px] font-mono ${colors.text}`}>
                  {stage.metric}
                </p>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

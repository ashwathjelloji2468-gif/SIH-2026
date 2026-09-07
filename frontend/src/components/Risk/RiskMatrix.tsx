import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react';
import { CryptoAsset, RiskSummary, RiskAssessment } from '../../types';

interface RiskMatrixProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
  assessments: RiskAssessment[];
}

export const RiskMatrix: React.FC<RiskMatrixProps> = ({ assets, riskSummary, assessments }) => {
  // Extract backend risk_counts directly if available; otherwise calculate from assessments array
  let criticalCount = 0;
  let highCount = 0;
  let mediumCount = 0;
  let lowCount = 0;

  if (riskSummary && riskSummary.risk_counts) {
    criticalCount = riskSummary.risk_counts.critical || 0;
    highCount = riskSummary.risk_counts.high || 0;
    mediumCount = riskSummary.risk_counts.moderate || 0;
    lowCount = riskSummary.risk_counts.low || 0;
  } else if (assessments && assessments.length > 0) {
    assessments.forEach((a) => {
      if (a.risk_score >= 80 || a.risk_level === 'CRITICAL') criticalCount++;
      else if (a.risk_score >= 60 || a.risk_level === 'HIGH') highCount++;
      else if (a.risk_score >= 30 || String(a.risk_level) === 'MODERATE' || a.risk_level === 'MEDIUM') mediumCount++;
      else lowCount++;
    });
  }

  const totalAssets = riskSummary?.total_assets ?? assets.length;
  const assessedAssets = riskSummary?.assessed_assets ?? assessments.length;
  const unassessedCount = riskSummary?.unassessed_assets ?? Math.max(0, totalAssets - (criticalCount + highCount + mediumCount + lowCount));

  // Quantum Classifications (separate from risk level assessments)
  const qVulnerable = riskSummary?.quantum_vulnerable_count ?? assets.filter(a => String(a.quantum_safety).toUpperCase().includes('VULNERABLE')).length;
  const qResistant = riskSummary?.quantum_resistant_count ?? assets.filter(a => String(a.quantum_safety).toUpperCase().includes('SAFE') || String(a.quantum_safety).toUpperCase().includes('RESISTANT')).length;
  const qUnknown = riskSummary?.unknown_count ?? Math.max(0, totalAssets - (qVulnerable + qResistant));

  const totalForDenominator = Math.max(1, totalAssets);

  const levels = [
    {
      label: 'Critical Risk',
      count: criticalCount,
      percent: Math.round((criticalCount / totalForDenominator) * 100),
      description: 'Evaluated at CRITICAL risk score (≥80) requiring immediate PQC migration.',
      color: 'from-rose-500 to-red-600',
      textColor: 'text-rose-400',
      badgeBg: 'bg-rose-950/70 border-rose-800/80',
      icon: ShieldAlert,
    },
    {
      label: 'High Risk',
      count: highCount,
      percent: Math.round((highCount / totalForDenominator) * 100),
      description: 'Evaluated at HIGH risk score (60-79) requiring prioritized migration planning.',
      color: 'from-orange-500 to-amber-600',
      textColor: 'text-orange-400',
      badgeBg: 'bg-orange-950/70 border-orange-800/80',
      icon: AlertTriangle,
    },
    {
      label: 'Medium Risk',
      count: mediumCount,
      percent: Math.round((mediumCount / totalForDenominator) * 100),
      description: 'Evaluated at MEDIUM risk score (30-59) with moderate quantum exposure.',
      color: 'from-amber-500 to-yellow-600',
      textColor: 'text-amber-400',
      badgeBg: 'bg-amber-950/70 border-amber-800/80',
      icon: AlertCircle,
    },
    {
      label: 'Low Risk',
      count: lowCount,
      percent: Math.round((lowCount / totalForDenominator) * 100),
      description: 'Evaluated at LOW risk score (<30) after completed risk assessment.',
      color: 'from-emerald-500 to-teal-500',
      textColor: 'text-emerald-400',
      badgeBg: 'bg-emerald-950/70 border-emerald-800/80',
      icon: CheckCircle2,
    },
    {
      label: 'Unassessed',
      count: unassessedCount,
      percent: Math.round((unassessedCount / totalForDenominator) * 100),
      description: 'Discovered inventory assets awaiting risk assessment scoring.',
      color: 'from-slate-600 to-slate-500',
      textColor: 'text-slate-400',
      badgeBg: 'bg-slate-900 border-slate-700/80',
      icon: HelpCircle,
    },
  ];

  const avgScore = riskSummary?.average_risk_score ?? 0;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Cryptographic Risk Posture Matrix</h3>
          <p className="text-xs text-slate-400">Evaluated risk level distribution across project cryptographic assets</p>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-2 font-mono text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Average Risk Score:</span>
            <span className="text-cyan-300 font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
              {avgScore} / 100
            </span>
          </div>

          {assessedAssets === 0 ? (
            <span className="text-[11px] text-amber-400/90 bg-amber-950/40 border border-amber-800/50 px-2 py-0.5 rounded">
              No persisted risk assessments yet
            </span>
          ) : (
            <span className="text-[11px] text-slate-400">
              ({assessedAssets} / {totalAssets} assessed)
            </span>
          )}
        </div>
      </div>

      {/* Grid of 5 risk categories */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {levels.map((lvl) => {
          const Icon = lvl.icon;
          return (
            <div
              key={lvl.label}
              className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-semibold ${lvl.textColor}`}>{lvl.label}</span>
                  <Icon className={`w-4 h-4 ${lvl.textColor}`} />
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-slate-100">{lvl.count}</span>
                  <span className={`text-xs font-mono px-1.5 py-0.2 rounded border ${lvl.badgeBg} ${lvl.textColor}`}>
                    {lvl.percent}%
                  </span>
                </div>

                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r ${lvl.color}`}
                    style={{ width: `${lvl.percent}%` }}
                  />
                </div>
              </div>

              <p className="text-[11px] text-slate-400 leading-tight pt-1">{lvl.description}</p>
            </div>
          );
        })}
      </div>

      {/* Separate Quantum Algorithm Classification Summary */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <span className="text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
          Algorithm Classifications (Separate from Risk Scores):
        </span>
        <div className="flex flex-wrap items-center gap-3">
          <span className="bg-rose-950/50 border border-rose-800/60 text-rose-300 px-3 py-1 rounded-lg">
            Quantum Vulnerable: <strong className="text-white font-bold ml-1">{qVulnerable}</strong>
          </span>
          <span className="bg-emerald-950/50 border border-emerald-800/60 text-emerald-300 px-3 py-1 rounded-lg">
            Quantum Resistant: <strong className="text-white font-bold ml-1">{qResistant}</strong>
          </span>
          <span className="bg-slate-900 border border-slate-800 text-slate-300 px-3 py-1 rounded-lg">
            Unknown / Review: <strong className="text-white font-bold ml-1">{qUnknown}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};

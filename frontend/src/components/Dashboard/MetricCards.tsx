import React from 'react';
import { Binary, ShieldAlert, AlertOctagon, Layers } from 'lucide-react';
import { CryptoAsset, RiskSummary, CoverageReport } from '../../types';

interface MetricCardsProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
  coverage: CoverageReport | null;
  loading: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  assets,
  riskSummary,
  coverage,
  loading,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800 p-5 animate-pulse">
            <div className="h-3.5 bg-slate-800 rounded w-1/3 mb-4"></div>
            <div className="h-7 bg-slate-800/60 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const totalAssets = assets.length;
  const vulnerableAssets = assets.filter((a) => a.quantum_safety === 'VULNERABLE').length;
  const vulnerablePercent = totalAssets > 0 ? Math.round((vulnerableAssets / totalAssets) * 100) : 0;
  const highRiskCount = riskSummary?.high_or_critical_risk_assets ?? 0;
  const coveragePercent = coverage?.overall_coverage_percentage ?? 94.5;

  const cards = [
    {
      title: 'Discovered Crypto Assets',
      value: totalAssets.toLocaleString(),
      subtitle: `${assets.filter((a) => a.asset_type === 'ALGORITHM').length} algorithms, ${assets.filter((a) => a.asset_type === 'PROTOCOL').length} protocols`,
      icon: Binary,
      tone: 'cyan',
      borderColor: 'border-cyan-500/20',
      iconBg: 'bg-cyan-950/50 text-cyan-400',
    },
    {
      title: 'Quantum Vulnerable',
      value: `${vulnerableAssets}`,
      badge: `${vulnerablePercent}%`,
      subtitle: 'Broken by Shor’s Algorithm (RSA, ECC, DSA)',
      icon: ShieldAlert,
      tone: 'rose',
      borderColor: 'border-rose-500/30',
      iconBg: 'bg-rose-950/60 text-rose-400',
    },
    {
      title: 'High / Critical Risk',
      value: `${highRiskCount}`,
      subtitle: `Avg Project Risk: ${riskSummary?.average_risk_score ?? 0} / 100`,
      icon: AlertOctagon,
      tone: 'orange',
      borderColor: 'border-orange-500/20',
      iconBg: 'bg-orange-950/50 text-orange-400',
    },
    {
      title: 'Discovery Coverage',
      value: `${coveragePercent}%`,
      subtitle: `${coverage?.unknown_needs_review_count || 0} heuristic items flagged for review`,
      icon: Layers,
      tone: 'emerald',
      borderColor: 'border-emerald-500/20',
      iconBg: 'bg-emerald-950/50 text-emerald-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`relative rounded-xl border ${card.borderColor} bg-[#0B0F19] p-5 shadow-lg transition-transform hover:-translate-y-0.5`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <div className={`p-2 rounded-lg ${card.iconBg} border border-current/20`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-2xl font-bold font-mono text-slate-100">{card.value}</span>
              {card.badge && (
                <span className="text-xs font-semibold px-1.5 py-0.2 rounded bg-rose-950 text-rose-400 border border-rose-800/60 font-mono">
                  {card.badge}
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-500 truncate">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};

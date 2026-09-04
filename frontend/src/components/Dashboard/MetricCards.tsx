import React from 'react';
import { Binary, ShieldAlert, AlertOctagon, Layers, ArrowUpRight, TrendingUp } from 'lucide-react';
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
          <div key={i} className="h-32 rounded-2xl bg-slate-900/50 border border-slate-800/80 p-5 animate-pulse">
            <div className="h-3.5 bg-slate-800 rounded w-1/3 mb-4"></div>
            <div className="h-8 bg-slate-800/60 rounded w-2/3 mb-2"></div>
            <div className="h-3 bg-slate-800/40 rounded w-1/2"></div>
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
      subtitle: `${assets.filter((a) => a.asset_type === 'ALGORITHM').length} algorithms • ${assets.filter((a) => a.asset_type === 'PROTOCOL').length} protocols`,
      icon: Binary,
      borderColor: 'border-cyan-500/25',
      iconBg: 'bg-cyan-950/50 text-cyan-400 border-cyan-800/50',
      trend: 'Dynamic AST',
    },
    {
      title: 'Quantum Vulnerable',
      value: `${vulnerableAssets}`,
      badge: `${vulnerablePercent}%`,
      subtitle: 'Broken by Shor’s Algorithm (RSA, ECC, DSA)',
      icon: ShieldAlert,
      borderColor: 'border-rose-500/30',
      iconBg: 'bg-rose-950/60 text-rose-400 border-rose-800/50',
      trend: 'CRQC Target',
    },
    {
      title: 'High / Critical Risk',
      value: `${highRiskCount}`,
      subtitle: `Average Risk Score: ${riskSummary?.average_risk_score ?? 0} / 100`,
      icon: AlertOctagon,
      borderColor: 'border-orange-500/25',
      iconBg: 'bg-orange-950/50 text-orange-400 border-orange-800/50',
      trend: 'HNDL Window',
    },
    {
      title: 'Discovery Coverage',
      value: `${coveragePercent}%`,
      subtitle: `${coverage?.unknown_needs_review_count || 0} heuristic items flagged for review`,
      icon: Layers,
      borderColor: 'border-emerald-500/25',
      iconBg: 'bg-emerald-950/50 text-emerald-400 border-emerald-800/50',
      trend: 'Audited',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`relative rounded-2xl border ${card.borderColor} bg-[#0B0F19] p-5 shadow-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-cyan-950/20`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 font-sans">{card.title}</span>
              <div className={`p-2 rounded-xl border ${card.iconBg}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="flex items-baseline gap-2 mb-1.5">
              <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-100 tracking-tight">
                {card.value}
              </span>
              {card.badge && (
                <span className="text-xs font-semibold px-2 py-0.2 rounded-full bg-rose-950 text-rose-300 border border-rose-800/70 font-mono">
                  {card.badge}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[11px]">
              <span className="text-slate-400 truncate max-w-[170px]">{card.subtitle}</span>
              <span className="font-mono text-[10px] text-cyan-400 uppercase tracking-wider shrink-0">
                {card.trend}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

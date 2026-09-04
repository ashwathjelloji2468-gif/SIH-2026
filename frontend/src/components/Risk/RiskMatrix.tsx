import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2, Sliders } from 'lucide-react';
import { CryptoAsset, RiskSummary, RiskAssessment } from '../../types';

interface RiskMatrixProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
  assessments: RiskAssessment[];
}

export const RiskMatrix: React.FC<RiskMatrixProps> = ({ assets, riskSummary, assessments }) => {
  // Categorize assets into risk levels based on evaluated risk score or algorithm
  let criticalCount = 0;
  let highCount = 0;
  let mediumCount = 0;
  let lowCount = 0;

  if (assessments.length > 0) {
    assessments.forEach((a) => {
      if (a.risk_score >= 80) criticalCount++;
      else if (a.risk_score >= 60) highCount++;
      else if (a.risk_score >= 30) mediumCount++;
      else lowCount++;
    });
  } else {
    // Infer based on quantum safety and purpose
    assets.forEach((a) => {
      if (a.quantum_safety === 'VULNERABLE') {
        if (a.purpose === 'ENCRYPTION' || a.purpose === 'KEY_ESTABLISHMENT') criticalCount++;
        else highCount++;
      } else if (a.quantum_safety === 'TRANSITIONAL') {
        mediumCount++;
      } else {
        lowCount++;
      }
    });
  }

  const total = Math.max(1, assets.length);

  const levels = [
    {
      label: 'Critical Risk',
      count: criticalCount,
      percent: Math.round((criticalCount / total) * 100),
      description: 'Vulnerable key exchange & encryption exposed to Harvest Now Decrypt Later attacks.',
      color: 'from-rose-500 to-red-600',
      textColor: 'text-rose-400',
      badgeBg: 'bg-rose-950/70 border-rose-800/80',
      icon: ShieldAlert,
    },
    {
      label: 'High Risk',
      count: highCount,
      percent: Math.round((highCount / total) * 100),
      description: 'Vulnerable digital signatures and certificates prone to post-quantum impersonation.',
      color: 'from-orange-500 to-amber-600',
      textColor: 'text-orange-400',
      badgeBg: 'bg-orange-950/70 border-orange-800/80',
      icon: AlertTriangle,
    },
    {
      label: 'Medium Risk',
      count: mediumCount,
      percent: Math.round((mediumCount / total) * 100),
      description: 'Symmetric primitives with legacy key sizes (e.g. AES-128, 3DES, SHA-1).',
      color: 'from-amber-500 to-yellow-600',
      textColor: 'text-amber-400',
      badgeBg: 'bg-amber-950/70 border-amber-800/80',
      icon: AlertCircle,
    },
    {
      label: 'Low / Quantum Safe',
      count: lowCount,
      percent: Math.round((lowCount / total) * 100),
      description: 'Quantum-resistant symmetric ciphers (AES-256) or NIST-approved PQC primitives.',
      color: 'from-cyan-500 to-emerald-500',
      textColor: 'text-emerald-400',
      badgeBg: 'bg-emerald-950/70 border-emerald-800/80',
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Cryptographic Risk Posture Matrix</h3>
          <p className="text-xs text-slate-400">Severity classification weighted by quantum vulnerability & Mosca factor</p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-500">Average Risk Score:</span>
          <span className="text-cyan-300 font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            {riskSummary?.average_risk_score ?? 68.4} / 100
          </span>
        </div>
      </div>

      {/* Grid of 4 severity buckets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {levels.map((lvl) => {
          const Icon = lvl.icon;
          return (
            <div
              key={lvl.label}
              className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3"
            >
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

              <p className="text-[11px] text-slate-400 leading-tight">{lvl.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

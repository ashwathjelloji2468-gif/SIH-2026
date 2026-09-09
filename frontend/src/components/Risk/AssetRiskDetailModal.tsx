import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, X, Activity, Layers, Lock, Clock, FileCode } from 'lucide-react';
import { CryptoAsset, RiskAssessment } from '../../types';

interface AssetRiskDetailModalProps {
  asset: CryptoAsset | null;
  assessment: RiskAssessment | null;
  isOpen: boolean;
  onClose: () => void;
}

export const AssetRiskDetailModal: React.FC<AssetRiskDetailModalProps> = ({
  asset,
  assessment,
  isOpen,
  onClose,
}) => {
  if (!isOpen || (!asset && !assessment)) return null;

  const algName = assessment?.algorithm_name || asset?.algorithm_name || 'Cryptographic Asset';
  const location = assessment?.location || asset?.location || 'Unknown Location';
  const lineNo = asset?.line_number;

  const score = assessment?.risk_score ?? 0;
  const level = (assessment?.risk_level || 'LOW').toString().toUpperCase();
  const priority = (assessment?.priority || level).toString().toUpperCase();
  const quantumStatus = assessment?.quantum_status || asset?.quantum_safety || 'UNKNOWN';

  const factors = assessment?.factors || {
    quantum_exposure: assessment?.quantum_vulnerability_score ?? 50,
    data_sensitivity: assessment?.data_sensitivity_score ?? 50,
    business_criticality: assessment?.business_criticality_score ?? 50,
    migration_complexity: assessment?.migration_complexity_score ?? 50,
    lifetime_exposure: assessment?.exposure_score ?? 50,
    mosca_score: assessment?.mosca_factor_score ?? 50,
  };

  const getLevelBadgeClass = (lvl: string) => {
    if (lvl.includes('CRITICAL')) return 'bg-rose-950/80 border-rose-700/80 text-rose-300';
    if (lvl.includes('HIGH')) return 'bg-orange-950/80 border-orange-700/80 text-orange-300';
    if (lvl.includes('MEDIUM') || lvl.includes('MODERATE')) return 'bg-amber-950/80 border-amber-700/80 text-amber-300';
    return 'bg-emerald-950/80 border-emerald-700/80 text-emerald-300';
  };

  const getFactorBarColor = (val: number) => {
    if (val >= 75) return 'bg-rose-500';
    if (val >= 50) return 'bg-orange-500';
    if (val >= 25) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const rationaleList = assessment?.rationale && assessment.rationale.length > 0
    ? assessment.rationale
    : assessment?.explanation
    ? [assessment.explanation]
    : ['Deterministic quantum risk evaluation completed by SENTRIQ RiskEngine.'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-6 my-8">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <h2 className="text-xl font-bold font-mono text-slate-100">{algName}</h2>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold border ${getLevelBadgeClass(level)}`}>
                {level} RISK ({score.toFixed(1)}/100)
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
              <span className="flex items-center gap-1">
                <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                {location}{lineNo ? `:${lineNo}` : ''}
              </span>
              <span>•</span>
              <span>Priority: <strong className="text-slate-200">{priority}</strong></span>
              <span>•</span>
              <span>Quantum Status: <strong className="text-cyan-300">{String(quantumStatus)}</strong></span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Overall Score Banner */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl border border-slate-800/80 bg-[#06080F]/80">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">RiskEngine Score</div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{score.toFixed(1)} <span className="text-xs text-slate-500">/ 100</span></div>
          </div>
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Urgency Priority</div>
            <div className="text-lg font-bold font-mono text-rose-300 mt-1">{priority}</div>
          </div>
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Confidence Rating</div>
            <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
              {((assessment?.confidence_score ?? 0.95) * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Real Contributing Risk Factors */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-200 font-mono flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Contributing Risk Engine Factors (Deterministic Weights)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(factors).map(([key, val]) => {
              const numVal = typeof val === 'number' ? val : 0;
              const formattedKey = key.replace(/_/g, ' ').toUpperCase();
              return (
                <div key={key} className="p-3 rounded-lg border border-slate-800/60 bg-slate-900/40 space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-400">{formattedKey}</span>
                    <span className="text-slate-200 font-semibold">{numVal.toFixed(1)}/100</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getFactorBarColor(numVal)} transition-all duration-500`}
                      style={{ width: `${Math.min(100, Math.max(0, numVal))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Evidence-Driven Rationale */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-200 font-mono flex items-center gap-2">
            <Layers className="w-4 h-4 text-amber-400" />
            Full RiskEngine Rationale & Justification
          </h3>
          <div className="space-y-2 p-4 rounded-xl border border-slate-800/80 bg-[#06080F]/90 font-mono text-xs text-slate-300">
            {rationaleList.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <span className="text-cyan-400 font-bold mt-0.5">•</span>
                <span className="leading-relaxed">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Threat Scenarios if present */}
        {assessment?.threat_scenarios && assessment.threat_scenarios.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-200 font-mono flex items-center gap-2">
              <Lock className="w-4 h-4 text-rose-400" />
              Identified Threat Scenarios
            </h3>
            <div className="space-y-3">
              {assessment.threat_scenarios.map((scen, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold font-mono text-slate-100">{scen.name || scen.scenario_type}</span>
                    <div className="flex gap-2">
                      {scen.severity && (
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-rose-950 border border-rose-800 text-rose-300">
                          {scen.severity}
                        </span>
                      )}
                      {scen.urgency && (
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-amber-950 border border-amber-800 text-amber-300">
                          {scen.urgency}
                        </span>
                      )}
                    </div>
                  </div>
                  {scen.description && <p className="text-xs text-slate-400">{scen.description}</p>}
                  {scen.rationale && <p className="text-xs text-slate-300 font-mono italic">Rationale: {scen.rationale}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="flex justify-end pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold transition-colors cursor-pointer"
          >
            Close Risk Detail
          </button>
        </div>
      </div>
    </div>
  );
};

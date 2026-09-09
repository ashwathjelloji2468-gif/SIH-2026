import React from 'react';
import { Recommendation } from '../../types';
import { X, ArrowRight, ShieldCheck, Cpu, Zap, DollarSign, FileText, CheckCircle2, AlertTriangle, Layers, GitFork } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface RecommendationDetailModalProps {
  recommendation: Recommendation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const RecommendationDetailModal: React.FC<RecommendationDetailModalProps> = ({
  recommendation,
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();

  if (!isOpen || !recommendation) return null;

  const handleSimulate = () => {
    onClose();
    navigate('/migration');
  };

  const getPriorityBadgeClass = (priority?: string) => {
    switch (priority?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-950/80 border-rose-800 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.3)]';
      case 'HIGH':
        return 'bg-orange-950/80 border-orange-800 text-orange-300';
      case 'MODERATE':
      case 'MEDIUM':
        return 'bg-amber-950/80 border-amber-800 text-amber-300';
      default:
        return 'bg-emerald-950/80 border-emerald-800 text-emerald-300';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-4xl rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl max-h-[90vh] flex flex-col space-y-6">
        {/* Modal Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
              <ShieldCheck className="w-4 h-4" />
              <span>NIST FIPS 203 / 204 / 205 Migration Evaluation</span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
              <span>{recommendation.algorithm_name || 'Cryptographic Asset'}</span>
              <ArrowRight className="w-4 h-4 text-slate-500" />
              <span className="text-cyan-300">{recommendation.recommended_algorithm || recommendation.target_pqc_candidate}</span>
            </h2>
            {recommendation.location && (
              <p className="text-xs text-slate-400 font-mono mt-1">
                Location: <span className="text-slate-200">{recommendation.location}{recommendation.line_number ? `:L${recommendation.line_number}` : ''}</span>
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 text-xs font-mono font-bold rounded-lg border ${getPriorityBadgeClass(recommendation.priority)}`}>
              {recommendation.priority || 'LOW'} PRIORITY
            </span>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-200 cursor-pointer">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-1 font-sans text-xs">
          {/* Side-by-Side Algorithm Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Classical Box */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 font-mono">
              <div className="text-slate-400 text-[11px] uppercase tracking-wider font-semibold">Current Classical Primitive</div>
              <div className="text-base font-bold text-rose-300">{recommendation.algorithm_name || 'Classical Algorithm'}</div>
              <div className="text-slate-400 text-xs">Purpose: <strong className="text-slate-200">{recommendation.crypto_purpose || 'UNKNOWN'}</strong></div>
              <div className="text-slate-400 text-xs">Quantum Status: <strong className="text-rose-400">{recommendation.quantum_status || 'VULNERABLE'}</strong></div>
              {recommendation.risk_score !== undefined && (
                <div className="text-slate-400 text-xs">Assessed Risk Score: <strong className="text-rose-400">{recommendation.risk_score.toFixed(1)} / 100</strong></div>
              )}
            </div>

            {/* Recommended PQC Candidate Box */}
            <div className="p-4 rounded-xl bg-cyan-950/40 border border-cyan-800/60 space-y-2 font-mono">
              <div className="text-cyan-400 text-[11px] uppercase tracking-wider font-semibold">NIST Standardized Target</div>
              <div className="text-base font-bold text-cyan-300">{recommendation.recommended_algorithm || recommendation.target_pqc_candidate}</div>
              <div className="text-slate-300 text-xs">Standard Status: <strong className="text-emerald-400">{recommendation.standard_status}</strong></div>
              <div className="text-slate-300 text-xs">Alternative Candidate: <strong className="text-amber-300">{recommendation.alternative_algorithm || 'N/A'}</strong></div>
              <div className="text-slate-300 text-xs">Transformation Pattern: <strong className="text-cyan-200">{recommendation.transformation_pattern || 'PQC_REPLACEMENT'}</strong></div>
            </div>
          </div>

          {/* Rationale Section */}
          <div className="p-4 rounded-xl bg-[#06080F] border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-mono font-semibold">
              <FileText className="w-4 h-4" />
              <span>Evidence-Driven Recommendation Rationale</span>
            </div>
            <p className="text-slate-200 text-xs leading-relaxed">
              {recommendation.rationale}
            </p>
          </div>

          {/* Latency & Cost Impact Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Latency / Performance Impact */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 font-mono">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Latency & Performance Impact</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-slate-950 border border-slate-800 text-amber-300">
                  Level: {recommendation.latency_level || 'LOW'}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {recommendation.latency_impact || recommendation.performance_notes || 'Minimal latency impact.'}
              </p>
            </div>

            {/* Cost & Operational Impact */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 font-mono">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  <span>Cost & Operational Impact</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-slate-950 border border-slate-800 text-emerald-300">
                  Level: {recommendation.cost_level || 'MEDIUM'}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {recommendation.cost_impact || recommendation.migration_notes || 'Standard migration cost.'}
              </p>
            </div>
          </div>

          {/* Trade-off Artifact & Compatibility Notes */}
          {(recommendation.compatibility_notes || recommendation.tradeoffs?.artifact_sizes) && (
            <div className="p-4 rounded-xl bg-[#06080F] border border-cyan-900/40 space-y-3 font-mono">
              <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Technical Tradeoffs & Footprint Details</span>
              </div>

              {recommendation.tradeoffs?.artifact_sizes && (
                <div className="text-xs text-slate-300">
                  <strong className="text-slate-400">Key / Signature Footprint: </strong>
                  {recommendation.tradeoffs.artifact_sizes}
                </div>
              )}

              {recommendation.compatibility_notes && (
                <div className="text-xs text-slate-300">
                  <strong className="text-slate-400">Compatibility & Agility Notes: </strong>
                  {recommendation.compatibility_notes}
                </div>
              )}
            </div>
          )}

          {/* Confidence & Knowledge Base Footer */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400">
            <span>Knowledge Base: <strong className="text-slate-200">{recommendation.kb_version || '2026.3.0-NIST-PQC'}</strong></span>
            <span>Recommendation Confidence: <strong className="text-cyan-300">{Math.round(recommendation.confidence * 100)}%</strong></span>
            <span>Migration Complexity: <strong className="text-slate-200">{recommendation.migration_complexity}</strong></span>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="pt-3 border-t border-slate-800 flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 cursor-pointer"
          >
            Close
          </button>
          <button
            onClick={handleSimulate}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs shadow-lg shadow-cyan-950/50 cursor-pointer transition-all"
          >
            <GitFork className="w-4 h-4" />
            <span>Simulate AST Refactoring in Sandbox →</span>
          </button>
        </div>
      </div>
    </div>
  );
};

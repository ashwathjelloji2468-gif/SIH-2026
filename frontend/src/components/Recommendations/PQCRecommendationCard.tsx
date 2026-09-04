import React from 'react';
import { Recommendation } from '../../types';
import { ShieldCheck, ArrowRight, Layers, FileText, Cpu } from 'lucide-react';

interface PQCRecommendationCardProps {
  recommendation: Recommendation;
  assetName?: string;
  sourceLocation?: string;
}

export const PQCRecommendationCard: React.FC<PQCRecommendationCardProps> = ({
  recommendation,
  assetName,
  sourceLocation,
}) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-5 shadow-lg space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Current Primitive:</span>
            <span className="text-xs font-mono font-bold text-rose-400">{assetName || 'Classical Primitive'}</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-sm font-mono font-bold text-cyan-300">
              {recommendation.target_pqc_candidate}
            </span>
          </div>
          {sourceLocation && (
            <div className="text-[11px] text-slate-500 font-mono mt-0.5 truncate max-w-md">
              {sourceLocation}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold uppercase">
            {recommendation.standard_status.replace('_', ' ')}
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
            Complexity: <strong className="text-slate-100">{recommendation.migration_complexity}</strong>
          </span>
        </div>
      </div>

      {/* Rationale */}
      <div className="space-y-1">
        <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-cyan-400" />
          <span>Migration Rationale</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed pl-5">
          {recommendation.rationale}
        </p>
      </div>

      {/* Performance & Overhead Callout */}
      {(recommendation.performance_notes || recommendation.compatibility_notes) && (
        <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-3 text-xs space-y-1.5 font-mono">
          {recommendation.performance_notes && (
            <div className="text-slate-400">
              <span className="text-slate-500 font-semibold">Overhead Profile: </span>
              <span className="text-slate-300">{recommendation.performance_notes}</span>
            </div>
          )}
          {recommendation.compatibility_notes && (
            <div className="text-slate-400">
              <span className="text-slate-500 font-semibold">Hybrid Agility: </span>
              <span className="text-slate-300">{recommendation.compatibility_notes}</span>
            </div>
          )}
        </div>
      )}

      {/* Footer metadata */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1">
        <span>Knowledge Base: {recommendation.kb_version || '2026.3.0-NIST-PQC'}</span>
        <span>Recommendation Confidence: {Math.round(recommendation.confidence * 100)}%</span>
      </div>
    </div>
  );
};

import React from 'react';
import { PerformancePredictionData } from '../../types';
import { Cpu, AlertCircle, Info, Database } from 'lucide-react';

interface PQCPerformanceEvidenceProps {
  performance?: PerformancePredictionData | null;
  compact?: boolean;
}

export const PQCPerformanceEvidence: React.FC<PQCPerformanceEvidenceProps> = ({
  performance,
  compact = false,
}) => {
  if (!performance) return null;

  const status = (performance.status || '').toUpperCase();
  const hasMissingFeatures = (performance.missing_features || []).length > 0;

  if (status === 'UNCONFIGURED') {
    return (
      <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-3 text-xs font-mono space-y-1">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <span className="font-semibold text-slate-300">Performance model unavailable</span>
        </div>
        {hasMissingFeatures && (
          <p className="text-[11px] text-slate-500 pl-5">
            Needs additional performance data
          </p>
        )}
      </div>
    );
  }

  if (status === 'ERROR') {
    return (
      <div className="rounded-lg bg-slate-950/70 border border-rose-900/40 p-3 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-rose-400">
          <AlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
          <span className="font-semibold">Performance prediction unavailable</span>
        </div>
      </div>
    );
  }

  if (status !== 'READY' || performance.predicted_latency_us === undefined || performance.predicted_latency_us === null) {
    return null;
  }

  const latencyVal = performance.predicted_latency_us;

  if (compact) {
    return (
      <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-cyan-950/40 border border-cyan-800/60 font-mono text-xs">
        <Cpu className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-950 border border-cyan-800 px-1 py-0.2 rounded">
          MODEL PREDICTION
        </span>
        <span className="text-slate-300 font-semibold">{latencyVal} µs</span>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-[#06080F] border border-cyan-900/50 p-4 space-y-3 font-mono">
      {/* Header Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-cyan-950/80 pb-2">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
            MODEL PERFORMANCE EVIDENCE
          </span>
        </div>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-700/80 uppercase">
          MODEL PREDICTION
        </span>
      </div>

      {/* Latency Display */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[11px] text-slate-400 font-semibold">Predicted CPU Latency</div>
          <div className="text-lg font-bold text-cyan-300">{latencyVal} µs</div>
          <div className="text-[10px] text-slate-500">Expm1 inverse log transformation applied</div>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1">
          <div className="text-[11px] text-slate-400 font-semibold">Model Provider & Version</div>
          <div className="text-xs font-bold text-slate-200 truncate">{performance.provider_name || 'CatBoostPerformancePredictionProvider'}</div>
          <div className="text-[10px] text-cyan-400 font-semibold">{performance.model_version || 'catboost-pqc-v1.0'}</div>
        </div>
      </div>

      {/* Metadata Provenance */}
      {performance.benchmark_source && (
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 pt-1 border-t border-slate-900">
          <Database className="w-3.5 h-3.5 text-cyan-500 shrink-0" />
          <span>Benchmark Dataset: <strong className="text-slate-300">{performance.benchmark_source}</strong></span>
        </div>
      )}

      {/* Explainability Disclaimer */}
      <p className="text-[10px] text-slate-500 font-sans italic pt-1 border-t border-slate-900 leading-relaxed">
        Latency is a model prediction from SENTRIQ's PQC performance model and is not an observed benchmark measurement.
      </p>
    </div>
  );
};

import React from 'react';
import { BlastRadiusResult, CryptoNode } from '../../types';
import { X, ShieldAlert, Zap, Clock, FileCode, Server, Database, ArrowRight } from 'lucide-react';

interface BlastRadiusSidePanelProps {
  node: CryptoNode | null;
  blastRadius: BlastRadiusResult | null;
  onClose: () => void;
  onSimulateMigration?: (assetId: string) => void;
  isLoading?: boolean;
}

export const BlastRadiusSidePanel: React.FC<BlastRadiusSidePanelProps> = ({
  node,
  blastRadius,
  onClose,
  onSimulateMigration,
  isLoading = false
}) => {
  if (!node) return null;

  const score = blastRadius?.radius_score || 0;
  const isHighRisk = score >= 70 || ['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE', 'VULNERABLE'].includes((node.quantum_risk || '').toUpperCase());

  return (
    <div className="w-full lg:w-96 shrink-0 bg-[#06080F]/95 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 space-y-6 shadow-2xl flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className={`w-5 h-5 ${isHighRisk ? 'text-rose-400' : 'text-emerald-400'}`} />
            <h3 className="text-sm font-bold text-slate-100 font-mono tracking-wide uppercase">
              Blast Radius Analysis
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Selected Node Details */}
        <div className="mt-4 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">{node.artefact_type}</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
              isHighRisk ? 'bg-rose-950/80 text-rose-300 border-rose-800' : 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
            }`}>
              {node.quantum_risk}
            </span>
          </div>
          <h4 className="text-base font-bold text-slate-100 break-all font-sans">{node.name}</h4>
          {node.location && (
            <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 break-all">
              <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>{node.location}</span>
            </p>
          )}
        </div>

        {/* Radial Score Gauge */}
        <div className="mt-5 p-4 rounded-xl bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-slate-800/80 text-center space-y-2">
          <div className="text-[11px] uppercase font-mono tracking-wider text-slate-400">Impact Score Gauge</div>
          <div className="relative inline-flex items-center justify-center">
            <span className={`text-3xl font-black font-mono tracking-tight ${
              score >= 75 ? 'text-rose-400' : score >= 45 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {score.toFixed(1)}
            </span>
            <span className="text-xs text-slate-500 font-mono ml-1">/ 100</span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                score >= 75 ? 'bg-gradient-to-r from-amber-500 to-rose-500' : 'bg-gradient-to-r from-emerald-500 to-cyan-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
            />
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60 space-y-1">
            <div className="text-[10px] text-slate-500 uppercase font-mono flex items-center gap-1">
              <Server className="w-3 h-3 text-cyan-400" />
              <span>Systems</span>
            </div>
            <div className="text-lg font-bold text-slate-200 font-mono">
              {blastRadius?.systems_count || 1}
            </div>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/60 space-y-1">
            <div className="text-[10px] text-slate-500 uppercase font-mono flex items-center gap-1">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>Est. Effort</span>
            </div>
            <div className="text-lg font-bold text-slate-200 font-mono">
              {blastRadius?.estimated_migration_effort || 1.0}d
            </div>
          </div>
        </div>

        {/* Sensitive Data Classes */}
        <div className="mt-4 space-y-2">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-purple-400" />
            <span>Exposed Data Classes</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(blastRadius?.data_classes || ['INTERNAL_APPLICATION_DATA']).map((cls) => (
              <span
                key={cls}
                className="px-2 py-0.5 bg-purple-950/50 border border-purple-800/50 text-purple-300 rounded text-[10px] font-mono"
              >
                {cls}
              </span>
            ))}
          </div>
        </div>

        {/* Affected Downstream Nodes */}
        <div className="mt-4 space-y-2">
          <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400">
            Downstream Affected Nodes ({blastRadius?.affected_nodes_count || 0})
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
            {blastRadius?.affected_nodes.map((an) => (
              <div
                key={an.node_id}
                className="flex items-center justify-between bg-slate-950/40 p-2 rounded-lg border border-slate-800/60 text-xs"
              >
                <div className="truncate max-w-[200px]">
                  <div className="text-slate-200 font-medium truncate">{an.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{an.location || an.artefact_type}</div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[10px] font-mono text-cyan-400">{an.distance} hop(s)</span>
                  <div className="text-[10px] font-mono text-slate-400">Impact {an.impact_score}</div>
                </div>
              </div>
            ))}
            {(!blastRadius?.affected_nodes || blastRadius.affected_nodes.length === 0) && (
              <div className="text-xs text-slate-500 italic p-2 bg-slate-950/20 rounded">
                No downstream node dependencies detected.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Migration Action Button */}
      {onSimulateMigration && node.asset_id && (
        <button
          onClick={() => onSimulateMigration(node.asset_id!)}
          className="w-full mt-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 text-xs uppercase tracking-wider transition-all"
        >
          <Zap className="w-4 h-4" />
          <span>Simulate PQC Migration</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

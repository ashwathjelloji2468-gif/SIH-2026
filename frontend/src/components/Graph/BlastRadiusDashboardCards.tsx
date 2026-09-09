import React from 'react';
import { TopBlastRadiusSummary } from '../../types';
import { ShieldAlert, KeyRound, AlertTriangle, ArrowUpRight } from 'lucide-react';

interface BlastRadiusDashboardCardsProps {
  summary: TopBlastRadiusSummary | null;
  onSelectNode: (nodeId: string) => void;
}

export const BlastRadiusDashboardCards: React.FC<BlastRadiusDashboardCardsProps> = ({
  summary,
  onSelectNode
}) => {
  if (!summary) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Card 1: Top 10 Largest Blast Radii */}
      <div className="bg-[#06080F]/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="text-xs font-bold text-slate-100 font-mono uppercase tracking-wider">
                Top 10 Largest Blast Radii
              </h3>
            </div>
            <span className="text-[10px] font-mono bg-rose-950 text-rose-300 px-2 py-0.5 rounded border border-rose-800">
              {summary.top_blast_radii.length} Impacted
            </span>
          </div>

          <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-1">
            {summary.top_blast_radii.map((br, idx) => (
              <div
                key={br.root_node_id || idx}
                onClick={() => onSelectNode(br.root_node_id)}
                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500/40 cursor-pointer transition-all group"
              >
                <div className="truncate max-w-[180px]">
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-cyan-300 truncate">
                    {br.root_node_name}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {br.systems_count} System(s) · {br.affected_nodes_count} Node(s)
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-mono font-bold ${
                    br.radius_score >= 70 ? 'text-rose-400' : 'text-amber-400'
                  }`}>
                    {br.radius_score.toFixed(1)}
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                </div>
              </div>
            ))}
            {summary.top_blast_radii.length === 0 && (
              <div className="text-xs text-slate-500 italic p-3 text-center">
                No blast radius records evaluated yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Card 2: Shared Keys & Certificates with Highest Impact */}
      <div className="bg-[#06080F]/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-slate-100 font-mono uppercase tracking-wider">
                Shared Keys & Certs Impact
              </h3>
            </div>
            <span className="text-[10px] font-mono bg-amber-950 text-amber-300 px-2 py-0.5 rounded border border-amber-800">
              {summary.shared_credentials_high_impact.length} Shared
            </span>
          </div>

          <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-1">
            {summary.shared_credentials_high_impact.map((sc, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200 truncate max-w-[180px]">{sc.credential_name}</span>
                  <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 px-1.5 py-0.2 rounded border border-amber-800">
                    {sc.risk_level}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono truncate">
                  {sc.source_location} ↔ {sc.target_location}
                </div>
              </div>
            ))}
            {summary.shared_credentials_high_impact.length === 0 && (
              <div className="text-xs text-slate-500 italic p-3 text-center">
                No shared key/certificate vulnerabilities detected.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Card 3: Single Points of Failure */}
      <div className="bg-[#06080F]/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-purple-400" />
              <h3 className="text-xs font-bold text-slate-100 font-mono uppercase tracking-wider">
                Single Points of Failure
              </h3>
            </div>
            <span className="text-[10px] font-mono bg-purple-950 text-purple-300 px-2 py-0.5 rounded border border-purple-800">
              {summary.single_points_of_failure.length} Critical
            </span>
          </div>

          <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-1">
            {summary.single_points_of_failure.map((sp, idx) => (
              <div
                key={sp.node_id || idx}
                onClick={() => onSelectNode(sp.node_id)}
                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-purple-500/40 cursor-pointer transition-all group"
              >
                <div className="truncate max-w-[180px]">
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-purple-300 truncate">
                    {sp.node_name}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Type: {sp.node_type} · {sp.affected_systems_count} Systems
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-purple-400">
                    SPOF {sp.radius_score.toFixed(0)}
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition-colors" />
                </div>
              </div>
            ))}
            {summary.single_points_of_failure.length === 0 && (
              <div className="text-xs text-slate-500 italic p-3 text-center">
                No single points of failure detected.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

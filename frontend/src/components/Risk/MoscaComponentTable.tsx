import React, { useState } from 'react';
import { MoscaProjectEvaluationResponse, MoscaUrgency } from '../../types/moscaEngine';
import { ShieldAlert, AlertCircle, Info, ChevronDown, ChevronUp, Clock, ArrowUpRight, Cpu } from 'lucide-react';

interface MoscaComponentTableProps {
  moscaContext: MoscaProjectEvaluationResponse | null;
  isLoading?: boolean;
}

export const MoscaComponentTable: React.FC<MoscaComponentTableProps> = ({ moscaContext, isLoading }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterUrgency, setFilterUrgency] = useState<string>('ALL');

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
        <div className="h-32 bg-slate-900 rounded-xl"></div>
      </div>
    );
  }

  if (!moscaContext || !moscaContext.components || moscaContext.components.length === 0) {
    return null;
  }

  const { components, total_components, critical_components, urgency_distribution } = moscaContext;

  const filteredComponents = components.filter(c => {
    if (filterUrgency === 'ALL') return true;
    return c.urgency === filterUrgency;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  const getUrgencyBadge = (urgency: MoscaUrgency) => {
    switch (urgency) {
      case 'CRITICAL':
        return <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-rose-950/90 border border-rose-700/80 text-rose-300">CRITICAL (M &gt; 5y)</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-amber-950/90 border border-amber-700/80 text-amber-300">HIGH (0 &lt; M ≤ 5y)</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-yellow-950/80 border border-yellow-700/70 text-yellow-300">BOUNDARY (M ≈ 0)</span>;
      case 'LOW':
        return <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-emerald-950/80 border border-emerald-700/70 text-emerald-300">LOW (M &lt; 0)</span>;
      case 'REQUIRES_REVIEW':
        return <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-slate-800 border border-slate-700 text-slate-300">REVIEW NEEDED</span>;
    }
  };

  const getBusinessPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-rose-900/40 text-rose-300 border border-rose-800/40">Critical</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-amber-900/40 text-amber-300 border border-amber-800/40">High</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-slate-800 text-slate-300 border border-slate-700">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-slate-800/60 text-slate-400">Low</span>;
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Cpu className="w-4 h-4" />
            <span>Component-Wise Mosca Risk Engine ($M_i = X + Y - Z_i$)</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100 font-mono">Integrated Component Urgency Prioritization</h2>
          <p className="text-xs text-slate-400 mt-1">
            Combines confidentiality lifetime ($X$), migration time ($Y$), and component quantum deadline ($Z_i$).
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-xl self-start sm:self-auto">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span className="text-xs font-mono text-slate-300">
            Action Required: <strong className="text-rose-400">{critical_components} of {total_components}</strong> components
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(urg => (
          <button
            key={urg}
            onClick={() => setFilterUrgency(urg)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors cursor-pointer ${
              filterUrgency === urg
                ? 'bg-rose-950 border-rose-700 text-rose-300 font-semibold'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {urg === 'ALL' ? `All (${components.length})` : urg}
          </button>
        ))}
      </div>

      {/* Components Table */}
      <div className="rounded-xl border border-slate-800 overflow-hidden bg-[#06080F]/90">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Component / Location</th>
                <th className="py-3 px-4">X (Lifetime)</th>
                <th className="py-3 px-4">Y (Migration)</th>
                <th className="py-3 px-4">Z_i (Quantum Deadline)</th>
                <th className="py-3 px-4">M_i Score ($X + Y - Z_i$)</th>
                <th className="py-3 px-4">Technical Urgency</th>
                <th className="py-3 px-4">Business Priority</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredComponents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-slate-500">
                    No components match the selected urgency filter.
                  </td>
                </tr>
              ) : (
                filteredComponents.map(c => {
                  const isExpanded = expandedId === c.component_id;
                  const xVal = c.x.value;
                  const yVal = c.y.value;
                  const zVal = c.z.z_value;
                  const score = c.mosca_score;

                  return (
                    <React.Fragment key={c.component_id}>
                      <tr className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-100">{c.algorithm}</div>
                          <div className="text-[11px] text-slate-500 font-sans truncate max-w-xs">{c.location || 'Codebase artifact'}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 text-xs rounded bg-slate-900 border border-slate-800 text-cyan-300">
                            X = {xVal}y
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 text-xs rounded bg-slate-900 border border-slate-800 text-cyan-300">
                            Y = {yVal}y
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 text-xs rounded bg-slate-900 border border-slate-800 text-amber-300">
                            {zVal !== undefined && zVal !== null ? `Z_i = ${zVal}y` : 'Non-numeric'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-bold font-mono">
                          {score !== null && score !== undefined ? (
                            <span className={score > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                              M = {score > 0 ? `+${score}` : score}y
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">{getUrgencyBadge(c.urgency)}</td>
                        <td className="py-3.5 px-4">{getBusinessPriorityBadge(c.business_priority)}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => toggleExpand(c.component_id)}
                            className="p-1 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded Rationale Row */}
                      {isExpanded && (
                        <tr className="bg-slate-900/80 border-t border-slate-800/80">
                          <td colSpan={8} className="p-4 space-y-3 font-sans">
                            <div className="bg-[#06080F] border border-slate-800 rounded-xl p-4 text-xs space-y-3">
                              <div className="flex items-center gap-2 text-cyan-400 font-mono font-semibold">
                                <Info className="w-4 h-4" />
                                <span>Step-by-Step Mosca Equation Breakdown</span>
                              </div>

                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
                                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                                  <span className="text-cyan-400 font-bold">X (Confidentiality):</span> {xVal} years
                                  <div className="text-[11px] text-slate-400 font-sans mt-0.5">{c.x.explanation}</div>
                                </div>
                                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                                  <span className="text-cyan-400 font-bold">Y (Migration):</span> {yVal} years
                                  <div className="text-[11px] text-slate-400 font-sans mt-0.5">{c.y.explanation}</div>
                                </div>
                                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                                  <span className="text-amber-400 font-bold">Z_i (Threat Deadline):</span> {zVal ?? 'Non-numeric'}
                                  <div className="text-[11px] text-slate-400 font-sans mt-0.5">{c.z.explanation}</div>
                                </div>
                              </div>

                              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-slate-200 leading-relaxed font-sans">
                                <strong>Rationale:</strong> {c.explanation}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

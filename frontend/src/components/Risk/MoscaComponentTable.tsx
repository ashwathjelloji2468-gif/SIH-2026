import React, { useState } from 'react';
import { MoscaProjectEvaluationResponse, MoscaUrgency } from '../../types/moscaEngine';
import { getProjectMoscaContext } from '../../services/moscaEngineService';
import { ShieldAlert, AlertCircle, Info, ChevronDown, ChevronUp, Clock, ArrowUpRight, Cpu } from 'lucide-react';

interface MoscaComponentTableProps {
  moscaContext: MoscaProjectEvaluationResponse | null;
  projectId?: string;
  isLoading?: boolean;
  onRefresh?: (params?: { user_x_years?: number; user_y_scenario?: string; quantum_horizon?: number }) => void;
}

export const MoscaComponentTable: React.FC<MoscaComponentTableProps> = ({
  moscaContext: initialMoscaContext,
  projectId,
  isLoading: initialLoading = false,
  onRefresh,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterUrgency, setFilterUrgency] = useState<string>('ALL');

  // Dynamic override state for X, Y, Z parameters
  const [customX, setCustomX] = useState<number | ''>('');
  const [customYScenario, setCustomYScenario] = useState<string>('MODERATE');
  const [customZ, setCustomZ] = useState<number | ''>('');

  const [activeMoscaContext, setActiveMoscaContext] = useState<MoscaProjectEvaluationResponse | null>(initialMoscaContext);
  const [loading, setLoading] = useState<boolean>(initialLoading);

  React.useEffect(() => {
    setActiveMoscaContext(initialMoscaContext);
  }, [initialMoscaContext]);

  React.useEffect(() => {
    setLoading(initialLoading);
  }, [initialLoading]);

  const handleApplyOverrides = async (xVal?: number, yScen?: string, zVal?: number) => {
    if (!projectId) return;
    setLoading(true);
    try {
      const params: any = {};
      const targetX = xVal !== undefined ? xVal : customX !== '' ? Number(customX) : undefined;
      const targetY = yScen !== undefined ? yScen : customYScenario;
      const targetZ = zVal !== undefined ? zVal : customZ !== '' ? Number(customZ) : undefined;

      if (targetX) params.user_x_years = targetX;
      if (targetY) params.user_y_scenario = targetY;
      if (targetZ) params.quantum_horizon = targetZ;

      const updated = await getProjectMoscaContext(projectId, params);
      setActiveMoscaContext(updated);
      if (onRefresh) onRefresh(params);
    } catch (err) {
      console.error('Failed to recalculate Mosca context with overrides:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setCustomX('');
    setCustomYScenario('MODERATE');
    setCustomZ('');
    if (!projectId) return;
    setLoading(true);
    try {
      const updated = await getProjectMoscaContext(projectId);
      setActiveMoscaContext(updated);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to reset Mosca context:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !activeMoscaContext) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
        <div className="h-32 bg-slate-900 rounded-xl"></div>
      </div>
    );
  }

  if (!activeMoscaContext || !activeMoscaContext.components || activeMoscaContext.components.length === 0) {
    return null;
  }

  const { components, total_components, critical_components, urgency_distribution } = activeMoscaContext;

  const filteredComponents = components.filter(c => {
    if (filterUrgency === 'ALL') return true;
    return c.urgency === filterUrgency;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  const getUrgencyBadge = (urgency: MoscaUrgency, score?: number | null) => {
    const isBreached = (score !== undefined && score !== null && score > 0) || urgency === 'CRITICAL' || urgency === 'HIGH';

    switch (urgency) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-rose-950/90 border border-rose-700/80 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.3)] animate-pulse">
            CRITICAL (M &gt; 5y)
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-amber-950/90 border border-amber-700/80 text-amber-300 shadow-[0_0_8px_rgba(245,158,11,0.2)]">
            HIGH (0 &lt; M ≤ 5y)
          </span>
        );
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

      {/* Dynamic Mosca Parameter Adjustment Controls */}
      <div className="p-4 rounded-xl bg-[#06080F] border border-cyan-900/40 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-cyan-300 font-bold uppercase tracking-wider">
            Interactive Parameter Adjustment Panel (Recalculate $M_i = X + Y - Z_i$)
          </span>
          <button
            onClick={handleReset}
            className="text-[11px] font-mono text-slate-400 hover:text-cyan-300 underline cursor-pointer"
          >
            Reset Defaults
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          <div>
            <label className="block text-slate-400 mb-1">Override X (Data Lifetime Years)</label>
            <input
              type="number"
              placeholder={`Default (${activeMoscaContext.evaluated_x?.value || 20}y)`}
              value={customX}
              onChange={(e) => setCustomX(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Override Y (Migration Scenario)</label>
            <select
              value={customYScenario}
              onChange={(e) => setCustomYScenario(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="MODERATE">MODERATE (Standard 3-5y)</option>
              <option value="AGGRESSIVE">AGGRESSIVE (Accelerated 1-2y)</option>
              <option value="CONSERVATIVE">CONSERVATIVE (Complex 5-10y)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Override Z (Quantum Target Year)</label>
            <input
              type="number"
              placeholder={`Default (${activeMoscaContext.evaluated_z_horizon || 2033})`}
              value={customZ}
              onChange={(e) => setCustomZ(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-amber-300 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="flex justify-end pt-1">
          <button
            onClick={() => handleApplyOverrides()}
            disabled={loading}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-colors shadow-md shadow-cyan-950/40 cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Recalculate MoscaEngine...' : 'Recalculate M_i Equations →'}
          </button>
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

                  const isHighRisk = score !== null && score !== undefined && score > 0;
                  const isCritical = c.urgency === 'CRITICAL';

                  return (
                    <React.Fragment key={c.component_id}>
                      <tr
                        className={`transition-colors ${
                          isCritical
                            ? 'bg-rose-950/25 hover:bg-rose-950/40 border-l-4 border-l-rose-500'
                            : isHighRisk
                            ? 'bg-amber-950/20 hover:bg-amber-950/30 border-l-4 border-l-amber-500'
                            : 'hover:bg-slate-900/40'
                        }`}
                      >
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-100 flex items-center gap-2">
                            <span>{c.algorithm}</span>
                            {isHighRisk && (
                              <span className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-rose-950 border border-rose-700 text-rose-300 uppercase">
                                M_i &gt; 0 Breach
                              </span>
                            )}
                          </div>
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
                            <span className={`px-2 py-0.5 rounded ${score > 0 ? 'bg-rose-950 border border-rose-800 text-rose-300 font-black' : 'text-emerald-400'}`}>
                              M = {score > 0 ? `+${score}` : score}y
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">{getUrgencyBadge(c.urgency, score)}</td>
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


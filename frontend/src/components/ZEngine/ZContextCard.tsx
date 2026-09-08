import React, { useState } from 'react';
import { ZProjectEvaluationResponse, ZResultResponse } from '../../types/zEngine';
import { Cpu, AlertTriangle, ShieldCheck, ShieldAlert, Info, ChevronDown, ChevronUp, Layers, HelpCircle } from 'lucide-react';

interface ZContextCardProps {
  zContext: ZProjectEvaluationResponse | null;
  isLoading?: boolean;
}

export const ZContextCard: React.FC<ZContextCardProps> = ({ zContext, isLoading }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterClass, setFilterClass] = useState<string>('ALL');

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-slate-800 rounded"></div>
        <div className="h-20 bg-slate-900 rounded-xl"></div>
      </div>
    );
  }

  if (!zContext) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl">
        <p className="text-slate-400 text-sm">No component-wise quantum exposure data available.</p>
      </div>
    );
  }

  const { class_breakdown, components, total_components, vulnerable_components, target_horizon_year, quantum_horizon } = zContext;

  const filteredComponents = components.filter(c => {
    if (filterClass === 'ALL') return true;
    return c.quantum_class === filterClass;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  const getClassBadge = (qClass: string) => {
    switch (qClass) {
      case 'SHOR_VULNERABLE':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-rose-950/80 border border-rose-800/80 text-rose-300">SHOR VULNERABLE (RSA/ECC)</span>;
      case 'QUANTUM_STRENGTH_REDUCTION':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-amber-950/80 border border-amber-800/80 text-amber-300">STRENGTH REDUCTION (AES/SHA)</span>;
      case 'PQC_RESISTANT':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-emerald-950/80 border border-emerald-800/80 text-emerald-300">PQC RESISTANT</span>;
      case 'HYBRID':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-cyan-950/80 border border-cyan-800/80 text-cyan-300">HYBRID COMPOSITE</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-slate-800 border border-slate-700 text-slate-400">UNKNOWN / REVIEW</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VULNERABLE_AT_HORIZON':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-rose-900/40 text-rose-400 border border-rose-800/50">Zi = {quantum_horizon}y (CRQC Deadline)</span>;
      case 'QUANTUM_UNACCEPTABLE_AT_HORIZON':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-rose-900/40 text-rose-400 border border-rose-800/50">Zi = {quantum_horizon}y (Unacceptable Strength)</span>;
      case 'REQUIRES_REVIEW':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-amber-900/40 text-amber-400 border border-amber-800/50">Policy Review Required</span>;
      case 'REDUCED_BUT_ACCEPTABLE':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-blue-900/40 text-blue-300 border border-blue-800/50">Reduced but Acceptable</span>;
      case 'NO_IMMEDIATE_QUANTUM_DEADLINE':
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-emerald-900/40 text-emerald-400 border border-emerald-800/50">No Immediate Deadline</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-mono rounded-md bg-slate-800 text-slate-400">Review Needed</span>;
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Cpu className="w-4 h-4" />
            <span>Z Engine — Component-Wise Quantum Exposure ($Z_i$)</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100 font-mono">Independent Component Risk Deadlines</h2>
          <p className="text-xs text-slate-400 mt-1">
            Evaluates quantum threat exposure individually for every discovered algorithm, key, and certificate.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3.5 py-1.5 rounded-xl self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span className="text-xs font-mono text-slate-300">
            Scenario Horizon: <strong className="text-cyan-300">T_Q = {quantum_horizon} Years (~{target_horizon_year})</strong>
          </span>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#06080F]/80 border border-slate-800/80 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-mono mb-1">Total Components</div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{total_components}</div>
          <div className="text-[11px] text-slate-500 mt-1">Analyzed independently</div>
        </div>

        <div className="bg-[#06080F]/80 border border-rose-900/40 rounded-xl p-4">
          <div className="text-rose-400 text-xs font-mono mb-1">Shor Vulnerable (RSA/ECC)</div>
          <div className="text-2xl font-bold text-rose-400 font-mono">{class_breakdown.SHOR_VULNERABLE || 0}</div>
          <div className="text-[11px] text-rose-300/70 mt-1">Fundamental Zi = {quantum_horizon}y</div>
        </div>

        <div className="bg-[#06080F]/80 border border-amber-900/40 rounded-xl p-4">
          <div className="text-amber-400 text-xs font-mono mb-1">Strength Reduced (AES/SHA)</div>
          <div className="text-2xl font-bold text-amber-300 font-mono">{class_breakdown.QUANTUM_STRENGTH_REDUCTION || 0}</div>
          <div className="text-[11px] text-amber-300/70 mt-1">Grover / BHT reduction</div>
        </div>

        <div className="bg-[#06080F]/80 border border-emerald-900/40 rounded-xl p-4">
          <div className="text-emerald-400 text-xs font-mono mb-1">Quantum Safe / PQC</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {(class_breakdown.PQC_RESISTANT || 0) + (class_breakdown.HYBRID || 0)}
          </div>
          <div className="text-[11px] text-emerald-300/70 mt-1">No immediate deadline</div>
        </div>
      </div>

      {/* Explanation Banner */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 text-xs text-slate-300 space-y-2">
        <div className="flex items-center gap-2 text-cyan-400 font-semibold font-mono">
          <Info className="w-4 h-4" />
          <span>Technical Model Distinction: Public-Key Factoring vs Symmetric Search Reduction</span>
        </div>
        <p className="leading-relaxed text-slate-400">
          Public-key cryptography (RSA, ECC) is fundamentally broken by Shor’s algorithm ($Z_i = T_Q$). Symmetric encryption (AES) and hashes (SHA) experience Grover search key-size reduction rather than structural collapse.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {['ALL', 'SHOR_VULNERABLE', 'QUANTUM_STRENGTH_REDUCTION', 'PQC_RESISTANT', 'UNKNOWN'].map(cat => (
          <button
            key={cat}
            onClick={() => setFilterClass(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors cursor-pointer ${
              filterClass === cat
                ? 'bg-cyan-950 border-cyan-500/50 text-cyan-300 font-semibold'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {cat === 'ALL' ? `All Components (${components.length})` : cat.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Components Table */}
      <div className="rounded-xl border border-slate-800 overflow-hidden bg-[#06080F]/90">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Component / Algorithm</th>
                <th className="py-3 px-4">Quantum Impact Class</th>
                <th className="py-3 px-4">Status & Deadline</th>
                <th className="py-3 px-4">Effective Bits (Classical → Quantum)</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredComponents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500">
                    No components match the selected filter.
                  </td>
                </tr>
              ) : (
                filteredComponents.map(c => {
                  const isExpanded = expandedId === c.component_id;
                  return (
                    <React.Fragment key={c.component_id}>
                      <tr className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-100">{c.algorithm || c.primitive}</div>
                          <div className="text-[11px] text-slate-500 font-sans truncate max-w-xs">{c.location || 'Codebase artifact'}</div>
                        </td>
                        <td className="py-3.5 px-4">{getClassBadge(c.quantum_class)}</td>
                        <td className="py-3.5 px-4">{getStatusBadge(c.status)}</td>
                        <td className="py-3.5 px-4">
                          {c.classical_security_bits !== undefined && c.classical_security_bits !== null ? (
                            <span className="text-slate-300">
                              {c.classical_security_bits} bits →{' '}
                              <strong className={c.quantum_security_bits === 0 ? 'text-rose-400' : 'text-amber-300'}>
                                {c.quantum_security_bits} bits
                              </strong>
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => toggleExpand(c.component_id)}
                            className="p-1 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded Details Row */}
                      {isExpanded && (
                        <tr className="bg-slate-900/80 border-t border-slate-800/80">
                          <td colSpan={5} className="p-4 space-y-3 font-sans">
                            <div className="bg-[#06080F] border border-slate-800 rounded-xl p-3 text-xs space-y-2">
                              <div className="flex items-center gap-2 text-cyan-400 font-mono font-semibold">
                                <Info className="w-3.5 h-3.5" />
                                <span>Component Rationale & Assessment Explanation</span>
                              </div>
                              <p className="text-slate-300 leading-relaxed font-sans">{c.explanation}</p>
                              {c.metadata?.disclaimer && (
                                <div className="text-[11px] text-slate-500 font-mono italic">
                                  Note: {c.metadata.disclaimer}
                                </div>
                              )}
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

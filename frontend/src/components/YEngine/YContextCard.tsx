import React from 'react';
import { Hourglass, Sliders, CheckCircle2, AlertCircle, Info, Layers } from 'lucide-react';
import { ProjectYContextResponse, YSource, YScenarioKey } from '../../types/yEngine';

interface YContextCardProps {
  yContext?: ProjectYContextResponse | null;
  onOpenModal: () => void;
  isLoading?: boolean;
}

export const YContextCard: React.FC<YContextCardProps> = ({ yContext, onOpenModal, isLoading }) => {
  const result = yContext?.y_result;
  const activeY = result?.value ?? 10;
  const source: YSource = result?.source ?? 'SYSTEM_DEFAULT';
  const scenario: YScenarioKey = result?.scenario ?? 'STANDARD';

  const getSourceBadge = (src: YSource) => {
    switch (src) {
      case 'USER_SELECTED':
        return {
          label: 'User Selected Scenario',
          bg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
          icon: <CheckCircle2 className="w-3.5 h-3.5" />
        };
      case 'SYSTEM_DEFAULT':
      default:
        return {
          label: 'Standard MVP Planning Assumption',
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: <AlertCircle className="w-3.5 h-3.5" />
        };
    }
  };

  const getScenarioBadge = (scen: YScenarioKey) => {
    switch (scen) {
      case 'FAST':
        return { label: 'Fast (5y)', bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' };
      case 'STANDARD':
        return { label: 'Standard (10y)', bg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' };
      case 'COMPLEX':
        return { label: 'Complex (15y)', bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
      case 'LEGACY_HEAVY':
        return { label: 'Legacy-Heavy (20y)', bg: 'bg-rose-500/20 text-rose-300 border-rose-500/40' };
    }
  };

  const srcBadge = getSourceBadge(source);
  const scenBadge = getScenarioBadge(scenario);

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Top Accent Line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-500 to-emerald-500" />

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-950/40 border border-blue-500/20 rounded-xl text-blue-400">
            <Hourglass className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white tracking-wide">Y Engine — Migration Time</h3>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${srcBadge.bg}`}>
                {srcBadge.icon}
                {srcBadge.label}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Estimated preparation duration <span className="font-mono text-cyan-300">$Y$</span> needed to transition cryptographic systems to quantum-safe standards.
            </p>
          </div>
        </div>

        <button
          onClick={onOpenModal}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 hover:border-blue-500/50 text-blue-300 text-sm font-semibold rounded-lg transition-all"
        >
          <Sliders className="w-4 h-4" />
          <span>Adjust Scenario (Y)</span>
        </button>
      </div>

      {/* Main Display Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        {/* Active Migration Duration */}
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4 flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Migration Preparation Duration (Y)</div>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-extrabold font-mono text-cyan-400">{activeY}</span>
              <span className="text-sm font-semibold text-slate-400">Years</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Refactoring completion target: <span className="font-mono text-slate-300 font-semibold">{new Date().getFullYear() + activeY}</span>
            </div>
          </div>
          <span className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border ${scenBadge.bg}`}>
            {scenBadge.label}
          </span>
        </div>

        {/* Core Distinction Box */}
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Mosca Planning Distinction</div>
          <div className="text-xs text-slate-300 leading-relaxed mt-2">
            <span className="font-semibold text-cyan-300">Y = Time WE need to prepare</span> (internal organizational refactoring), separate from <span className="font-semibold text-rose-300">Z = Quantum threat arrival</span>.
          </div>
          <div className="text-[11px] text-slate-500 mt-1 italic">
            Repository-wide planning constant for MVP risk modeling.
          </div>
        </div>
      </div>

      {/* Explanation Banner */}
      {result?.explanation && (
        <div className="mt-4 p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-white">Y Engine Planning Assumption:</span> {result.explanation}
          </div>
        </div>
      )}
    </div>
  );
};

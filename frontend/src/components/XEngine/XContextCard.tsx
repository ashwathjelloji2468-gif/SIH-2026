import React from 'react';
import { Clock, ShieldAlert, Building2, Sliders, CheckCircle2, AlertCircle, Info, Folder } from 'lucide-react';
import { ProjectXContextResponse, XSource } from '../../types/xEngine';

interface XContextCardProps {
  xContext?: ProjectXContextResponse | null;
  onOpenModal: () => void;
  isLoading?: boolean;
}

export const XContextCard: React.FC<XContextCardProps> = ({ xContext, onOpenModal, isLoading }) => {
  const result = xContext?.x_result;
  const activeX = result?.value ?? 20;
  const source: XSource = result?.source ?? 'SYSTEM_DEFAULT';

  const getSourceBadge = (src: XSource) => {
    switch (src) {
      case 'USER':
        return {
          label: 'User Organization Horizon',
          bg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
          icon: <CheckCircle2 className="w-3.5 h-3.5" />
        };
      case 'DOMAIN_BASELINE':
        return {
          label: 'Domain Baseline Estimate',
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <Building2 className="w-3.5 h-3.5" />
        };
      case 'SYSTEM_DEFAULT':
      default:
        return {
          label: 'System Default Fallback',
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertCircle className="w-3.5 h-3.5" />
        };
    }
  };

  const badge = getSourceBadge(source);
  const folderEntries = Object.entries(xContext?.folder_contexts || {});

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Top Accent Line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-amber-500" />

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-950/40 border border-cyan-500/20 rounded-xl text-cyan-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white tracking-wide">X Engine — Confidentiality Horizon</h3>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badge.bg}`}>
                {badge.icon}
                {badge.label}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Determines required confidentiality duration <span className="font-mono text-cyan-300">$X$</span> before data exposure harm diminishes.
            </p>
          </div>
        </div>

        <button
          onClick={onOpenModal}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-500/50 text-cyan-300 text-sm font-semibold rounded-lg transition-all"
        >
          <Sliders className="w-4 h-4" />
          <span>Adjust Horizon (X)</span>
        </button>
      </div>

      {/* Main Stats Display */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {/* Active Confidentiality Horizon */}
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Confidentiality Horizon (X)</div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold font-mono text-cyan-400">{activeX}</span>
            <span className="text-sm font-semibold text-slate-400">Years</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Target Year: <span className="font-mono text-slate-300 font-semibold">{new Date().getFullYear() + activeX}</span>
          </div>
        </div>

        {/* User Organization Preference */}
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Organization Preference ($X_{"{"}user{"}"}$)</div>
          <div className="flex items-baseline gap-2 mt-2">
            {result?.userX ? (
              <>
                <span className="text-3xl font-extrabold font-mono text-white">{result.userX}</span>
                <span className="text-sm font-semibold text-slate-400">Years</span>
              </>
            ) : (
              <span className="text-sm font-medium text-slate-500 italic mt-2 block">Not set (using estimate)</span>
            )}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {result?.userX ? 'Authoritative override active' : 'Can set custom business requirement'}
          </div>
        </div>

        {/* System Domain Estimate */}
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Domain Baseline Estimate ($X_{"{"}domain{"}"}$)</div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold font-mono text-emerald-400">{result?.estimatedDomainX ?? 20}</span>
            <span className="text-sm font-semibold text-slate-400">Years</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Category: <span className="text-slate-300 font-medium">{result?.domainTitle || 'Unclassified'}</span>
          </div>
        </div>
      </div>

      {/* Explanation Banner */}
      {result?.explanation && (
        <div className="mt-4 p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-white">X Engine Evaluation:</span> {result.explanation}
          </div>
        </div>
      )}

      {/* Folder Context Overrides */}
      {folderEntries.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/80">
          <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
            <Folder className="w-3.5 h-3.5 text-cyan-400" />
            <span>Folder / Module Level Confidentiality Adjustments ({folderEntries.length})</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {folderEntries.map(([fPath, fCtx]) => (
              <div key={fPath} className="bg-slate-950/60 border border-slate-800/60 rounded-md p-2.5 flex items-center justify-between text-xs">
                <div className="truncate pr-2">
                  <span className="font-mono text-cyan-300 font-semibold">{fPath}</span>
                  {fCtx.notes && <span className="text-slate-400 block text-[11px] truncate">{fCtx.notes}</span>}
                </div>
                <span className="px-2 py-0.5 bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 font-mono font-bold rounded">
                  {fCtx.user_x_years} y
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

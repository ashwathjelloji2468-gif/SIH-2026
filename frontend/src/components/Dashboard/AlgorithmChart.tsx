import React, { useState } from 'react';
import { CryptoAsset } from '../../types';
import { AssetDetailDrawer } from '../Inventory/AssetDetailDrawer';
import { ChevronRight, ExternalLink, X } from 'lucide-react';

interface AlgorithmChartProps {
  assets: CryptoAsset[];
}

export const AlgorithmChart: React.FC<AlgorithmChartProps> = ({ assets }) => {
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset | null>(null);
  const [pickerAlgName, setPickerAlgName] = useState<string | null>(null);
  const [pickerAssets, setPickerAssets] = useState<CryptoAsset[]>([]);

  // Aggregate algorithm frequencies
  const counts: Record<string, number> = {};
  const safetyMap: Record<string, string> = {};

  assets.forEach((a) => {
    const alg = a.algorithm_name || 'UNKNOWN';
    counts[alg] = (counts[alg] || 0) + 1;
    if (!safetyMap[alg]) {
      safetyMap[alg] = a.quantum_safety;
    }
  });

  const sortedAlgs = Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);

  const maxCount = Math.max(...sortedAlgs.map(([, c]) => c), 1);

  const handleAlgClick = (algName: string) => {
    const matches = assets.filter((a) => (a.algorithm_name || 'UNKNOWN') === algName);
    if (matches.length === 1) {
      setSelectedAsset(matches[0]);
    } else if (matches.length > 1) {
      setPickerAlgName(algName);
      setPickerAssets(matches);
    } else {
      // Fallback case: attempt case-insensitive match
      const ciMatches = assets.filter(
        (a) => (a.algorithm_name || 'UNKNOWN').toLowerCase() === algName.toLowerCase()
      );
      if (ciMatches.length === 1) {
        setSelectedAsset(ciMatches[0]);
      } else if (ciMatches.length > 1) {
        setPickerAlgName(algName);
        setPickerAssets(ciMatches);
      }
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl relative">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Discovered Cryptographic Primitives</h3>
          <p className="text-xs text-slate-400">
            Click any algorithm to inspect source code evidence & risk analysis
          </p>
        </div>
        <span className="text-xs font-mono text-cyan-400 font-medium">
          {Object.keys(counts).length} Distinct Algorithms
        </span>
      </div>

      {sortedAlgs.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No cryptographic assets discovered in this project yet.
        </div>
      ) : (
        <div className="space-y-2">
          {sortedAlgs.map(([alg, count]) => {
            const safety = safetyMap[alg];
            const isVulnerable = safety === 'VULNERABLE';
            const percentage = Math.round((count / (assets.length || 1)) * 100);
            const barWidth = Math.max(8, Math.round((count / maxCount) * 100));

            return (
              <button
                key={alg}
                onClick={() => handleAlgClick(alg)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleAlgClick(alg);
                  }
                }}
                aria-label={`Inspect ${alg} crypto asset details`}
                className="w-full text-left group p-2.5 rounded-xl border border-transparent hover:border-slate-700/80 hover:bg-slate-900/80 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all cursor-pointer block"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-semibold group-hover:text-cyan-300 transition-colors flex items-center gap-1.5">
                        <span>{alg}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-all" />
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.2 rounded border uppercase font-mono ${
                          isVulnerable
                            ? 'bg-rose-950/60 text-rose-400 border-rose-800/60'
                            : 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                        }`}
                      >
                        {safety}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="group-hover:text-slate-200 transition-colors">
                        {count} occurrence{count !== 1 ? 's' : ''}
                      </span>
                      <span className="text-slate-500 text-[11px]">({percentage}%)</span>
                    </div>
                  </div>

                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isVulnerable
                          ? 'bg-gradient-to-r from-rose-600 to-rose-400'
                          : 'bg-gradient-to-r from-cyan-500 to-emerald-400'
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Asset Selection Picker Modal (for algorithms with multiple asset locations) */}
      {pickerAlgName && pickerAssets.length > 0 && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#0D1322] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                  <span>{pickerAlgName}</span>
                  <span className="text-xs text-cyan-400">({pickerAssets.length} Discovered Assets)</span>
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Select a specific asset file to view evidence & risk details:
                </p>
              </div>
              <button
                onClick={() => {
                  setPickerAlgName(null);
                  setPickerAssets([]);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {pickerAssets.map((asset) => (
                <button
                  key={asset.id}
                  onClick={() => {
                    setPickerAlgName(null);
                    setPickerAssets([]);
                    setSelectedAsset(asset);
                  }}
                  className="w-full text-left p-3 rounded-xl bg-[#0B0F19] border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition-all font-mono text-xs cursor-pointer flex items-center justify-between group"
                >
                  <div className="space-y-1 truncate pr-2">
                    <div className="font-semibold text-slate-200 group-hover:text-cyan-300 truncate">
                      {asset.name}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate">
                      {asset.location}
                      {asset.line_number ? `:L${asset.line_number}` : ''}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded border uppercase ${
                        asset.quantum_safety === 'VULNERABLE'
                          ? 'bg-rose-950 text-rose-300 border-rose-800'
                          : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      {asset.quantum_safety}
                    </span>
                    <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Slide-over Asset Detail & Evidence Drawer */}
      <AssetDetailDrawer asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
    </div>
  );
};


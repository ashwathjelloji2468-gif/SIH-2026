import React from 'react';
import { CryptoAsset } from '../../types';

interface AlgorithmChartProps {
  assets: CryptoAsset[];
}

export const AlgorithmChart: React.FC<AlgorithmChartProps> = ({ assets }) => {
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

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Discovered Cryptographic Primitives</h3>
          <p className="text-xs text-slate-400">Distribution across active codebase AST & regex detections</p>
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
        <div className="space-y-3.5">
          {sortedAlgs.map(([alg, count]) => {
            const safety = safetyMap[alg];
            const isVulnerable = safety === 'VULNERABLE';
            const percentage = Math.round((count / assets.length) * 100);
            const barWidth = Math.max(8, Math.round((count / maxCount) * 100));

            return (
              <div key={alg} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-200 font-semibold">{alg}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded border uppercase ${
                        isVulnerable
                          ? 'bg-rose-950/60 text-rose-400 border-rose-800/60'
                          : 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                      }`}
                    >
                      {safety}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400">
                    <span>{count} occurrences</span>
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
            );
          })}
        </div>
      )}
    </div>
  );
};

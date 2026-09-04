import React from 'react';

interface ConfidenceBadgeProps {
  score: number; // 0.00 to 1.00
  showLabel?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ score, showLabel = true }) => {
  const percentage = Math.round(score * 100);

  let toneClasses = 'text-cyan-400 bg-cyan-950/40 border-cyan-800/50';
  let qualityText = 'High';

  if (percentage < 60) {
    toneClasses = 'text-amber-400 bg-amber-950/40 border-amber-800/50';
    qualityText = 'Heuristic';
  } else if (percentage < 85) {
    toneClasses = 'text-blue-400 bg-blue-950/40 border-blue-800/50';
    qualityText = 'Confirmed';
  } else {
    toneClasses = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50';
    qualityText = 'Deterministic';
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border font-mono text-xs ${toneClasses}`}
      title={`Detection Confidence: ${percentage}% (${qualityText})`}
    >
      {showLabel && <span className="text-slate-400 font-sans text-[10px] uppercase tracking-wider">Conf:</span>}
      <span className="font-semibold">{percentage}%</span>
      <span className="text-[10px] opacity-75 hidden sm:inline">({qualityText})</span>
    </div>
  );
};

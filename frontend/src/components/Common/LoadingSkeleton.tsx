import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number; type?: 'table' | 'cards' }> = ({
  rows = 5,
  type = 'cards',
}) => {
  if (type === 'cards') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800/80 p-5">
            <div className="h-3.5 bg-slate-800 rounded w-1/3 mb-4"></div>
            <div className="h-7 bg-slate-800/60 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden animate-pulse">
      <div className="h-11 bg-slate-900/80 border-b border-slate-800"></div>
      <div className="p-4 space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 py-2 border-b border-slate-800/50">
            <div className="h-4 bg-slate-800 rounded w-1/4"></div>
            <div className="h-4 bg-slate-800/70 rounded w-1/6"></div>
            <div className="h-4 bg-slate-800/50 rounded w-1/3"></div>
            <div className="h-4 bg-slate-800/80 rounded w-1/12 ml-auto"></div>
          </div>
        ))}
      </div>
    </div>
  );
};

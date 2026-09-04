import React from 'react';
import { LucideIcon, ShieldAlert } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = ShieldAlert,
  title,
  description,
  actionText,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-slate-800 bg-[#0B0F19]/60 my-6">
      <div className="p-3.5 rounded-full bg-slate-900 border border-slate-800 text-cyan-400 mb-4">
        <Icon className="w-8 h-8" />
      </div>
      <h3 className="text-base font-semibold text-slate-100 mb-1.5">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-semibold tracking-wide transition-all shadow-lg shadow-cyan-950/40 cursor-pointer"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

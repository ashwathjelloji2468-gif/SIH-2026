import React from 'react';
import { QuantumSafety, RiskLevel, ScanStatus, ValidationStatus } from '../../types';

interface StatusBadgeProps {
  type: 'quantum' | 'risk' | 'scan' | 'validation' | 'evidence';
  value: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (type === 'quantum') {
    switch (value as QuantumSafety) {
      case 'SAFE':
        colorClasses = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
        break;
      case 'VULNERABLE':
        colorClasses = 'bg-rose-950/60 text-rose-400 border-rose-800/60 font-semibold';
        break;
      case 'TRANSITIONAL':
        colorClasses = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
        break;
      default:
        colorClasses = 'bg-purple-950/60 text-purple-400 border-purple-800/60';
        break;
    }
  } else if (type === 'risk') {
    switch (value as RiskLevel) {
      case 'CRITICAL':
        colorClasses = 'bg-rose-950/70 text-rose-300 border-rose-700 font-bold animate-pulse';
        break;
      case 'HIGH':
        colorClasses = 'bg-orange-950/60 text-orange-400 border-orange-800/60 font-semibold';
        break;
      case 'MEDIUM':
        colorClasses = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
        break;
      case 'LOW':
        colorClasses = 'bg-blue-950/60 text-blue-400 border-blue-800/60';
        break;
      default:
        colorClasses = 'bg-slate-800 text-slate-400 border-slate-700';
        break;
    }
  } else if (type === 'scan') {
    switch (value as ScanStatus) {
      case 'COMPLETED':
        colorClasses = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
        break;
      case 'RUNNING':
        colorClasses = 'bg-cyan-950/70 text-cyan-300 border-cyan-700 animate-pulse';
        break;
      case 'QUEUED':
        colorClasses = 'bg-blue-950/60 text-blue-300 border-blue-800/60';
        break;
      case 'FAILED':
        colorClasses = 'bg-rose-950/60 text-rose-400 border-rose-800/60';
        break;
      case 'CANCELLED':
        colorClasses = 'bg-slate-800 text-slate-400 border-slate-700';
        break;
    }
  } else if (type === 'validation') {
    switch (value as ValidationStatus) {
      case 'SUCCESS':
        colorClasses = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
        break;
      case 'FAILED':
      case 'ERROR':
        colorClasses = 'bg-rose-950/60 text-rose-400 border-rose-800/60';
        break;
      case 'IN_PROGRESS':
        colorClasses = 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60 animate-pulse';
        break;
    }
  } else if (type === 'evidence') {
    if (value === 'OBSERVED') {
      colorClasses = 'bg-emerald-950/50 text-emerald-300 border-emerald-800/50';
    } else if (value === 'INFERRED') {
      colorClasses = 'bg-amber-950/50 text-amber-300 border-amber-800/50';
    } else {
      colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
    }
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono tracking-tight uppercase ${sizeClasses} ${colorClasses}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {value.replace('_', ' ')}
    </span>
  );
};

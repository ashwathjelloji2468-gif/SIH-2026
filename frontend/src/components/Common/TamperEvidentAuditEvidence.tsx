import React from 'react';
import { ShieldCheck, AlertTriangle, Cpu, Copy, CheckCircle2 } from 'lucide-react';
import { AuditEvidenceData } from '../../types';

interface TamperEvidentAuditEvidenceProps {
  audit?: AuditEvidenceData | null;
  compact?: boolean;
  className?: string;
}

export const TamperEvidentAuditEvidence: React.FC<TamperEvidentAuditEvidenceProps> = ({
  audit,
  compact = false,
  className = '',
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!audit) {
    return null;
  }

  const status = audit.status?.toUpperCase() || 'UNCONFIGURED';
  const isReady = status === 'READY';
  const isUnconfigured = status === 'UNCONFIGURED';
  const isError = status === 'ERROR';

  const handleCopyDigest = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (audit.digest) {
      navigator.clipboard.writeText(audit.digest);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Compact Mode (e.g., table cells or cards)
  if (compact) {
    if (isReady && audit.digest) {
      return (
        <div className={`flex items-center gap-1.5 font-mono text-[10px] ${className}`}>
          <span className="px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-bold uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            AUDIT VERIFIED
          </span>
          <span className="text-slate-400 truncate max-w-[120px]" title={audit.digest}>
            {audit.digest.substring(0, 12)}...
          </span>
        </div>
      );
    }

    if (isUnconfigured) {
      return (
        <div className={`flex items-center gap-1.5 text-[10px] text-amber-400 ${className}`}>
          <span className="px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-800/80 text-amber-300 font-semibold uppercase">
            AUDIT UNCONFIGURED
          </span>
        </div>
      );
    }

    return (
      <div className={`flex items-center gap-1.5 text-[10px] text-rose-400 ${className}`}>
        <span className="px-1.5 py-0.5 rounded bg-rose-950/60 border border-rose-800/80 text-rose-300 font-semibold uppercase">
          AUDIT ERROR
        </span>
      </div>
    );
  }

  // Full Display Mode
  return (
    <div className={`rounded-lg border bg-slate-950/80 p-3 text-xs space-y-2 font-sans ${
      isReady
        ? 'border-emerald-900/60 text-slate-300'
        : isUnconfigured
        ? 'border-amber-900/60 text-amber-200/90'
        : 'border-rose-900/60 text-rose-200/90'
    } ${className}`}>
      {/* Header Badge Row */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className={`w-4 h-4 ${isReady ? 'text-emerald-400' : isUnconfigured ? 'text-amber-400' : 'text-rose-400'}`} />
          <span className="font-bold tracking-wider text-[11px] uppercase text-white">
            TAMPER-EVIDENT AUDIT
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
            isReady
              ? 'bg-emerald-950 border border-emerald-800 text-emerald-300'
              : isUnconfigured
              ? 'bg-amber-950 border border-amber-800 text-amber-300'
              : 'bg-rose-950 border border-rose-800 text-rose-300'
          }`}>
            {status}
          </span>
        </div>

        {/* Truthful Provider Attribution */}
        <span className="text-[10px] font-mono text-slate-400">
          {audit.provider_name === 'MockBlockchainAuditProvider'
            ? 'Digest recorded by Mock/In-Memory Audit Provider'
            : audit.provider_name || 'SENTRIQ Audit Layer'}
        </span>
      </div>

      {/* READY State Details */}
      {isReady && audit.digest && (
        <div className="space-y-1.5 pt-1">
          {/* SHA-256 Digest Row */}
          <div className="flex items-center justify-between bg-slate-900/90 rounded border border-slate-800/80 p-2 font-mono text-[11px]">
            <div className="flex items-center gap-2 overflow-hidden mr-2">
              <span className="text-emerald-400 font-bold text-[10px] uppercase shrink-0">SHA-256 DIGEST</span>
              <span className="text-slate-200 select-all truncate font-mono" title={audit.digest}>
                {audit.digest}
              </span>
            </div>
            <button
              onClick={handleCopyDigest}
              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] flex items-center gap-1 shrink-0 transition-colors"
              title="Copy SHA-256 Digest"
            >
              {copied ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          {/* Artifact Metadata Grid */}
          <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 font-mono pt-1">
            <div>
              <span className="text-slate-500">Artifact Type:</span>{' '}
              <span className="text-slate-300">{audit.artifact_type}</span>
            </div>
            <div>
              <span className="text-slate-500">Artifact ID:</span>{' '}
              <span className="text-slate-300">{audit.artifact_id}</span>
            </div>
            {audit.network && (
              <div>
                <span className="text-slate-500">Network:</span>{' '}
                <span className="text-slate-300">{audit.network}</span>
              </div>
            )}
            {audit.transaction_id && (
              <div>
                <span className="text-slate-500">Tx Hash:</span>{' '}
                <span className="text-slate-300 select-all">{audit.transaction_id}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* UNCONFIGURED State Details */}
      {isUnconfigured && (
        <p className="text-[11px] text-amber-300/80">
          {audit.warnings?.[0] || 'Audit infrastructure is not configured. Artifact digest has not been recorded.'}
        </p>
      )}

      {/* ERROR State Details */}
      {isError && (
        <p className="text-[11px] text-rose-300/80">
          {audit.warnings?.[0] || 'Audit operation encountered an error during digest recording.'}
        </p>
      )}

      {/* Disclaimer */}
      <p className="text-[9.5px] text-slate-500 italic pt-0.5">
        Cryptographic digest evidence proves artifact contents have not been modified since recording.
      </p>
    </div>
  );
};

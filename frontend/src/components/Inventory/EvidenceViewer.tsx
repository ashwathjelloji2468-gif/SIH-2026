import React from 'react';
import { Evidence, CryptoAsset, Recommendation, RiskAssessment } from '../../types';
import { CodeSnippet } from '../Common/CodeSnippet';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { StatusBadge } from '../Common/StatusBadge';
import { ShieldCheck, Info, FileCode, AlertTriangle, ArrowRight, Zap, CheckCircle2, Cpu } from 'lucide-react';

export interface EvidenceViewerProps {
  evidence: Evidence[];
  asset?: CryptoAsset | null;
  recommendation?: Recommendation | null;
  riskAssessment?: RiskAssessment | null;
  riskExplanation?: string | null;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  evidence,
  asset,
  recommendation,
  riskAssessment,
  riskExplanation,
}) => {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800/80 bg-[#1E293B] p-8 text-center text-xs text-[#94A3B8] shadow-lg">
        <Info className="w-6 h-6 text-[#22D3EE] mx-auto mb-2 opacity-60" />
        No cryptographic evidence records attached. Scan target repository to record AST provenance.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {evidence.map((item, idx) => {
        const isVulnerable = asset?.quantum_safety === 'VULNERABLE';
        const confidencePct = Math.round((item.confidence_score || 0.95) * 100);

        return (
          <div
            key={item.id || idx}
            className="rounded-3xl border border-[#22D3EE]/30 bg-[#1E293B] p-6 sm:p-8 space-y-6 shadow-2xl hover:border-[#22D3EE]/60 transition-all duration-300 relative overflow-hidden"
          >
            {/* Top Cyan Ambient Glow Accent */}
            <div className="absolute top-0 right-0 w-80 h-32 bg-[#22D3EE]/5 blur-3xl pointer-events-none" />

            {/* Panel Header & Provenance Badges */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-700/60">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#22D3EE]/10 border border-[#22D3EE]/30 text-[#22D3EE]">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#22D3EE]">
                      Cryptographic Provenance Proof #{idx + 1}
                    </span>
                    <StatusBadge type="evidence" value={item.evidence_type} />
                  </div>
                  <div className="text-sm font-bold font-mono text-[#F8FAFC] truncate max-w-md mt-0.5">
                    {item.source_file} {item.line_number ? `: Line ${item.line_number}` : ''}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="px-3 py-1 rounded-full border border-[#22D3EE]/40 bg-[#0B1120] text-[#22D3EE] font-mono text-xs font-bold shadow-[0_0_12px_rgba(34,211,238,0.2)]">
                  {confidencePct}% Deterministic Confidence
                </div>
                <span className="text-xs text-[#94A3B8] font-mono">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* The 4 First-Class Evidence Pillars Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 1. WHAT DID WE FIND? */}
              <div className="rounded-2xl border border-[#22D3EE]/25 bg-[#0B1120]/90 p-5 space-y-2 shadow-md">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#22D3EE] uppercase tracking-wider">
                  <Cpu className="w-4 h-4" />
                  <span>1. WHAT (Primitive Specification)</span>
                </div>
                <div className="text-lg font-bold font-mono text-[#F8FAFC]">
                  {asset?.algorithm_name || 'Cryptographic Primitive'}
                </div>
                <div className="space-y-1 text-xs text-[#94A3B8]">
                  <div>Purpose: <strong className="text-[#F8FAFC] font-mono">{asset?.purpose || 'General Cryptography'}</strong></div>
                  <div>Key Size / Curve: <strong className="text-[#F8FAFC] font-mono">{asset?.key_size ? `${asset.key_size} bits` : 'Standard'}</strong></div>
                  <div>Classification: <strong className="text-cyan-300 font-mono">{asset?.asset_type || 'AST Declaration'}</strong></div>
                </div>
              </div>

              {/* 2. WHERE DID WE FIND IT? */}
              <div className="rounded-2xl border border-[#22D3EE]/25 bg-[#0B1120]/90 p-5 space-y-2 shadow-md">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider">
                  <FileCode className="w-4 h-4" />
                  <span>2. WHERE (Source Coordinates)</span>
                </div>
                <div className="text-xs font-mono text-[#F8FAFC] truncate font-semibold">
                  {item.source_file}
                </div>
                <div className="space-y-1 text-xs text-[#94A3B8]">
                  <div>Line Number: <strong className="text-[#22D3EE] font-mono">{item.line_number || 'Global Scope'}</strong></div>
                  <div>Detector Engine: <strong className="text-[#F8FAFC] font-mono">{item.detector_name || 'SENTRIQ AST Engine'} v{item.detector_version || '2.0'}</strong></div>
                  <div>Proof Type: <strong className="text-[#22D3EE] font-mono">{item.evidence_type}</strong></div>
                </div>
              </div>

              {/* 3. WHY DOES IT MATTER? */}
              <div className="rounded-2xl border border-rose-500/35 bg-[#0B1120]/90 p-5 md:col-span-2 space-y-2.5 shadow-md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-400 uppercase tracking-wider">
                    <AlertTriangle className="w-4 h-4" />
                    <span>3. WHY (Quantum Risk & Vulnerability Rationale)</span>
                  </div>
                  {riskAssessment && (
                    <span className="text-xs font-mono font-bold text-rose-300 bg-rose-950/80 px-3 py-0.5 rounded-full border border-rose-800/80 shadow-[0_0_10px_rgba(244,63,94,0.3)]">
                      Risk Score: {riskAssessment.risk_score} / 100
                    </span>
                  )}
                </div>
                <p className="text-xs text-[#F8FAFC] leading-relaxed font-sans">
                  {riskExplanation || (isVulnerable
                    ? `Algorithm ${asset?.algorithm_name || 'Primitive'} relies on classical integer factorization or discrete logarithms solved in polynomial time by Shor's Algorithm on a cryptanalytically relevant quantum computer (CRQC).`
                    : `Primitive maintains quantum resistance against Grover's search algorithm under current key size parameters.`
                  )}
                </p>
              </div>

              {/* 4. WHAT SHOULD WE DO NEXT? */}
              <div className="rounded-2xl border border-[#22D3EE]/40 bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#0B1120] p-5 md:col-span-2 space-y-2.5 shadow-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#22D3EE] uppercase tracking-wider">
                    <Zap className="w-4 h-4" />
                    <span>4. WHAT NEXT (NIST PQC Migration Pathway)</span>
                  </div>
                  {recommendation && (
                    <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/40 font-bold uppercase">
                      {recommendation.standard_status}
                    </span>
                  )}
                </div>

                {recommendation ? (
                  <div className="space-y-2">
                    <div className="text-sm font-bold font-mono text-[#22D3EE]">
                      Recommended Candidate: {recommendation.target_pqc_candidate}
                    </div>
                    <p className="text-xs text-[#F8FAFC] leading-relaxed font-sans">
                      {recommendation.rationale}
                    </p>
                    {recommendation.performance_notes && (
                      <div className="text-[11px] text-[#94A3B8] font-mono bg-[#0B1120] p-2.5 rounded-xl border border-slate-700/80">
                        <strong className="text-[#F8FAFC]">Footprint Overhead:</strong> {recommendation.performance_notes}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-[#94A3B8]">
                    Symmetric primitive has sufficient key strength. Maintain key rotation schedules and cryptographic agility.
                  </p>
                )}
              </div>
            </div>

            {/* Source Code Snippet Viewer */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-[#F8FAFC] uppercase tracking-wider text-[11px]">
                  Verified AST Source Excerpt
                </span>
                <span className="text-[#94A3B8] text-[11px]">Detector: {item.detector_name}</span>
              </div>
              <CodeSnippet
                sourceFile={item.source_file}
                lineNumber={item.line_number}
                excerpt={item.excerpt}
                detectorName={item.detector_name}
                detectorVersion={item.detector_version}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default EvidenceViewer;

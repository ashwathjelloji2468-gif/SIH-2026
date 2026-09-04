import React, { useState, useEffect } from 'react';
import { X, ExternalLink, ShieldAlert, Cpu, ArrowRight, CheckCircle2, AlertTriangle, FileCode } from 'lucide-react';
import { CryptoAsset, Evidence, Recommendation, RiskAssessment } from '../../types';
import { inventoryService } from '../../services/inventoryService';
import { recommendationService } from '../../services/recommendationService';
import { riskService } from '../../services/riskService';
import { StatusBadge } from '../Common/StatusBadge';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { EvidenceViewer } from './EvidenceViewer';
import { Link } from 'react-router-dom';

interface AssetDetailDrawerProps {
  asset: CryptoAsset | null;
  onClose: () => void;
}

export const AssetDetailDrawer: React.FC<AssetDetailDrawerProps> = ({ asset, onClose }) => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [riskExplanation, setRiskExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!asset) return;

    let isMounted = true;
    const fetchDetails = async () => {
      setLoading(true);
      try {
        const [evs, recs, risk, expl] = await Promise.allSettled([
          inventoryService.getAssetEvidence(asset.id),
          recommendationService.getAssetRecommendations(asset.id),
          riskService.getAssetRisk(asset.id),
          riskService.getAssetRiskExplanation(asset.id),
        ]);

        if (isMounted) {
          if (evs.status === 'fulfilled') setEvidenceList(evs.value || []);
          if (recs.status === 'fulfilled') setRecommendations(recs.value || []);
          if (risk.status === 'fulfilled') setRiskAssessment(risk.value || null);
          if (expl.status === 'fulfilled') setRiskExplanation(expl.value?.explanation || null);
        }
      } catch (err) {
        console.error('Failed to load asset details:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDetails();
    return () => {
      isMounted = false;
    };
  }, [asset]);

  if (!asset) return null;

  const isVulnerable = asset.quantum_safety === 'VULNERABLE';
  const primaryEvidence = evidenceList[0];
  const primaryRec = recommendations[0];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-[#0B0F19] border-l border-slate-800 shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/40">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <StatusBadge type="quantum" value={asset.quantum_safety} />
                <span className="font-mono text-xs text-slate-400">ID: {asset.id.slice(0, 8)}</span>
                {primaryEvidence && <ConfidenceBadge score={primaryEvidence.confidence_score} />}
              </div>
              <h2 className="text-xl font-bold font-mono text-slate-100">{asset.algorithm_name}</h2>
              <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mt-1 truncate">
                <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="truncate">{asset.location}</span>
                {asset.line_number && <span className="text-cyan-400 font-semibold">:L{asset.line_number}</span>}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* 4-Step Explanation Framework: WHAT -> WHERE -> WHY -> WHAT NEXT */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* WHAT */}
              <div className="rounded-xl border border-slate-800 bg-[#070A12] p-3.5">
                <div className="text-[10px] uppercase tracking-wider font-mono text-cyan-400 font-semibold mb-1">
                  1. WHAT (Cryptographic Primitive)
                </div>
                <div className="text-sm font-bold font-mono text-slate-100">{asset.algorithm_name}</div>
                <div className="text-xs text-slate-400 mt-1">
                  Purpose: <span className="text-slate-200 font-semibold font-mono">{asset.purpose}</span>
                </div>
                {asset.key_size && (
                  <div className="text-xs text-slate-400">
                    Key Size: <span className="text-slate-200 font-mono">{asset.key_size} bits</span>
                  </div>
                )}
              </div>

              {/* WHERE */}
              <div className="rounded-xl border border-slate-800 bg-[#070A12] p-3.5">
                <div className="text-[10px] uppercase tracking-wider font-mono text-blue-400 font-semibold mb-1">
                  2. WHERE (Code Location)
                </div>
                <div className="text-xs font-mono text-slate-200 truncate">{asset.location}</div>
                <div className="text-xs text-slate-400 mt-1">
                  Line: <span className="text-cyan-300 font-mono font-semibold">{asset.line_number || 'Global'}</span>
                </div>
                <div className="text-[11px] text-slate-500 font-mono truncate">
                  Type: {asset.asset_type}
                </div>
              </div>

              {/* WHY */}
              <div className="rounded-xl border border-slate-800 bg-[#070A12] p-3.5 sm:col-span-2">
                <div className="text-[10px] uppercase tracking-wider font-mono text-rose-400 font-semibold mb-1">
                  3. WHY (Quantum Risk & Explainability)
                </div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-300">
                    Quantum Safety Status: <strong className={isVulnerable ? 'text-rose-400' : 'text-emerald-400'}>{asset.quantum_safety}</strong>
                  </span>
                  {riskAssessment && (
                    <span className="text-xs font-mono font-bold text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/60">
                      Risk Score: {riskAssessment.risk_score} / 100
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {riskExplanation || (isVulnerable
                    ? `Algorithm ${asset.algorithm_name} relies on classical discrete logarithm or integer factorization problems solved in polynomial time by Shor's Algorithm on a cryptanalytically relevant quantum computer (CRQC).`
                    : `Symmetric algorithm ${asset.algorithm_name} with sufficient key strength maintains security against Grover's quantum search algorithm.`
                  )}
                </p>
              </div>

              {/* WHAT NEXT */}
              <div className="rounded-xl border border-cyan-900/50 bg-gradient-to-br from-cyan-950/20 to-slate-900/40 p-4 sm:col-span-2">
                <div className="text-[10px] uppercase tracking-wider font-mono text-cyan-400 font-semibold mb-1">
                  4. WHAT NEXT (PQC Migration Recommendation)
                </div>
                {primaryRec ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold font-mono text-cyan-300">
                        Target: {primaryRec.target_pqc_candidate}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                        {primaryRec.standard_status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {primaryRec.rationale}
                    </p>
                    {primaryRec.performance_notes && (
                      <div className="text-[11px] text-slate-400 font-mono bg-slate-950/60 p-2 rounded border border-slate-800">
                        <strong className="text-slate-300">Overhead:</strong> {primaryRec.performance_notes}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">
                    Symmetric primitive has sufficient quantum resistance. Monitor key schedule and crypto-agility.
                  </p>
                )}
              </div>
            </div>

            {/* Evidence Viewer Section */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider font-mono text-slate-400 mb-3 flex items-center justify-between">
                <span>Cryptographic Discovery Evidence ({evidenceList.length})</span>
                <span className="text-[11px] text-slate-500 lowercase font-normal">Deterministic AST & regex provenance</span>
              </h3>
              <EvidenceViewer evidence={evidenceList} />
            </div>
          </div>

          {/* Drawer Footer Actions */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <Link
              to="/migration"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <span>Add to Migration Plan</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

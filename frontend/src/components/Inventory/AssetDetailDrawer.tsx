import React, { useState, useEffect } from 'react';
import { X, ExternalLink, ShieldAlert, Cpu, ArrowRight, CheckCircle2, AlertTriangle, FileCode, GitFork, Network } from 'lucide-react';
import { CryptoAsset, Evidence, Recommendation, RiskAssessment, AssetImpact } from '../../types';
import { inventoryService } from '../../services/inventoryService';
import { recommendationService } from '../../services/recommendationService';
import { riskService } from '../../services/riskService';
import { graphService } from '../../services/graphService';
import { migrationService } from '../../services/migrationService';
import { StatusBadge } from '../Common/StatusBadge';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { EvidenceViewer } from './EvidenceViewer';
import { useNavigate } from 'react-router-dom';

interface AssetDetailDrawerProps {
  asset: CryptoAsset | null;
  onClose: () => void;
  onAssetReviewed?: () => void;
}

export const AssetDetailDrawer: React.FC<AssetDetailDrawerProps> = ({ asset, onClose, onAssetReviewed }) => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [riskExplanation, setRiskExplanation] = useState<string | null>(null);
  const [impact, setImpact] = useState<AssetImpact | null>(null);
  const [migrationInfo, setMigrationInfo] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [reviewAlgo, setReviewAlgo] = useState<string>('');
  const [reviewPurpose, setReviewPurpose] = useState<string>('ENCRYPTION');
  const [reviewAction, setReviewAction] = useState<'RESOLVE' | 'REJECT'>('RESOLVE');
  const [reviewSubmitting, setReviewSubmitting] = useState<boolean>(false);
  const [reviewSuccess, setReviewSuccess] = useState<boolean>(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!asset) return;

    let isMounted = true;
    const fetchDetails = async () => {
      setLoading(true);
      try {
        const [evs, recs, risk, expl, impactRes, migRes] = await Promise.allSettled([
          inventoryService.getAssetEvidence(asset.id),
          recommendationService.getAssetRecommendations(asset.id),
          riskService.getAssetRisk(asset.id),
          riskService.getAssetRiskExplanation(asset.id),
          graphService.getAssetImpact(asset.id),
          migrationService.getAssetMigration(asset.id),
        ]);

        if (isMounted) {
          if (evs.status === 'fulfilled') setEvidenceList(evs.value || []);
          if (recs.status === 'fulfilled') setRecommendations(recs.value || []);
          if (risk.status === 'fulfilled') setRiskAssessment(risk.value || null);
          if (expl.status === 'fulfilled') setRiskExplanation(expl.value?.explanation || null);
          if (impactRes.status === 'fulfilled') setImpact(impactRes.value || null);
          if (migRes.status === 'fulfilled') setMigrationInfo(migRes.value || null);
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

  useEffect(() => {
    if (asset) {
      setReviewAlgo(asset.algorithm_name === 'UNKNOWN_ALGORITHM' ? 'AES' : asset.algorithm_name);
      setReviewPurpose(asset.purpose || 'ENCRYPTION');
      setReviewSuccess(false);
    }
  }, [asset]);

  const handleReviewSubmit = async () => {
    if (!asset) return;
    setReviewSubmitting(true);
    try {
      await inventoryService.reviewUnknownAsset(asset.id, {
        algorithm_name: reviewAction === 'RESOLVE' ? reviewAlgo : undefined,
        purpose: reviewAction === 'RESOLVE' ? (reviewPurpose as any) : undefined,
        action: reviewAction,
      });
      setReviewSuccess(true);
      if (onAssetReviewed) onAssetReviewed();
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setReviewSubmitting(false);
    }
  };

  if (!asset) return null;

  const isVulnerable = asset.quantum_safety === 'VULNERABLE';
  const primaryEvidence = evidenceList[0];
  const primaryRec = recommendations[0];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-8">
        <div className="w-screen max-w-2xl bg-[#080C16] border-l border-slate-800 shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="p-6 border-b border-slate-800/80 flex items-start justify-between bg-slate-900/50">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge type="quantum" value={asset.quantum_safety} />
                <span className="font-mono text-xs text-slate-400">ID: {asset.id.slice(0, 8)}</span>
                {primaryEvidence && (
                  <ConfidenceBadge score={primaryEvidence.confidence_score} />
                )}
              </div>
              <h2 className="text-xl font-bold font-mono text-slate-100">{asset.algorithm_name}</h2>
              <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 truncate">
                <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="text-slate-300 truncate">{asset.location}</span>
                {asset.line_number && <span className="text-cyan-400 font-semibold">:L{asset.line_number}</span>}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Human Review Controls Section */}
            {(asset.is_unknown || asset.review_status === 'PENDING' || (asset.review_status as string) === 'PENDING_REVIEW') && (
              <div className="rounded-2xl border border-amber-500/40 bg-[#1E293B] p-5 space-y-4 shadow-xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-700/80">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-amber-950/80 border border-amber-800/80 text-amber-400">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold font-mono text-slate-100">Human-in-the-Loop Review</h3>
                      <p className="text-[11px] text-slate-400">Preserving original automated evidence while submitting human classification decision</p>
                    </div>
                  </div>
                  {reviewSuccess && (
                    <span className="text-xs font-mono text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Reviewed & Saved
                    </span>
                  )}
                </div>

                {/* Automated Evidence Snapshot (Untouched) */}
                <div className="rounded-xl border border-slate-700/60 bg-[#0B0F19] p-3 text-[11px] font-mono space-y-1">
                  <div className="text-slate-400">Detector: <span className="text-cyan-300">{primaryEvidence?.detector_name || 'AST_Pattern_Engine'}</span></div>
                  <div className="text-slate-400">Confidence: <span className="text-emerald-300">{Math.round((primaryEvidence?.confidence_score || 0.95) * 100)}%</span></div>
                  <div className="text-slate-400">Reason: <span className="text-amber-300">{asset.unknown_reason || 'Unclassified heuristic detection'}</span></div>
                </div>

                {!reviewSuccess && (
                  <div className="space-y-3 pt-1">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-mono text-slate-300 mb-1">Identified Algorithm</label>
                        <input
                          type="text"
                          value={reviewAlgo}
                          onChange={(e) => setReviewAlgo(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-slate-700 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-mono text-slate-300 mb-1">Crypto Purpose</label>
                        <select
                          value={reviewPurpose}
                          onChange={(e) => setReviewPurpose(e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg bg-[#0B0F19] border border-slate-700 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                        >
                          <option value="ENCRYPTION">ENCRYPTION</option>
                          <option value="SIGNATURE">DIGITAL_SIGNATURE</option>
                          <option value="KEY_ESTABLISHMENT">KEY_ESTABLISHMENT</option>
                          <option value="HASHING">HASHING</option>
                          <option value="MAC">MAC</option>
                          <option value="AUTHENTICATION">AUTHENTICATION</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setReviewAction('RESOLVE')}
                          className={`px-3 py-1 rounded-lg text-xs font-mono cursor-pointer border ${
                            reviewAction === 'RESOLVE'
                              ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-bold'
                              : 'bg-slate-900 border-slate-800 text-slate-400'
                          }`}
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          onClick={() => setReviewAction('REJECT')}
                          className={`px-3 py-1 rounded-lg text-xs font-mono cursor-pointer border ${
                            reviewAction === 'REJECT'
                              ? 'bg-rose-950/80 border-rose-500 text-rose-300 font-bold'
                              : 'bg-slate-900 border-slate-800 text-slate-400'
                          }`}
                        >
                          Reject
                        </button>
                      </div>

                      <button
                        type="button"
                        onClick={handleReviewSubmit}
                        disabled={reviewSubmitting}
                        className="px-4 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold font-mono transition-all cursor-pointer shadow-md shadow-amber-950/40"
                      >
                        {reviewSubmitting ? 'Saving...' : 'Submit Review'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
            {/* 4-Step Explainability Framework: WHAT -> WHERE -> WHY -> WHAT NEXT */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* WHAT */}
              <div className="rounded-2xl border border-[#22D3EE]/20 bg-[#1E293B] p-5 space-y-1.5 shadow-lg hover:-translate-y-1 hover:border-[#22D3EE]/40 transition-all">
                <div className="text-[10px] uppercase tracking-wider font-mono text-[#22D3EE] font-bold mb-1">
                  1. WHAT (Primitive Specification)
                </div>
                <div className="text-lg font-bold font-mono text-[#F8FAFC]">{asset.algorithm_name}</div>
                <div className="text-xs text-[#94A3B8]">
                  Purpose: <strong className="text-[#F8FAFC] font-mono">{asset.purpose}</strong>
                </div>
                {asset.key_size && (
                  <div className="text-xs text-[#94A3B8]">
                    Key Size: <strong className="text-[#F8FAFC] font-mono">{asset.key_size} bits</strong>
                  </div>
                )}
              </div>

              {/* WHERE */}
              <div className="rounded-2xl border border-[#22D3EE]/20 bg-[#1E293B] p-5 space-y-1.5 shadow-lg hover:-translate-y-1 hover:border-[#22D3EE]/40 transition-all">
                <div className="text-[10px] uppercase tracking-wider font-mono text-cyan-300 font-bold mb-1">
                  2. WHERE (Source Coordinates)
                </div>
                <div className="text-xs font-mono text-[#F8FAFC] truncate">{asset.location}</div>
                <div className="text-xs text-[#94A3B8]">
                  Line Number: <strong className="text-[#22D3EE] font-mono">{asset.line_number || 'Global'}</strong>
                </div>
                <div className="text-[11px] text-[#94A3B8] font-mono">
                  Asset Classification: {asset.asset_type}
                </div>
              </div>

              {/* WHY */}
              <div className="rounded-2xl border border-rose-500/30 bg-[#1E293B] p-5 sm:col-span-2 space-y-3 shadow-lg hover:-translate-y-1 hover:border-rose-500/50 transition-all">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] uppercase tracking-wider font-mono text-rose-400 font-bold">
                    3. WHY (Quantum Risk Rationale)
                  </div>
                  {riskAssessment && (
                    <span className="text-xs font-mono font-bold text-rose-300 bg-rose-950/80 px-3 py-1 rounded-full border border-rose-800/80 shadow-[0_0_10px_rgba(244,63,94,0.3)]">
                      Risk Score: {riskAssessment.risk_score} / 100
                    </span>
                  )}
                </div>
                <p className="text-xs text-[#F8FAFC] leading-relaxed font-sans">
                  {riskExplanation || (isVulnerable
                    ? `Algorithm ${asset.algorithm_name} relies on classical discrete logarithm or integer factorization problems solved in polynomial time by Shor's Algorithm on a cryptanalytically relevant quantum computer (CRQC).`
                    : `Symmetric algorithm ${asset.algorithm_name} with sufficient key strength maintains quantum resistance against Grover's quantum search algorithm.`
                  )}
                </p>
                <div className="flex items-center gap-4 text-[11px] font-mono text-[#94A3B8] pt-2 border-t border-slate-700/60">
                  <span>Quantum Safety: <strong className={isVulnerable ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>{asset.quantum_safety}</strong></span>
                  <span>•</span>
                  <span>Confidence: <strong className="text-[#22D3EE]">{Math.round((primaryEvidence?.confidence_score || 0.95) * 100)}% (Deterministic)</strong></span>
                </div>
              </div>

              {/* WHAT NEXT */}
              <div className="rounded-2xl border border-[#22D3EE]/40 bg-gradient-to-br from-[#1E293B] via-[#0F172A] to-[#1E293B] p-5 sm:col-span-2 space-y-3 shadow-xl hover:-translate-y-1 transition-all">
                <div className="text-[10px] uppercase tracking-wider font-mono text-[#22D3EE] font-bold">
                  4. WHAT NEXT (NIST PQC Migration Pathway)
                </div>
                {primaryRec ? (
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold font-mono text-[#22D3EE]">
                        Target Candidate: {primaryRec.target_pqc_candidate}
                      </span>
                      <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#22D3EE]/20 text-[#22D3EE] border border-[#22D3EE]/40 font-bold uppercase">
                        {primaryRec.standard_status}
                      </span>
                    </div>
                    <p className="text-xs text-[#F8FAFC] leading-relaxed font-sans">
                      {primaryRec.rationale}
                    </p>
                    {primaryRec.performance_notes && (
                      <div className="text-[11px] text-[#94A3B8] font-mono bg-[#0B1120] p-3 rounded-xl border border-slate-700/80">
                        <strong className="text-[#F8FAFC]">Footprint Overhead:</strong> {primaryRec.performance_notes}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-[#94A3B8] font-sans">
                    Symmetric primitive has sufficient quantum resistance. Monitor key lifecycle and cryptographic agility.
                  </p>
                )}
              </div>
            </div>

            {/* Impact Analysis Section */}
            {impact && impact.affected_components_count > 0 && (
              <div className="rounded-2xl border border-purple-500/30 bg-[#1E293B] p-5 space-y-2 shadow-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Network className="w-4 h-4 text-purple-400" />
                  <span className="text-[10px] uppercase tracking-wider font-mono text-purple-400 font-bold">
                    Dependency Impact Analysis
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-[#0B0F19] border border-slate-800 p-3">
                    <div className="text-[10px] text-slate-500 font-mono uppercase">Affected Components</div>
                    <div className="text-lg font-bold font-mono text-purple-300">{impact.affected_components_count}</div>
                  </div>
                  <div className="rounded-xl bg-[#0B0F19] border border-slate-800 p-3">
                    <div className="text-[10px] text-slate-500 font-mono uppercase">Impacted Assets</div>
                    <div className="text-lg font-bold font-mono text-cyan-300">{impact.impacted_asset_ids.length}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Migration Status Section */}
            {migrationInfo && (
              <div className="rounded-2xl border border-cyan-500/20 bg-[#1E293B] p-5 space-y-2 shadow-lg">
                <div className="flex items-center gap-2 mb-2">
                  <GitFork className="w-4 h-4 text-cyan-400" />
                  <span className="text-[10px] uppercase tracking-wider font-mono text-cyan-400 font-bold">
                    Migration Status
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="rounded-xl bg-[#0B0F19] border border-slate-800 p-3">
                    <div className="text-[10px] text-slate-500 font-mono uppercase">Priority</div>
                    <div className="text-sm font-bold font-mono text-cyan-300">
                      {migrationInfo.priority || 'N/A'}
                    </div>
                  </div>
                  <div className="rounded-xl bg-[#0B0F19] border border-slate-800 p-3">
                    <div className="text-[10px] text-slate-500 font-mono uppercase">Effort</div>
                    <div className="text-sm font-bold font-mono text-amber-300">
                      {migrationInfo.estimated_person_days ? `${migrationInfo.estimated_person_days}d` : 'N/A'}
                    </div>
                  </div>
                  <div className="rounded-xl bg-[#0B0F19] border border-slate-800 p-3">
                    <div className="text-[10px] text-slate-500 font-mono uppercase">Status</div>
                    <div className="text-sm font-bold font-mono text-emerald-300">
                      {migrationInfo.status || 'Not started'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Deterministic Evidence Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">
                  Cryptographic Evidence Proofs ({evidenceList.length})
                </span>
                <span className="text-slate-500 text-[11px]">Deterministic AST & regex provenance</span>
              </div>
              <EvidenceViewer
                evidence={evidenceList}
                asset={asset}
                recommendation={primaryRec}
                riskAssessment={riskAssessment}
                riskExplanation={riskExplanation}
              />
            </div>
          </div>

          {/* Drawer Footer Actions */}
          <div className="p-4 border-t border-slate-800/80 bg-slate-900/70 flex items-center justify-between">
            <button
              onClick={() => {
                onClose();
                navigate('/migration');
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-md shadow-cyan-950/50 transition-all cursor-pointer"
            >
              <GitFork className="w-3.5 h-3.5" />
              <span>Simulate PQC Upgrade Plan</span>
            </button>

            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect, useCallback } from 'react';
import { Sliders, Calculator, ShieldAlert, Info, RotateCcw, Save, AlertTriangle, CheckCircle2, History, ArrowRightLeft } from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { businessCriticalityService, ProjectBusinessCriticality } from '../services/businessCriticalityService';
import { auditService } from '../services/auditService';

interface FactorDefinition {
  id: string;
  name: string;
  weight: number;
  description: string;
}

const FACTORS: FactorDefinition[] = [
  { id: 'dataSensitivity', name: 'Data Sensitivity', weight: 0.15, description: 'Classification level of processed or stored data (Public to Secret).' },
  { id: 'dataShelfLife', name: 'Data Shelf-Life', weight: 0.10, description: 'Duration for which confidentiality must be maintained.' },
  { id: 'confidentialityImpact', name: 'Confidentiality Impact', weight: 0.15, description: 'Impact level if encrypted data is compromised or decrypted.' },
  { id: 'integrityImpact', name: 'Integrity Impact', weight: 0.10, description: 'Impact of unauthorized data modification or signature forgery.' },
  { id: 'availabilityImpact', name: 'Availability Impact', weight: 0.10, description: 'System downtime and service interruption exposure.' },
  { id: 'regulatoryExposure', name: 'Regulatory Exposure', weight: 0.15, description: 'Compliance penalties, audit breaches, and regulatory fines.' },
  { id: 'financialImpact', name: 'Financial Impact', weight: 0.15, description: 'Direct financial loss, transaction liability, and breach costs.' },
  { id: 'reputationalImpact', name: 'Reputational Impact', weight: 0.10, description: 'Customer trust loss, brand damage, and public disclosure impact.' },
];

export const BusinessCriticality: React.FC = () => {
  const { currentProject } = useProject();

  const [critData, setCritData] = useState<ProjectBusinessCriticality | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Local factor ratings state (synced with backend)
  const [ratings, setRatings] = useState<Record<string, number>>({
    dataSensitivity: 5,
    dataShelfLife: 4,
    confidentialityImpact: 5,
    integrityImpact: 4,
    availabilityImpact: 4,
    regulatoryExposure: 5,
    financialImpact: 5,
    reputationalImpact: 4,
    exposureRating: 4,
  });

  // User Planning Override Form state
  const [overrideValue, setOverrideValue] = useState<string>('HIGH');
  const [adjustmentReason, setAdjustmentReason] = useState<string>('');

  // Audit trail state
  const [auditEvents, setAuditEvents] = useState<any[]>([]);

  const loadCriticalityData = useCallback(async () => {
    if (!currentProject) return;
    setLoading(true);
    setError(null);
    try {
      const data = await businessCriticalityService.getProjectBusinessCriticality(currentProject.id);
      setCritData(data);
      if (data.factor_ratings) {
        setRatings(data.factor_ratings);
      }
      if (data.user_override) {
        setOverrideValue(data.user_override);
      } else {
        setOverrideValue(data.system_criticality);
      }
      if (data.adjustment_reason) {
        setAdjustmentReason(data.adjustment_reason);
      } else {
        setAdjustmentReason('');
      }

      // Fetch audit events
      try {
        const audits = await auditService.getProjectAuditTrail(currentProject.id);
        const filtered = (audits || []).filter((a: any) =>
          ['BUSINESS_CRITICALITY_OVERRIDE', 'BUSINESS_CRITICALITY_OVERRIDE_REVERTED', 'UPDATE_USER_CONTEXT'].includes(a.action)
        );
        setAuditEvents(filtered);
      } catch (_) {
        setAuditEvents([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load business criticality for project.');
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  useEffect(() => {
    loadCriticalityData();
  }, [loadCriticalityData]);

  const handleRatingChange = (id: string, value: number) => {
    setRatings((prev) => ({ ...prev, [id]: value }));
  };

  const handleSaveFactorRatings = async () => {
    if (!currentProject) return;
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await businessCriticalityService.updateProjectBusinessCriticality(currentProject.id, {
        factor_ratings: ratings,
      });
      setCritData(updated);
      setSuccessMsg('Factor ratings saved successfully and risk assessments updated.');
    } catch (err: any) {
      setError(err.message || 'Failed to save factor ratings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveOverride = async () => {
    if (!currentProject) return;
    if (!adjustmentReason.trim()) {
      setError('Adjustment reason is required when setting a planning criticality override.');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await businessCriticalityService.overrideBusinessCriticality(
        currentProject.id,
        overrideValue,
        adjustmentReason.trim()
      );
      setCritData(updated);
      setSuccessMsg(`Planning criticality override saved to ${overrideValue}. Risk & Priority queues updated.`);
      loadCriticalityData();
    } catch (err: any) {
      setError(err.message || 'Failed to save business criticality override.');
    } finally {
      setSaving(false);
    }
  };

  const handleRevertOverride = async () => {
    if (!currentProject) return;
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await businessCriticalityService.revertBusinessCriticality(currentProject.id);
      setCritData(updated);
      setAdjustmentReason('');
      setSuccessMsg('Override reverted. Effective planning criticality restored to system classification.');
      loadCriticalityData();
    } catch (err: any) {
      setError(err.message || 'Failed to revert business criticality override.');
    } finally {
      setSaving(false);
    }
  };

  const handleResetLocalDemoExample = () => {
    setRatings({
      dataSensitivity: 5,
      dataShelfLife: 4,
      confidentialityImpact: 5,
      integrityImpact: 4,
      availabilityImpact: 4,
      regulatoryExposure: 5,
      financialImpact: 5,
      reputationalImpact: 4,
      exposureRating: 4,
    });
    setSuccessMsg('Loaded worked example factor values in local view (click Save to persist to project).');
  };

  // Local calculations matching methodology
  const contributions = FACTORS.map((f) => ({
    ...f,
    rating: ratings[f.id] ?? 0,
    contribution: (ratings[f.id] ?? 0) * f.weight,
  }));

  const wis = contributions.reduce((sum, item) => sum + item.contribution, 0);
  const expRating = ratings['exposureRating'] ?? 4;
  const exposureMultiplier = 1.0 + 0.09375 * expRating;
  const rawScore = wis * exposureMultiplier;
  const normalizedValue = Math.min(5.0, Number((rawScore / 1.5).toFixed(2)));

  const getCriticalityBadge = (val: string) => {
    const s = (val || '').toUpperCase();
    if (s === 'CRITICAL') return { label: 'CRITICAL', class: 'bg-rose-950/80 border-rose-700/80 text-rose-300' };
    if (s === 'HIGH') return { label: 'HIGH', class: 'bg-orange-950/80 border-orange-700/80 text-orange-300' };
    if (s === 'MEDIUM') return { label: 'MEDIUM', class: 'bg-amber-950/80 border-amber-700/80 text-amber-300' };
    return { label: 'LOW', class: 'bg-emerald-950/80 border-emerald-700/80 text-emerald-300' };
  };

  const sysBadge = getCriticalityBadge(critData?.system_criticality || 'HIGH');
  const effBadge = getCriticalityBadge(critData?.effective_criticality || 'HIGH');

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Sliders className="w-4 h-4" />
            <span>Governance &amp; Planning Framework (Priority 3)</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">
            Business Criticality — {currentProject?.name || 'Select Project'}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative Weighted Impact Score (WIS), system classification, and user planning override engine.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetLocalDemoExample}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Load Worked Example (Local Demo)</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/50 border border-emerald-800/60 text-xs text-emerald-300 font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-cyan-800/60 bg-gradient-to-br from-cyan-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider">Weighted Impact (WIS)</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{wis.toFixed(2)} <span className="text-xs text-slate-500">/ 5.00</span></div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Sum of factor ratings × weights</p>
        </div>

        <div className="rounded-xl border border-amber-800/60 bg-gradient-to-br from-amber-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-amber-400 uppercase tracking-wider">System Classification</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-2.5 py-1 rounded font-mono font-bold border ${sysBadge.class}`}>
              {sysBadge.label}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Derived from AST discovery &amp; rules</p>
        </div>

        <div className="rounded-xl border border-purple-800/60 bg-gradient-to-br from-purple-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-purple-400 uppercase tracking-wider">User Planning Override</div>
          <div className="flex items-center gap-2 mt-1">
            {critData?.user_override ? (
              <span className={`text-xs px-2.5 py-1 rounded font-mono font-bold border ${getCriticalityBadge(critData.user_override).class}`}>
                {critData.user_override} (OVERRIDDEN)
              </span>
            ) : (
              <span className="text-xs font-mono text-slate-500 italic">None (Using System)</span>
            )}
          </div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Organization planning context</p>
        </div>

        <div className="rounded-xl border border-rose-800/60 bg-gradient-to-br from-rose-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-mono text-rose-400 uppercase tracking-wider">Effective Criticality</span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold border ${effBadge.class}`}>
              {effBadge.label}
            </span>
          </div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-1">{effBadge.label}</div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Used for Risk, Priority &amp; Roadmap</p>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Factor Sliders & Backend Sync */}
        <div className="lg:col-span-6 rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
              <Calculator className="w-4 h-4 text-cyan-400" />
              Factor Rating Sliders (0 – 5)
            </h2>
            <button
              onClick={handleSaveFactorRatings}
              disabled={saving}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-mono font-bold transition-all cursor-pointer shadow-md shadow-cyan-950/50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Factor Ratings</span>
            </button>
          </div>

          <div className="space-y-4">
            {FACTORS.map((f) => {
              const ratingVal = ratings[f.id] ?? 0;
              const contribVal = (ratingVal * f.weight).toFixed(2);
              return (
                <div key={f.id} className="p-3 rounded-xl bg-[#06080F] border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-semibold text-slate-200">{f.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500 text-[11px]">Weight: {(f.weight * 100).toFixed(0)}%</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold">
                        Rating: {ratingVal}
                      </span>
                      <span className="text-emerald-400 font-bold text-[11px]">
                        +{contribVal}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="grid grid-cols-6 gap-1">
                      {[0, 1, 2, 3, 4, 5].map((num) => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => handleRatingChange(f.id, num)}
                          className={`py-1 rounded text-xs font-mono font-bold transition-all cursor-pointer ${
                            ratingVal === num
                              ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-950/50'
                              : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>

                    <input
                      type="range"
                      min={0}
                      max={5}
                      step={1}
                      value={ratingVal}
                      onChange={(e) => handleRatingChange(f.id, Number(e.target.value))}
                      className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">{f.description}</p>
                </div>
              );
            })}

            {/* Exposure Rating Slider */}
            <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2 pt-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-amber-300">Exposure Rating</span>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-bold">
                    Rating: {expRating}
                  </span>
                  <span className="text-amber-400 font-bold text-[11px]">
                    EM = {exposureMultiplier.toFixed(3)}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-6 gap-1">
                {[0, 1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => handleRatingChange('exposureRating', num)}
                    className={`py-1 rounded text-xs font-mono font-bold transition-all cursor-pointer ${
                      expRating === num
                        ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-950/50'
                        : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <input
                type="range"
                min={0}
                max={5}
                step={1}
                value={expRating}
                onChange={(e) => handleRatingChange('exposureRating', Number(e.target.value))}
                className="w-full accent-amber-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
              <p className="text-[10px] text-slate-400">
                Application exposure multiplier based on deployment topology and network accessibility.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: User Planning Override & Audit Trail */}
        <div className="lg:col-span-6 space-y-6">
          {/* User Override Card */}
          <div className="rounded-2xl border border-purple-900/60 bg-[#0B0F19] p-6 shadow-xl space-y-4">
            <div className="pb-3 border-b border-purple-900/40 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-bold">
                  User Planning Override
                </span>
                <h2 className="text-base font-bold font-mono text-slate-100">
                  Override Effective Planning Criticality
                </h2>
              </div>
              {critData?.is_overridden && (
                <button
                  onClick={handleRevertOverride}
                  disabled={saving}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-600 text-slate-300 text-xs font-mono transition-all cursor-pointer"
                >
                  Revert to System Default
                </button>
              )}
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  Planning Criticality Tier
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((tier) => (
                    <button
                      key={tier}
                      type="button"
                      onClick={() => setOverrideValue(tier)}
                      className={`py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        overrideValue === tier
                          ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/60 border border-purple-400'
                          : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {tier}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  Adjustment Reason <span className="text-rose-400">* (Mandatory)</span>
                </label>
                <textarea
                  value={adjustmentReason}
                  onChange={(e) => setAdjustmentReason(e.target.value)}
                  placeholder="e.g. Payment processing system has contractual SLA requirements and regulatory exposure."
                  className="w-full h-24 p-3 rounded-xl bg-[#06080F] border border-slate-800 text-slate-200 text-xs font-mono placeholder-slate-600 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-slate-500">
                  Updates RiskAssessments, Priority Queue, and Roadmap Effort.
                </span>
                <button
                  onClick={handleSaveOverride}
                  disabled={saving || !adjustmentReason.trim()}
                  className="px-4 py-2 rounded-xl bg-purple-500 hover:bg-purple-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-purple-950/50 cursor-pointer transition-all"
                >
                  Save Override &amp; Audit
                </button>
              </div>
            </div>
          </div>

          {/* Audit Trail Card */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800 text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
              <History className="w-4 h-4" />
              <span>Audited Criticality Changes &amp; Overrides</span>
            </div>

            {auditEvents && auditEvents.length > 0 ? (
              <div className="space-y-3 font-mono text-xs max-h-60 overflow-y-auto pr-1">
                {auditEvents.map((evt: any, idx: number) => {
                  const d = evt.details || {};
                  return (
                    <div key={idx} className="p-3 rounded-xl bg-[#06080F] border border-slate-800/80 space-y-1">
                      <div className="flex justify-between items-center text-slate-300 font-bold">
                        <span className="text-cyan-300">{evt.action}</span>
                        <span className="text-[10px] text-slate-500">{new Date(evt.created_at).toLocaleString()}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Actor: <span className="text-slate-200">{evt.actor}</span>
                      </div>
                      {d.reason && (
                        <div className="text-[11px] text-purple-300 italic">
                          "{d.reason}"
                        </div>
                      )}
                      {d.changes && Array.isArray(d.changes) && (
                        <div className="text-[10px] text-slate-500">
                          {d.changes.join(', ')}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-500 font-mono">
                No business criticality override events recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessCriticality;

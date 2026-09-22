import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { qarsService } from '../services/qarsService';
import type {
  QARSProjectResult,
  QARSAssetResult,
  QARSLevel,
} from '../types';
import {
  Binary,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  Info,
  ChevronDown,
  ChevronUp,
  X,
  Clock,
  Layers,
  Activity,
  Sliders,
  Cpu,
} from 'lucide-react';

export const QARS: React.FC = () => {
  const { currentProject } = useProject();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [projectQars, setProjectQars] = useState<QARSProjectResult | null>(null);

  // Selected asset detail drawer state
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [assetDetailLoading, setAssetDetailLoading] = useState<boolean>(false);
  const [assetDetailError, setAssetDetailError] = useState<string | null>(null);
  const [assetDetail, setAssetDetail] = useState<QARSAssetResult | null>(null);

  // Accordion state for "Why this score?"
  const [whyExpanded, setWhyExpanded] = useState<boolean>(false);

  const fetchProjectData = async () => {
    if (!currentProject?.id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await qarsService.getProjectQARS(currentProject.id);
      setProjectQars(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch project QARS evaluation.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectData();
    setSelectedAssetId(null);
    setAssetDetail(null);
  }, [currentProject?.id]);

  const handleAssetClick = async (assetId: string) => {
    if (!currentProject?.id) return;
    setSelectedAssetId(assetId);
    setAssetDetailLoading(true);
    setAssetDetailError(null);
    try {
      const res = await qarsService.getAssetQARS(currentProject.id, assetId);
      setAssetDetail(res);
    } catch (err: any) {
      setAssetDetailError(err?.message || 'Failed to load asset QARS details.');
    } finally {
      setAssetDetailLoading(false);
    }
  };

  // Helper formatting functions (strictly preserving null / unconfigured semantics)
  const formatScore = (val?: number | null): string => {
    if (val === null || val === undefined) return 'Not configured';
    return `${val.toFixed(1)}`;
  };

  const formatPercentage = (val?: number | null): string => {
    if (val === null || val === undefined) return 'Not configured';
    return `${(val * 100).toFixed(1)}%`;
  };

  const getLevelBadgeClass = (level?: string | QARSLevel): string => {
    const l = String(level || '').toUpperCase();
    switch (l) {
      case 'CRITICAL':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
      case 'HIGH':
        return 'bg-rose-900/60 text-rose-200 border-rose-700/60';
      case 'MEDIUM':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
      case 'LOW':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
      default:
        return 'bg-slate-900/80 text-slate-400 border-slate-700/80';
    }
  };

  const getLevelColor = (level?: string | QARSLevel): string => {
    const l = String(level || '').toUpperCase();
    switch (l) {
      case 'CRITICAL':
      case 'HIGH':
        return '#F43F5E'; // rose-500
      case 'MEDIUM':
        return '#F59E0B'; // amber-500
      case 'LOW':
        return '#10B981'; // emerald-500
      default:
        return '#64748B'; // slate-500
    }
  };

  // Representative primary asset for executive header/breakdown (if assets present)
  const primaryAsset: QARSAssetResult | null =
    projectQars && projectQars.assets.length > 0 ? projectQars.assets[0] : null;

  return (
    <div className="space-y-8 pb-12">
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1.5">
            <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 shadow-xs">
              <Binary className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white font-sans flex items-center gap-2">
                QARS
                <span className="text-xs font-mono font-semibold text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded-full border border-cyan-800/80">
                  Phase 5A Production Engine
                </span>
              </h1>
              <p className="text-xs font-mono text-slate-400">Quantum-Aware Risk Scoring</p>
            </div>
          </div>
          <p className="text-xs text-slate-400 max-w-3xl leading-relaxed mt-2">
            QARS combines quantum timeline pressure with cryptographic algorithm impact, system business exposure, infrastructure availability, structural crypto agility, and migration complexity into a bounded, explainable evaluation pipeline.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={fetchProjectData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 text-xs font-medium transition-all shadow-xs disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refetch</span>
          </button>
        </div>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="space-y-6">
          <div className="h-44 rounded-2xl bg-slate-900/40 border border-slate-800/80 animate-pulse p-6 flex flex-col justify-between">
            <div className="h-6 bg-slate-800/60 rounded-md w-1/4" />
            <div className="h-12 bg-slate-800/60 rounded-md w-1/2" />
            <div className="h-4 bg-slate-800/60 rounded-md w-1/3" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-36 rounded-2xl bg-slate-900/40 border border-slate-800/80 animate-pulse p-4 space-y-3">
                <div className="h-4 bg-slate-800/60 rounded-md w-3/4" />
                <div className="h-8 bg-slate-800/60 rounded-md w-1/2" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ERROR STATE */}
      {!loading && error && (
        <div className="rounded-2xl border border-rose-900/80 bg-rose-950/30 p-6 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-rose-200">Failed to Load QARS Evaluation</h3>
            <p className="text-xs text-rose-300/80 font-mono">{error}</p>
            <button
              onClick={fetchProjectData}
              className="mt-2 px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-800/80 text-rose-100 border border-rose-700/80 text-xs font-medium transition-all"
            >
              Retry Action
            </button>
          </div>
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && !error && projectQars && projectQars.asset_count === 0 && (
        <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-12 text-center space-y-4 max-w-2xl mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <HelpCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No QARS Results Available</h3>
          <p className="text-xs text-slate-400 leading-relaxed max-w-md mx-auto">
            No QARS results are available for this project yet. QARS requires scanned cryptographic assets with sufficient runtime context (shelf-life X, migration Y, and quantum horizon Z).
          </p>
        </div>
      )}

      {/* MAIN QARS DASHBOARD DISPLAY */}
      {!loading && !error && projectQars && projectQars.asset_count > 0 && (
        <>
          {/* EXECUTIVE QARS HERO CARD */}
          <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-br from-[#0D1527] via-[#0B0F19] to-[#080B14] p-6 md:p-8 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
              {/* Executive Gauge Ring & Primary Score */}
              <div className="lg:col-span-5 flex flex-col sm:flex-row items-center gap-6 border-b lg:border-b-0 lg:border-r border-slate-800/80 pb-6 lg:pb-0 lg:pr-8">
                {/* SVG Executive Score Gauge */}
                <div className="relative w-36 h-36 shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      className="text-slate-800/80 stroke-current"
                      strokeWidth="8"
                      fill="transparent"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      className="transition-all duration-1000 stroke-current"
                      strokeWidth="8"
                      strokeDasharray={251.2}
                      strokeDashoffset={
                        projectQars.summary.qars_average !== null && projectQars.summary.qars_average !== undefined
                          ? 251.2 - (251.2 * Math.min(100, Math.max(0, projectQars.summary.qars_average))) / 100
                          : 251.2
                      }
                      strokeLinecap="round"
                      fill="transparent"
                      style={{
                        stroke: getLevelColor(
                          projectQars.summary.qars_average !== null && projectQars.summary.qars_average !== undefined
                            ? projectQars.summary.qars_average >= 80
                              ? 'CRITICAL'
                              : projectQars.summary.qars_average >= 60
                              ? 'HIGH'
                              : projectQars.summary.qars_average >= 35
                              ? 'MEDIUM'
                              : 'LOW'
                            : 'UNCONFIGURED'
                        ),
                      }}
                    />
                  </svg>

                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-3xl font-extrabold font-mono tracking-tight text-white">
                      {projectQars.summary.qars_average !== null && projectQars.summary.qars_average !== undefined
                        ? projectQars.summary.qars_average.toFixed(1)
                        : 'UNCONFIGURED'}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mt-0.5">
                      QARS Avg
                    </span>
                  </div>
                </div>

                <div className="space-y-3 text-center sm:text-left">
                  <div>
                    <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
                      Project Executive QARS
                    </div>
                    <div className="flex items-center justify-center sm:justify-start gap-2">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${getLevelBadgeClass(primaryAsset?.level)}`}>
                        {primaryAsset?.level ? String(primaryAsset.level).toUpperCase() : 'UNCONFIGURED'}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        {projectQars.asset_count} Assets Evaluated
                      </span>
                    </div>
                  </div>

                  {primaryAsset && (
                    <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs">
                      <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                        <div className="text-[10px] text-slate-500">Core</div>
                        <div className="text-slate-200 font-bold">{primaryAsset.base_score.toFixed(1)}</div>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                        <div className="text-[10px] text-slate-500 font-sans">Adjustments</div>
                        <div className="text-cyan-400 font-bold">
                          +{Object.values(primaryAsset.adjustments).reduce((a, b) => a + b, 0).toFixed(1)}
                        </div>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                        <div className="text-[10px] text-slate-500">Final</div>
                        <div className="text-white font-bold">{primaryAsset.final_score.toFixed(1)}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Severity Breakdown Summary Cards */}
              <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-900/50 p-3.5 rounded-xl border border-rose-900/40 space-y-1">
                  <div className="text-[10px] font-mono text-rose-400 uppercase tracking-wider font-semibold">Critical</div>
                  <div className="text-2xl font-bold font-mono text-rose-300">{projectQars.summary.critical_count}</div>
                  <div className="text-[10px] text-slate-500 font-mono">QARS &ge; 80</div>
                </div>

                <div className="bg-slate-900/50 p-3.5 rounded-xl border border-rose-900/30 space-y-1">
                  <div className="text-[10px] font-mono text-rose-400 uppercase tracking-wider font-semibold">High</div>
                  <div className="text-2xl font-bold font-mono text-rose-200">{projectQars.summary.high_count}</div>
                  <div className="text-[10px] text-slate-500 font-mono">60 &le; QARS &lt; 80</div>
                </div>

                <div className="bg-slate-900/50 p-3.5 rounded-xl border border-amber-900/40 space-y-1">
                  <div className="text-[10px] font-mono text-amber-400 uppercase tracking-wider font-semibold">Medium</div>
                  <div className="text-2xl font-bold font-mono text-amber-300">{projectQars.summary.medium_count}</div>
                  <div className="text-[10px] text-slate-500 font-mono">35 &le; QARS &lt; 60</div>
                </div>

                <div className="bg-slate-900/50 p-3.5 rounded-xl border border-emerald-900/40 space-y-1">
                  <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider font-semibold">Low</div>
                  <div className="text-2xl font-bold font-mono text-emerald-300">{projectQars.summary.low_count}</div>
                  <div className="text-[10px] text-slate-500 font-mono">QARS &lt; 35</div>
                </div>
              </div>
            </div>
          </div>

          {/* COMPONENT ANALYSIS SECTION */}
          {primaryAsset && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white tracking-tight font-sans flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <span>Component Factor Analysis</span>
                </h2>
                <span className="text-xs font-mono text-slate-400">
                  Bounded Policy Adjustments (&le; 25.0 max)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 1. Algorithm Risk (AQR) */}
                <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-5 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Algorithm Risk</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700/60 text-slate-300">
                      {primaryAsset.algorithm_risk?.calibration_status || 'UNCONFIGURED'}
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold font-mono text-white">
                      {formatPercentage(primaryAsset.algorithm_risk?.aqr_score)}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      AQR Contribution: <strong className="text-cyan-300 font-mono">+{primaryAsset.adjustments['algorithm_risk'] || 0.0}</strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal line-clamp-2">
                    {primaryAsset.algorithm_risk?.explanation || 'Algorithm risk configuration pending.'}
                  </p>
                </div>

                {/* 2. Availability */}
                <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-5 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Availability</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700/60 text-slate-300">
                      {primaryAsset.availability?.status || 'UNCONFIGURED'}
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold font-mono text-white">
                      {primaryAsset.availability?.score !== undefined && primaryAsset.availability?.score !== null
                        ? (primaryAsset.availability.score * 100).toFixed(0) + '/100'
                        : 'Not configured'}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      AV Contribution: <strong className="text-cyan-300 font-mono">+{primaryAsset.adjustments['availability'] || 0.0}</strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal line-clamp-2">
                    {primaryAsset.availability?.explanation || 'Availability business rating unconfigured.'}
                  </p>
                </div>

                {/* 3. Crypto Agility */}
                <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-5 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Crypto Agility</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700/60 text-slate-300">
                      {primaryAsset.crypto_agility_evidence?.status || 'UNCONFIGURED'}
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold font-mono text-white">
                      {formatScore(primaryAsset.crypto_agility_evidence?.agility_score)}
                      {primaryAsset.crypto_agility_evidence?.agility_score !== null && primaryAsset.crypto_agility_evidence?.agility_score !== undefined && (
                        <span className="text-xs text-slate-400 font-normal"> / 100</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      CAR Risk Contribution: <strong className="text-cyan-300 font-mono">+{primaryAsset.adjustments['crypto_agility'] || 0.0}</strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal line-clamp-2">
                    AST AST-parser structural analysis across code abstractions and replaceable interfaces.
                  </p>
                </div>

                {/* 4. Migration Complexity */}
                <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-5 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Migration Complexity</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700/60 text-slate-300">
                      {primaryAsset.migration_complexity?.status || 'UNCONFIGURED'}
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold font-mono text-white">
                      {formatScore(primaryAsset.migration_complexity?.score)}
                      {primaryAsset.migration_complexity?.score !== null && primaryAsset.migration_complexity?.score !== undefined && (
                        <span className="text-xs text-slate-400 font-normal"> / 100</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      MC Contribution: <strong className="text-cyan-300 font-mono">+{primaryAsset.adjustments['migration_complexity'] || 0.0}</strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal line-clamp-2">
                    {primaryAsset.migration_complexity?.explanation || 'Migration complexity evidence collection pending.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* QUANTUM TIMELINE & CORE FORMULA BREAKDOWN GRID */}
          {primaryAsset && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* QUANTUM TIMELINE CARD */}
              <div className="lg:col-span-5 rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white tracking-tight font-sans flex items-center gap-2">
                    <Clock className="w-4 h-4 text-cyan-400" />
                    <span>Quantum Horizon & Timeline Uncertainty</span>
                  </h3>
                  <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {primaryAsset.z_uncertainty?.status || 'POINT_ESTIMATE_ONLY'}
                  </span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Data Shelf-Life (X)</span>
                    <span className="text-cyan-300 font-bold">{primaryAsset.core_input.x_years} years</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Migration Duration (Y)</span>
                    <span className="text-amber-300 font-bold">{primaryAsset.core_input.y_years} years</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Quantum Deadline (Z Central)</span>
                    <span className="text-rose-300 font-bold">{primaryAsset.core_input.z_years} years</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">ZEngine Confidence</span>
                    <span className="text-emerald-400 font-bold">{primaryAsset.z_uncertainty?.confidence || 'HIGH'}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                  <p className="font-semibold text-slate-300 mb-1">Uncertainty Contract Status:</p>
                  <p>Central planning horizon available. Lower/upper statistical bounds unavailable.</p>
                </div>
              </div>

              {/* QARS CORE EXPLAINABLE FORMULA BREAKDOWN */}
              <div className="lg:col-span-7 rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white tracking-tight font-sans flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" />
                    <span>QARS Core Formula Breakdown</span>
                  </h3>
                  <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">
                    Base: {primaryAsset.base_score.toFixed(2)}
                  </span>
                </div>

                {/* Mathematical Formula Banner */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-sans font-semibold">Conceptual Formula</div>
                  <code>QARS_core = 100 &times; T &times; Sn &times; En</code>
                  <div className="text-[11px] text-slate-400 mt-1 font-sans">
                    where <code className="text-cyan-300">T = clamp((X+Y-Z)/Z, 0, 1)</code>, <code className="text-cyan-300">Sn = (S-1)/4</code>, <code className="text-cyan-300">En = (E-1)/4</code>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 font-mono text-xs">
                  <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 text-center">
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Timeline Pressure T</div>
                    <div className="text-base font-bold text-white mt-1">
                      {primaryAsset.explanation.timeline_pressure.toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 text-center">
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Sensitivity Sn (S={primaryAsset.core_input.data_sensitivity})</div>
                    <div className="text-base font-bold text-white mt-1">
                      {primaryAsset.explanation.sensitivity_normalized.toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 text-center">
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Exposure En (E={primaryAsset.core_input.exposure})</div>
                    <div className="text-base font-bold text-white mt-1">
                      {primaryAsset.explanation.exposure_normalized.toFixed(3)}
                    </div>
                  </div>
                </div>

                {/* SECURITY OBJECTIVES COMPACT CHIPS */}
                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">
                    Security Objectives Addressed
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {primaryAsset.explanation.security_objectives && primaryAsset.explanation.security_objectives.length > 0 ? (
                      primaryAsset.explanation.security_objectives.map((obj) => (
                        <span
                          key={obj}
                          className="px-2.5 py-1 rounded-lg bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 text-xs font-mono uppercase font-bold tracking-wider"
                        >
                          {obj}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs font-mono text-slate-500">None explicitly mapped</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* EXPANDABLE "WHY THIS SCORE?" SECTION */}
          {primaryAsset && (
            <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] overflow-hidden">
              <button
                onClick={() => setWhyExpanded(!whyExpanded)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-900/40 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <Info className="w-5 h-5 text-cyan-400" />
                  <div>
                    <h3 className="text-sm font-bold text-white font-sans">Why this score? (Explainable QARS Lineage)</h3>
                    <p className="text-xs text-slate-400 font-mono">
                      WHAT &bull; WHERE &bull; WHY &bull; WHAT NEXT
                    </p>
                  </div>
                </div>
                {whyExpanded ? (
                  <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
              </button>

              {whyExpanded && (
                <div className="px-6 pb-6 pt-2 border-t border-slate-800/60 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1.5">
                      <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">WHAT</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Evaluated base QARS Core score of <strong className="font-mono text-white">{primaryAsset.base_score.toFixed(1)}</strong> based on timeline pressure T = {primaryAsset.explanation.timeline_pressure.toFixed(2)}.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1.5">
                      <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">WHERE</div>
                      <p className="text-xs text-slate-300 leading-relaxed font-mono">
                        Asset ID: {primaryAsset.asset_id} | Project: {primaryAsset.project_id || 'Current Scope'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1.5">
                      <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">WHY</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Applied total bounded policy adjustment of <strong className="font-mono text-cyan-300">+{Object.values(primaryAsset.adjustments).reduce((a, b) => a + b, 0).toFixed(1)}</strong> across active component factors.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1.5">
                      <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">WHAT NEXT</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Review recommended post-quantum algorithm candidates and migration complexity profiles in SENTRIQ.
                      </p>
                    </div>
                  </div>

                  {/* PROVENANCE METADATA */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 font-mono text-xs">
                    <div className="text-[11px] text-slate-400 font-bold uppercase tracking-wider font-sans">
                      Runtime Provenance & Calibration Metadata
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-[11px] text-slate-400">
                      <div>X Source: <span className="text-slate-200">{primaryAsset.provenance.x_source}</span></div>
                      <div>Y Source: <span className="text-slate-200">{primaryAsset.provenance.y_source}</span></div>
                      <div>Z Source: <span className="text-slate-200">{primaryAsset.provenance.z_source}</span></div>
                      <div>S Source: <span className="text-slate-200">{primaryAsset.provenance.s_source}</span></div>
                      <div>E Source: <span className="text-slate-200">{primaryAsset.provenance.e_source}</span></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ASSET-LEVEL QARS TABLE */}
          <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] overflow-hidden space-y-4 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white tracking-tight font-sans flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span>Asset-Level QARS Evaluation</span>
              </h2>
              <span className="text-xs font-mono text-slate-400">
                {projectQars.assets.length} Cryptographic Assets Scanned
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px] tracking-wider bg-slate-900/40">
                    <th className="py-3 px-4">Algorithm</th>
                    <th className="py-3 px-4">Asset ID</th>
                    <th className="py-3 px-4">QARS</th>
                    <th className="py-3 px-4">Level</th>
                    <th className="py-3 px-4">Core</th>
                    <th className="py-3 px-4">AQR</th>
                    <th className="py-3 px-4">AV</th>
                    <th className="py-3 px-4">Agility</th>
                    <th className="py-3 px-4">Migration</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {projectQars.assets.map((asset) => (
                    <tr
                      key={asset.asset_id}
                      onClick={() => handleAssetClick(asset.asset_id)}
                      className="hover:bg-slate-900/60 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-bold text-white">
                        {asset.algorithm_risk?.algorithm || 'UNKNOWN'}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                        {asset.asset_id}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-cyan-300">
                        {asset.final_score.toFixed(1)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getLevelBadgeClass(asset.level)}`}>
                          {String(asset.level).toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300">
                        {asset.base_score.toFixed(1)}
                      </td>
                      <td className="py-3.5 px-4">
                        {formatPercentage(asset.algorithm_risk?.aqr_score)}
                      </td>
                      <td className="py-3.5 px-4">
                        {asset.availability?.score !== undefined && asset.availability?.score !== null
                          ? (asset.availability.score * 100).toFixed(0)
                          : '—'}
                      </td>
                      <td className="py-3.5 px-4">
                        {formatScore(asset.crypto_agility_evidence?.agility_score)}
                      </td>
                      <td className="py-3.5 px-4">
                        {formatScore(asset.migration_complexity?.score)}
                      </td>
                      <td className="py-3.5 px-4 text-[11px] text-slate-400">
                        {asset.algorithm_risk?.calibration_status || 'CONFIGURED'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ASSET DETAIL DRAWER / MODAL */}
      {selectedAssetId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex justify-end z-50 transition-opacity">
          <div className="w-full max-w-xl bg-[#0B0F19] border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-white font-sans flex items-center gap-2">
                  <Binary className="w-5 h-5 text-cyan-400" />
                  <span>Asset QARS Detail</span>
                </h3>
                <p className="text-xs font-mono text-slate-400">{selectedAssetId}</p>
              </div>
              <button
                onClick={() => setSelectedAssetId(null)}
                className="p-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white border border-slate-800 hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {assetDetailLoading && (
              <div className="p-8 text-center space-y-3 font-mono text-xs text-slate-400">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                <p>Loading asset QARS evaluation details...</p>
              </div>
            )}

            {!assetDetailLoading && assetDetailError && (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900 text-xs text-rose-300 font-mono">
                {assetDetailError}
              </div>
            )}

            {!assetDetailLoading && !assetDetailError && assetDetail && (
              <div className="space-y-6 text-xs font-mono">
                {/* Score Header */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Final QARS Score</div>
                    <div className="text-2xl font-bold text-cyan-300 mt-0.5">{assetDetail.final_score.toFixed(1)}</div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getLevelBadgeClass(assetDetail.level)}`}>
                    {String(assetDetail.level).toUpperCase()}
                  </span>
                </div>

                {/* XYZ & Inputs */}
                <div className="space-y-2">
                  <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] font-sans">
                    Timeline Inputs (X, Y, Z, S, E)
                  </div>
                  <div className="grid grid-cols-2 gap-2 bg-slate-900/50 p-3 rounded-xl border border-slate-800/80 text-slate-300">
                    <div>X (Shelf-Life): <span className="text-white font-bold">{assetDetail.core_input.x_years} y</span></div>
                    <div>Y (Migration): <span className="text-white font-bold">{assetDetail.core_input.y_years} y</span></div>
                    <div>Z (Quantum): <span className="text-white font-bold">{assetDetail.core_input.z_years} y</span></div>
                    <div>S (Sensitivity): <span className="text-white font-bold">{assetDetail.core_input.data_sensitivity}</span></div>
                    <div>E (Exposure): <span className="text-white font-bold">{assetDetail.core_input.exposure}</span></div>
                  </div>
                </div>

                {/* Sub-Score Breakdown */}
                <div className="space-y-2">
                  <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] font-sans">
                    Sub-Scores & Component Factors
                  </div>
                  <div className="space-y-1.5">
                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 flex justify-between items-center">
                      <span className="text-slate-400">Algorithm Risk (AQR)</span>
                      <span className="text-cyan-300 font-bold">{formatPercentage(assetDetail.algorithm_risk?.aqr_score)}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 flex justify-between items-center">
                      <span className="text-slate-400">Availability (AV)</span>
                      <span className="text-cyan-300 font-bold">
                        {assetDetail.availability?.score !== undefined && assetDetail.availability?.score !== null
                          ? (assetDetail.availability.score * 100).toFixed(0) + '/100'
                          : 'Not configured'}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 flex justify-between items-center">
                      <span className="text-slate-400">Crypto Agility (CAR)</span>
                      <span className="text-cyan-300 font-bold">{formatScore(assetDetail.crypto_agility_evidence?.car_score)}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 flex justify-between items-center">
                      <span className="text-slate-400">Migration Complexity (MC)</span>
                      <span className="text-cyan-300 font-bold">{formatScore(assetDetail.migration_complexity?.score)}</span>
                    </div>
                  </div>
                </div>

                {/* Policy Adjustments */}
                <div className="space-y-2">
                  <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] font-sans">
                    Policy Component Adjustments
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1 text-slate-300">
                    {Object.entries(assetDetail.adjustments).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-slate-400">{k}</span>
                        <span className="text-cyan-300 font-bold">+{v.toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Provenance & Calibration */}
                <div className="space-y-2">
                  <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] font-sans">
                    Calibration Datasets
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-1 text-[11px] text-slate-400">
                    <div>Algorithm: {assetDetail.algorithm_risk?.calibration_version || 'SENTRIQ Prototype v1'}</div>
                    <div>Agility: {assetDetail.crypto_agility_evidence?.calibration_version || 'SENTRIQ Prototype v1'}</div>
                    <div>Migration: {assetDetail.migration_complexity?.calibration_version || 'SENTRIQ Prototype v1'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

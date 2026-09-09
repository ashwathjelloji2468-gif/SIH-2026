import React, { useState, useEffect, useMemo } from 'react';
import { useProject } from '../context/ProjectContext';
import { recommendationService, RecommendationSummaryResponse } from '../services/recommendationService';
import { Recommendation } from '../types';
import { PQCRecommendationCard } from '../components/Recommendations/PQCRecommendationCard';
import { PQCCatalogModal } from '../components/Recommendations/PQCCatalogModal';
import { RecommendationDetailModal } from '../components/Recommendations/RecommendationDetailModal';
import {
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  BookOpen,
  ArrowRight,
  Zap,
  DollarSign,
  FileCode,
  Eye,
  GitFork,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Cpu,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Recommendations: React.FC = () => {
  const { currentProject } = useProject();
  const navigate = useNavigate();

  const [summary, setSummary] = useState<RecommendationSummaryResponse | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');

  const [isCatalogOpen, setIsCatalogOpen] = useState<boolean>(false);
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false);

  const fetchRecommendations = async () => {
    if (!currentProject) {
      setSummary(null);
      setRecommendations([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await recommendationService.getProjectRecommendationSummary(currentProject.id);
      setSummary(data);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error('Failed to load project recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateProject = async () => {
    if (!currentProject) return;
    setEvaluating(true);
    try {
      const data = await recommendationService.evaluateProjectRecommendations(currentProject.id);
      setSummary(data);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error('Failed to evaluate project recommendations:', err);
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [currentProject]);

  // Derived Summary Counts fallback
  const categoryCounts = useMemo(() => {
    let pqc = 0;
    let retain = 0;
    let manual = 0;
    recommendations.forEach((rec) => {
      const cat = (rec.category || '').toUpperCase();
      if (cat.includes('PQC_REPLACEMENT') || cat.includes('MIGRATE')) pqc++;
      else if (cat.includes('RETAIN')) retain++;
      else manual++;
    });

    return {
      pqc: summary?.category_summary?.pqc_replacement_count ?? pqc,
      retain: summary?.category_summary?.retain_crypto_count ?? retain,
      manual: summary?.category_summary?.manual_review_count ?? manual,
    };
  }, [recommendations, summary]);

  // Filtered List
  const filteredList = useMemo(() => {
    return recommendations.filter((rec) => {
      const alg = (rec.algorithm_name || '').toLowerCase();
      const loc = (rec.location || '').toLowerCase();
      const target = (rec.target_pqc_candidate || rec.recommended_algorithm || '').toLowerCase();
      const query = searchQuery.toLowerCase();

      const matchesSearch = !query || alg.includes(query) || loc.includes(query) || target.includes(query);

      const cat = (rec.category || '').toUpperCase();
      const matchesCategory =
        categoryFilter === 'ALL' ||
        (categoryFilter === 'PQC_REPLACEMENT' && (cat.includes('PQC_REPLACEMENT') || cat.includes('MIGRATE'))) ||
        (categoryFilter === 'HYBRID' && (cat.includes('HYBRID') || rec.alternative_algorithm?.includes('HYBRID'))) ||
        (categoryFilter === 'RETAIN' && cat.includes('RETAIN')) ||
        (categoryFilter === 'MANUAL_REVIEW' && cat.includes('MANUAL'));

      const prio = (rec.priority || 'LOW').toUpperCase();
      const matchesPriority =
        priorityFilter === 'ALL' ||
        (priorityFilter === 'CRITICAL' && prio === 'CRITICAL') ||
        (priorityFilter === 'HIGH' && prio === 'HIGH') ||
        (priorityFilter === 'MODERATE' && (prio === 'MODERATE' || prio === 'MEDIUM')) ||
        (priorityFilter === 'LOW' && prio === 'LOW');

      return matchesSearch && matchesCategory && matchesPriority;
    });
  }, [recommendations, searchQuery, categoryFilter, priorityFilter]);

  const handleOpenDetail = (rec: Recommendation) => {
    setSelectedRec(rec);
    setIsDetailOpen(true);
  };

  const getCategoryBadge = (category?: string, altAlgo?: string) => {
    const catUpper = (category || '').toUpperCase();
    if (catUpper.includes('PQC_REPLACEMENT') || catUpper.includes('MIGRATE')) {
      return <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-cyan-950/90 border border-cyan-700/80 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]">Pure PQC Replacement</span>;
    }
    if (catUpper.includes('HYBRID') || altAlgo?.includes('HYBRID')) {
      return <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-md bg-blue-950/90 border border-blue-700/80 text-blue-300">Hybrid Deployment</span>;
    }
    if (catUpper.includes('RETAIN')) {
      return <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-emerald-950/80 border border-emerald-700/70 text-emerald-300">Retain Primitives</span>;
    }
    return <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-amber-950/80 border border-amber-700/70 text-amber-300">Manual Audit</span>;
  };

  const getPriorityBadge = (priority?: string) => {
    switch (priority?.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-rose-950 text-rose-300 border border-rose-800">Critical</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-orange-950 text-orange-300 border border-orange-800">High</span>;
      case 'MODERATE':
      case 'MEDIUM':
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-amber-950 text-amber-300 border border-amber-800">Moderate</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-mono rounded bg-slate-900 text-slate-400 border border-slate-800">Low</span>;
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>NIST PQC Migration Guidance Engine</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Cryptographic Recommendations Console</h1>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Recommendation Engine: <span className="text-slate-200 font-mono">RecommendationEngine v2.0</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleEvaluateProject}
            disabled={evaluating || loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-mono text-xs font-bold transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] cursor-pointer"
          >
            <Cpu className={`w-4 h-4 ${evaluating ? 'animate-spin' : ''}`} />
            <span>{evaluating ? 'Evaluating Engine...' : 'Run Recommendation Engine'}</span>
          </button>

          <button
            onClick={() => setIsCatalogOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-300 font-mono text-xs font-semibold transition-all cursor-pointer"
          >
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>NIST PQC Catalog</span>
          </button>
          <button
            onClick={fetchRecommendations}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh Recommendations"
          >
            <RefreshCw className={`w-4 h-4 ${loading || evaluating ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Assets Card */}
        <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-5 shadow-lg space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Evaluated Assets</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100">{summary?.total_assets || recommendations.length}</div>
          <p className="text-[11px] text-slate-400 font-mono">Total scanned cryptographic primitives</p>
        </div>

        {/* PQC Replacement Card */}
        <div className="rounded-xl border border-cyan-800/60 bg-gradient-to-br from-cyan-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-cyan-300 uppercase tracking-wider font-semibold">PQC Replacements</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100">{categoryCounts.pqc}</div>
          <p className="text-[11px] text-slate-400 font-mono">ML-KEM (FIPS 203) / ML-DSA (FIPS 204)</p>
        </div>

        {/* Retained Primitives Card */}
        <div className="rounded-xl border border-emerald-800/60 bg-gradient-to-br from-emerald-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-300 uppercase tracking-wider font-semibold">Retained Symmetric</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100">{categoryCounts.retain}</div>
          <p className="text-[11px] text-slate-400 font-mono">AES-256 / SHA-256 / HMAC retained</p>
        </div>

        {/* Manual Audit Card */}
        <div className="rounded-xl border border-amber-800/60 bg-gradient-to-br from-amber-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-amber-300 uppercase tracking-wider font-semibold">Manual Reviews</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100">{categoryCounts.manual}</div>
          <p className="text-[11px] text-slate-400 font-mono">Custom or unclassified primitives</p>
        </div>
      </div>

      {/* Recommendations Table & Toolbar */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-4">
        {/* Controls Toolbar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100">Discovered Asset Recommendations & Migration Guidance</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Showing {filteredList.length} of {recommendations.length} total recommendations evaluated by RecommendationEngine
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search primitive, PQC target..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 text-xs rounded-xl bg-[#06080F] border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-56"
              />
            </div>

            {/* Category Filter */}
            <div className="flex items-center gap-1.5 bg-[#06080F] border border-slate-800 rounded-xl px-2.5 py-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-transparent text-xs font-mono text-slate-300 outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-[#0B0F19]">All Categories</option>
                <option value="PQC_REPLACEMENT" className="bg-[#0B0F19]">Pure PQC Replacement</option>
                <option value="HYBRID" className="bg-[#0B0F19]">Hybrid Deployment</option>
                <option value="RETAIN" className="bg-[#0B0F19]">Retain Symmetric/Hash</option>
                <option value="MANUAL_REVIEW" className="bg-[#0B0F19]">Manual Review</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div className="flex items-center gap-1.5 bg-[#06080F] border border-slate-800 rounded-xl px-2.5 py-1.5">
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-transparent text-xs font-mono text-slate-300 outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-[#0B0F19]">All Priorities</option>
                <option value="CRITICAL" className="bg-[#0B0F19]">Critical Priority</option>
                <option value="HIGH" className="bg-[#0B0F19]">High Priority</option>
                <option value="MODERATE" className="bg-[#0B0F19]">Moderate Priority</option>
                <option value="LOW" className="bg-[#0B0F19]">Low Priority</option>
              </select>
            </div>
          </div>
        </div>

        {/* Main Recommendation Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Classical Primitive & Source Location</th>
                <th className="py-3 px-4">Target PQC Candidate</th>
                <th className="py-3 px-4">Mode / Category</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Latency & Performance Impact</th>
                <th className="py-3 px-4">Cost / Operational Impact</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading || evaluating ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 font-mono">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <Cpu className="w-6 h-6 text-cyan-400 animate-spin" />
                      <span>Evaluating PQC recommendations across codebase artifacts...</span>
                    </div>
                  </td>
                </tr>
              ) : recommendations.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 font-mono space-y-3">
                    <div className="flex justify-center mb-2">
                      <AlertTriangle className="w-8 h-8 text-amber-400" />
                    </div>
                    <div className="text-slate-200 font-bold text-sm">No recommendations evaluated yet for {currentProject?.name}</div>
                    <div className="text-xs text-slate-400 max-w-md mx-auto">
                      Run the NIST PQC Recommendation Engine to analyze all discovered cryptographic primitives and map them to FIPS 203/204/205 standards.
                    </div>
                    <div className="pt-2">
                      <button
                        onClick={handleEvaluateProject}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono text-xs font-bold transition-all shadow-md cursor-pointer"
                      >
                        <Cpu className="w-4 h-4" />
                        <span>Run Recommendation Engine</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ) : filteredList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 font-mono">
                    No recommendations match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredList.map((rec, idx) => {
                  const targetAlgo = rec.recommended_algorithm || rec.target_pqc_candidate;
                  const isHighPriority = rec.priority === 'CRITICAL' || rec.priority === 'HIGH';

                  return (
                    <tr key={rec.id || rec.asset_id || idx} className={`hover:bg-slate-900/60 transition-colors ${isHighPriority ? 'bg-cyan-950/10' : ''}`}>
                      {/* Classical Primitive & Location */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-100 text-sm flex items-center gap-2">
                          <span>{rec.algorithm_name || rec.asset_name || 'Primitive'}</span>
                          <span className="text-[10px] text-slate-500 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800 font-sans">
                            {rec.crypto_purpose || 'UNKNOWN'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                          <FileCode className="w-3 h-3 text-cyan-400 shrink-0" />
                          <span className="truncate max-w-xs">{rec.location || 'Codebase artifact'}{rec.line_number ? `:L${rec.line_number}` : ''}</span>
                        </div>
                      </td>

                      {/* Target PQC Candidate */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-cyan-300 text-sm flex items-center gap-1.5">
                          <span>{targetAlgo}</span>
                          <ArrowRight className="w-3 h-3 text-cyan-500" />
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Status: <span className="text-emerald-400 font-semibold">{rec.standard_status}</span>
                        </div>
                      </td>

                      {/* Mode / Category */}
                      <td className="py-3.5 px-4">
                        {getCategoryBadge(rec.category, rec.alternative_algorithm)}
                      </td>

                      {/* Priority */}
                      <td className="py-3.5 px-4">
                        {getPriorityBadge(rec.priority)}
                      </td>

                      {/* Latency & Performance Impact */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <div className="flex items-center gap-1.5 text-[11px]">
                          <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <span className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-amber-300 text-[10px]">
                            {rec.latency_level || 'LOW'}
                          </span>
                          <span className="truncate text-slate-300 font-sans">{rec.latency_impact || 'Minimal latency impact'}</span>
                        </div>
                      </td>

                      {/* Cost / Operational Impact */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <div className="flex items-center gap-1.5 text-[11px]">
                          <DollarSign className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-emerald-300 text-[10px]">
                            {rec.cost_level || 'MEDIUM'}
                          </span>
                          <span className="truncate text-slate-300 font-sans">{rec.cost_impact || 'Standard migration cost'}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            onClick={() => handleOpenDetail(rec)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-cyan-800/80 bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 text-xs font-mono transition-colors cursor-pointer"
                            title="Inspect full trade-offs and rationale"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Details
                          </button>
                          <button
                            onClick={() => navigate('/migration')}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-colors cursor-pointer"
                            title="Simulate AST migration in Sandbox"
                          >
                            <GitFork className="w-3.5 h-3.5" />
                            Simulate
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      <PQCCatalogModal
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
      />

      <RecommendationDetailModal
        recommendation={selectedRec}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />
    </div>
  );
};

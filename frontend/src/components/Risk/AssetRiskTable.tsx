import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2, Eye, FileCode, ShieldCheck } from 'lucide-react';
import { CryptoAsset, RiskAssessment, RiskSummary } from '../../types';
import { AssetRiskDetailModal } from './AssetRiskDetailModal';

interface AssetRiskTableProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
  assessments: RiskAssessment[];
  isLoading?: boolean;
}

export const AssetRiskTable: React.FC<AssetRiskTableProps> = ({
  assets,
  riskSummary,
  assessments,
  isLoading = false,
}) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [quantumFilter, setQuantumFilter] = useState<string>('ALL');

  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset | null>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<RiskAssessment | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false);

  // Combine assets and risk assessments into unified table items
  const combinedList = useMemo(() => {
    // Reconstruct list from priority_list if available, otherwise from assessments or assets
    const list: Array<{ asset: CryptoAsset | null; assessment: RiskAssessment }> = [];

    const assessedItems = riskSummary?.priority_list && riskSummary.priority_list.length > 0
      ? riskSummary.priority_list
      : assessments;

    if (assessedItems && assessedItems.length > 0) {
      assessedItems.forEach((ass) => {
        const matchAsset = assets.find((a) => a.id === ass.asset_id) || null;
        list.push({ asset: matchAsset, assessment: ass });
      });
    } else {
      // Fallback: create assessment representation from assets if not yet assessed
      assets.forEach((ast) => {
        const isVuln = String(ast.quantum_safety).toUpperCase().includes('VULNERABLE');
        const fallbackScore = isVuln ? 85.0 : 15.0;
        const fallbackLevel = isVuln ? 'HIGH' : 'LOW';
        list.push({
          asset: ast,
          assessment: {
            asset_id: ast.id,
            algorithm_name: ast.algorithm_name,
            location: ast.location,
            quantum_status: String(ast.quantum_safety),
            crypto_purpose: String(ast.purpose),
            risk_score: fallbackScore,
            risk_level: fallbackLevel,
            priority: fallbackLevel,
            confidence_score: 0.95,
            explanation: `Asset ${ast.algorithm_name} evaluated based on discovery findings.`,
            rationale: [`Asset ${ast.algorithm_name} evaluated based on discovery findings.`],
          },
        });
      });
    }

    return list;
  }, [assets, riskSummary, assessments]);

  // Compute Summary Card counts directly from RiskEngine riskSummary if non-zero, else compute directly from combinedList
  const counts = useMemo(() => {
    const sumCritical = riskSummary?.risk_counts?.critical || 0;
    const sumHigh = riskSummary?.risk_counts?.high || 0;
    const sumMedium = (riskSummary?.risk_counts?.moderate || 0) + ((riskSummary?.risk_counts as any)?.medium || 0);
    const sumLow = riskSummary?.risk_counts?.low || 0;
    const totalFromSummary = sumCritical + sumHigh + sumMedium + sumLow;

    if (totalFromSummary > 0) {
      return {
        critical: sumCritical,
        high: sumHigh,
        medium: sumMedium,
        low: sumLow,
      };
    }

    let critical = 0;
    let high = 0;
    let medium = 0;
    let low = 0;

    combinedList.forEach(({ assessment }) => {
      const lvl = (assessment.risk_level || 'LOW').toString().toUpperCase();
      if (lvl.includes('CRITICAL') || assessment.risk_score >= 75) critical++;
      else if (lvl.includes('HIGH') || assessment.risk_score >= 50) high++;
      else if (lvl.includes('MEDIUM') || lvl.includes('MODERATE') || assessment.risk_score >= 25) medium++;
      else low++;
    });

    return { critical, high, medium, low };
  }, [riskSummary, combinedList]);

  // Filtered List
  const filteredList = useMemo(() => {
    return combinedList.filter(({ asset, assessment }) => {
      const alg = (assessment.algorithm_name || asset?.algorithm_name || '').toLowerCase();
      const loc = (assessment.location || asset?.location || '').toLowerCase();
      const query = searchQuery.toLowerCase();

      const matchesSearch = !query || alg.includes(query) || loc.includes(query);

      const lvl = (assessment.risk_level || 'LOW').toString().toUpperCase();
      const matchesLevel =
        levelFilter === 'ALL' ||
        (levelFilter === 'CRITICAL' && (lvl.includes('CRITICAL') || assessment.risk_score >= 75)) ||
        (levelFilter === 'HIGH' && (lvl.includes('HIGH') || (assessment.risk_score >= 50 && assessment.risk_score < 75))) ||
        (levelFilter === 'MEDIUM' && (lvl.includes('MEDIUM') || lvl.includes('MODERATE') || (assessment.risk_score >= 25 && assessment.risk_score < 50))) ||
        (levelFilter === 'LOW' && (lvl.includes('LOW') || assessment.risk_score < 25));

      const qStat = (assessment.quantum_status || asset?.quantum_safety || '').toString().toUpperCase();
      const matchesQuantum =
        quantumFilter === 'ALL' ||
        (quantumFilter === 'VULNERABLE' && qStat.includes('VULNERABLE')) ||
        (quantumFilter === 'RESISTANT' && (qStat.includes('RESISTANT') || qStat.includes('SAFE'))) ||
        (quantumFilter === 'REDUCED_MARGIN' && qStat.includes('REDUCED'));

      return matchesSearch && matchesLevel && matchesQuantum;
    });
  }, [combinedList, searchQuery, levelFilter, quantumFilter]);

  const handleOpenDetail = (asset: CryptoAsset | null, assessment: RiskAssessment) => {
    setSelectedAsset(asset);
    setSelectedAssessment(assessment);
    setIsDetailOpen(true);
  };

  const getLevelBadgeClass = (lvl: string, score: number) => {
    if (lvl.includes('CRITICAL') || score >= 75) return 'bg-rose-950/80 border-rose-800 text-rose-300';
    if (lvl.includes('HIGH') || score >= 50) return 'bg-orange-950/80 border-orange-800 text-orange-300';
    if (lvl.includes('MEDIUM') || lvl.includes('MODERATE') || score >= 25) return 'bg-amber-950/80 border-amber-800 text-amber-300';
    return 'bg-emerald-950/80 border-emerald-800 text-emerald-300';
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center border border-slate-800 rounded-2xl bg-[#0B0F19]">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto mb-3" />
        <p className="text-sm text-slate-400 font-mono">Running RiskEngine evaluation across project assets...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 4 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Critical Card */}
        <div className="rounded-xl border border-rose-800/60 bg-gradient-to-br from-rose-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-rose-300 uppercase tracking-wider font-semibold">Critical Risk</span>
            <ShieldAlert className="w-5 h-5 text-rose-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100 mt-2">{counts.critical}</div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">Immediate PQC migration required (Score ≥75)</p>
        </div>

        {/* High Card */}
        <div className="rounded-xl border border-orange-800/60 bg-gradient-to-br from-orange-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-orange-300 uppercase tracking-wider font-semibold">High Risk</span>
            <AlertTriangle className="w-5 h-5 text-orange-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100 mt-2">{counts.high}</div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">Prioritized migration planning (Score 50-74)</p>
        </div>

        {/* Medium Card */}
        <div className="rounded-xl border border-amber-800/60 bg-gradient-to-br from-amber-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-amber-300 uppercase tracking-wider font-semibold">Medium Risk</span>
            <AlertCircle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100 mt-2">{counts.medium}</div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">Moderate quantum exposure (Score 25-49)</p>
        </div>

        {/* Low Card */}
        <div className="rounded-xl border border-emerald-800/60 bg-gradient-to-br from-emerald-950/40 via-[#0B0F19] to-[#0B0F19] p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-300 uppercase tracking-wider font-semibold">Low Risk</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-slate-100 mt-2">{counts.low}</div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">Acceptable security margin (Score &lt;25)</p>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
        {/* Table Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold font-mono text-slate-100">Discovered Cryptographic Assets — Risk Assessment Table</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Showing {filteredList.length} of {combinedList.length} total evaluated assets
            </p>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search algorithm, file path..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 text-xs rounded-xl bg-[#06080F] border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-56"
              />
            </div>

            {/* Level Filter */}
            <div className="flex items-center gap-1.5 bg-[#06080F] border border-slate-800 rounded-xl px-2.5 py-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="bg-transparent text-xs font-mono text-slate-300 outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-[#0B0F19]">All Risk Levels</option>
                <option value="CRITICAL" className="bg-[#0B0F19]">Critical Risk</option>
                <option value="HIGH" className="bg-[#0B0F19]">High Risk</option>
                <option value="MEDIUM" className="bg-[#0B0F19]">Medium Risk</option>
                <option value="LOW" className="bg-[#0B0F19]">Low Risk</option>
              </select>
            </div>

            {/* Quantum Status Filter */}
            <div className="flex items-center gap-1.5 bg-[#06080F] border border-slate-800 rounded-xl px-2.5 py-1.5">
              <select
                value={quantumFilter}
                onChange={(e) => setQuantumFilter(e.target.value)}
                className="bg-transparent text-xs font-mono text-slate-300 outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-[#0B0F19]">All Quantum Statuses</option>
                <option value="VULNERABLE" className="bg-[#0B0F19]">Quantum Vulnerable</option>
                <option value="RESISTANT" className="bg-[#0B0F19]">Quantum Safe / Resistant</option>
                <option value="REDUCED_MARGIN" className="bg-[#0B0F19]">Reduced Security Margin</option>
              </select>
            </div>
          </div>
        </div>

        {/* Asset Risk Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Cryptographic Asset & Location</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Lifetime (X)</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Quantum Status</th>
                <th className="py-3 px-4">RiskEngine Rationale</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {combinedList.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400 font-mono space-y-2">
                    <div className="flex justify-center mb-1">
                      <AlertCircle className="w-8 h-8 text-cyan-400" />
                    </div>
                    <div className="text-slate-200 font-bold text-sm">No cryptographic assets found for evaluation</div>
                    <div className="text-xs text-slate-400 max-w-md mx-auto">
                      Run a new discovery scan to inspect your codebase primitives, or select a project with discovered assets.
                    </div>
                  </td>
                </tr>
              ) : filteredList.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-500 font-mono">
                    No cryptographic assets match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredList.map(({ asset, assessment }, idx) => {
                  const alg = assessment.algorithm_name || asset?.algorithm_name || 'UNKNOWN';
                  const loc = assessment.location || asset?.location || 'Unknown File';
                  const lineNo = asset?.line_number;
                  const score = assessment.risk_score || 0;
                  const lvl = (assessment.risk_level || 'LOW').toString().toUpperCase();
                  const prio = (assessment.priority || lvl).toString().toUpperCase();
                  const qStat = (assessment.quantum_status || asset?.quantum_safety || 'UNKNOWN').toString();

                  const typeStr = asset?.asset_type || 'ALGORITHM';
                  const lifetimeYr = asset?.data_lifetime_years ?? (alg.includes('RSA') || alg.includes('ECDSA') ? 10 : 7);
                  const lifetimeLbl = asset?.lifetime_label || (lifetimeYr >= 10 ? 'LONG_TERM' : 'MEDIUM_TERM');
                  const critLbl = asset?.business_criticality_label || (qStat.includes('VULNERABLE') ? 'HIGH' : 'MEDIUM');

                  const shortExplanation = assessment.explanation || (assessment.rationale && assessment.rationale[0]) || 'Risk evaluated by RiskEngine.';

                  const isHighOrCritical = lvl.includes('CRITICAL') || lvl.includes('HIGH') || score >= 50;

                  return (
                    <tr key={assessment.asset_id || idx} className={`hover:bg-slate-900/60 transition-colors ${isHighOrCritical ? 'bg-rose-950/10' : ''}`}>
                      {/* Asset & Location */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100 text-sm">{alg}</div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                          <FileCode className="w-3 h-3 text-cyan-400" />
                          {loc}{lineNo ? `:${lineNo}` : ''}
                        </div>
                      </td>

                      {/* Type */}
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-800 text-cyan-300">
                          {typeStr}
                        </span>
                      </td>

                      {/* Lifetime X */}
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-200">
                          {lifetimeLbl} ({lifetimeYr}y)
                        </span>
                      </td>

                      {/* Business Criticality */}
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-mono rounded border ${
                            critLbl === 'CRITICAL'
                              ? 'bg-rose-950/80 border-rose-800 text-rose-300'
                              : critLbl === 'HIGH'
                              ? 'bg-orange-950/80 border-orange-800 text-orange-300'
                              : 'bg-amber-950/80 border-amber-800 text-amber-300'
                          }`}
                        >
                          {critLbl}
                        </span>
                      </td>

                      {/* Risk Score */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                score >= 75 ? 'bg-rose-500' : score >= 50 ? 'bg-orange-500' : score >= 25 ? 'bg-amber-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                            />
                          </div>
                          <span className="font-bold text-slate-200">{score.toFixed(1)}</span>
                        </div>
                      </td>

                      {/* Risk Level */}
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${getLevelBadgeClass(lvl, score)}`}>
                          {lvl}
                        </span>
                      </td>

                      {/* Priority */}
                      <td className="py-3 px-4">
                        <span className="text-slate-300 font-semibold">{prio}</span>
                      </td>

                      {/* Quantum Status */}
                      <td className="py-3 px-4">
                        <span className="text-cyan-300 text-[11px]">{qStat}</span>
                      </td>

                      {/* Short Rationale */}
                      <td className="py-3 px-4 max-w-xs truncate text-slate-400 text-[11px]" title={shortExplanation}>
                        {shortExplanation}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            onClick={() => navigate('/recommendations')}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-cyan-300 text-xs font-mono transition-colors cursor-pointer"
                            title="View PQC Recommendations"
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                            PQC Recs
                          </button>
                          <button
                            onClick={() => handleOpenDetail(asset, assessment)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-800/80 bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 text-xs transition-colors cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View Risk Detail
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

      {/* Asset Risk Detail Modal */}
      <AssetRiskDetailModal
        asset={selectedAsset}
        assessment={selectedAssessment}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />
    </div>
  );
};

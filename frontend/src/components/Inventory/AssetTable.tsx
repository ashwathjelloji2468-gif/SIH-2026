import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight, Eye, AlertCircle, FileCode, ShieldAlert, ShieldCheck, FileSpreadsheet, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { CryptoAsset } from '../../types';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { AssetDetailDrawer } from './AssetDetailDrawer';
import { UnknownReviewModal } from './UnknownReviewModal';

interface AssetTableProps {
  assets: CryptoAsset[];
  loading: boolean;
  onRefresh?: () => void;
}

type SortColumn = 'algorithm_name' | 'asset_type' | 'quantum_safety' | 'business_criticality' | 'confidence' | 'location';
type SortDirection = 'asc' | 'desc';

export const AssetTable: React.FC<AssetTableProps> = ({ assets, loading, onRefresh }) => {
  const navigate = useNavigate();
  const [search, setSearch] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [safetyFilter, setSafetyFilter] = useState<string>('ALL');
  const [purposeFilter, setPurposeFilter] = useState<string>('ALL');
  const [onlyUnknowns, setOnlyUnknowns] = useState<boolean>(false);
  const [sortColumn, setSortColumn] = useState<SortColumn>('quantum_safety');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset | null>(null);
  const [reviewAsset, setReviewAsset] = useState<CryptoAsset | null>(null);

  const pageSize = 15;

  // Real data category counts
  const categoryCounts = useMemo(() => {
    const counts = {
      ALL: assets.length,
      ALGORITHMS: 0,
      CERTIFICATES: 0,
      KEYS: 0,
      PROTOCOLS: 0,
      INFRASTRUCTURE: 0,
      DEPENDENCIES: 0,
      BINARIES: 0,
      VENDOR: 0,
      UNKNOWN: 0
    };

    assets.forEach((a) => {
      if (a.is_unknown) counts.UNKNOWN++;
      const t = (a.asset_type || '').toUpperCase();
      if (t === 'ALGORITHM' || t === 'API_CALL') counts.ALGORITHMS++;
      else if (t === 'CERTIFICATE' || t === 'KEY_STORE') counts.CERTIFICATES++;
      else if (t === 'KEY') counts.KEYS++;
      else if (t === 'PROTOCOL') counts.PROTOCOLS++;
      else if (t === 'HSM' || t === 'TPM' || t === 'CLOUD_KMS') counts.INFRASTRUCTURE++;
      else if (t === 'DEPENDENCY') counts.DEPENDENCIES++;
      else if (t === 'BINARY') counts.BINARIES++;
      else if (t === 'VENDOR_MANAGED') counts.VENDOR++;
    });

    return counts;
  }, [assets]);

  // Filtered and Sorted list
  const filteredAssets = useMemo(() => {
    let result = assets.filter((asset) => {
      if (onlyUnknowns && !asset.is_unknown) return false;
      if (safetyFilter !== 'ALL' && asset.quantum_safety !== safetyFilter) return false;
      if (purposeFilter !== 'ALL' && asset.purpose !== purposeFilter) return false;

      // Category Type filter
      if (typeFilter !== 'ALL') {
        const t = (asset.asset_type || '').toUpperCase();
        if (typeFilter === 'ALGORITHMS' && !(t === 'ALGORITHM' || t === 'API_CALL')) return false;
        if (typeFilter === 'CERTIFICATES' && !(t === 'CERTIFICATE' || t === 'KEY_STORE')) return false;
        if (typeFilter === 'KEYS' && t !== 'KEY') return false;
        if (typeFilter === 'PROTOCOLS' && t !== 'PROTOCOL') return false;
        if (typeFilter === 'INFRASTRUCTURE' && !(t === 'HSM' || t === 'TPM' || t === 'CLOUD_KMS')) return false;
        if (typeFilter === 'DEPENDENCIES' && t !== 'DEPENDENCY') return false;
        if (typeFilter === 'BINARIES' && t !== 'BINARY') return false;
        if (typeFilter === 'VENDOR' && t !== 'VENDOR_MANAGED') return false;
        if (typeFilter === 'UNKNOWN' && !asset.is_unknown) return false;
      }

      // Search matching across all real fields (including AWS, Azure, GCP, KMS, PKCS11, TPM, TLS, SSH)
      if (search.trim()) {
        const query = search.toLowerCase();
        const ev = asset.evidence_items?.[0];
        const searchTarget = [
          asset.algorithm_name,
          asset.name,
          asset.asset_type,
          asset.location,
          asset.purpose,
          asset.quantum_safety,
          asset.business_criticality_label,
          ev?.detector_name,
          ev?.evidence_type,
          ev?.source_file,
          JSON.stringify((asset as any).extra_metadata || {})
        ].filter(Boolean).join(' ').toLowerCase();

        if (!searchTarget.includes(query)) return false;
      }

      return true;
    });

    // Column sorting
    result.sort((a, b) => {
      let valA: any = a[sortColumn as keyof CryptoAsset] ?? '';
      let valB: any = b[sortColumn as keyof CryptoAsset] ?? '';

      if (sortColumn === 'quantum_safety') {
        const safetyWeight: Record<string, number> = {
          VULNERABLE: 4,
          QUANTUM_VULNERABLE: 4,
          TRANSITIONAL: 3,
          UNKNOWN: 2,
          SAFE: 1,
          QUANTUM_SAFE: 1
        };
        valA = safetyWeight[a.quantum_safety || 'UNKNOWN'] || 0;
        valB = safetyWeight[b.quantum_safety || 'UNKNOWN'] || 0;
      } else if (sortColumn === 'business_criticality') {
        const critWeight: Record<string, number> = { CRITICAL: 4, HIGH: 3, MODERATE: 2, MEDIUM: 2, LOW: 1 };
        valA = critWeight[a.business_criticality_label || ''] || 0;
        valB = critWeight[b.business_criticality_label || ''] || 0;
      } else if (sortColumn === 'confidence') {
        valA = a.evidence_items?.[0]?.confidence_score ?? -1;
        valB = b.evidence_items?.[0]?.confidence_score ?? -1;
      }

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [assets, search, typeFilter, safetyFilter, purposeFilter, onlyUnknowns, sortColumn, sortDirection]);

  const totalPages = Math.ceil(filteredAssets.length / pageSize) || 1;
  const paginatedAssets = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAssets.slice(start, start + pageSize);
  }, [filteredAssets, currentPage]);

  const handleSort = (col: SortColumn) => {
    if (sortColumn === col) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDirection('desc');
    }
  };

  const renderSortIcon = (col: SortColumn) => {
    if (sortColumn !== col) return <ArrowUpDown className="w-3 h-3 text-slate-600 inline ml-1" />;
    return sortDirection === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400 inline ml-1" /> : <ArrowDown className="w-3 h-3 text-cyan-400 inline ml-1" />;
  };

  return (
    <div className="space-y-4">
      {/* Category Filter Chips with Real Data Counts */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800 text-xs font-mono">
        <span className="text-slate-500 uppercase tracking-wider text-[10px] shrink-0 mr-1">Filter Type:</span>
        <button
          onClick={() => { setTypeFilter('ALL'); setCurrentPage(1); }}
          className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
            typeFilter === 'ALL' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          All ({categoryCounts.ALL})
        </button>
        {categoryCounts.ALGORITHMS > 0 && (
          <button
            onClick={() => { setTypeFilter('ALGORITHMS'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'ALGORITHMS' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Algorithms ({categoryCounts.ALGORITHMS})
          </button>
        )}
        {categoryCounts.CERTIFICATES > 0 && (
          <button
            onClick={() => { setTypeFilter('CERTIFICATES'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'CERTIFICATES' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Certificates ({categoryCounts.CERTIFICATES})
          </button>
        )}
        {categoryCounts.KEYS > 0 && (
          <button
            onClick={() => { setTypeFilter('KEYS'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'KEYS' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Keys ({categoryCounts.KEYS})
          </button>
        )}
        {categoryCounts.PROTOCOLS > 0 && (
          <button
            onClick={() => { setTypeFilter('PROTOCOLS'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'PROTOCOLS' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Protocols ({categoryCounts.PROTOCOLS})
          </button>
        )}
        {categoryCounts.INFRASTRUCTURE > 0 && (
          <button
            onClick={() => { setTypeFilter('INFRASTRUCTURE'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'INFRASTRUCTURE' ? 'bg-purple-950/80 border-purple-500 text-purple-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Infrastructure (HSM/TPM/KMS) ({categoryCounts.INFRASTRUCTURE})
          </button>
        )}
        {categoryCounts.DEPENDENCIES > 0 && (
          <button
            onClick={() => { setTypeFilter('DEPENDENCIES'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'DEPENDENCIES' ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Dependencies ({categoryCounts.DEPENDENCIES})
          </button>
        )}
        {categoryCounts.UNKNOWN > 0 && (
          <button
            onClick={() => { setTypeFilter('UNKNOWN'); setCurrentPage(1); }}
            className={`px-2.5 py-1 rounded-lg border shrink-0 transition-colors cursor-pointer ${
              typeFilter === 'UNKNOWN' ? 'bg-amber-950/80 border-amber-500 text-amber-300 font-semibold' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Needs Review ({categoryCounts.UNKNOWN})
          </button>
        )}
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#0B0F19] p-4 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search AWS, Azure, KMS, PKCS11, TPM, TLS, SSH, RSA, location..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {/* Quantum Safety Filter */}
          <select
            value={safetyFilter}
            onChange={(e) => {
              setSafetyFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Quantum Safety</option>
            <option value="VULNERABLE">Vulnerable (RSA/ECC)</option>
            <option value="SAFE">Quantum Safe</option>
            <option value="TRANSITIONAL">Transitional</option>
            <option value="UNKNOWN">Unknown</option>
          </select>

          {/* Purpose Filter */}
          <select
            value={purposeFilter}
            onChange={(e) => {
              setPurposeFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Purposes</option>
            <option value="ENCRYPTION">Encryption</option>
            <option value="SIGNATURE">Signature</option>
            <option value="KEY_ESTABLISHMENT">Key Establishment</option>
            <option value="HASHING">Hashing</option>
            <option value="AUTHENTICATION">Authentication</option>
          </select>

          {/* Unknown / Needs Review Toggle */}
          <button
            onClick={() => {
              setOnlyUnknowns(!onlyUnknowns);
              setCurrentPage(1);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono transition-colors cursor-pointer ${
              onlyUnknowns
                ? 'bg-amber-950/70 border-amber-600 text-amber-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Needs Review</span>
          </button>

          <button
            onClick={() => navigate('/risk')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-800/80 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 text-xs font-mono font-semibold transition-colors cursor-pointer"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>View Risk Assessment</span>
          </button>

          <button
            onClick={() => navigate('/recommendations')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-800/80 bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 text-xs font-mono font-semibold transition-colors cursor-pointer"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>PQC Recommendations</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold transition-colors cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export CBOM</span>
          </button>
        </div>
      </div>

      {/* Asset Table Container */}
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase tracking-wider border-b border-slate-800 text-[11px]">
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors" onClick={() => handleSort('algorithm_name')}>
                  Algorithm / Asset {renderSortIcon('algorithm_name')}
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors" onClick={() => handleSort('asset_type')}>
                  Type {renderSortIcon('asset_type')}
                </th>
                <th className="py-3 px-4">
                  <div>Data Lifetime (X)</div>
                  <div className="text-[9px] text-cyan-400 font-sans normal-case tracking-normal">Project Context</div>
                </th>
                <th className="py-3 px-4">
                  <div>Migration Time (Y)</div>
                  <div className="text-[9px] text-amber-400 font-sans normal-case tracking-normal">Project Context</div>
                </th>
                <th className="py-3 px-4">
                  <div>Threat Horizon (Z)</div>
                  <div className="text-[9px] text-purple-400 font-sans normal-case tracking-normal">ZEngine Target</div>
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors" onClick={() => handleSort('business_criticality')}>
                  Business Criticality {renderSortIcon('business_criticality')}
                </th>
                <th className="py-3 px-4">Purpose</th>
                <th className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors" onClick={() => handleSort('location')}>
                  Source Location {renderSortIcon('location')}
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors" onClick={() => handleSort('confidence')}>
                  Confidence {renderSortIcon('confidence')}
                </th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {paginatedAssets.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500 font-sans">
                    No cryptographic assets match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                paginatedAssets.map((asset) => {
                  const ev = asset.evidence_items && asset.evidence_items[0];

                  // UNFABRICATED values: display canonical effective data or honest "Not assessed"
                  const confidence = ev?.confidence_score != null ? ev.confidence_score : null;
                  const lifetimeYr = asset.effective_x_years != null ? `${asset.effective_x_years}y` : null;
                  const lifetimeLbl = asset.lifetime_label || null;
                  const migrationYr = asset.effective_y_years != null ? `${asset.effective_y_years}y` : null;
                  const threatZ = asset.effective_z_target_year != null ? asset.effective_z_target_year : null;
                  const critLbl = asset.business_criticality_label || null;

                  return (
                    <tr
                      key={asset.id}
                      onClick={() => setSelectedAsset(asset)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                            {asset.algorithm_name}
                          </span>
                          {asset.key_size && (
                            <span className="text-[10px] text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                              {asset.key_size}b
                            </span>
                          )}
                          {asset.is_unknown && (
                            <span className="text-[10px] text-amber-400 bg-amber-950/60 px-1.5 py-0.2 rounded border border-amber-800/60">
                              Review
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-sans truncate">
                          {asset.name}
                        </div>
                      </td>

                      {/* Type */}
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-800 text-cyan-300">
                          {asset.asset_type || 'ALGORITHM'}
                        </span>
                      </td>

                      {/* Lifetime X */}
                      <td className="py-3 px-4">
                        {lifetimeYr ? (
                          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-200">
                            {lifetimeYr} {lifetimeLbl ? `(${lifetimeLbl})` : ''}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-600 font-sans">Not assessed</span>
                        )}
                      </td>

                      {/* Migration Y */}
                      <td className="py-3 px-4">
                        {migrationYr ? (
                          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-950/60 border border-amber-800/60 text-amber-200">
                            {migrationYr}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-600 font-sans">Not assessed</span>
                        )}
                      </td>

                      {/* Horizon Z */}
                      <td className="py-3 px-4">
                        {threatZ ? (
                          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-purple-950/60 border border-purple-800/60 text-purple-200">
                            {threatZ}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-600 font-sans">Not assessed</span>
                        )}
                      </td>

                      {/* Business Criticality */}
                      <td className="py-3 px-4">
                        {critLbl ? (
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
                        ) : (
                          <span className="text-[10px] text-slate-600 font-sans">Not assessed</span>
                        )}
                      </td>

                      {/* Purpose */}
                      <td className="py-3 px-4">
                        <span className="text-slate-300">{asset.purpose || 'UNKNOWN'}</span>
                      </td>

                      {/* Location */}
                      <td className="py-3 px-4 max-w-xs truncate text-slate-400">
                        <div className="flex items-center gap-1.5 truncate">
                          <FileCode className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          <span className="truncate">{asset.location}</span>
                          {asset.line_number && (
                            <span className="text-cyan-400 font-semibold">:L{asset.line_number}</span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        {confidence != null ? (
                          <ConfidenceBadge score={confidence} showLabel={false} />
                        ) : (
                          <span className="text-[10px] text-slate-600 font-sans">Not available</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          {asset.is_unknown && (
                            <button
                              onClick={() => setReviewAsset(asset)}
                              className="px-2 py-1 rounded bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-800/80 text-[11px] font-sans font-semibold transition-colors cursor-pointer"
                            >
                              Triage
                            </button>
                          )}
                          <button
                            onClick={() => navigate(`/risk?asset_id=${asset.id}`)}
                            className="px-2 py-1 rounded bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/60 text-[11px] font-mono font-semibold transition-colors cursor-pointer flex items-center gap-1"
                            title="View Risk Engine Assessment for this asset"
                          >
                            <ShieldAlert className="w-3 h-3" />
                            Risk
                          </button>
                          <button
                            onClick={() => setSelectedAsset(asset)}
                            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                            title="Inspect Evidence & Recommendations"
                          >
                            <Eye className="w-3.5 h-3.5" />
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

        {/* Pagination Footer */}
        <div className="p-3 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
          <div>
            Showing <span className="text-slate-200">{filteredAssets.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</span> to{' '}
            <span className="text-slate-200">{Math.min(currentPage * pageSize, filteredAssets.length)}</span> of{' '}
            <span className="text-slate-200">{filteredAssets.length}</span> assets
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent cursor-pointer transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent cursor-pointer transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over Asset Detail & Evidence Drawer */}
      <AssetDetailDrawer
        asset={selectedAsset}
        onClose={() => setSelectedAsset(null)}
      />

      {/* Unknown Asset Review Modal */}
      {reviewAsset && (
        <UnknownReviewModal
          asset={reviewAsset}
          onClose={() => setReviewAsset(null)}
          onReviewed={() => {
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </div>
  );
};

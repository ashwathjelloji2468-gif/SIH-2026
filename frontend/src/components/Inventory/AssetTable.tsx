import React, { useState, useMemo } from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, Eye, AlertCircle, FileCode, CheckCircle2 } from 'lucide-react';
import { CryptoAsset, QuantumSafety, CryptoPurpose } from '../../types';
import { StatusBadge } from '../Common/StatusBadge';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { AssetDetailDrawer } from './AssetDetailDrawer';
import { UnknownReviewModal } from './UnknownReviewModal';

interface AssetTableProps {
  assets: CryptoAsset[];
  loading: boolean;
  onRefresh?: () => void;
}

export const AssetTable: React.FC<AssetTableProps> = ({ assets, loading, onRefresh }) => {
  const [search, setSearch] = useState<string>('');
  const [safetyFilter, setSafetyFilter] = useState<string>('ALL');
  const [purposeFilter, setPurposeFilter] = useState<string>('ALL');
  const [onlyUnknowns, setOnlyUnknowns] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset | null>(null);
  const [reviewAsset, setReviewAsset] = useState<CryptoAsset | null>(null);

  const pageSize = 15;

  // Filtered list
  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      if (onlyUnknowns && !asset.is_unknown) return false;
      if (safetyFilter !== 'ALL' && asset.quantum_safety !== safetyFilter) return false;
      if (purposeFilter !== 'ALL' && asset.purpose !== purposeFilter) return false;

      if (search.trim()) {
        const query = search.toLowerCase();
        const matchesAlg = asset.algorithm_name.toLowerCase().includes(query);
        const matchesLoc = asset.location.toLowerCase().includes(query);
        const matchesPurpose = asset.purpose.toLowerCase().includes(query);
        if (!matchesAlg && !matchesLoc && !matchesPurpose) return false;
      }

      return true;
    });
  }, [assets, search, safetyFilter, purposeFilter, onlyUnknowns]);

  const totalPages = Math.ceil(filteredAssets.length / pageSize) || 1;
  const paginatedAssets = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAssets.slice(start, start + pageSize);
  }, [filteredAssets, currentPage]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="space-y-4">
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
            placeholder="Search algorithm, file path, purpose..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
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
        </div>
      </div>

      {/* Asset Table Container */}
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase tracking-wider border-b border-slate-800 text-[11px]">
              <tr>
                <th className="py-3 px-4">Algorithm & Primitive</th>
                <th className="py-3 px-4">Purpose</th>
                <th className="py-3 px-4">Quantum Safety</th>
                <th className="py-3 px-4">Source Location</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {paginatedAssets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 font-sans">
                    No cryptographic assets match the selected criteria.
                  </td>
                </tr>
              ) : (
                paginatedAssets.map((asset) => {
                  const ev = asset.evidence_items && asset.evidence_items[0];
                  const confidence = ev ? ev.confidence_score : 0.95;

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

                      <td className="py-3 px-4">
                        <span className="text-slate-300">{asset.purpose}</span>
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge type="quantum" value={asset.quantum_safety} />
                      </td>

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
                        <ConfidenceBadge score={confidence} showLabel={false} />
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
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent cursor-pointer transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
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

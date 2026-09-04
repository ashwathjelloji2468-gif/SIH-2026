import React, { useState, useEffect, useCallback } from 'react';
import { useProject } from '../context/ProjectContext';
import { inventoryService } from '../services/inventoryService';
import { CryptoAsset, CoverageReport } from '../types';
import { AssetTable } from '../components/Inventory/AssetTable';
import { DisclaimerBanner } from '../components/Common/DisclaimerBanner';
import { Binary, AlertTriangle, RefreshCw, Layers } from 'lucide-react';

export const Inventory: React.FC = () => {
  const { currentProject } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'all' | 'unknowns'>('all');

  const fetchInventory = useCallback(async () => {
    if (!currentProject) {
      setAssets([]);
      setCoverage(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [invData, covData] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        inventoryService.getProjectCoverage(currentProject.id),
      ]);

      if (invData.status === 'fulfilled') setAssets(invData.value || []);
      if (covData.status === 'fulfilled') setCoverage(covData.value || null);
    } catch (err) {
      console.error('Failed to load inventory:', err);
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const unknownAssets = assets.filter((a) => a.is_unknown);
  const displayAssets = activeTab === 'all' ? assets : unknownAssets;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Binary className="w-4 h-4" />
            <span>Cryptographic Asset Inventory</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Discovered Cryptographic Primitives</h1>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Total Discovered: <strong className="text-slate-200 font-mono">{assets.length}</strong> assets
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchInventory}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh inventory"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Discovery Limits Disclaimer */}
      <DisclaimerBanner
        coveragePercentage={coverage?.overall_coverage_percentage}
        unknownCount={coverage?.unknown_needs_review_count}
      />

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('all')}
          className={`pb-3 px-1 text-xs font-mono font-semibold transition-colors relative cursor-pointer ${
            activeTab === 'all'
              ? 'text-cyan-300 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          All Cryptographic Assets ({assets.length})
        </button>

        <button
          onClick={() => setActiveTab('unknowns')}
          className={`pb-3 px-1 text-xs font-mono font-semibold transition-colors relative cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'unknowns'
              ? 'text-amber-300 border-b-2 border-amber-400'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>Needs Review ({unknownAssets.length})</span>
        </button>
      </div>

      {/* Main Asset Table */}
      <AssetTable
        assets={displayAssets}
        loading={loading}
        onRefresh={fetchInventory}
      />
    </div>
  );
};

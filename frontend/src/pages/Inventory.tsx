import React, { useState, useEffect, useCallback } from 'react';
import { useProject } from '../context/ProjectContext';
import { inventoryService } from '../services/inventoryService';
import { CryptoAsset, CoverageReport } from '../types';
import { AssetTable } from '../components/Inventory/AssetTable';
import { CoveragePanel } from '../components/Inventory/CoveragePanel';
import { UnknownReviewModal } from '../components/Inventory/UnknownReviewModal';
import { NetworkNodes3D } from '../components/Three/NetworkNodes3D';
import { Binary, AlertTriangle, RefreshCw, Layers, Box, Table, ShieldCheck } from 'lucide-react';

export const Inventory: React.FC = () => {
  const { currentProject } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'coverage' | 'all' | 'unknowns'>('coverage');
  const [viewMode, setViewMode] = useState<'table' | '3d'>('table');
  const [reviewAsset, setReviewAsset] = useState<CryptoAsset | null>(null);

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
  const displayAssets = activeTab === 'unknowns' ? unknownAssets : assets;

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
          {/* View Mode Switcher (only relevant in asset views) */}
          {(activeTab === 'all' || activeTab === 'unknowns') && (
            <div className="flex items-center p-1 rounded-xl border border-slate-800 bg-[#0B0F19]">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  viewMode === 'table' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Table className="w-3.5 h-3.5" />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode('3d')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  viewMode === '3d' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Box className="w-3.5 h-3.5" />
                <span>3D Graph</span>
              </button>
            </div>
          )}

          <button
            onClick={fetchInventory}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh inventory"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-4 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('coverage')}
          className={`pb-3 px-1 text-xs font-mono font-semibold transition-colors relative cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'coverage'
              ? 'text-cyan-300 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Coverage & Scope</span>
        </button>

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

      {/* Tab Content */}
      {activeTab === 'coverage' ? (
        <CoveragePanel
          coverage={coverage}
          unknownAssets={unknownAssets}
          onReviewAsset={(asset) => setReviewAsset(asset)}
        />
      ) : viewMode === '3d' ? (
        <div className="rounded-2xl border border-slate-800/80 bg-[#0B0F19] p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 font-mono">3D Cryptographic Dependency Mesh</h3>
              <p className="text-xs text-slate-400">Interactive node network map of detected primitives and cryptographic call graph</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-rose-400"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>Vulnerable (RSA/ECC)</span>
              <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>Quantum Safe (AES/ML-KEM)</span>
            </div>
          </div>
          <div className="h-[500px] w-full rounded-xl overflow-hidden bg-[#06080F]/80 border border-slate-800/60 relative">
            <NetworkNodes3D className="w-full h-full" />
          </div>
        </div>
      ) : (
        <AssetTable
          assets={displayAssets}
          loading={loading}
          onRefresh={fetchInventory}
        />
      )}

      {/* Unknown Asset Review Modal */}
      {reviewAsset && (
        <UnknownReviewModal
          asset={reviewAsset}
          onClose={() => setReviewAsset(null)}
          onReviewed={() => {
            setReviewAsset(null);
            fetchInventory();
          }}
        />
      )}
    </div>
  );
};

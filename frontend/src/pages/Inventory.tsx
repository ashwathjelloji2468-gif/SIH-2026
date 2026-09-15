import React, { useState, useEffect, useCallback } from 'react';
import { useProject } from '../context/ProjectContext';
import { inventoryService } from '../services/inventoryService';
import { CryptoAsset, CoverageReport } from '../types';
import { AssetTable } from '../components/Inventory/AssetTable';
import { CoveragePanel } from '../components/Inventory/CoveragePanel';
import { UnknownReviewModal } from '../components/Inventory/UnknownReviewModal';
import { NetworkNodes3D } from '../components/Three/NetworkNodes3D';
import { Binary, AlertTriangle, RefreshCw, Box, Table, ShieldCheck, AlertCircle, Cpu, Key, FileCheck, Network, Lock, Package } from 'lucide-react';

export const Inventory: React.FC = () => {
  const { currentProject } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'coverage' | 'all' | 'unknowns'>('coverage');
  const [viewMode, setViewMode] = useState<'table' | '3d'>('table');
  const [reviewAsset, setReviewAsset] = useState<CryptoAsset | null>(null);

  const fetchInventory = useCallback(async () => {
    if (!currentProject) {
      setAssets([]);
      setCoverage(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [invRes, covRes] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        inventoryService.getProjectCoverage(currentProject.id),
      ]);

      if (invRes.status === 'fulfilled') {
        setAssets(invRes.value || []);
      } else {
        console.error('Inventory fetch error:', invRes.reason);
        setError('Unable to load cryptographic inventory from backend server.');
      }

      if (covRes.status === 'fulfilled') {
        setCoverage(covRes.value || null);
      }
    } catch (err: any) {
      console.error('Failed to load inventory:', err);
      setError(err?.message || 'Unable to load cryptographic inventory.');
    } finally {
      setLoading(false);
    }
  }, [currentProject]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const unknownAssets = assets.filter((a) => a.is_unknown);
  const displayAssets = activeTab === 'unknowns' ? unknownAssets : assets;

  // Real data breakdown summary counts
  const summaryCounts = {
    total: assets.length,
    algorithms: assets.filter((a) => ['ALGORITHM', 'API_CALL'].includes((a.asset_type || '').toUpperCase())).length,
    certificates: assets.filter((a) => ['CERTIFICATE', 'KEY_STORE'].includes((a.asset_type || '').toUpperCase())).length,
    keys: assets.filter((a) => (a.asset_type || '').toUpperCase() === 'KEY').length,
    protocols: assets.filter((a) => (a.asset_type || '').toUpperCase() === 'PROTOCOL').length,
    infrastructure: assets.filter((a) => ['HSM', 'TPM', 'CLOUD_KMS'].includes((a.asset_type || '').toUpperCase())).length,
    dependencies: assets.filter((a) => (a.asset_type || '').toUpperCase() === 'DEPENDENCY').length,
  };

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
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Discovered Assets: <strong className="text-slate-200 font-mono">{assets.length}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
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
            disabled={loading}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer disabled:opacity-50"
            title="Refresh inventory"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Real Data Breakdown Summary Cards */}
      {assets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Algorithms</div>
            <div className="text-lg font-bold font-mono text-cyan-400 mt-0.5">{summaryCounts.algorithms}</div>
          </div>
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Certificates</div>
            <div className="text-lg font-bold font-mono text-emerald-400 mt-0.5">{summaryCounts.certificates}</div>
          </div>
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Keys & Stores</div>
            <div className="text-lg font-bold font-mono text-amber-400 mt-0.5">{summaryCounts.keys}</div>
          </div>
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Protocols</div>
            <div className="text-lg font-bold font-mono text-blue-400 mt-0.5">{summaryCounts.protocols}</div>
          </div>
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Infrastructure</div>
            <div className="text-lg font-bold font-mono text-purple-400 mt-0.5">{summaryCounts.infrastructure}</div>
          </div>
          <div className="p-3 rounded-xl border border-slate-800 bg-[#0B0F19]">
            <div className="text-[10px] text-slate-500 font-mono uppercase">Dependencies</div>
            <div className="text-lg font-bold font-mono text-slate-300 mt-0.5">{summaryCounts.dependencies}</div>
          </div>
        </div>
      )}

      {/* Error State Banner */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/40 text-rose-300 text-xs font-mono flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchInventory}
            className="px-3 py-1.5 rounded-lg bg-rose-900 hover:bg-rose-800 text-white font-semibold transition-colors cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      )}

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

import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { inventoryService } from '../services/inventoryService';
import { riskService } from '../services/riskService';
import { scanService } from '../services/scanService';
import { migrationService } from '../services/migrationService';
import { validationService } from '../services/validationService';
import { recommendationService } from '../services/recommendationService';
import { CryptoAsset, RiskSummary, CoverageReport, Scan, Recommendation } from '../types';
import { MigrationSummary, SimulationRecord } from '../services/migrationService';
import { ValidationSummary } from '../services/validationService';
import { ExecutiveHero } from '../components/Dashboard/ExecutiveHero';
import { MetricCards } from '../components/Dashboard/MetricCards';
import { AlgorithmChart } from '../components/Dashboard/AlgorithmChart';
import { MoscaUrgencyCard } from '../components/Dashboard/MoscaUrgencyCard';
import { PipelineStatus } from '../components/Dashboard/PipelineStatus';
import { TopMigrationPrioritiesCard } from '../components/Dashboard/TopMigrationPrioritiesCard';
import { DataHandlingSecurityCard } from '../components/Dashboard/DataHandlingSecurityCard';
import { ValidationSummaryCard } from '../components/Dashboard/ValidationSummaryCard';
import { AssetDetailDrawer } from '../components/Inventory/AssetDetailDrawer';
import { DisclaimerBanner } from '../components/Common/DisclaimerBanner';
import { StatusBadge } from '../components/Common/StatusBadge';
import { Link } from 'react-router-dom';
import { ArrowRight, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export const Home: React.FC = () => {
  const { currentProject, setIsScanModalOpen } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [migrationSummary, setMigrationSummary] = useState<MigrationSummary | null>(null);
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  const [simulations, setSimulations] = useState<SimulationRecord[]>([]);
  const [recommendations, setRecommendations] = useState<Map<string, Recommendation[]>>(new Map());
  const [selectedAsset, setSelectedAsset] = useState<CryptoAsset | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<boolean>(false);

  const loadDashboardData = async () => {
    if (!currentProject) return;
    setLoading(true);
    setApiError(false);
    try {
      const [invRes, riskRes, covRes, scansRes, migRes, valRes, simRes] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        riskService.getRiskSummary(currentProject.id),
        inventoryService.getProjectCoverage(currentProject.id),
        scanService.getProjectScans(currentProject.id),
        migrationService.getMigrationSummary(currentProject.id),
        validationService.getValidationSummary(currentProject.id),
        migrationService.listSimulations(currentProject.id),
      ]);

      const loadedAssets = invRes.status === 'fulfilled' ? (invRes.value || []) : [];
      setAssets(loadedAssets);
      if (riskRes.status === 'fulfilled') setRiskSummary(riskRes.value || null);
      if (covRes.status === 'fulfilled') setCoverage(covRes.value || null);
      if (scansRes.status === 'fulfilled') setScans(scansRes.value || []);
      if (migRes.status === 'fulfilled') setMigrationSummary(migRes.value || null);
      if (valRes.status === 'fulfilled') setValidationSummary(valRes.value || null);
      if (simRes.status === 'fulfilled') setSimulations(simRes.value || []);

      const isConnectionError = (res: PromiseSettledResult<any>) => {
        if (res.status === 'rejected') {
          const reason = res.reason;
          return reason?.status === 0 || reason?.message?.includes('Network request failed') || reason?.name === 'TypeError';
        }
        return false;
      };

      if (isConnectionError(invRes) || isConnectionError(riskRes)) {
        setApiError(true);
      }

      // Fetch recommendations for vulnerable assets (batch, non-blocking)
      const vulnerableAssets = loadedAssets.filter((a: CryptoAsset) => a.quantum_safety === 'VULNERABLE');
      if (vulnerableAssets.length > 0) {
        const recResults = await Promise.allSettled(
          vulnerableAssets.slice(0, 10).map((a: CryptoAsset) =>
            recommendationService.getAssetRecommendations(a.id)
          )
        );
        const recMap = new Map<string, Recommendation[]>();
        recResults.forEach((res, idx) => {
          if (res.status === 'fulfilled' && res.value) {
            recMap.set(vulnerableAssets[idx].id, res.value);
          }
        });
        setRecommendations(recMap);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setApiError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentProject) {
      setAssets([]);
      setRiskSummary(null);
      setCoverage(null);
      setScans([]);
      setMigrationSummary(null);
      setValidationSummary(null);
      setSimulations([]);
      setRecommendations(new Map());
      setLoading(false);
      setApiError(false);
      return;
    }

    loadDashboardData();
  }, [currentProject]);

  return (
    <div className="space-y-8 pb-12">
      {/* Executive Hero */}
      <ExecutiveHero />

      {/* Backend API Connection Alert */}
      {apiError && (
        <div className="rounded-xl border border-amber-800/80 bg-amber-950/40 p-4 text-xs font-mono text-amber-300 flex items-center justify-between shadow-xl">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Backend Service Alert:</strong> Unable to connect to SENTRIQ backend service at{' '}
              <code className="text-amber-200 bg-amber-900/50 px-1 py-0.5 rounded">{api.getBaseUrl()}</code>.
              Metrics reflect current live state.
            </span>
          </div>
          <button
            onClick={() => loadDashboardData()}
            className="px-3 py-1 rounded bg-amber-900/60 hover:bg-amber-800 border border-amber-700 text-amber-200 text-xs font-sans font-semibold transition-colors cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Scope and Discovery Disclaimer */}
      <DisclaimerBanner
        coveragePercentage={coverage?.overall_coverage_percentage}
        unknownCount={coverage?.unknown_needs_review_count}
      />

      {/* PQC Transition Pipeline Status */}
      <PipelineStatus
        assets={assets}
        riskSummary={riskSummary}
        migrationSummary={migrationSummary}
        validationSummary={validationSummary}
        loading={loading}
      />

      {/* Primary KPI Metric Cards */}
      <MetricCards
        assets={assets}
        riskSummary={riskSummary}
        coverage={coverage}
        loading={loading}
      />

      {/* Mosca Theorem Urgency & Algorithm Distribution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <MoscaUrgencyCard />
        </div>
        <div className="lg:col-span-6">
          <AlgorithmChart assets={assets} />
        </div>
      </div>

      {/* Top Migration Priorities & Data Handling Security Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <TopMigrationPrioritiesCard
            assets={assets}
            recommendations={recommendations}
            loading={loading}
            onSelectAsset={(asset) => setSelectedAsset(asset)}
          />
        </div>
        <div className="lg:col-span-5">
          <DataHandlingSecurityCard />
        </div>
      </div>

      {/* Validation Summary Section */}
      <ValidationSummaryCard
        validationSummary={validationSummary}
        simulations={simulations}
        loading={loading}
      />

      {/* Recent Scans Activity Section */}
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Cryptographic Scan Telemetry</h3>
            <p className="text-xs text-slate-400">Recent AST analysis and CBOM generation activity</p>
          </div>
          <Link
            to="/scan"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300"
          >
            <span>Scan Console</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {scans.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No scans performed on this repository yet. Click "Scan Source Code" to start discovery.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {scans.slice(0, 5).map((scan) => (
              <div key={scan.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <StatusBadge type="scan" value={scan.status} />
                  <span className="text-slate-300 truncate max-w-xs sm:max-w-md">
                    {scan.target_path}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-slate-400 text-[11px]">
                  <span>CBOM: v{scan.cbom_version}</span>
                  <span>{new Date(scan.created_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Interactive Asset Detail Drawer for Selected Priority Asset */}
      <AssetDetailDrawer asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
    </div>
  );
};

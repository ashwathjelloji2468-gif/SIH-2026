import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { inventoryService } from '../services/inventoryService';
import { riskService } from '../services/riskService';
import { scanService } from '../services/scanService';
import { CryptoAsset, RiskSummary, CoverageReport, Scan } from '../types';
import { ExecutiveHero } from '../components/Dashboard/ExecutiveHero';
import { MetricCards } from '../components/Dashboard/MetricCards';
import { AlgorithmChart } from '../components/Dashboard/AlgorithmChart';
import { MoscaUrgencyCard } from '../components/Dashboard/MoscaUrgencyCard';
import { DisclaimerBanner } from '../components/Common/DisclaimerBanner';
import { StatusBadge } from '../components/Common/StatusBadge';
import { Link } from 'react-router-dom';
import { ArrowRight, ScanSearch, CheckCircle2, Clock } from 'lucide-react';

export const Home: React.FC = () => {
  const { currentProject, setIsScanModalOpen } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!currentProject) {
      setAssets([]);
      setRiskSummary(null);
      setCoverage(null);
      setScans([]);
      setLoading(false);
      return;
    }

    let isMounted = true;
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        const [invRes, riskRes, covRes, scansRes] = await Promise.allSettled([
          inventoryService.getProjectInventory(currentProject.id),
          riskService.getRiskSummary(currentProject.id),
          inventoryService.getProjectCoverage(currentProject.id),
          scanService.getProjectScans(currentProject.id),
        ]);

        if (isMounted) {
          if (invRes.status === 'fulfilled') setAssets(invRes.value || []);
          if (riskRes.status === 'fulfilled') setRiskSummary(riskRes.value || null);
          if (covRes.status === 'fulfilled') setCoverage(covRes.value || null);
          if (scansRes.status === 'fulfilled') setScans(scansRes.value || []);
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, [currentProject]);

  return (
    <div className="space-y-8 pb-12">
      {/* Executive Hero */}
      <ExecutiveHero />

      {/* Scope and Discovery Disclaimer */}
      <DisclaimerBanner
        coveragePercentage={coverage?.overall_coverage_percentage}
        unknownCount={coverage?.unknown_needs_review_count}
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
    </div>
  );
};

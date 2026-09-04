import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { riskService } from '../services/riskService';
import { inventoryService } from '../services/inventoryService';
import { graphService } from '../services/graphService';
import { CryptoAsset, RiskSummary, RiskAssessment, ThreatScenario, ProjectGraph } from '../types';
import { RiskMatrix } from '../components/Risk/RiskMatrix';
import { MoscaSimulator } from '../components/Risk/MoscaSimulator';
import { DependencyGraph } from '../components/Graph/DependencyGraph';
import { ShieldAlert, RefreshCw, Cpu, Network } from 'lucide-react';

export const Risk: React.FC = () => {
  const { currentProject } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [scenarios, setScenarios] = useState<ThreatScenario[]>([]);
  const [graph, setGraph] = useState<ProjectGraph | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchRiskData = async () => {
    if (!currentProject) {
      setAssets([]);
      setRiskSummary(null);
      setAssessments([]);
      setGraph(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [invRes, sumRes, scenRes, graphRes] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        riskService.getRiskSummary(currentProject.id),
        riskService.listThreatScenarios(),
        graphService.getProjectGraph(currentProject.id),
      ]);

      if (invRes.status === 'fulfilled') setAssets(invRes.value || []);
      if (sumRes.status === 'fulfilled') setRiskSummary(sumRes.value || null);
      if (scenRes.status === 'fulfilled') setScenarios(scenRes.value || []);
      if (graphRes.status === 'fulfilled') setGraph(graphRes.value || null);
    } catch (err) {
      console.error('Failed to load risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
  }, [currentProject]);

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Quantum Risk & Exposure Modeling</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Quantum Vulnerability Assessment</h1>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Risk Model Version: <span className="text-slate-200 font-mono">2.0-MOSCA</span>
          </p>
        </div>

        <button
          onClick={fetchRiskData}
          className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer self-start sm:self-auto"
          title="Refresh risk assessment"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Interactive Mosca Theorem Simulator */}
      <MoscaSimulator scenarios={scenarios} />

      {/* Risk Severity Posture Matrix */}
      <RiskMatrix
        assets={assets}
        riskSummary={riskSummary}
        assessments={assessments}
      />

      {/* Cryptographic Topology & Centrality Graph */}
      <DependencyGraph
        graph={graph}
        loading={loading}
      />
    </div>
  );
};

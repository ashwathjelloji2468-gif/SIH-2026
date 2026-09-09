import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { riskService } from '../services/riskService';
import { inventoryService } from '../services/inventoryService';
import { graphService } from '../services/graphService';
import { getProjectXContext, updateProjectXContext } from '../services/xEngineService';
import { getProjectYContext, updateProjectYContext } from '../services/yEngineService';
import { getProjectZContext } from '../services/zEngineService';
import { getProjectMoscaContext } from '../services/moscaEngineService';
import { CryptoAsset, RiskSummary, RiskAssessment, ThreatScenario, ProjectGraph } from '../types';
import { ProjectXContextResponse, XContextUpdateInput } from '../types/xEngine';
import { ProjectYContextResponse, YContextUpdateInput } from '../types/yEngine';
import { ZProjectEvaluationResponse } from '../types/zEngine';
import { MoscaProjectEvaluationResponse } from '../types/moscaEngine';
import { AssetRiskTable } from '../components/Risk/AssetRiskTable';
import { MoscaSimulator } from '../components/Risk/MoscaSimulator';
import { MoscaComponentTable } from '../components/Risk/MoscaComponentTable';
import { DependencyGraph } from '../components/Graph/DependencyGraph';
import { MoscaGraph3D } from '../components/Three/MoscaGraph3D';
import { XContextCard } from '../components/XEngine/XContextCard';
import { XContextModal } from '../components/XEngine/XContextModal';
import { YContextCard } from '../components/YEngine/YContextCard';
import { YContextModal } from '../components/YEngine/YContextModal';
import { ZContextCard } from '../components/ZEngine/ZContextCard';
import { ShieldAlert, RefreshCw, Box, Play } from 'lucide-react';

export const Risk: React.FC = () => {
  const { currentProject } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [scenarios, setScenarios] = useState<ThreatScenario[]>([]);
  const [graph, setGraph] = useState<ProjectGraph | null>(null);
  const [xContext, setXContext] = useState<ProjectXContextResponse | null>(null);
  const [yContext, setYContext] = useState<ProjectYContextResponse | null>(null);
  const [zContext, setZContext] = useState<ZProjectEvaluationResponse | null>(null);
  const [moscaContext, setMoscaContext] = useState<MoscaProjectEvaluationResponse | null>(null);
  const [isXModalOpen, setIsXModalOpen] = useState<boolean>(false);
  const [isYModalOpen, setIsYModalOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [reassessing, setReassessing] = useState<boolean>(false);

  const fetchRiskData = async () => {
    if (!currentProject) {
      setAssets([]);
      setRiskSummary(null);
      setAssessments([]);
      setGraph(null);
      setXContext(null);
      setYContext(null);
      setZContext(null);
      setMoscaContext(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [invRes, sumRes, scenRes, graphRes, xRes, yRes, zRes, mRes] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        riskService.getRiskSummary(currentProject.id),
        riskService.listThreatScenarios(),
        graphService.getProjectGraph(currentProject.id),
        getProjectXContext(currentProject.id),
        getProjectYContext(currentProject.id),
        getProjectZContext(currentProject.id),
        getProjectMoscaContext(currentProject.id),
      ]);

      if (invRes.status === 'fulfilled') setAssets(invRes.value || []);
      if (sumRes.status === 'fulfilled' && sumRes.value) {
        setRiskSummary(sumRes.value);
        if (sumRes.value.priority_list) {
          setAssessments(sumRes.value.priority_list);
        }
      }
      if (scenRes.status === 'fulfilled') setScenarios(scenRes.value || []);
      if (graphRes.status === 'fulfilled') setGraph(graphRes.value || null);
      if (xRes.status === 'fulfilled') setXContext(xRes.value || null);
      if (yRes.status === 'fulfilled') setYContext(yRes.value || null);
      if (zRes.status === 'fulfilled') setZContext(zRes.value || null);
      if (mRes.status === 'fulfilled') setMoscaContext(mRes.value || null);
    } catch (err) {
      console.error('Failed to load risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReassessProject = async () => {
    if (!currentProject) return;
    setReassessing(true);
    try {
      await riskService.assessProjectRisk(currentProject.id);
      await fetchRiskData();
    } catch (err) {
      console.error('Failed to reassess project risk:', err);
    } finally {
      setReassessing(false);
    }
  };

  const handleSaveXContext = async (input: XContextUpdateInput) => {
    if (!currentProject) return;
    try {
      const updated = await updateProjectXContext(currentProject.id, input);
      setXContext(updated);
    } catch (err) {
      console.error('Failed to update X Context', err);
    }
  };

  const handleSaveYContext = async (input: YContextUpdateInput) => {
    if (!currentProject) return;
    try {
      const updated = await updateProjectYContext(currentProject.id, input);
      setYContext(updated);
    } catch (err) {
      console.error('Failed to update Y Context', err);
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
          <h1 className="text-2xl font-bold font-mono text-slate-100">Quantum Risk Assessment Console</h1>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Risk Engine: <span className="text-slate-200 font-mono">RiskEngine v2.0</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleReassessProject}
            disabled={reassessing || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-mono text-xs font-semibold transition-all cursor-pointer shadow-lg shadow-cyan-500/20 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${reassessing ? 'animate-spin' : ''}`} />
            {reassessing ? 'Evaluating RiskEngine...' : 'Run Full Risk Assessment'}
          </button>
          <button
            onClick={fetchRiskData}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh risk assessment"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Asset Risk Assessment Table & Summary Cards */}
      <AssetRiskTable
        assets={assets}
        riskSummary={riskSummary}
        assessments={assessments}
        isLoading={loading}
      />

      {/* Confidentiality & Migration Time Engines (X & Y) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <XContextCard
          xContext={xContext}
          onOpenModal={() => setIsXModalOpen(true)}
          isLoading={loading}
        />
        <YContextCard
          yContext={yContext}
          onOpenModal={() => setIsYModalOpen(true)}
          isLoading={loading}
        />
      </div>

      {/* Z Engine — Component-Wise Quantum Exposure Card */}
      <ZContextCard
        zContext={zContext}
        isLoading={loading}
      />

      {/* Integrated Mosca Engine Component Risk Table (M_i = X + Y - Z_i) */}
      <MoscaComponentTable
        moscaContext={moscaContext}
        isLoading={loading}
      />

      {/* 3D Mosca Threat Horizon Visualization Card */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Box className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100 font-mono">3D Threat Horizon & Risk Exposure Space</h3>
          </div>
          <span className="text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-1 rounded-full">
            Theorem: X ({xContext?.x_result?.value || riskSummary?.mosca?.data_lifetime_years || 20}y) + Y ({yContext?.y_result?.value || riskSummary?.mosca?.migration_time_years || 10}y) &gt; Z ({riskSummary?.mosca?.quantum_threat_horizon || 2033})
          </span>
        </div>
        <div className="h-[380px] w-full rounded-xl overflow-hidden bg-[#06080F]/90 border border-slate-800/60 relative">
          <MoscaGraph3D
            dataLifetime={xContext?.x_result?.value || riskSummary?.mosca?.data_lifetime_years || 20}
            migrationTime={yContext?.y_result?.value || riskSummary?.mosca?.migration_time_years || 10}
            threatHorizon={riskSummary?.mosca?.quantum_threat_horizon || 2033}
            className="w-full h-full"
          />
        </div>
      </div>

      {/* Interactive Mosca Theorem Simulator */}
      <MoscaSimulator scenarios={scenarios} />

      {/* Cryptographic Topology & Centrality Graph */}
      <DependencyGraph
        graph={graph}
        loading={loading}
      />

      {/* X Context Override Modal */}
      <XContextModal
        isOpen={isXModalOpen}
        onClose={() => setIsXModalOpen(false)}
        xContext={xContext}
        onSave={handleSaveXContext}
      />

      {/* Y Context Override Modal */}
      <YContextModal
        isOpen={isYModalOpen}
        onClose={() => setIsYModalOpen(false)}
        yContext={yContext}
        onSave={handleSaveYContext}
      />
    </div>
  );
};

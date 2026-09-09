import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import { riskService } from '../services/riskService';
import { inventoryService } from '../services/inventoryService';
import { graphService } from '../services/graphService';
import { getProjectXContext, updateProjectXContext } from '../services/xEngineService';
import { getProjectYContext, updateProjectYContext } from '../services/yEngineService';
import { getProjectZContext } from '../services/zEngineService';
import { getProjectMoscaContext } from '../services/moscaEngineService';
import {
  CryptoAsset, RiskSummary, RiskAssessment, ThreatScenario, ProjectGraph,
  ScanGraph, BlastRadiusResult, TopBlastRadiusSummary, CryptoNode
} from '../types';
import { ProjectXContextResponse, XContextUpdateInput } from '../types/xEngine';
import { ProjectYContextResponse, YContextUpdateInput } from '../types/yEngine';
import { ZProjectEvaluationResponse } from '../types/zEngine';
import { MoscaProjectEvaluationResponse } from '../types/moscaEngine';
import { AssetRiskTable } from '../components/Risk/AssetRiskTable';
import { MoscaSimulator } from '../components/Risk/MoscaSimulator';
import { MoscaComponentTable } from '../components/Risk/MoscaComponentTable';
import { InteractiveNetworkMap } from '../components/Graph/InteractiveNetworkMap';
import { BlastRadiusSidePanel } from '../components/Graph/BlastRadiusSidePanel';
import { BlastRadiusDashboardCards } from '../components/Graph/BlastRadiusDashboardCards';
import { MoscaGraph3D } from '../components/Three/MoscaGraph3D';
import { XContextCard } from '../components/XEngine/XContextCard';
import { XContextModal } from '../components/XEngine/XContextModal';
import { YContextCard } from '../components/YEngine/YContextCard';
import { YContextModal } from '../components/YEngine/YContextModal';
import { ZContextCard } from '../components/ZEngine/ZContextCard';
import { ScrollNavControl } from '../components/Migration/ScrollNavControl';
import { ShieldAlert, RefreshCw, Box, Play, ShieldCheck, Network, Download } from 'lucide-react';

export const Risk: React.FC = () => {
  const navigate = useNavigate();
  const { currentProject, latestScan } = useProject();
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [scenarios, setScenarios] = useState<ThreatScenario[]>([]);
  const [graph, setGraph] = useState<ProjectGraph | null>(null);
  const [xContext, setXContext] = useState<ProjectXContextResponse | null>(null);
  const [yContext, setYContext] = useState<ProjectYContextResponse | null>(null);
  const [zContext, setZContext] = useState<ZProjectEvaluationResponse | null>(null);
  const [moscaContext, setMoscaContext] = useState<MoscaProjectEvaluationResponse | null>(null);

  // Stage 8 Blast Radius State
  const [summaryData, setSummaryData] = useState<TopBlastRadiusSummary | null>(null);
  const [scanGraphData, setScanGraphData] = useState<ScanGraph | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<CryptoNode | null>(null);
  const [blastRadiusResult, setBlastRadiusResult] = useState<BlastRadiusResult | null>(null);
  const [isRebuildingGraph, setIsRebuildingGraph] = useState<boolean>(false);

  const [isXModalOpen, setIsXModalOpen] = useState<boolean>(false);
  const [isYModalOpen, setIsYModalOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [reassessing, setReassessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchRiskData = async (skipCache: boolean = false) => {
    if (!currentProject) {
      setAssets([]);
      setRiskSummary(null);
      setAssessments([]);
      setGraph(null);
      setSummaryData(null);
      setScanGraphData(null);
      setXContext(null);
      setYContext(null);
      setZContext(null);
      setMoscaContext(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const scanId = latestScan?.id || currentProject.id;

    try {
      const [invRes, sumRes, scenRes, graphRes, xRes, yRes, zRes, mRes, topBrRes] = await Promise.allSettled([
        inventoryService.getProjectInventory(currentProject.id),
        riskService.getRiskSummary(currentProject.id, { skipCache }),
        riskService.listThreatScenarios(),
        graphService.getProjectGraph(currentProject.id),
        getProjectXContext(currentProject.id),
        getProjectYContext(currentProject.id),
        getProjectZContext(currentProject.id),
        getProjectMoscaContext(currentProject.id),
        graphService.getProjectTopBlastRadius(currentProject.id),
      ]);

      if (invRes.status === 'fulfilled') setAssets(invRes.value || []);
      if (sumRes.status === 'fulfilled' && sumRes.value) {
        setRiskSummary(sumRes.value);
        if (sumRes.value.priority_list) {
          setAssessments(sumRes.value.priority_list);
        }
      }
      if (scenRes.status === 'fulfilled') setScenarios(scenRes.value || []);

      if (graphRes.status === 'fulfilled' && graphRes.value) {
        const rawGraph = graphRes.value;
        setGraph(rawGraph);

        // Convert ProjectGraph to ScanGraph for InteractiveNetworkMap
        const sGraph: ScanGraph = {
          scan_id: scanId,
          nodes: (rawGraph.nodes || []).map((n: any) => ({
            id: n.id,
            scan_id: scanId,
            asset_id: n.id.startsWith('asset:') ? n.id.replace('asset:', '') : null,
            artefact_type: n.type ? n.type.toUpperCase() : 'ALGORITHM',
            name: n.label || n.id,
            location: n.metadata?.location || null,
            quantum_risk: n.metadata?.quantum_safety || (n.metadata?.algorithm_name?.includes('RSA') ? 'QUANTUM_VULNERABLE' : 'LOW'),
            mosca_x: 10,
            business_criticality: 50,
            extra_metadata: n.metadata
          })),
          edges: (rawGraph.edges || []).map((e: any, idx: number) => ({
            id: `edge-${idx}`,
            scan_id: scanId,
            source_node_id: e.source,
            target_node_id: e.target,
            relation_type: e.relationship || 'uses',
            strength: 1.0
          })),
          total_nodes: rawGraph.nodes?.length || 0,
          total_edges: rawGraph.edges?.length || 0,
          single_points_of_failure: []
        };
        setScanGraphData(sGraph);

        if (sGraph.nodes.length > 0 && !selectedNodeId) {
          const topNode = sGraph.nodes.find(n => ['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE'].includes(n.quantum_risk.toUpperCase())) || sGraph.nodes[0];
          handleSelectGraphNode(topNode.id, sGraph.nodes);
        }
      }

      if (xRes.status === 'fulfilled') setXContext(xRes.value || null);
      if (yRes.status === 'fulfilled') setYContext(yRes.value || null);
      if (zRes.status === 'fulfilled') setZContext(zRes.value || null);
      if (mRes.status === 'fulfilled') setMoscaContext(mRes.value || null);
      if (topBrRes.status === 'fulfilled') setSummaryData(topBrRes.value || null);
    } catch (err) {
      console.error('Failed to load risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGraphNode = async (nodeId: string, currentNodes = scanGraphData?.nodes || []) => {
    setSelectedNodeId(nodeId);
    const n = currentNodes.find(item => item.id === nodeId || item.asset_id === nodeId) || null;
    setSelectedGraphNode(n);

    if (nodeId) {
      try {
        const scanId = latestScan?.id || currentProject?.id;
        const br = await graphService.getNodeBlastRadius(nodeId, scanId);
        setBlastRadiusResult(br);
      } catch (err) {
        console.warn('Failed to calculate blast radius for node:', nodeId);
      }
    }
  };

  const handleRebuildGraph = async () => {
    if (!currentProject) return;
    setIsRebuildingGraph(true);
    try {
      const scanId = latestScan?.id || currentProject.id;
      await graphService.buildScanGraph(scanId);
      await fetchRiskData(true);
    } catch (err) {
      console.error('Rebuild graph failed:', err);
    } finally {
      setIsRebuildingGraph(false);
    }
  };

  const handleDownloadGraph = () => {
    const scanId = latestScan?.id || currentProject?.id || 'default';
    graphService.downloadGraphJson(scanId, scanGraphData);
  };

  const handleReassessProject = async () => {
    if (!currentProject) return;
    setReassessing(true);
    setErrorMessage(null);
    try {
      await riskService.assessProjectRisk(currentProject.id);
      await fetchRiskData(true);
    } catch (err: any) {
      console.error('Failed to reassess project risk:', err);
      setErrorMessage(err?.message || 'Failed to complete RiskEngine evaluation. Please check backend logs.');
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
  }, [currentProject, latestScan]);

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Quantum Risk & Exposure Modeling</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Quantum Risk Assessment & Blast Radius Console</h1>
          <p className="text-xs text-slate-400 mt-1">
            Project: <span className="text-cyan-300 font-mono">{currentProject?.name}</span> • Risk Engine: <span className="text-slate-200 font-mono">RiskEngine v2.0</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/recommendations')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-300 font-mono text-xs font-semibold transition-all cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>PQC Recommendations</span>
          </button>
          <button
            onClick={handleReassessProject}
            disabled={reassessing || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-mono text-xs font-semibold transition-all cursor-pointer shadow-lg shadow-cyan-500/20 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${reassessing ? 'animate-spin' : ''}`} />
            {reassessing ? 'Evaluating RiskEngine...' : 'Run Full Risk Assessment'}
          </button>
          <button
            onClick={() => fetchRiskData(true)}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh risk assessment"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-xs font-mono text-rose-200">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-slate-400 hover:text-white transition-colors text-xs cursor-pointer ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Asset Risk Assessment Table & Summary Cards */}
      <AssetRiskTable
        assets={assets}
        riskSummary={riskSummary}
        assessments={assessments}
        isLoading={loading}
      />

      {/* Single Authoritative Cryptographic Interdependencies & Blast Radius Console */}
      <div className="space-y-6 pt-6 border-t border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
              <Network className="w-4 h-4" />
              <span>Cryptographic Topology & Blast Radius</span>
            </div>
            <h3 className="text-xl font-bold font-mono text-slate-100">Cryptographic Interdependencies & Blast Radius Analysis</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Analyze downstream system impact, shared key dependencies, and single points of failure across your post-quantum migration graph.
            </p>
          </div>
          <button
            onClick={handleDownloadGraph}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-xl text-xs font-mono font-semibold transition-all shrink-0 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export dependency-graph.json</span>
          </button>
        </div>

        {/* Executive Blast Radius Dashboard Cards (Top 10 Blast Radii, Shared Keys, Single Points of Failure) */}
        <BlastRadiusDashboardCards
          summary={summaryData}
          onSelectNode={(nodeId) => handleSelectGraphNode(nodeId)}
        />

        {/* Main Interactive Network Map & Blast Radius Side Panel */}
        <div className="flex flex-col lg:flex-row gap-6 items-start">
          <div className="flex-1 w-full min-w-0">
            <InteractiveNetworkMap
              nodes={scanGraphData?.nodes || []}
              edges={scanGraphData?.edges || []}
              selectedNodeId={selectedNodeId}
              onSelectNode={(nodeId) => handleSelectGraphNode(nodeId)}
              onRebuildGraph={handleRebuildGraph}
              isLoading={loading || isRebuildingGraph}
            />
          </div>

          <BlastRadiusSidePanel
            node={selectedGraphNode}
            blastRadius={blastRadiusResult}
            onClose={() => { setSelectedNodeId(null); setSelectedGraphNode(null); setBlastRadiusResult(null); }}
            onSimulateMigration={(assetId) => navigate('/migration', { state: { selectedAssetId: assetId } })}
            isLoading={loading}
          />
        </div>
      </div>

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
        projectId={currentProject?.id}
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

      {/* Floating Scroll Top / Bottom Control */}
      <ScrollNavControl />
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { graphService } from '../services/graphService';
import { ScanGraph, BlastRadiusResult, TopBlastRadiusSummary, CryptoNode } from '../types';
import { InteractiveNetworkMap } from '../components/Graph/InteractiveNetworkMap';
import { BlastRadiusSidePanel } from '../components/Graph/BlastRadiusSidePanel';
import { BlastRadiusDashboardCards } from '../components/Graph/BlastRadiusDashboardCards';
import { Network, Download, RefreshCw, ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const BlastRadiusPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentProject } = useProject();

  const [graphData, setGraphData] = useState<ScanGraph | null>(null);
  const [summaryData, setSummaryData] = useState<TopBlastRadiusSummary | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<CryptoNode | null>(null);
  const [blastRadiusResult, setBlastRadiusResult] = useState<BlastRadiusResult | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRebuilding, setIsRebuilding] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    if (!currentProject) return;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch Top Blast Radius Summary for project
      const summary = await graphService.getProjectTopBlastRadius(currentProject.id);
      setSummaryData(summary);

      // 2. Fetch latest scan graph (or overall project graph)
      const graph = await graphService.getProjectGraph(currentProject.id);
      // Map legacy/ProjectGraph format to ScanGraph
      const scanGraph: ScanGraph = {
        scan_id: currentProject.id,
        nodes: (graph.nodes || []).map((n: any) => ({
          id: n.id,
          scan_id: currentProject.id,
          asset_id: n.id.startsWith('asset:') ? n.id.replace('asset:', '') : null,
          artefact_type: n.type ? n.type.toUpperCase() : 'ALGORITHM',
          name: n.label || n.id,
          location: n.metadata?.location || null,
          quantum_risk: n.metadata?.quantum_safety || (n.metadata?.algorithm_name?.includes('RSA') ? 'QUANTUM_VULNERABLE' : 'LOW'),
          mosca_x: 10,
          business_criticality: 50,
          extra_metadata: n.metadata
        })),
        edges: (graph.edges || []).map((e: any, idx: number) => ({
          id: `edge-${idx}`,
          scan_id: currentProject.id,
          source_node_id: e.source,
          target_node_id: e.target,
          relation_type: e.relationship || 'uses',
          strength: 1.0
        })),
        total_nodes: graph.nodes?.length || 0,
        total_edges: graph.edges?.length || 0,
        single_points_of_failure: []
      };

      setGraphData(scanGraph);

      // Select first high-risk node by default if available
      if (scanGraph.nodes.length > 0) {
        const topNode = scanGraph.nodes.find(n => ['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE'].includes(n.quantum_risk.toUpperCase())) || scanGraph.nodes[0];
        handleSelectNode(topNode.id, scanGraph.nodes);
      }
    } catch (err: any) {
      console.error('Failed to load blast radius data:', err);
      setError(err.message || 'Failed to load graph data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentProject]);

  const handleSelectNode = async (nodeId: string, currentNodes = graphData?.nodes || []) => {
    setSelectedNodeId(nodeId);
    const n = currentNodes.find(item => item.id === nodeId || item.asset_id === nodeId) || null;
    setSelectedNode(n);

    if (nodeId) {
      try {
        const br = await graphService.getNodeBlastRadius(nodeId);
        setBlastRadiusResult(br);
      } catch (err) {
        console.warn('Failed to calculate blast radius for node:', nodeId);
      }
    }
  };

  const handleRebuildGraph = async () => {
    if (!currentProject) return;
    setIsRebuilding(true);
    try {
      await loadData();
    } finally {
      setIsRebuilding(false);
    }
  };

  const handleDownloadGraph = () => {
    if (!currentProject) return;
    const url = graphService.getGraphDownloadUrl(currentProject.id);
    window.open(url, '_blank');
  };

  const handleSimulateMigration = (assetId: string) => {
    navigate('/migration', { state: { selectedAssetId: assetId } });
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mb-1">
            <span>Risk & Threat Science</span>
            <span>/</span>
            <span className="text-cyan-400 font-semibold">Blast Radius & Network Map</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 font-sans flex items-center gap-3">
            <Network className="w-8 h-8 text-cyan-400" />
            <span>Blast Radius & Cryptographic Topology</span>
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1 max-w-3xl">
            Analyze downstream system impact, shared key dependencies, and single points of failure across your post-quantum migration graph.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadGraph}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-xl text-xs font-semibold transition-all"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            <span>Export dependency-graph.json</span>
          </button>
          <button
            onClick={handleRebuildGraph}
            disabled={isRebuilding}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold rounded-xl text-xs uppercase tracking-wider transition-all shadow-md shadow-cyan-500/20"
          >
            <RefreshCw className={`w-4 h-4 ${isRebuilding ? 'animate-spin' : ''}`} />
            <span>Rebuild Graph</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-rose-300 text-xs flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 3 Executive Dashboard Cards */}
      <BlastRadiusDashboardCards
        summary={summaryData}
        onSelectNode={(nodeId) => handleSelectNode(nodeId)}
      />

      {/* Main Network Map + Side Panel Section */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* SVG Interactive Map */}
        <div className="flex-1 w-full min-w-0">
          <InteractiveNetworkMap
            nodes={graphData?.nodes || []}
            edges={graphData?.edges || []}
            selectedNodeId={selectedNodeId}
            onSelectNode={(nodeId) => handleSelectNode(nodeId)}
            onRebuildGraph={handleRebuildGraph}
            isLoading={isLoading || isRebuilding}
          />
        </div>

        {/* Selected Node Blast Radius Side Panel */}
        <BlastRadiusSidePanel
          node={selectedNode}
          blastRadius={blastRadiusResult}
          onClose={() => { setSelectedNodeId(null); setSelectedNode(null); setBlastRadiusResult(null); }}
          onSimulateMigration={handleSimulateMigration}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default BlastRadiusPage;

import React, { useState } from 'react';
import { ProjectGraph, GraphNode, AssetImpact } from '../../types';
import { graphService } from '../../services/graphService';
import { Network, AlertTriangle, ShieldCheck, Loader2, Target, Share2 } from 'lucide-react';

interface DependencyGraphProps {
  graph: ProjectGraph | null;
  loading: boolean;
  onNodeSelect?: (node: GraphNode) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ graph, loading, onNodeSelect }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [blastImpact, setBlastImpact] = useState<AssetImpact | null>(null);
  const [impactLoading, setImpactLoading] = useState<boolean>(false);

  const handleNodeClick = async (node: GraphNode) => {
    setSelectedNode(node);
    if (onNodeSelect) onNodeSelect(node);

    setImpactLoading(true);
    try {
      const imp = await graphService.getAssetImpact(node.id);
      setBlastImpact(imp);
    } catch {
      setBlastImpact(null);
    } finally {
      setImpactLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 rounded-3xl border border-slate-800 bg-[#0B0F19] flex flex-col items-center justify-center gap-3 text-xs font-mono text-slate-400 animate-pulse">
        <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
        <span>Computing cryptographic blast radius and centrality vectors...</span>
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="h-96 rounded-3xl border border-dashed border-slate-800 bg-[#0B0F19] flex items-center justify-center text-xs font-mono text-slate-500">
        No cryptographic dependency links cataloged for this repository.
      </div>
    );
  }

  // Visual layout computation
  const width = 800;
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 150;

  const nodesWithPos = graph.nodes.slice(0, 24).map((node, i, arr) => {
    const angle = (i / arr.length) * 2 * Math.PI;
    const x = centerX + radius * Math.cos(angle) + (Math.sin(i * 3.5) * 25);
    const y = centerY + radius * Math.sin(angle) + (Math.cos(i * 3.5) * 25);
    return { ...node, x, y };
  });

  const nodeMap = new Map(nodesWithPos.map((n) => [n.id, n]));
  const impactedIds = new Set(blastImpact?.impacted_asset_ids || []);

  return (
    <div className="rounded-3xl border border-slate-800 bg-[#0B0F19] p-6 sm:p-8 shadow-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Network className="w-4 h-4" />
            <span>Cryptographic Topology & Blast Radius</span>
          </div>
          <h3 className="text-xl font-bold font-mono text-slate-100">Cryptographic Interdependencies & Blast Radius</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Click any node to evaluate blast radius across interconnected protocols and data pipelines.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400 shrink-0">
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span>Vulnerable (Shor)</span>
          </span>
          <span className="flex items-center gap-1.5 text-cyan-400">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            <span>Symmetric / PQC</span>
          </span>
        </div>
      </div>

      <div className="relative rounded-2xl border border-slate-800/80 bg-[#06080F] overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-96 select-none">
          {/* Edges */}
          {graph.edges.slice(0, 48).map((edge, idx) => {
            const source = nodeMap.get(edge.source);
            const target = nodeMap.get(edge.target);
            if (!source || !target) return null;

            const isImpacted = impactedIds.has(edge.source) || impactedIds.has(edge.target);

            return (
              <line
                key={idx}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke={isImpacted ? '#F43F5E' : 'rgba(6, 182, 212, 0.22)'}
                strokeWidth={isImpacted ? '2' : '1'}
                strokeDasharray={edge.type === 'CALLS' ? '4,4' : undefined}
                className="transition-all duration-300"
              />
            );
          })}

          {/* Nodes */}
          {nodesWithPos.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const isImpacted = impactedIds.has(node.id);
            const isVulnerable = node.algorithm === 'RSA' || node.algorithm === 'ECDSA' || node.algorithm === 'DSA';
            const size = Math.max(8, Math.min(20, (node.centrality || 0.1) * 40));

            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform duration-200 hover:scale-110"
                onClick={() => handleNodeClick(node)}
              >
                {/* Selected Halo Ring */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={size + 5}
                  fill="none"
                  stroke={isSelected ? '#06B6D4' : isImpacted ? '#F43F5E' : 'transparent'}
                  strokeWidth="2.5"
                  strokeDasharray={isSelected ? '3,3' : undefined}
                  className={isSelected ? 'animate-spin' : ''}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={size}
                  fill={isVulnerable ? '#F43F5E' : '#06B6D4'}
                  opacity={0.88}
                />
                <text
                  x={node.x}
                  y={node.y - size - 5}
                  fill="#94A3B8"
                  fontSize="9.5"
                  fontFamily="JetBrains Mono"
                  textAnchor="middle"
                  className="pointer-events-none font-semibold"
                >
                  {node.name || node.algorithm || node.id.slice(0, 6)}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node & Blast Radius Details Panel */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 right-4 sm:right-auto sm:max-w-sm p-4 rounded-2xl border border-cyan-800/80 bg-slate-900/95 backdrop-blur-xl text-xs font-mono space-y-2 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between text-cyan-300 font-bold border-b border-slate-800 pb-1.5">
              <div className="flex items-center gap-1.5">
                <Target className="w-4 h-4 text-cyan-400" />
                <span>{selectedNode.algorithm || selectedNode.name}</span>
              </div>
              <span className="text-[10px] text-slate-400">
                Centrality: {((selectedNode.centrality || 0) * 100).toFixed(1)}%
              </span>
            </div>

            <div className="text-[11px] text-slate-400 truncate">
              Primitive ID: <code className="text-slate-200">{selectedNode.id}</code>
            </div>

            {impactLoading ? (
              <div className="text-[11px] text-cyan-300 flex items-center gap-1.5 py-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating component blast radius...</span>
              </div>
            ) : blastImpact ? (
              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-[11px]">Affected Components:</span>
                  <span className="text-rose-400 font-bold font-mono">
                    {blastImpact.affected_components_count} Modules
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-sans leading-tight">
                  Refactoring this primitive directly impacts dependencies highlighted in red.
                </p>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

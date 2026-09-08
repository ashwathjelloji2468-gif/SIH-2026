import React, { useState } from 'react';
import { ProjectGraph, GraphNode, AssetImpact } from '../../types';
import { graphService } from '../../services/graphService';
import { Network, Loader2, Target } from 'lucide-react';

interface DependencyGraphProps {
  graph: ProjectGraph | null;
  loading: boolean;
  onNodeSelect?: (node: GraphNode | null) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ graph, loading, onNodeSelect }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [blastImpact, setBlastImpact] = useState<AssetImpact | null>(null);
  const [impactLoading, setImpactLoading] = useState<boolean>(false);

  const handleNodeClick = async (node: GraphNode) => {
    // Toggle selection if clicking already selected node
    if (selectedNode?.id === node.id) {
      setSelectedNode(null);
      setBlastImpact(null);
      if (onNodeSelect) onNodeSelect(null);
      return;
    }

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

  const selectedId = selectedNode?.id;

  // Compute 1-hop direct downstream dependents (PRIMARY -> DIRECT)
  const directIds = new Set<string>();
  if (selectedId) {
    graph.edges.forEach((edge) => {
      if (edge.source === selectedId && edge.target !== selectedId) {
        directIds.add(edge.target);
      }
    });
    // Fallback if graph edge direction in dataset is target -> source
    if (directIds.size === 0) {
      graph.edges.forEach((edge) => {
        if (edge.target === selectedId && edge.source !== selectedId) {
          directIds.add(edge.source);
        }
      });
    }
  }

  // Compute downstream/reachable indirect dependents beyond 1-hop (DIRECT -> INDIRECT)
  const indirectIds = new Set<string>();
  if (selectedId && directIds.size > 0) {
    const visited = new Set<string>([selectedId, ...Array.from(directIds)]);
    const queue = Array.from(directIds);

    while (queue.length > 0) {
      const curr = queue.shift()!;
      graph.edges.forEach((edge) => {
        if (edge.source === curr && !visited.has(edge.target)) {
          visited.add(edge.target);
          indirectIds.add(edge.target);
          queue.push(edge.target);
        }
      });
    }
  }

  // Order node rendering: Unaffected -> Indirect -> Direct -> Primary (Primary renders on top)
  const sortedNodes = [...nodesWithPos].sort((a, b) => {
    const getOrder = (nId: string) => {
      if (nId === selectedId) return 4;
      if (directIds.has(nId)) return 3;
      if (indirectIds.has(nId)) return 2;
      return 1;
    };
    return getOrder(a.id) - getOrder(b.id);
  });

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

          {/* Graph Context Status Line when a node is selected */}
          {selectedNode && (
            <div className="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-slate-800/60 font-mono text-xs text-cyan-300">
              <span className="flex items-center gap-1.5 bg-cyan-950/60 border border-cyan-800/60 px-3 py-1 rounded-full font-bold">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Primary Asset: <span className="text-white ml-1">{selectedNode.name || selectedNode.algorithm || selectedNode.id}</span>
                {selectedNode.location && <span className="text-slate-400 ml-1">· {selectedNode.location}</span>}
              </span>
              <span className="bg-slate-900 border border-slate-800 text-slate-300 px-3 py-1 rounded-full font-semibold">
                {directIds.size} Direct · {indirectIds.size} Indirect Impact
              </span>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-1.5 text-xs font-mono text-slate-400 shrink-0">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span>Vulnerable (Shor)</span>
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span>Symmetric / PQC</span>
            </span>
          </div>
          {selectedId && (
            <div className="flex items-center gap-2.5 pt-1 border-t border-slate-800/80 text-[10px] text-slate-400">
              <span className="flex items-center gap-1 text-cyan-300 font-bold">
                <span className="w-2 h-2 rounded-full border border-cyan-400 bg-cyan-500/20" />
                <span>Primary</span>
              </span>
              <span className="flex items-center gap-1 text-cyan-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span>Direct</span>
              </span>
              <span className="flex items-center gap-1 text-slate-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400/50" />
                <span>Indirect</span>
              </span>
              <span className="flex items-center gap-1 text-slate-600">
                <span className="w-2 h-2 rounded-full bg-slate-700" />
                <span>Unaffected</span>
              </span>
            </div>
          )}
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
            const isPrimaryEdge = selectedId ? ((edge.source === selectedId && directIds.has(edge.target)) || (edge.target === selectedId && directIds.has(edge.source))) : false;
            const isDirectToIndirectEdge = selectedId ? ((directIds.has(edge.source) && indirectIds.has(edge.target)) || (directIds.has(edge.target) && indirectIds.has(edge.source))) : false;

            let strokeColor = isImpacted ? '#F43F5E' : 'rgba(6, 182, 212, 0.22)';
            let strokeWidth = isImpacted ? '2' : '1';
            let strokeOpacity = 1.0;

            if (selectedId) {
              if (isPrimaryEdge) {
                strokeColor = isImpacted ? '#F43F5E' : '#06B6D4';
                strokeWidth = '3';
                strokeOpacity = 1.0;
              } else if (isDirectToIndirectEdge) {
                strokeColor = isImpacted ? '#F43F5E' : 'rgba(6, 182, 212, 0.7)';
                strokeWidth = '1.75';
                strokeOpacity = 0.75;
              } else {
                strokeColor = 'rgba(148, 163, 184, 0.15)';
                strokeWidth = '1';
                strokeOpacity = 0.2;
              }
            }

            return (
              <line
                key={idx}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                opacity={strokeOpacity}
                strokeDasharray={edge.type === 'CALLS' ? '4,4' : undefined}
                className="transition-all duration-300"
              />
            );
          })}

          {/* Nodes */}
          {sortedNodes.map((node) => {
            const isSelected = selectedId === node.id;
            const isDirect = selectedId ? directIds.has(node.id) : false;
            const isIndirect = selectedId ? indirectIds.has(node.id) : false;
            const isUnaffected = selectedId ? (!isSelected && !isDirect && !isIndirect) : false;
            const isImpacted = impactedIds.has(node.id);
            const isVulnerable = node.algorithm === 'RSA' || node.algorithm === 'ECDSA' || node.algorithm === 'DSA';

            const baseSize = Math.max(8, Math.min(20, (node.centrality || 0.1) * 40));
            const nodeSize = isSelected
              ? baseSize * 1.6
              : isDirect
              ? baseSize * 1.25
              : baseSize;

            const nodeOpacity = isSelected || isDirect
              ? 1.0
              : isIndirect
              ? 0.75
              : isUnaffected
              ? 0.25
              : 0.88;

            const baseColor = isVulnerable ? '#F43F5E' : '#06B6D4';

            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform duration-200 hover:scale-110"
                onClick={() => handleNodeClick(node)}
              >
                {/* Outer Glow & Halo Rings */}
                {isSelected && (
                  <>
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={nodeSize + 10}
                      fill="rgba(6, 182, 212, 0.15)"
                      stroke="#06B6D4"
                      strokeWidth="2"
                      strokeDasharray="4,4"
                      className="animate-spin"
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={nodeSize + 4}
                      fill="none"
                      stroke="#06B6D4"
                      strokeWidth="2"
                    />
                  </>
                )}

                {isDirect && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={nodeSize + 4}
                    fill="none"
                    stroke="#06B6D4"
                    strokeWidth="1.5"
                    opacity="0.9"
                  />
                )}

                {isIndirect && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={nodeSize + 3}
                    fill="none"
                    stroke="#06B6D4"
                    strokeWidth="1"
                    strokeDasharray="2,2"
                    opacity="0.5"
                  />
                )}

                {!isSelected && !isDirect && !isIndirect && isImpacted && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={nodeSize + 4}
                    fill="none"
                    stroke="#F43F5E"
                    strokeWidth="2"
                  />
                )}

                {/* Primary Node Badge Label */}
                {isSelected && (
                  <g transform={`translate(${node.x}, ${node.y - nodeSize - 18})`}>
                    <rect
                      x="-25"
                      y="-9"
                      width="50"
                      height="15"
                      rx="7.5"
                      fill="#06B6D4"
                      stroke="#FFFFFF"
                      strokeWidth="1"
                    />
                    <text
                      x="0"
                      y="2.5"
                      fill="#06080F"
                      fontSize="8.5"
                      fontWeight="900"
                      fontFamily="JetBrains Mono"
                      textAnchor="middle"
                    >
                      PRIMARY
                    </text>
                  </g>
                )}

                {/* Main Node Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={nodeSize}
                  fill={baseColor}
                  stroke={isSelected ? '#FFFFFF' : isDirect ? '#06B6D4' : 'none'}
                  strokeWidth={isSelected ? '2.5' : isDirect ? '1.5' : '0'}
                  opacity={nodeOpacity}
                />

                {/* Node Label Text */}
                <text
                  x={node.x}
                  y={node.y - nodeSize - (isSelected ? 25 : 5)}
                  fill={isSelected ? '#22D3EE' : isDirect ? '#E2E8F0' : isUnaffected ? '#475569' : '#94A3B8'}
                  fontSize={isSelected ? '11' : isDirect ? '10' : '9.5'}
                  fontFamily="JetBrains Mono"
                  textAnchor="middle"
                  fontWeight={isSelected ? '800' : isDirect ? '700' : '600'}
                  opacity={nodeOpacity}
                  className="pointer-events-none"
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


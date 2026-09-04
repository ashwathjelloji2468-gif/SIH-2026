import React, { useState, useEffect } from 'react';
import { ProjectGraph, GraphNode } from '../../types';
import { Network, ZoomIn, ZoomOut, RefreshCw, Info } from 'lucide-react';

interface DependencyGraphProps {
  graph: ProjectGraph | null;
  loading: boolean;
  onNodeSelect?: (node: GraphNode) => void;
}

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ graph, loading, onNodeSelect }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  if (loading) {
    return (
      <div className="h-96 rounded-2xl border border-slate-800 bg-[#0B0F19] flex items-center justify-center text-xs text-slate-500 animate-pulse">
        Computing graph centrality and dependency vectors...
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="h-96 rounded-2xl border border-dashed border-slate-800 bg-[#0B0F19] flex items-center justify-center text-xs text-slate-500">
        No cryptographic dependency links detected for this repository.
      </div>
    );
  }

  // Calculate layout coordinates in a circular or force-arranged canvas space
  const width = 700;
  const height = 380;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 140;

  const nodesWithPos = graph.nodes.slice(0, 20).map((node, i, arr) => {
    const angle = (i / arr.length) * 2 * Math.PI;
    const x = centerX + radius * Math.cos(angle) + (Math.sin(i * 3) * 20);
    const y = centerY + radius * Math.sin(angle) + (Math.cos(i * 3) * 20);
    return { ...node, x, y };
  });

  const nodeMap = new Map(nodesWithPos.map((n) => [n.id, n]));

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-0.5">
            <Network className="w-4 h-4" />
            <span>Cryptographic Topology & Centrality</span>
          </div>
          <h3 className="text-sm font-bold text-slate-100">Blast Radius & Primitive Interdependencies</h3>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <span>{graph.nodes.length} Nodes</span>
          <span>•</span>
          <span>{graph.edges.length} Edges</span>
        </div>
      </div>

      <div className="relative rounded-xl border border-slate-800/80 bg-[#070A12] overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-80 select-none">
          {/* Edges */}
          {graph.edges.slice(0, 40).map((edge, idx) => {
            const source = nodeMap.get(edge.source);
            const target = nodeMap.get(edge.target);
            if (!source || !target) return null;

            return (
              <line
                key={idx}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="rgba(6, 182, 212, 0.25)"
                strokeWidth="1.2"
                strokeDasharray={edge.type === 'CALLS' ? '4,4' : undefined}
              />
            );
          })}

          {/* Nodes */}
          {nodesWithPos.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const size = Math.max(7, Math.min(18, (node.centrality || 0.1) * 35));

            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform"
                onClick={() => {
                  setSelectedNode(node);
                  if (onNodeSelect) onNodeSelect(node);
                }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={size + 3}
                  fill="none"
                  stroke={isSelected ? '#06B6D4' : 'transparent'}
                  strokeWidth="2"
                  className={isSelected ? 'animate-pulse' : ''}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={size}
                  fill={node.algorithm === 'RSA' || node.algorithm === 'ECDSA' ? '#F43F5E' : '#06B6D4'}
                  opacity={0.85}
                />
                <text
                  x={node.x}
                  y={node.y - size - 4}
                  fill="#94A3B8"
                  fontSize="9"
                  fontFamily="JetBrains Mono"
                  textAnchor="middle"
                  className="pointer-events-none"
                >
                  {node.name || node.algorithm || node.id.slice(0, 6)}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Inspector Overlay */}
        {selectedNode && (
          <div className="absolute bottom-3 left-3 right-3 sm:right-auto sm:max-w-xs p-3 rounded-xl border border-cyan-800/80 bg-slate-900/90 backdrop-blur-md text-xs font-mono space-y-1 shadow-2xl">
            <div className="flex items-center justify-between text-cyan-300 font-bold">
              <span>{selectedNode.algorithm || selectedNode.name}</span>
              <span className="text-[10px] text-slate-400">
                Centrality: {((selectedNode.centrality || 0) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="text-[11px] text-slate-400 truncate">ID: {selectedNode.id}</div>
          </div>
        )}
      </div>
    </div>
  );
};

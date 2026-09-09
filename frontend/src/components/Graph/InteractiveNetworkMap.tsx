import React, { useState, useMemo, useRef } from 'react';
import { CryptoNode, CryptoEdge } from '../../types';
import { Search, ZoomIn, ZoomOut, RefreshCw, ShieldAlert, Layers, Zap } from 'lucide-react';

interface InteractiveNetworkMapProps {
  nodes: CryptoNode[];
  edges: CryptoEdge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  onRebuildGraph?: () => void;
  isLoading?: boolean;
}

export const InteractiveNetworkMap: React.FC<InteractiveNetworkMapProps> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  onRebuildGraph,
  isLoading = false
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    return nodes.filter(n => {
      const matchesSearch = n.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            (n.location && n.location.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesRisk = filterRisk === 'ALL' ||
                          (filterRisk === 'HIGH' && ['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE', 'VULNERABLE'].includes(n.quantum_risk.toUpperCase())) ||
                          (filterRisk === 'SAFE' && ['LOW', 'SAFE', 'QUANTUM_SAFE'].includes(n.quantum_risk.toUpperCase()));
      return matchesSearch && matchesRisk;
    });
  }, [nodes, searchTerm, filterRisk]);

  // Compute 2D node coordinates deterministically around center
  const nodePositions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    const total = nodes.length;
    if (total === 0) return map;

    const width = 800;
    const height = 550;
    const centerX = width / 2;
    const centerY = height / 2;

    // Group nodes by type / component for circular layout
    const radius = Math.min(width, height) * 0.35;

    nodes.forEach((node, index) => {
      const angle = (index / total) * 2 * Math.PI;
      // Add subtle offset based on artefact_type
      let rOffset = 0;
      if (node.artefact_type === 'COMPONENT') rOffset = -60;
      if (node.artefact_type === 'FILE') rOffset = -20;
      if (node.artefact_type === 'ALGORITHM' || node.artefact_type === 'KEY') rOffset = 40;

      const currentRadius = radius + rOffset;
      const x = centerX + currentRadius * Math.cos(angle);
      const y = centerY + currentRadius * Math.sin(angle);
      map.set(node.id, { x, y });
    });

    return map;
  }, [nodes]);

  // Color lookup helper
  const getNodeColor = (node: CryptoNode) => {
    const risk = (node.quantum_risk || '').toUpperCase();
    if (['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE', 'VULNERABLE'].includes(risk)) {
      return { bg: '#F43F5E', border: '#E11D48', glow: 'rgba(244, 63, 94, 0.4)', text: '#FFE4E6' };
    }
    if (['MODERATE', 'MEDIUM', 'TRANSITIONAL'].includes(risk)) {
      return { bg: '#F59E0B', border: '#D97706', glow: 'rgba(245, 158, 11, 0.4)', text: '#FEF3C7' };
    }
    if (node.artefact_type === 'COMPONENT' || node.artefact_type === 'FILE') {
      return { bg: '#0284C7', border: '#0369A1', glow: 'rgba(2, 132, 199, 0.3)', text: '#E0F2FE' };
    }
    return { bg: '#10B981', border: '#059669', glow: 'rgba(16, 185, 129, 0.3)', text: '#D1FAE5' };
  };

  // Drag pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="relative w-full rounded-2xl border border-slate-800 bg-[#06080F]/90 backdrop-blur-xl p-4 overflow-hidden shadow-2xl">
      {/* Top Map Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 z-10 relative bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search crypto nodes, algorithms, files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        {/* Risk Filter */}
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Nodes ({nodes.length})</option>
            <option value="HIGH">Quantum Vulnerable Only</option>
            <option value="SAFE">Quantum Safe Only</option>
          </select>
        </div>

        {/* Zoom & Rebuild Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom(prev => Math.min(prev + 0.2, 2.5))}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(prev => Math.max(prev - 0.2, 0.5))}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 rounded-lg border border-slate-700"
          >
            Reset
          </button>
          {onRebuildGraph && (
            <button
              onClick={onRebuildGraph}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded-lg text-xs font-semibold"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Rebuild Graph</span>
            </button>
          )}
        </div>
      </div>

      {/* SVG Interactive Canvas */}
      <div
        className="w-full h-[520px] bg-grid-cyber relative cursor-grab active:cursor-grabbing overflow-hidden rounded-xl border border-slate-900"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg className="w-full h-full">
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
            </marker>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* Render Edges */}
            {edges.map((edge) => {
              const srcPos = nodePositions.get(edge.source_node_id);
              const tgtPos = nodePositions.get(edge.target_node_id);
              if (!srcPos || !tgtPos) return null;

              const isSelected = selectedNodeId === edge.source_node_id || selectedNodeId === edge.target_node_id;
              const isSharesKey = edge.relation_type === 'shares_key';

              return (
                <g key={edge.id}>
                  <line
                    x1={srcPos.x}
                    y1={srcPos.y}
                    x2={tgtPos.x}
                    y2={tgtPos.y}
                    stroke={isSharesKey ? '#F43F5E' : isSelected ? '#22D3EE' : '#334155'}
                    strokeWidth={isSharesKey ? 2 : isSelected ? 2.5 : 1.2}
                    strokeDasharray={isSharesKey ? '4 3' : 'none'}
                    markerEnd="url(#arrow)"
                    opacity={isSelected ? 1 : 0.6}
                  />
                  {isSelected && (
                    <text
                      x={(srcPos.x + tgtPos.x) / 2}
                      y={(srcPos.y + tgtPos.y) / 2 - 4}
                      fill="#94A3B8"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {edge.relation_type}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Render Nodes */}
            {filteredNodes.map((node) => {
              const pos = nodePositions.get(node.id);
              if (!pos) return null;

              const color = getNodeColor(node);
              const isSelected = node.id === selectedNodeId;
              const size = isSelected ? 26 : node.artefact_type === 'COMPONENT' ? 22 : 18;

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectNode(node.id);
                  }}
                  className="cursor-pointer group"
                >
                  {/* Outer Glow Circle */}
                  <circle
                    r={size + 6}
                    fill={color.glow}
                    opacity={isSelected ? 0.9 : 0.4}
                    filter="url(#glow)"
                  />
                  {/* Node Circle */}
                  <circle
                    r={size}
                    fill={color.bg}
                    stroke={isSelected ? '#FFFFFF' : color.border}
                    strokeWidth={isSelected ? 3 : 2}
                    className="transition-all duration-200 group-hover:scale-110"
                  />
                  {/* Node Label */}
                  <text
                    y={size + 14}
                    fill={isSelected ? '#FFFFFF' : '#CBD5E1'}
                    fontSize={isSelected ? '11' : '10'}
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    fontFamily="sans-serif"
                    textAnchor="middle"
                    pointerEvents="none"
                  >
                    {node.name.length > 20 ? `${node.name.slice(0, 18)}...` : node.name}
                  </text>
                  <text
                    y={size + 25}
                    fill="#64748B"
                    fontSize="8"
                    fontFamily="monospace"
                    textAnchor="middle"
                    pointerEvents="none"
                  >
                    {node.artefact_type}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>

        {/* Bottom Legend Overlay */}
        <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-xl p-2.5 text-[11px] font-mono text-slate-400 flex flex-wrap gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 shadow-xs shadow-rose-500/50" />
            <span>Shor-Vulnerable</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500" />
            <span>Transitional</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50" />
            <span>PQC Ready</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-600" />
            <span>File / System</span>
          </div>
        </div>
      </div>
    </div>
  );
};

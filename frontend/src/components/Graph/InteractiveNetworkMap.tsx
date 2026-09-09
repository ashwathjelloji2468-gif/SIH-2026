import React, { useState, useMemo, useRef, useEffect } from 'react';
import { CryptoNode, CryptoEdge } from '../../types';
import { Search, ZoomIn, ZoomOut, RefreshCw, Layers, ShieldAlert, KeyRound, CheckCircle } from 'lucide-react';

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
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Filtered nodes based on search & risk filter
  const filteredNodes = useMemo(() => {
    return nodes.filter(n => {
      const matchesSearch = !searchTerm ||
                            n.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            (n.location && n.location.toLowerCase().includes(searchTerm.toLowerCase())) ||
                            n.artefact_type.toLowerCase().includes(searchTerm.toLowerCase());

      const riskUpper = (n.quantum_risk || '').toUpperCase();
      const matchesRisk = filterRisk === 'ALL' ||
                          (filterRisk === 'HIGH' && ['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE', 'VULNERABLE'].includes(riskUpper)) ||
                          (filterRisk === 'SAFE' && ['LOW', 'SAFE', 'QUANTUM_SAFE'].includes(riskUpper));

      return matchesSearch && matchesRisk;
    });
  }, [nodes, searchTerm, filterRisk]);

  // Compute node fan-in & degree counts
  const nodeDegrees = useMemo(() => {
    const degrees = new Map<string, { total: number; in: number; out: number }>();
    nodes.forEach(n => degrees.set(n.id, { total: 0, in: 0, out: 0 }));
    edges.forEach(e => {
      const src = degrees.get(e.source_node_id);
      if (src) { src.out++; src.total++; }
      const tgt = degrees.get(e.target_node_id);
      if (tgt) { tgt.in++; tgt.total++; }
    });
    return degrees;
  }, [nodes, edges]);

  // Compute 2D node coordinates using Force-Directed + Hierarchical Directory Cluster Simulation
  const { nodePositions, initialPan, initialZoom } = useMemo(() => {
    const map = new Map<string, { x: number; y: number; radius: number }>();
    if (nodes.length === 0) return { nodePositions: map, initialPan: { x: 0, y: 0 }, initialZoom: 1 };

    // 1. Group nodes into directory / component clusters
    const clusters = new Map<string, CryptoNode[]>();
    nodes.forEach(node => {
      let comp = 'Core';
      if (node.location) {
        const parts = node.location.replace(/\\/g, '/').split('/').filter(p => p && p !== '.' && p !== '..');
        if (parts.length > 1) comp = parts[parts.length - 2];
      }
      if (node.artefact_type === 'COMPONENT') comp = node.name;

      if (!clusters.has(comp)) clusters.set(comp, []);
      clusters.get(comp)!.push(node);
    });

    const clusterKeys = Array.from(clusters.keys());
    const numClusters = clusterKeys.length;

    // 2. Assign cluster centers in spaced grid layout
    const clusterCenters = new Map<string, { x: number; y: number }>();
    const gridCols = Math.ceil(Math.sqrt(numClusters));
    const clusterSpacing = Math.max(320, Math.min(650, 200 + Math.sqrt(nodes.length) * 18));

    clusterKeys.forEach((cKey, idx) => {
      const row = Math.floor(idx / gridCols);
      const col = idx % gridCols;
      clusterCenters.set(cKey, {
        x: (col - (gridCols - 1) / 2) * clusterSpacing,
        y: (row - (gridCols - 1) / 2) * clusterSpacing
      });
    });

    // 3. Initialize node positions near cluster center with layer offset
    const posMap = new Map<string, { x: number; y: number; vx: number; vy: number; radius: number }>();
    nodes.forEach((node, idx) => {
      let comp = 'Core';
      if (node.location) {
        const parts = node.location.replace(/\\/g, '/').split('/').filter(p => p && p !== '.' && p !== '..');
        if (parts.length > 1) comp = parts[parts.length - 2];
      }
      if (node.artefact_type === 'COMPONENT') comp = node.name;

      const center = clusterCenters.get(comp) || { x: 0, y: 0 };
      const deg = nodeDegrees.get(node.id)?.total || 1;
      const isShared = deg > 1;
      const radius = isShared ? 22 : node.artefact_type === 'COMPONENT' ? 24 : node.artefact_type === 'FILE' ? 18 : 14;

      const compNodes = clusters.get(comp) || [];
      const angle = (idx / Math.max(1, compNodes.length)) * 2 * Math.PI;
      let layerRadius = 50;
      if (node.artefact_type === 'COMPONENT') layerRadius = 0;
      else if (node.artefact_type === 'FILE') layerRadius = 65 + (idx % 3) * 25;
      else layerRadius = 125 + (idx % 5) * 30;

      posMap.set(node.id, {
        x: center.x + layerRadius * Math.cos(angle) + (Math.random() - 0.5) * 8,
        y: center.y + layerRadius * Math.sin(angle) + (Math.random() - 0.5) * 8,
        vx: 0,
        vy: 0,
        radius
      });
    });

    // 4. Force Simulation Iterations (Repulsion + Edge Attraction + Hard Collision Solver)
    const iterations = 85;
    const kRepulsion = 30000;
    const kAttraction = 0.07;
    const minPadding = 38; // Guaranteed space between node centers

    const nodeArray = Array.from(posMap.entries());

    for (let iter = 0; iter < iterations; iter++) {
      const tempFactor = Math.max(0.1, 1 - iter / iterations);

      // Coulomb Repulsion & Hard Collision Solver
      for (let i = 0; i < nodeArray.length; i++) {
        const [_, nodeA] = nodeArray[i];
        for (let j = i + 1; j < nodeArray.length; j++) {
          const [__, nodeB] = nodeArray[j];
          let dx = nodeB.x - nodeA.x;
          let dy = nodeB.y - nodeA.y;
          let distSq = dx * dx + dy * dy;
          if (distSq === 0) {
            dx = (Math.random() - 0.5) * 2;
            dy = (Math.random() - 0.5) * 2;
            distSq = dx * dx + dy * dy;
          }
          const dist = Math.sqrt(distSq);
          const minDist = nodeA.radius + nodeB.radius + minPadding;

          let force = (kRepulsion / distSq) * tempFactor;

          // Hard collision repulsion when nodes get too close
          if (dist < minDist) {
            force += (minDist - dist) * 1.8;
          }

          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          nodeA.vx -= fx;
          nodeA.vy -= fy;
          nodeB.vx += fx;
          nodeB.vy += fy;
        }
      }

      // Edge Hooke Attraction
      edges.forEach(edge => {
        const nodeA = posMap.get(edge.source_node_id);
        const nodeB = posMap.get(edge.target_node_id);
        if (nodeA && nodeB) {
          const dx = nodeB.x - nodeA.x;
          const dy = nodeB.y - nodeA.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 110) * kAttraction * tempFactor;

          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          nodeA.vx += fx;
          nodeA.vy += fy;
          nodeB.vx -= fx;
          nodeB.vy -= fy;
        }
      });

      // Apply velocity step with dampening
      nodeArray.forEach(([_, n]) => {
        n.x += Math.max(-25, Math.min(25, n.vx * 0.35));
        n.y += Math.max(-25, Math.min(25, n.vy * 0.35));
        n.vx *= 0.5;
        n.vy *= 0.5;
      });
    }

    // 5. Fit Zoom & Pan to Bounding Box
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    posMap.forEach(n => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });

    const graphWidth = Math.max(400, maxX - minX + 140);
    const graphHeight = Math.max(400, maxY - minY + 140);
    const viewportW = 850;
    const viewportH = 520;

    const scaleX = viewportW / graphWidth;
    const scaleY = viewportH / graphHeight;
    const fitZoom = Math.max(0.2, Math.min(1.1, Math.min(scaleX, scaleY)));

    const graphCenterX = (minX + maxX) / 2;
    const graphCenterY = (minY + maxY) / 2;

    const fitPan = {
      x: viewportW / 2 - graphCenterX * fitZoom,
      y: viewportH / 2 - graphCenterY * fitZoom
    };

    posMap.forEach((n, id) => map.set(id, { x: n.x, y: n.y, radius: n.radius }));

    return { nodePositions: map, initialPan: fitPan, initialZoom: fitZoom };
  }, [nodes, edges, nodeDegrees]);

  // Set initial zoom/pan when layout finishes
  useEffect(() => {
    setZoom(initialZoom);
    setPan(initialPan);
  }, [initialZoom, initialPan]);

  // Calculate active connected nodes for hover / focus highlighting
  const activeNodeId = hoveredNodeId || selectedNodeId;
  const connectedNodeIds = useMemo(() => {
    if (!activeNodeId) return new Set<string>();
    const set = new Set<string>([activeNodeId]);
    edges.forEach(e => {
      if (e.source_node_id === activeNodeId) set.add(e.target_node_id);
      if (e.target_node_id === activeNodeId) set.add(e.source_node_id);
    });
    return set;
  }, [activeNodeId, edges]);

  // Node color helper matching SENTRIQ theme
  const getNodeColor = (node: CryptoNode) => {
    const risk = (node.quantum_risk || '').toUpperCase();
    if (['CRITICAL', 'HIGH', 'QUANTUM_VULNERABLE', 'VULNERABLE'].includes(risk)) {
      return { bg: '#F43F5E', border: '#E11D48', glow: 'rgba(244, 63, 94, 0.45)', text: '#FFE4E6' };
    }
    if (['MODERATE', 'MEDIUM', 'TRANSITIONAL'].includes(risk)) {
      return { bg: '#F59E0B', border: '#D97706', glow: 'rgba(245, 158, 11, 0.45)', text: '#FEF3C7' };
    }
    if (node.artefact_type === 'COMPONENT' || node.artefact_type === 'FILE') {
      return { bg: '#0284C7', border: '#0369A1', glow: 'rgba(2, 132, 199, 0.35)', text: '#E0F2FE' };
    }
    return { bg: '#10B981', border: '#059669', glow: 'rgba(16, 185, 129, 0.35)', text: '#D1FAE5' };
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

  // Truncate node label for display
  const getShortLabel = (node: CryptoNode) => {
    let text = node.name;
    if (node.location) {
      const parts = node.location.replace(/\\/g, '/').split('/');
      text = parts[parts.length - 1];
    }
    return text.length > 16 ? `${text.slice(0, 14)}..` : text;
  };

  return (
    <div className="relative w-full rounded-2xl border border-slate-800 bg-[#06080F]/90 backdrop-blur-xl p-4 overflow-hidden shadow-2xl">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 z-10 relative bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search crypto nodes, algorithms, files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-sans"
          />
        </div>

        {/* Risk Filter */}
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="ALL">All Nodes ({nodes.length})</option>
            <option value="HIGH">Quantum Vulnerable Only</option>
            <option value="SAFE">Quantum Safe Only</option>
          </select>
        </div>

        {/* Zoom & Rebuild Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom(prev => Math.min(prev + 0.15, 2.5))}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(prev => Math.max(prev - 0.15, 0.15))}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => { setZoom(initialZoom); setPan(initialPan); }}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 rounded-lg border border-slate-700 transition-colors"
          >
            Fit Content
          </button>
          {onRebuildGraph && (
            <button
              onClick={onRebuildGraph}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded-lg text-xs font-semibold font-mono transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Rebuild Graph</span>
            </button>
          )}
        </div>
      </div>

      {/* SVG Interactive Canvas */}
      <div
        className="w-full h-[540px] bg-grid-cyber relative cursor-grab active:cursor-grabbing overflow-hidden rounded-xl border border-slate-900"
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
            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* Render Edges */}
            {edges.map((edge) => {
              const srcPos = nodePositions.get(edge.source_node_id);
              const tgtPos = nodePositions.get(edge.target_node_id);
              if (!srcPos || !tgtPos) return null;

              const isEdgeActive = activeNodeId && (edge.source_node_id === activeNodeId || edge.target_node_id === activeNodeId);
              const isSharesKey = edge.relation_type === 'shares_key';

              // Dim non-connected edges when a node is hovered / focused
              const opacity = activeNodeId ? (isEdgeActive ? 0.95 : 0.08) : 0.25;

              return (
                <g key={edge.id}>
                  <line
                    x1={srcPos.x}
                    y1={srcPos.y}
                    x2={tgtPos.x}
                    y2={tgtPos.y}
                    stroke={isSharesKey ? '#F43F5E' : isEdgeActive ? '#22D3EE' : '#334155'}
                    strokeWidth={isSharesKey ? 2.2 : isEdgeActive ? 2.5 : 1.2}
                    strokeDasharray={isSharesKey ? '5 3' : 'none'}
                    markerEnd="url(#arrow)"
                    opacity={opacity}
                  />
                  {isEdgeActive && (
                    <text
                      x={(srcPos.x + tgtPos.x) / 2}
                      y={(srcPos.y + tgtPos.y) / 2 - 4}
                      fill="#94A3B8"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                      className="select-none"
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
              const isHovered = node.id === hoveredNodeId;
              const isConnected = connectedNodeIds.has(node.id);
              const isDimmed = activeNodeId && !isConnected;

              const degInfo = nodeDegrees.get(node.id);
              const totalDeg = degInfo?.total || 1;
              const isShared = totalDeg > 1;

              const baseRadius = pos.radius;
              const radius = isSelected || isHovered ? baseRadius + 4 : baseRadius;

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectNode(node.id);
                  }}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  opacity={isDimmed ? 0.2 : 1.0}
                  className="cursor-pointer transition-opacity duration-200"
                >
                  {/* Outer Glow Circle */}
                  {(isSelected || isHovered || isShared) && (
                    <circle
                      r={radius + 8}
                      fill={color.glow}
                      opacity={isSelected || isHovered ? 0.9 : 0.5}
                      filter="url(#glow)"
                    />
                  )}

                  {/* Dual Ring Border for Shared Assets */}
                  {isShared && (
                    <circle
                      r={radius + 4}
                      fill="none"
                      stroke="#22D3EE"
                      strokeWidth="1.5"
                      strokeDasharray="3 2"
                      opacity="0.8"
                    />
                  )}

                  {/* Main Node Body */}
                  <circle
                    r={radius}
                    fill={color.bg}
                    stroke={isSelected ? '#FFFFFF' : isHovered ? '#22D3EE' : color.border}
                    strokeWidth={isSelected ? 3 : isHovered ? 2.5 : 1.8}
                  />

                  {/* Short Node Name */}
                  <text
                    y={radius + 14}
                    fill={isSelected || isHovered ? '#FFFFFF' : '#CBD5E1'}
                    fontSize={isSelected || isHovered ? '11' : '10'}
                    fontWeight={isSelected || isHovered ? 'bold' : 'normal'}
                    fontFamily="sans-serif"
                    textAnchor="middle"
                    pointerEvents="none"
                    className="select-none"
                  >
                    {isHovered || isSelected ? node.name : getShortLabel(node)}
                  </text>

                  {/* Shared Badge / Type Label */}
                  <text
                    y={radius + 25}
                    fill={isShared ? '#22D3EE' : '#64748B'}
                    fontSize="8"
                    fontWeight={isShared ? 'bold' : 'normal'}
                    fontFamily="monospace"
                    textAnchor="middle"
                    pointerEvents="none"
                    className="select-none"
                  >
                    {isShared ? `SHARED (${totalDeg})` : node.artefact_type}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>

        {/* Bottom Legend & Node Count Overlay */}
        <div className="absolute bottom-3 left-3 bg-slate-950/85 backdrop-blur-md border border-slate-800 rounded-xl p-2.5 text-[11px] font-mono text-slate-400 flex flex-wrap items-center gap-4">
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
            <span>File / Component</span>
          </div>
          <div className="flex items-center gap-1.5 border-l border-slate-800 pl-3">
            <span className="w-3 h-3 rounded-full border border-dashed border-cyan-400 bg-cyan-950/40" />
            <span className="text-cyan-300 font-bold">Shared Asset (Fan-in &gt; 1)</span>
          </div>
          <div className="border-l border-slate-800 pl-3 text-slate-400">
            Showing <strong className="text-slate-200">{filteredNodes.length}</strong> / {nodes.length} nodes
          </div>
        </div>
      </div>
    </div>
  );
};

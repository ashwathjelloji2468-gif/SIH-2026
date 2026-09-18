import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float, Html } from '@react-three/drei';
import * as THREE from 'three';
import { CryptoAsset } from '../../types';

interface NodeData {
  id: string;
  name: string;
  type: string;
  safety: 'SAFE' | 'VULNERABLE' | 'TRANSITIONAL' | 'UNKNOWN';
  position: [number, number, number];
}

interface NodeMeshGroupProps {
  nodes: NodeData[];
}

const NodeMeshGroup: React.FC<NodeMeshGroupProps> = ({ nodes }) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
    }
  });

  const linePositions = useMemo(() => {
    if (nodes.length < 2) return new Float32Array(0);
    const pos: number[] = [];
    for (let i = 0; i < nodes.length; i++) {
      const nextIdx = (i + 1) % nodes.length;
      pos.push(...nodes[i].position, ...nodes[nextIdx].position);
      if (nodes.length > 3 && i % 2 === 0) {
        const crossIdx = (i + Math.floor(nodes.length / 2)) % nodes.length;
        pos.push(...nodes[i].position, ...nodes[crossIdx].position);
      }
    }
    return new Float32Array(pos);
  }, [nodes]);

  return (
    <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.2}>
      <group ref={groupRef}>
        {/* Connecting Lines */}
        {nodes.length > 1 && (
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[linePositions, 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#06B6D4" transparent opacity={0.35} linewidth={1} />
          </lineSegments>
        )}

        {/* Sphere Nodes */}
        {nodes.map((node) => {
          const color =
            node.safety === 'VULNERABLE'
              ? '#F43F5E'
              : node.safety === 'SAFE'
              ? '#10B981'
              : node.safety === 'TRANSITIONAL'
              ? '#F59E0B'
              : '#94A3B8';

          return (
            <group key={node.id} position={node.position}>
              <mesh>
                <sphereGeometry args={[0.22, 24, 24]} />
                <meshStandardMaterial
                  color={color}
                  emissive={color}
                  emissiveIntensity={0.4}
                  roughness={0.2}
                />
              </mesh>
              {/* Outer glow ring */}
              <mesh>
                <sphereGeometry args={[0.28, 16, 16]} />
                <meshBasicMaterial color={color} transparent opacity={0.15} wireframe />
              </mesh>
              {/* Label */}
              <Html distanceFactor={8} position={[0, 0.35, 0]} center>
                <div className="px-2 py-0.5 rounded bg-[#06080F]/90 border border-slate-700/80 text-[10px] font-mono font-bold whitespace-nowrap pointer-events-none" style={{ color }}>
                  {node.name}
                </div>
              </Html>
            </group>
          );
        })}
      </group>
    </Float>
  );
};

export interface NetworkNodes3DProps {
  className?: string;
  assets?: CryptoAsset[];
}

export const NetworkNodes3D: React.FC<NetworkNodes3DProps> = ({ className, assets = [] }) => {
  const nodes: NodeData[] = useMemo(() => {
    if (!assets || assets.length === 0) return [];
    const total = assets.length;
    return assets.map((asset, i) => {
      let position: [number, number, number];
      if (total === 1) {
        position = [0, 0, 0];
      } else {
        const phi = Math.acos(-1 + (2 * i + 1) / total);
        const theta = Math.sqrt(total * Math.PI) * phi;
        const radius = 2.2;
        const x = radius * Math.cos(theta) * Math.sin(phi);
        const y = radius * Math.sin(theta) * Math.sin(phi);
        const z = radius * Math.cos(phi);
        position = [Number(x.toFixed(2)), Number(y.toFixed(2)), Number(z.toFixed(2))];
      }

      const safety: 'SAFE' | 'VULNERABLE' | 'TRANSITIONAL' | 'UNKNOWN' =
        asset.quantum_safety === 'SAFE'
          ? 'SAFE'
          : asset.quantum_safety === 'VULNERABLE'
          ? 'VULNERABLE'
          : asset.quantum_safety === 'TRANSITIONAL'
          ? 'TRANSITIONAL'
          : 'UNKNOWN';

      return {
        id: asset.id,
        name: asset.algorithm_name || asset.name || 'Unknown',
        type: asset.asset_type || 'ALGORITHM',
        safety,
        position
      };
    });
  }, [assets]);

  if (!assets || assets.length === 0) {
    return (
      <div className={`w-full h-full flex flex-col items-center justify-center p-8 text-center bg-[#06080F]/80 border border-slate-800/60 rounded-xl ${className || ''}`}>
        <p className="text-sm font-mono text-slate-400">No discovered cryptographic assets for this scan.</p>
      </div>
    );
  }

  return (
    <div className={`w-full h-full relative ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.7} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          <NodeMeshGroup nodes={nodes} />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default NetworkNodes3D;

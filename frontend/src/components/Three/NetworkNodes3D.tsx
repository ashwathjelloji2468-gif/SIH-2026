import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float, Html } from '@react-three/drei';
import * as THREE from 'three';

interface NodeData {
  id: string;
  name: string;
  type: string;
  safety: 'SAFE' | 'VULNERABLE' | 'TRANSITIONAL';
  position: [number, number, number];
}

const NODES: NodeData[] = [
  { id: '1', name: 'RSA-2048', type: 'ENCRYPTION', safety: 'VULNERABLE', position: [-2, 1, 0] },
  { id: '2', name: 'ECDSA-P256', type: 'SIGNATURE', safety: 'VULNERABLE', position: [-1, -1.5, 1] },
  { id: '3', name: 'AES-256-GCM', type: 'SYMMETRIC', safety: 'SAFE', position: [1.5, 1.2, -0.5] },
  { id: '4', name: 'ML-KEM-768', type: 'PQC_KEM', safety: 'SAFE', position: [2, -0.8, 0.5] },
  { id: '5', name: 'SHA-256', type: 'HASH', safety: 'SAFE', position: [0, 2, -1] },
  { id: '6', name: 'ML-DSA-65', type: 'PQC_SIG', safety: 'SAFE', position: [0.5, -2, -0.8] },
  { id: '7', name: 'DH-2048', type: 'KEY_EXCHANGE', safety: 'VULNERABLE', position: [-2.5, -0.5, -1] },
  { id: '8', name: 'SLH-DSA', type: 'PQC_SIG', safety: 'SAFE', position: [2.2, 0.2, -1.5] },
];

const CONNECTIONS: [number, number][] = [
  [0, 1], [0, 2], [1, 3], [2, 3], [2, 4], [3, 5], [0, 6], [5, 7], [3, 7]
];

const NodeMeshGroup: React.FC = () => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
    }
  });

  const linePositions = useMemo(() => {
    const pos: number[] = [];
    CONNECTIONS.forEach(([startIdx, endIdx]) => {
      const start = NODES[startIdx].position;
      const end = NODES[endIdx].position;
      pos.push(...start, ...end);
    });
    return new Float32Array(pos);
  }, []);

  return (
    <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.2}>
      <group ref={groupRef}>
        {/* Connecting Lines */}
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[linePositions, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#06B6D4" transparent opacity={0.35} linewidth={1} />
        </lineSegments>

        {/* Sphere Nodes */}
        {NODES.map((node) => {
          const color =
            node.safety === 'VULNERABLE'
              ? '#F43F5E'
              : node.safety === 'SAFE'
              ? '#10B981'
              : '#F59E0B';

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
}

export const NetworkNodes3D: React.FC<NetworkNodes3DProps> = ({ className }) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.7} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          <NodeMeshGroup />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default NetworkNodes3D;

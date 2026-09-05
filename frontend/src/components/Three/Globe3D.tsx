import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Float } from '@react-three/drei';
import * as THREE from 'three';

const GlobeMesh: React.FC = () => {
  const globeRef = useRef<THREE.Group>(null);
  const dotsRef = useRef<THREE.Points>(null);

  // Generate 600 points on sphere surface
  const { positions, colors } = useMemo(() => {
    const pos = new Float32Array(600 * 3);
    const col = new Float32Array(600 * 3);
    const radius = 2;

    for (let i = 0; i < 600; i++) {
      const phi = Math.acos(-1 + (2 * i) / 600);
      const theta = Math.sqrt(600 * Math.PI) * phi;

      pos[i * 3] = radius * Math.cos(theta) * Math.sin(phi);
      pos[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
      pos[i * 3 + 2] = radius * Math.cos(phi);

      // Randomly color nodes: cyan, emerald, rose
      const color = new THREE.Color(
        i % 7 === 0 ? '#F43F5E' : i % 5 === 0 ? '#10B981' : '#06B6D4'
      );
      col[i * 3] = color.r;
      col[i * 3 + 1] = color.g;
      col[i * 3 + 2] = color.b;
    }

    return { positions: pos, colors: col };
  }, []);

  useFrame((_, delta) => {
    if (globeRef.current) {
      globeRef.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
      <group ref={globeRef}>
        {/* Inner wireframe sphere */}
        <mesh>
          <sphereGeometry args={[1.98, 32, 32]} />
          <meshBasicMaterial color="#06B6D4" wireframe transparent opacity={0.12} />
        </mesh>

        {/* Inner glow core */}
        <mesh>
          <sphereGeometry args={[1.5, 32, 32]} />
          <meshBasicMaterial color="#22D3EE" transparent opacity={0.08} />
        </mesh>

        {/* Surface dot cloud */}
        <points ref={dotsRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[positions, 3]}
            />
            <bufferAttribute
              attach="attributes-color"
              args={[colors, 3]}
            />
          </bufferGeometry>
          <pointsMaterial size={0.05} vertexColors transparent opacity={0.9} />
        </points>
      </group>
    </Float>
  );
};

export interface Globe3DProps {
  className?: string;
}

export const Globe3D: React.FC<Globe3DProps> = ({ className }) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.6} />
          <Stars radius={80} depth={40} count={3000} factor={3} saturation={0} fade speed={1} />
          <GlobeMesh />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default Globe3D;

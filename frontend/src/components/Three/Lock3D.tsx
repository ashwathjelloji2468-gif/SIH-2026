import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import * as THREE from 'three';

interface LockMeshProps {
  status?: 'vulnerable' | 'safe' | 'migrating';
}

const LockScene: React.FC<LockMeshProps> = ({ status = 'safe' }) => {
  const groupRef = useRef<THREE.Group>(null);
  const shackleRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.2;
    }
  });

  const mainColor =
    status === 'vulnerable'
      ? '#F43F5E'
      : status === 'migrating'
      ? '#F59E0B'
      : '#10B981';

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
      <group ref={groupRef}>
        {/* Outer Cyber Shield Wireframe */}
        <mesh position={[0, 0, 0]}>
          <icosahedronGeometry args={[1.6, 2]} />
          <meshBasicMaterial color={mainColor} wireframe transparent opacity={0.3} />
        </mesh>

        {/* Lock Shackle */}
        <mesh ref={shackleRef} position={[0, 0.5, 0]}>
          <torusGeometry args={[0.45, 0.08, 16, 32, Math.PI]} />
          <meshStandardMaterial
            color={mainColor}
            metalness={0.8}
            roughness={0.2}
            emissive={mainColor}
            emissiveIntensity={0.4}
          />
        </mesh>

        {/* Lock Body */}
        <mesh position={[0, -0.2, 0]}>
          <boxGeometry args={[0.9, 0.8, 0.4]} />
          <meshStandardMaterial
            color="#0F1523"
            metalness={0.9}
            roughness={0.1}
          />
        </mesh>

        {/* Pulsing Core Sphere */}
        <mesh position={[0, -0.2, 0.22]}>
          <sphereGeometry args={[0.12, 24, 24]} />
          <meshStandardMaterial
            color={mainColor}
            emissive={mainColor}
            emissiveIntensity={0.8}
          />
        </mesh>

        {/* Orbit Ring */}
        <mesh rotation={[Math.PI / 3, 0, 0]}>
          <torusGeometry args={[1.8, 0.015, 16, 64]} />
          <meshBasicMaterial color="#06B6D4" transparent opacity={0.6} />
        </mesh>
      </group>
    </Float>
  );
};

export interface Lock3DProps {
  status?: 'vulnerable' | 'safe' | 'migrating';
  className?: string;
}

export const Lock3D: React.FC<Lock3DProps> = ({ status = 'safe', className }) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <LockScene status={status} />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default Lock3D;

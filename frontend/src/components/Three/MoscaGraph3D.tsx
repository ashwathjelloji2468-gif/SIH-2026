import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float, Html } from '@react-three/drei';
import * as THREE from 'three';

interface MoscaMeshProps {
  dataLifetime?: number;
  migrationTime?: number;
  threatHorizon?: number;
}

const MoscaScene: React.FC<MoscaMeshProps> = ({
  dataLifetime = 10,
  migrationTime = 3,
  threatHorizon = 2033,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const planeRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.12;
    }
  });

  const isBreached = dataLifetime + migrationTime > threatHorizon - 2026;

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.2}>
      <group ref={groupRef}>
        {/* 3D Coordinate Axes Grid */}
        <gridHelper args={[6, 12, '#06B6D4', '#1E293B']} position={[0, -1.5, 0]} />

        {/* Threat Horizon Breach Plane */}
        <mesh ref={planeRef} position={[0, 0, 0]} rotation={[-Math.PI / 4, 0, 0]}>
          <planeGeometry args={[4, 3]} />
          <meshBasicMaterial
            color={isBreached ? '#F43F5E' : '#10B981'}
            transparent
            opacity={0.2}
            side={THREE.DoubleSide}
            wireframe
          />
        </mesh>

        {/* Intersection Pulse Sphere (Risk Exposure Point) */}
        <mesh position={[0, 0.2, 0]}>
          <sphereGeometry args={[0.35, 32, 32]} />
          <meshStandardMaterial
            color={isBreached ? '#F43F5E' : '#10B981'}
            emissive={isBreached ? '#F43F5E' : '#10B981'}
            emissiveIntensity={0.6}
          />
        </mesh>

        {/* Orbit Ring */}
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[2.2, 0.02, 16, 64]} />
          <meshBasicMaterial color="#06B6D4" transparent opacity={0.4} />
        </mesh>

        {/* Dynamic Labels */}
        <Html position={[-2, 1.2, 0]} center>
          <div className="px-2 py-1 rounded bg-[#06080F]/90 border border-cyan-500/40 text-[10px] font-mono text-cyan-300 font-bold whitespace-nowrap shadow-lg">
            X (Lifetime) = {dataLifetime}y
          </div>
        </Html>

        <Html position={[2, 1.2, 0]} center>
          <div className="px-2 py-1 rounded bg-[#06080F]/90 border border-emerald-500/40 text-[10px] font-mono text-emerald-300 font-bold whitespace-nowrap shadow-lg">
            Y (Migration) = {migrationTime}y
          </div>
        </Html>

        <Html position={[0, -1.8, 2]} center>
          <div className="px-2 py-1 rounded bg-[#06080F]/90 border border-rose-500/40 text-[10px] font-mono text-rose-300 font-bold whitespace-nowrap shadow-lg">
            Z (Horizon) = {threatHorizon}
          </div>
        </Html>
      </group>
    </Float>
  );
};

export interface MoscaGraph3DProps {
  dataLifetime?: number;
  migrationTime?: number;
  threatHorizon?: number;
  className?: string;
}

export const MoscaGraph3D: React.FC<MoscaGraph3DProps> = ({
  dataLifetime = 10,
  migrationTime = 3,
  threatHorizon = 2033,
  className,
}) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 1.5, 5], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <MoscaScene
            dataLifetime={dataLifetime}
            migrationTime={migrationTime}
            threatHorizon={threatHorizon}
          />
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.6} />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default MoscaGraph3D;

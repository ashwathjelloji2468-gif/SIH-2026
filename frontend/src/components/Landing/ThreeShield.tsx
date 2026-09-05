import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface ThreeShieldProps {
  className?: string;
}

const ShieldMesh = () => {
  const outerRef = useRef<THREE.Mesh>(null);
  const midRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Group>(null);
  
  const { mouse } = useThree();

  const particlesCount = 280;
  const positions = useMemo(() => {
    const pos = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount; i++) {
      const angle = (i / particlesCount) * Math.PI * 2;
      const radius = 2.6 + (Math.sin(i * 0.5) * 0.3);
      pos[i * 3] = Math.cos(angle) * radius;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 0.6;
      pos[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return pos;
  }, [particlesCount]);

  useFrame((state, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.y += delta * 0.15;
      outerRef.current.rotation.x += delta * 0.05;
      
      // Mouse tracking parallax for depth
      outerRef.current.position.x = THREE.MathUtils.lerp(outerRef.current.position.x, (mouse.x * 0.6), 0.08);
      outerRef.current.position.y = THREE.MathUtils.lerp(outerRef.current.position.y, (mouse.y * 0.6), 0.08);
    }

    if (midRef.current) {
      midRef.current.rotation.y -= delta * 0.22;
      midRef.current.rotation.z += delta * 0.08;
    }
    
    if (innerRef.current) {
      // Smooth breathing scale
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2.2) * 0.06;
      innerRef.current.scale.set(scale, scale, scale);
    }

    if (ringRef.current) {
      ringRef.current.rotation.y -= delta * 0.25;
      ringRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.6) * 0.25;
    }
  });

  return (
    <group>
      <Float speed={1.8} rotationIntensity={0.3} floatIntensity={0.6}>
        {/* Outer Geodesic Wireframe Sphere */}
        <mesh ref={outerRef}>
          <icosahedronGeometry args={[2.0, 1]} />
          <meshBasicMaterial color="#22D3EE" wireframe transparent opacity={0.45} />
        </mesh>

        {/* Middle Counter-rotating Wireframe Layer */}
        <mesh ref={midRef}>
          <icosahedronGeometry args={[1.5, 0]} />
          <meshBasicMaterial color="#06B6D4" wireframe transparent opacity={0.35} />
        </mesh>
        
        {/* Inner Glowing Core Sphere */}
        <mesh ref={innerRef}>
          <sphereGeometry args={[1.1, 32, 32]} />
          <meshStandardMaterial
            color="#22D3EE"
            emissive="#06B6D4"
            emissiveIntensity={0.6}
            transparent
            opacity={0.25}
          />
        </mesh>

        {/* Center Point Light */}
        <pointLight color="#22D3EE" intensity={3} distance={6} />
      </Float>

      {/* Orbiting Particle Ring */}
      <group ref={ringRef}>
        <points>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[positions, 3]}
            />
          </bufferGeometry>
          <pointsMaterial size={0.04} color="#67E8F9" transparent opacity={0.85} />
        </points>
      </group>
    </group>
  );
};

export const ThreeShield: React.FC<ThreeShieldProps> = ({ className }) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 5.8], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[5, 5, 8]} intensity={1.2} color="#22D3EE" />
          <Stars radius={90} depth={45} count={3500} factor={3} saturation={0} fade speed={1} />
          <ShieldMesh />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default ThreeShield;

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface ThreeShieldProps {
  className?: string;
}

const ShieldMesh = () => {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Group>(null);
  
  const { mouse } = useThree();

  const particlesCount = 200;
  const positions = useMemo(() => {
    const positions = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount; i++) {
      const angle = (i / particlesCount) * Math.PI * 2;
      const radius = 2.5 + Math.random() * 0.5;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 0.5;
      positions[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return positions;
  }, [particlesCount]);

  useFrame((state, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.y += delta * 0.2;
      outerRef.current.rotation.x += delta * 0.1;
      
      // Mouse tracking parallax
      outerRef.current.position.x = THREE.MathUtils.lerp(outerRef.current.position.x, (mouse.x * 0.5), 0.1);
      outerRef.current.position.y = THREE.MathUtils.lerp(outerRef.current.position.y, (mouse.y * 0.5), 0.1);
    }
    
    if (innerRef.current) {
      // Breathing scale 0.95 to 1.05
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.05;
      innerRef.current.scale.set(scale, scale, scale);
    }

    if (ringRef.current) {
      ringRef.current.rotation.y -= delta * 0.3;
      ringRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    }
  });

  return (
    <group>
      <Float speed={1.5} rotationIntensity={0.5} floatIntensity={1}>
        {/* Outer Wireframe Icosahedron */}
        <mesh ref={outerRef}>
          <icosahedronGeometry args={[1.8, 0]} />
          <meshBasicMaterial color="#06B6D4" wireframe transparent opacity={0.6} />
        </mesh>
        
        {/* Inner Glowing Sphere */}
        <mesh ref={innerRef}>
          <sphereGeometry args={[1.2, 32, 32]} />
          <meshBasicMaterial color="#22D3EE" transparent opacity={0.15} />
        </mesh>
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
            <pointsMaterial size={0.03} color="#06B6D4" transparent opacity={0.8} />
          </points>
        </group>
      </group>
    );
  };

export const ThreeShield: React.FC<ThreeShieldProps> = ({ className }) => {
  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
        <React.Suspense fallback={null}>
          <color attach="background" args={['transparent']} />
          <ambientLight intensity={0.5} />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
          <ShieldMesh />
        </React.Suspense>
      </Canvas>
    </div>
  );
};

export default ThreeShield;

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface SentriqLogoMeshProps {
  interactive?: boolean;
}

const SentriqLogoMesh: React.FC<SentriqLogoMeshProps> = ({ interactive = true }) => {
  const groupRef = useRef<THREE.Group>(null);
  const outerShieldRef = useRef<THREE.Mesh>(null);
  const innerSRef = useRef<THREE.Mesh>(null);

  // Define 2D Shape for the Outer Shield matching the SENTRIQ logo
  const shieldShape = useMemo(() => {
    const shape = new THREE.Shape();
    // Shield path: top center -> top right -> right edge -> bottom point -> left edge -> top left -> close
    shape.moveTo(0, 1.6);
    shape.lineTo(1.1, 1.3);
    shape.lineTo(1.2, 0.1);
    shape.lineTo(0, -1.6);
    shape.lineTo(-1.2, 0.1);
    shape.lineTo(-1.1, 1.3);
    shape.closePath();

    // Inner hole for border shield look
    const hole = new THREE.Path();
    hole.moveTo(0, 1.35);
    hole.lineTo(-0.9, 1.1);
    hole.lineTo(-1.0, 0.1);
    hole.lineTo(0, -1.35);
    hole.lineTo(1.0, 0.1);
    hole.lineTo(0.9, 1.1);
    hole.closePath();

    shape.holes.push(hole);
    return shape;
  }, []);

  // Define 2D Shape for the stylized 'S' inside
  const sShape = useMemo(() => {
    const shape = new THREE.Shape();
    // Ribbon 'S' path
    shape.moveTo(-0.5, 0.85);
    shape.lineTo(0.5, 0.85);
    shape.lineTo(0.5, 0.55);
    shape.lineTo(-0.2, 0.55);
    shape.lineTo(0.5, 0.1);
    shape.lineTo(0.5, -0.7);
    shape.lineTo(-0.5, -0.7);
    shape.lineTo(-0.5, -0.4);
    shape.lineTo(0.2, -0.4);
    shape.lineTo(-0.5, 0.05);
    shape.closePath();
    return shape;
  }, []);

  const extrudeSettings = useMemo(
    () => ({
      depth: 0.2,
      bevelEnabled: true,
      bevelSegments: 4,
      steps: 2,
      bevelSize: 0.05,
      bevelThickness: 0.05,
    }),
    []
  );

  const innerExtrudeSettings = useMemo(
    () => ({
      depth: 0.25,
      bevelEnabled: true,
      bevelSegments: 3,
      steps: 2,
      bevelSize: 0.04,
      bevelThickness: 0.04,
    }),
    []
  );

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Smooth 3D rotation
      groupRef.current.rotation.y += delta * 0.6;

      if (interactive) {
        // Subtle mouse follow tilt
        const mouseX = (state.pointer.x * Math.PI) / 6;
        const mouseY = (state.pointer.y * Math.PI) / 6;
        groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, mouseY * 0.4, 0.05);
        groupRef.current.rotation.z = THREE.MathUtils.lerp(groupRef.current.rotation.z, -mouseX * 0.2, 0.05);
      }
    }
  });

  const cyanMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color('#00E5FF'),
        emissive: new THREE.Color('#00B4D8'),
        emissiveIntensity: 0.8,
        metalness: 0.7,
        roughness: 0.15,
      }),
    []
  );

  const glowWireframeMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: new THREE.Color('#00F0FF'),
        wireframe: true,
        transparent: true,
        opacity: 0.3,
      }),
    []
  );

  return (
    <Float speed={2} rotationIntensity={0.3} floatIntensity={0.4}>
      <group ref={groupRef}>
        {/* Extruded Outer Shield Mesh */}
        <mesh ref={outerShieldRef} material={cyanMaterial} position={[0, 0, -0.1]}>
          <extrudeGeometry args={[shieldShape, extrudeSettings]} />
        </mesh>

        {/* Ambient Wireframe Outer Glow Shield */}
        <mesh position={[0, 0, 0]}>
          <extrudeGeometry args={[shieldShape, { ...extrudeSettings, depth: 0.24 }]} />
          <primitive object={glowWireframeMaterial} />
        </mesh>

        {/* Extruded Inner Stylized 'S' Mesh */}
        <mesh ref={innerSRef} material={cyanMaterial} position={[0, 0, 0.02]}>
          <extrudeGeometry args={[sShape, innerExtrudeSettings]} />
        </mesh>

        {/* Orbiting Cyber Ring */}
        <mesh rotation={[Math.PI / 3, 0, 0]}>
          <torusGeometry args={[1.9, 0.015, 16, 64]} />
          <meshBasicMaterial color="#00F0FF" transparent opacity={0.6} />
        </mesh>

        {/* Core Emissive Light */}
        <pointLight color="#00F0FF" intensity={3} distance={5} />
      </group>
    </Float>
  );
};

export interface Sentriq3DLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'hero';
  showText?: boolean;
  interactive?: boolean;
}

export const Sentriq3DLogo: React.FC<Sentriq3DLogoProps> = ({
  className,
  size = 'md',
  showText = true,
  interactive = true,
}) => {
  const containerDimensions = {
    sm: 'w-10 h-10',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
    hero: 'w-72 h-72 lg:w-96 lg:h-96',
  }[size];

  const cameraFov = size === 'sm' || size === 'md' ? 40 : 45;

  return (
    <div className={`flex items-center gap-3 ${className || ''}`}>
      <div className={`relative ${containerDimensions} flex-shrink-0`}>
        <Canvas camera={{ position: [0, 0, 4.8], fov: cameraFov }}>
          <React.Suspense fallback={null}>
            <color attach="background" args={['transparent']} />
            <ambientLight intensity={0.8} />
            <directionalLight position={[5, 5, 8]} intensity={1.5} color="#00F0FF" />
            <directionalLight position={[-5, -5, -5]} intensity={0.5} color="#0055FF" />
            <SentriqLogoMesh interactive={interactive} />
            {interactive && <OrbitControls enableZoom={false} enablePan={false} maxPolarAngle={Math.PI / 1.8} minPolarAngle={Math.PI / 2.2} />}
          </React.Suspense>
        </Canvas>
      </div>

      {showText && (
        <span
          className={`font-mono font-extrabold tracking-wider bg-gradient-to-r from-white via-[#80F2FF] to-[#00E5FF] bg-clip-text text-transparent ${
            size === 'sm'
              ? 'text-base'
              : size === 'md'
              ? 'text-xl'
              : size === 'lg'
              ? 'text-3xl'
              : 'text-5xl lg:text-6xl'
          }`}
        >
          SENTRIQ
        </span>
      )}
    </div>
  );
};

export default Sentriq3DLogo;

import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import * as THREE from "three";

interface FlameSceneProps {
  paused: boolean;
  particles: boolean;
  mode: "morphology" | "boundary";
}

function FlameOrb({ paused, mode }: { paused: boolean; mode: "morphology" | "boundary" }) {
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        toneMapped: false,
        uniforms: { uTime: { value: 0 }, uMode: { value: 0 } },
        vertexShader: `
          varying vec2 vUv;
          varying vec3 vNormal;
          void main() {
            vUv = uv;
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform float uTime;
          uniform float uMode;
          varying vec2 vUv;
          varying vec3 vNormal;
          void main() {
            vec2 p = vUv - 0.5;
            float radius = length(p);
            float wave = sin(atan(p.y, p.x) * 7.0 + uTime * 0.8) * 0.025
                       + sin(p.y * 31.0 - uTime * 0.55) * 0.012;
            float edge = 1.0 - smoothstep(0.17, 0.52, radius + wave);
            float rim = smoothstep(0.28, 0.42, radius) * (1.0 - smoothstep(0.43, 0.50, radius));
            vec3 cool = vec3(0.04, 0.28, 0.80);
            vec3 gold = vec3(1.0, 0.24, 0.04);
            vec3 core = vec3(1.0, 0.76, 0.40);
            float coreBlend = 1.0 - smoothstep(0.04, 0.30, radius);
            vec3 color = mix(cool, gold, smoothstep(0.16, 0.43, radius));
            color = mix(color, core, coreBlend * 0.9);
            color = mix(color, cool, rim * 0.65);
            float light = 0.72 + 0.28 * max(vNormal.z, 0.0);
            if (uMode > 0.5) {
              edge = rim;
              color = mix(cool * 0.7, vec3(0.50, 0.92, 1.0), rim);
            }
            gl_FragColor = vec4(color * light * (1.0 + coreBlend * 0.7), edge * 0.94);
          }
        `,
      }),
    [],
  );
  const mesh = useRef<THREE.Mesh>(null);

  useEffect(() => {
    material.uniforms.uMode.value = mode === "boundary" ? 1 : 0;
  }, [material, mode]);

  useFrame((state, delta) => {
    if (!paused) material.uniforms.uTime.value += delta;
    if (mesh.current && !paused) {
      mesh.current.rotation.y += delta * 0.06;
      mesh.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 0.65) * 0.012);
    }
  });

  return (
    <mesh ref={mesh} material={material}>
      <sphereGeometry args={[1, 96, 96]} />
    </mesh>
  );
}

function ParticleField({ enabled, paused }: { enabled: boolean; paused: boolean }) {
  const points = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const result = new Float32Array(240 * 3);
    for (let i = 0; i < 240; i += 1) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 1.25 + Math.random() * 1.15;
      result[i * 3] = Math.cos(angle) * radius;
      result[i * 3 + 1] = (Math.random() - 0.5) * 3.2;
      result[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return result;
  }, []);

  useFrame((_, delta) => {
    if (points.current && enabled && !paused) points.current.rotation.y += delta * 0.018;
  });

  if (!enabled) return null;
  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#92dfff" size={0.018} transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}

function StarField() {
  const positions = useMemo(() => {
    const result = new Float32Array(320 * 3);
    for (let i = 0; i < 320; i += 1) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 4 + Math.random() * 9;
      result[i * 3] = Math.cos(angle) * radius;
      result[i * 3 + 1] = (Math.random() - 0.5) * 12;
      result[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return result;
  }, []);

  return (
    <points>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry>
      <pointsMaterial color="#91aac0" size={0.012} transparent opacity={0.38} sizeAttenuation />
    </points>
  );
}

function SceneControls() {
  const { camera, gl } = useThree();
  const controls = useMemo(() => new OrbitControls(camera, gl.domElement), [camera, gl]);

  useEffect(() => {
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 3.5;
    controls.maxDistance = 7;
    return () => controls.dispose();
  }, [controls]);

  useFrame(() => controls.update());

  return null;
}

export default function FlameScene({ paused, particles, mode }: FlameSceneProps) {
  return (
    <Canvas
      camera={{ position: [0, 0, 4.7], fov: 40 }}
      dpr={[1, 1.5]}
      gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
      fallback={<div className="scene-fallback">3D rendering is unavailable on this device.</div>}
      aria-label="Interactive illustrative 3D microgravity flame"
    >
      <Suspense fallback={null}>
        <ambientLight intensity={0.55} />
        <pointLight position={[2, 1, 3]} color="#ff6c36" intensity={20} distance={8} />
        <pointLight position={[-2, -1, 2]} color="#367dff" intensity={8} distance={8} />
        <StarField />
        <ParticleField enabled={particles} paused={paused} />
        <FlameOrb paused={paused} mode={mode} />
        <SceneControls />
      </Suspense>
    </Canvas>
  );
}

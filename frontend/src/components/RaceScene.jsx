import { useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

const CATEGORIES = [
  { id: "aero", title: "AERODYNAMICS", detail: "Front wing, floor, diffuser and rear wing manage airflow and downforce." },
  { id: "power", title: "POWER UNIT", detail: "Engine cover and airbox represent the power-unit package." },
  { id: "fuel", title: "FUEL CELL", detail: "The fuel cell sits within the protected central chassis." },
  { id: "chassis", title: "CARBON CHASSIS", detail: "The survival cell, cockpit and halo protect the driver." },
];

function HoloPart({ geometry, position = [0, 0, 0], rotation = [0, 0, 0], category = "chassis", selected, dense = false }) {
  const active = selected === category || selected === "all";
  const fillColor = "#073348";
  const edges = useMemo(
    () => dense ? new THREE.WireframeGeometry(geometry) : new THREE.EdgesGeometry(geometry, 22),
    [geometry, dense]
  );
  return (
    <group position={position} rotation={rotation}>
      <mesh geometry={geometry}>
        <meshBasicMaterial color={fillColor} transparent opacity={active ? 0.36 : 0.2} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
      <lineSegments geometry={edges}>
  <lineBasicMaterial
    color={selected === category ? "#ff4658" : "#65f5ff"}
    transparent
    opacity={selected === category ? 1 : 0.82}
  />
</lineSegments>
    </group>
  );
}

function BoxPart({ args, position, rotation, category, selected, dense = false }) {
  const geometry = useMemo(() => new THREE.BoxGeometry(...args, dense ? 5 : 1, 2, dense ? 5 : 1), [args, dense]);
  return <HoloPart geometry={geometry} position={position} rotation={rotation} category={category} selected={selected} dense={dense} />;
}


function Rod({ start, end, selected, category = "chassis" }) {
  const a = new THREE.Vector3(...start);
  const b = new THREE.Vector3(...end);
  const direction = b.clone().sub(a);
  const length = direction.length();

  const geometry = new THREE.CylinderGeometry(0.014,0.014,length,6);
  const quaternion = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.clone().normalize()
  );

  const active = selected === "all" || selected === category;

  return (
    <mesh
      geometry={geometry}
      position={a.add(b).multiplyScalar(0.5)}
      quaternion={quaternion}
    >
      <meshBasicMaterial color={active ? "#ff4658" : "#65f5ff"} />
    </mesh>
  );
}

function Wheel({ position, selected }) {
  const geometry = useMemo(() => new THREE.CylinderGeometry(0.34, 0.34, 0.22, 32, 1), []);
  const rimGeometry = useMemo(() => new THREE.CylinderGeometry(0.2, 0.2, 0.235, 24, 1), []);
  const active = selected === "all" || selected === "chassis";
  return (
    <group position={position} rotation={[0, 0, Math.PI / 2]}>
      <mesh geometry={geometry}>
        <meshBasicMaterial
  color="#073348"
  wireframe={false}
  transparent
  opacity={0.06}
  depthWrite={false}
  side={THREE.DoubleSide}
/>
      </mesh>
      <mesh geometry={rimGeometry}>
        <meshBasicMaterial color={active ? "#ff4658" : "#65f5ff"} wireframe />
      </mesh>
    </group>
  );
}

function RaceCar({ selected }) {
  return (
    <group rotation={[0.08, -0.32, 0]} scale={0.92}>
      {/* Main survival cell and nose; front of car points toward +Z. */}
      <BoxPart args={[0.42, 0.28, 1.05]}position={[0, 0.12, -0.58]}category="power" selected={selected} dense/>
      <HoloPart geometry={new THREE.ConeGeometry(0.29, 1.7, 20, 6)} position={[0, 0.02, 1.35]} rotation={[Math.PI / 2, 0, 0]} category="chassis" selected={selected} dense />
      <HoloPart geometry={new THREE.SphereGeometry(1, 20, 14)} position={[0, 0.12, -0.65]} rotation={[0.1, 0, 0]} category="power" selected={selected} />
      {/* Sidepods */}
      {[-1, 1].map((side) => (
        <group key={side}>
          <BoxPart args={[0.48, 0.25, 0.9]}position={[side * 0.47, 0, -0.28]}rotation={[0, 0, side * -0.08]} category="power" selected={selected} dense/>
          <BoxPart args={[0.1, 0.15, 0.42]} position={[side * 0.59, 0.12, -0.08]} category="power" selected={selected} />
          {[0, 1, 2].map((i) => <BoxPart key={i} args={[0.025, 0.02, 0.1]} position={[side * 0.86, 0.11, -0.12 - i * 0.13]} category="power" selected={selected} />)}
        </group>
      ))}
      {/* Cockpit, helmet and halo */}
      <HoloPart geometry={new THREE.TorusGeometry(0.27, 0.035, 8, 28)} position={[0, 0.31, 0.12]} rotation={[Math.PI / 2, 0, 0]} category="chassis" selected={selected} />
      <HoloPart geometry={new THREE.SphereGeometry(0.14, 16, 12)} position={[0, 0.42, 0.08]} category="chassis" selected={selected} />
      <HoloPart geometry={new THREE.TorusGeometry(0.29, 0.018, 6, 28, Math.PI)} position={[0, 0.53, 0.08]} rotation={[Math.PI / 2, 0, 0]} category="chassis" selected={selected} />
      <Rod start={[-0.26, 0.3, 0.12]} end={[0, 0.52, 0.14]} selected={selected} />
      <Rod start={[0.26, 0.3, 0.12]} end={[0, 0.52, 0.14]} selected={selected} />
      {/* Floor and wings */}
      <BoxPart args={[1.5, 0.05, 3.4]} position={[0, -0.16, -0.02]} category="aero" selected={selected} dense />
      {[0, 1, 2].map((i) => <BoxPart key={i} args={[2.05 - i * 0.16, 0.035, 0.11]} position={[0, -0.1 + i * 0.045, 2.02 - i * 0.11]} category="aero" selected={selected} dense />)}
      <BoxPart args={[1.55, 0.05, 0.22]} position={[0, 0.64, -1.52]} category="aero" selected={selected} dense />
      <BoxPart args={[1.42, 0.04, 0.17]} position={[0, 0.85, -1.55]} category="aero" selected={selected} dense />
      {[-1, 1].map((side) => (
        <group key={side}>
          <BoxPart args={[0.05, 0.26, 0.3]} position={[side * 1.02, -0.02, 2.0]} category="aero" selected={selected} />
          <BoxPart args={[0.05, 0.4, 0.25]} position={[side * 0.72, 0.7, -1.52]} category="aero" selected={selected} />
          <Wheel position={[side * 0.83, -0.02, 1.02]} selected={selected} />
          <Wheel position={[side * 0.83, -0.02, -1.12]} selected={selected} />
          <Rod start={[side * 0.28, 0.12, 0.72]} end={[side * 0.83, 0.08, 1.02]} selected={selected} />
          <Rod start={[side * 0.28, -0.1, 0.84]} end={[side * 0.83, -0.1, 1.02]} selected={selected} />
          <Rod start={[side * 0.3, 0.12, -0.75]} end={[side * 0.83, 0.08, -1.12]} selected={selected} />
          <Rod start={[side * 0.3, -0.1, -0.84]} end={[side * 0.83, -0.1, -1.12]} selected={selected} />
        </group>
      ))}
      {/* Fuel cell marker and red telemetry spine */}
      <BoxPart args={[0.38, 0.17, 0.52]} position={[0, 0.12, -0.42]} category="fuel" selected={selected} />
      <BoxPart args={[0.035, 0.018, 0.95]} position={[0, 0.3, -0.35]} category="chassis" selected="all" />
    </group>
  );
}

function HologramScene({ selected }) {
  return (
    <>
      <color attach="background" args={["#050e1d"]} />
      <ambientLight intensity={0.8} />
      <pointLight position={[3, 3, 3]} intensity={12} color="#ff3045" />
      <pointLight position={[-3, 2, -2]} intensity={10} color="#39dfff" />
      <RaceCar selected={selected} />
      <gridHelper args={[14, 28, "#155a70", "#0b2f40"]} position={[0, -0.49, 0]} />
      {[2.7, 3.4, 4.1].map((radius, i) => (
        <mesh key={radius} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.475 + i * 0.001, 0]}>
          <ringGeometry args={[radius, radius + 0.012, 96]} />
          <meshBasicMaterial color={i === 1 ? "#ff4658" : "#2e7184"} transparent opacity={0.7} />
        </mesh>
      ))}
      <OrbitControls enablePan={false} minDistance={4.5} maxDistance={10} maxPolarAngle={Math.PI / 2.02} autoRotate autoRotateSpeed={0.35} />
    </>
  );
}

export default function RaceScene() {
  const [selected, setSelected] = useState("all");
  const active = CATEGORIES.find((item) => item.id === selected);
  return (
    <div className="race-scene race-scene-holo">
      <Canvas camera={{ position: [5, 3.5, 6], fov: 39 }} dpr={[1, 1.5]}>
        <HologramScene selected={selected} />
      </Canvas>
      <div className="scene-overlay scene-label">APEX / HOLOGRAPHIC TELEMETRY</div>
      <div className="scene-overlay scene-controls">DRAG TO ORBIT · SCROLL TO ZOOM</div>
      <div className="holo-callouts">
        {CATEGORIES.map((item) => (
          <button
            type="button"
            key={item.id}
            className={`holo-callout ${selected === item.id ? "selected" : ""}`}
            onClick={() => setSelected(selected === item.id ? "all" : item.id)}
            aria-pressed={selected === item.id}
          >
            <span>{item.title}</span>
            <strong>{selected === item.id ? "ACTIVE" : "SELECT"}</strong>
          </button>
        ))}
      </div>
      {active && selected !== "all" && <div className="holo-detail">{active.detail}</div>}
    </div>
  );
}

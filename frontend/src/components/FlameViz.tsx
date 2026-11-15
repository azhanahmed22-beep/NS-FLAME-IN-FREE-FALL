import { lazy, Suspense, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Maximize2, Pause, Play, RotateCcw, Sparkles } from "lucide-react";
const FlameScene = lazy(() => import("./FlameScene"));

export default function FlameViz() {
  const [paused, setPaused] = useState(false);
  const [particles, setParticles] = useState(true);
  const [mode, setMode] = useState<"morphology" | "boundary">("morphology");
  const [resetKey, setResetKey] = useState(0);
  const [sceneReady, setSceneReady] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setSceneReady(true), 250);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (preference.matches) setPaused(true);
    const updatePreference = (event: MediaQueryListEvent) => setPaused(event.matches);
    preference.addEventListener("change", updatePreference);
    return () => preference.removeEventListener("change", updatePreference);
  }, []);

  return (
    <section className="flame-panel" aria-label="Illustrative microgravity flame visualization">
      <div className="flame-panel-top">
        <div>
          <div className="eyebrow"><span className="live-dot" /> VISUALIZATION MODE</div>
          <h2>Flame morphology</h2>
        </div>
        <span className="sim-tag">ILLUSTRATIVE · NOT EXPERIMENT DATA</span>
      </div>
      <motion.div key={resetKey} className="flame-stage" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="flame-orbit orbit-one" />
        <div className="flame-orbit orbit-two" />
        <div className="flame-label label-fuel"><span /> FUEL SPECIMEN</div>
        <div className="flame-label label-boundary"><span /> FLAME BOUNDARY</div>
        <div className="flame-label label-field"><span /> OXYGEN FIELD · UNMAPPED</div>
        {sceneReady
          ? <Suspense fallback={<div className="scene-loading">Preparing 3D scene…</div>}><FlameScene paused={paused} particles={particles} mode={mode} /></Suspense>
          : <div className="scene-loading">Preparing 3D scene…</div>}
        <div className="scale-mark"><span>VISUAL SCALE</span><i /></div>
      </motion.div>
      <div className="flame-controls" aria-label="Visualization controls">
        <button className="icon-button" onClick={() => setPaused((value) => !value)} aria-label={paused ? "Resume animation" : "Pause animation"}>
          {paused ? <Play size={15} /> : <Pause size={15} />}<span>{paused ? "Resume" : "Pause"}</span>
        </button>
        <button className={`icon-button ${particles ? "is-selected" : ""}`} onClick={() => setParticles((value) => !value)} aria-pressed={particles}>
          <Sparkles size={15} /><span>Particles</span>
        </button>
        <label className="viz-mode">MODE
          <select value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}>
            <option value="morphology">Morphology</option><option value="boundary">Boundary</option>
          </select>
        </label>
        <button className="icon-button" onClick={() => setResetKey((value) => value + 1)}>
          <RotateCcw size={15} /><span>Reset view</span>
        </button>
        <span className="drag-hint"><Maximize2 size={13} /> Drag to rotate · scroll to zoom</span>
      </div>
    </section>
  );
}

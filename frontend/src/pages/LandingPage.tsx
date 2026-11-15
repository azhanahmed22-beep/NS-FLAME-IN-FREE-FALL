import { motion } from "framer-motion";
import { ArrowDown, ArrowRight, Atom, Orbit } from "lucide-react";
import { Link } from "react-router-dom";
import FlameViz from "../components/FlameViz";

export default function LandingPage() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="brand-lockup">
          <span className="brand-mark"><Atom size={21} /></span>
          <span><strong>ZYNTARA</strong><small>FLAME IN FREEFALL</small></span>
        </Link>
        <div className="landing-links"><span>MISSION 01 / COMBUSTION SCIENCE</span><Link to="/app/overview">RESEARCH CONSOLE <ArrowRight size={14} /></Link></div>
      </header>
      <section className="hero">
        <div className="hero-grid" />
        <div className="hero-copy">
          <motion.div className="eyebrow hero-eyebrow" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <span className="live-dot" /> A MICROGRAVITY RESEARCH WORKSPACE
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.08 }}>
            FIRE BEHAVIOR.<br /><span>REIMAGINED</span><br />BEYOND EARTH.
          </motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.22 }}>
            Decoding combustion in microgravity through NASA research, scientific intelligence, and explainable AI.
          </motion.p>
          <motion.div className="hero-actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
            <Link to="/app/overview" className="primary-button">EXPLORE THE MISSION <ArrowRight size={15} /></Link>
            <Link to="/app/investigations" className="text-button">VIEW SCIENTIFIC DATA <ArrowDown size={14} /></Link>
          </motion.div>
          <div className="hero-footnote"><span>01</span><i /> RESEARCH INTERFACE · DATA AVAILABILITY DEPENDS ON API</div>
        </div>
        <div className="hero-visual">
          <div className="visual-orbit orbit-a" /><div className="visual-orbit orbit-b" />
          <div className="visual-crosshair crosshair-a" /><div className="visual-crosshair crosshair-b" />
          <div className="hero-flame"><FlameViz /></div>
          <div className="coordinate coord-top">FIELD STUDY / 001<br /><b>MICROGRAVITY</b></div>
          <div className="coordinate coord-bottom">VISUALIZATION<br /><b>ILLUSTRATIVE</b></div>
        </div>
        <div className="hero-scroll"><span>SCROLL TO EXPLORE</span><i /></div>
        <div className="hero-side-code">ZYNTARA / COMBUSTION SYSTEMS / 2026</div>
      </section>
      <section className="landing-below">
        <div className="section-index">01 — THE RESEARCH FRONTIER</div>
        <div className="below-grid">
          <h2>Combustion science<br /><span>without gravity’s assumptions.</span></h2>
          <div><p>Explore research datasets, compare measured behaviors, and inspect where evidence is available. ZYNTARA distinguishes source data from illustrative visualizations at every step.</p><Link to="/app/overview">ENTER RESEARCH WORKSPACE <ArrowRight size={14} /></Link></div>
        </div>
        <div className="mission-strip"><span><Orbit size={16} /> MICROGRAVITY ENVIRONMENTS</span><span><Atom size={16} /> COMBUSTION PHENOMENA</span><span>DATA PROVENANCE FIRST</span></div>
      </section>
      <footer className="landing-footer"><span>ZYNTARA / FLAME IN FREEFALL</span><span>Research interface · Not a certified safety assessment</span></footer>
    </div>
  );
}

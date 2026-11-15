import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity, Atom, BarChart3, BookOpen, ChevronDown, CircleHelp, Database,
  FlaskConical, Gauge, Layers3, Menu, MessageSquareText, Microscope, X,
} from "lucide-react";
import { useApiResource } from "../hooks/useApiResource";
import type { HealthResponse } from "../types/api";
import { LoadingState } from "../components/DataStates";

const links = [
  { to: "/app/overview", label: "Mission overview", icon: Gauge },
  { to: "/app/investigations", label: "Investigations", icon: BookOpen },
  { to: "/app/analytics", label: "Combustion analytics", icon: BarChart3 },
  { to: "/app/materials", label: "Material intelligence", icon: Layers3 },
  { to: "/app/smoke", label: "Smoke analysis", icon: Activity },
  { to: "/app/lab", label: "Microgravity lab", icon: FlaskConical },
  { to: "/app/assistant", label: "Research assistant", icon: MessageSquareText },
  { to: "/app/reports", label: "Reports", icon: Database },
  { to: "/app/about", label: "About ZYNTARA", icon: CircleHelp },
];

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const health = useApiResource<HealthResponse>("/health");
  const online = health.data?.status === "ok";

  return (
    <div className="workspace">
      <a className="skip-link" href="#workspace-main">Skip to research workspace</a>
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <span className="brand-mark"><Atom size={21} /></span>
          <span><strong>ZYNTARA</strong><small>FLAME IN FREEFALL</small></span>
          <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="nav-caption">RESEARCH WORKSPACE</div>
        <nav aria-label="Research workspace">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <Icon size={17} strokeWidth={1.7} /><span>{label}</span>
              {label === "Microgravity lab" && <span className="nav-new">3D</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="api-indicator">
            <span className={health.loading ? "status-dot pending" : online ? "status-dot" : "status-dot offline"} />
            <span>{health.loading ? "Checking API" : online ? "API connected" : "API unavailable"}</span>
            {health.loading && <LoadingState label=" " />}
          </div>
          <div className="sidebar-note"><Microscope size={15} /><span>Research interface<br />Experimental data only</span></div>
        </div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close menu" />}
      <div className="workspace-main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
          <div className="breadcrumb"><span>ZYNTARA</span><ChevronDown size={13} /><span>Research console</span></div>
          <div className="topbar-right">
            <span className="environment-pill"><span /> SCIENCE PREVIEW</span>
            <div className="topbar-divider" />
            <span className="avatar">ZR</span>
          </div>
        </header>
        <main id="workspace-main" className="page-content"><Outlet /></main>
      </div>
    </div>
  );
}

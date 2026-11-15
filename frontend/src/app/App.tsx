import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "../layout/AppLayout";
const LandingPage = lazy(() => import("../pages/LandingPage"));
const WorkspacePages = lazy(() => import("../pages/WorkspacePages"));

function NotFound() {
  return (
    <main className="fatal-error">
      <span className="eyebrow">404 / ROUTE NOT FOUND</span>
      <h1>This research path does not exist.</h1>
      <p>Use the mission landing page or workspace navigation to continue.</p>
      <a className="primary-button" href="/">RETURN TO MISSION</a>
    </main>
  );
}

export default function App() {
  return (
    <Suspense fallback={<div className="route-loading" role="status">Loading research interface…</div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path=":section" element={<WorkspacePages />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

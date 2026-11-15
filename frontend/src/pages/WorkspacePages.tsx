import { lazy, Suspense, useState } from "react";
import type { FormEvent } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Download, FileText, Info, Microscope, Send, ShieldAlert } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useApiResource } from "../hooks/useApiResource";
import { ApiFailure, postApi } from "../services/api";
import type { HealthResponse, MaterialRecord, ResearchAssistantResponse, SystemStatus } from "../types/api";
import type { DatasetRow } from "../types/api";
import { ErrorState, ResourceState } from "../components/DataStates";
import EndpointPanel from "../components/EndpointPanel";
import FlameViz from "../components/FlameViz";
const ScientificChart = lazy(() => import("../components/ScientificChart"));

const pages: Record<string, { title: string; kicker: string; description: string }> = {
  overview: { title: "Mission overview", kicker: "FLAME IN FREEFALL / RESEARCH CONSOLE", description: "A live view of data services and scientific evidence currently exposed by the connected backend." },
  investigations: { title: "NASA investigations", kicker: "SOURCE EXPLORER", description: "Browse investigations and source records returned by the research API." },
  analytics: { title: "Combustion analytics", kicker: "MEASUREMENTS / COMPARISON", description: "Scientific charts render only when measurement series are returned by the API." },
  materials: { title: "Material intelligence", kicker: "MATERIALS / EVIDENCE", description: "Compare evidence and coverage without implying a certified spacecraft safety assessment." },
  smoke: { title: "Smoke analysis", kicker: "PARTICULATE / DETECTION", description: "Inspect smoke measurements and provenance when the backend exposes them." },
  lab: { title: "Microgravity lab", kicker: "INTERACTIVE VISUALIZATION", description: "Explore a clearly labeled illustrative flame scene; it is not a validated physical simulation." },
  assistant: { title: "AI research assistant", kicker: "SCIENTIFIC QUERY / SOURCE-LED", description: "Research queries are sent to the configured backend. No generated answers are simulated in this interface." },
  reports: { title: "Research reports", kicker: "EXPORT / PROVENANCE", description: "Reports require real measurements and source metadata from the backend." },
  about: { title: "About ZYNTARA", kicker: "MISSION / LIMITATIONS", description: "A research interface focused on traceable evidence about combustion in microgravity." },
};

export default function WorkspacePages() {
  const location = useLocation();
  const section = location.pathname.split("/").filter(Boolean)[1] ?? "overview";
  const page = pages[section] ?? pages.overview;

  return (
    <motion.div className="page-enter" key={section} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>
      <div className="page-heading">
        <div><div className="eyebrow"><span className="live-dot" /> {page.kicker}</div><h1>{page.title}</h1><p>{page.description}</p></div>
        <div className="heading-stamp"><span>ZY / 01</span><i /><span>SCIENCE<br />INTERFACE</span></div>
      </div>
      {section === "overview" && <OverviewPage />}
      {section === "investigations" && <InvestigationsPage />}
      {section === "analytics" && <AnalyticsPage />}
      {section === "materials" && <MaterialsPage />}
      {section === "smoke" && <SmokePage />}
      {section === "lab" && <LabPage />}
      {section === "assistant" && <AssistantPage />}
      {section === "reports" && <ReportsPage />}
      {section === "about" && <AboutPage />}
    </motion.div>
  );
}

function OverviewPage() {
  const status = useApiResource<SystemStatus>("/api/v1/system/status");
  const health = useApiResource<HealthResponse>("/health");
  const metrics = [
    { label: "Investigations indexed", value: status.data?.investigations, foot: "Database count" },
    { label: "Datasets completed", value: status.data?.dataset_versions.completed, foot: "Ingestion status" },
    { label: "Ingestion issues", value: status.data?.ingestion_issues, foot: "Recorded by pipeline" },
  ];

  return (
    <>
      <section className="mission-banner">
        <div className="mission-symbol"><Microscope size={23} /></div>
        <div><span className="eyebrow">EVIDENCE STATUS</span><h2>Measure what the API can verify.</h2><p>Available indicators below are read live from the FastAPI service; unsupported modules remain clearly marked.</p></div>
        <div className="service-health"><span className={health.data?.status === "ok" ? "status-dot" : health.loading ? "status-dot pending" : "status-dot offline"} />{health.loading ? "CONNECTING" : health.data?.status === "ok" ? "API ONLINE" : "API OFFLINE"}</div>
      </section>
      {status.error && <ErrorState error={status.error} retry={status.reload} />}
      {status.loading && <div className="metric-grid">{metrics.map((metric) => <MetricCard key={metric.label} label={metric.label} value="…" foot={metric.foot} />)}</div>}
      {status.data && <div className="metric-grid">{metrics.map((metric) => <MetricCard key={metric.label} label={metric.label} value={metric.value ?? "—"} foot={metric.foot} />)}</div>}
      <div className="overview-grid">
        <section className="panel overview-panel">
          <div className="panel-heading"><div><span className="eyebrow">SERVICE TELEMETRY</span><h2>Data system status</h2></div><span className="live-label"><span className="status-dot" /> LIVE</span></div>
          <div className="status-list">
            <StatusRow label="API health endpoint" value={health.data?.status ?? (health.loading ? "Checking…" : "Unavailable")} />
            <StatusRow label="Database connection" value={status.data?.database ?? "Not reported"} />
            <StatusRow label="Dataset versions processing" value={status.data?.dataset_versions.processing ?? "Not reported"} />
            <StatusRow label="Dataset versions failed" value={status.data?.dataset_versions.failed ?? "Not reported"} />
          </div>
          <p className="panel-footnote">Health check and counters from <code>/health</code> and <code>/api/v1/system/status</code>.</p>
        </section>
        <section className="panel unavailable-panel">
          <div className="panel-heading"><div><span className="eyebrow">MODULE AVAILABILITY</span><h2>Research services</h2></div></div>
          <div className="module-row"><span>Investigation explorer</span><span>LIVE DATA</span></div>
          <div className="module-row"><span>Combustion analytics</span><span>LIVE DATA</span></div>
          <div className="module-row"><span>AI evidence assistant</span><span>LOCAL / GEMINI OPTIONAL</span></div>
          <Link className="panel-link" to="/app/investigations">Inspect data availability <ArrowRight size={14} /></Link>
        </section>
      </div>
      <div className="data-integrity"><Info size={16} /><span>Data integrity note</span><p>No experimental charts or NASA-derived totals are inferred on the client. A missing backend endpoint is not treated as an empty successful result.</p></div>
    </>
  );
}

function MetricCard({ label, value, foot }: { label: string; value: number | string; foot: string }) {
  return <div className="metric-card"><span className="metric-label">{label}</span><strong>{value}</strong><span className="metric-foot">{foot}</span></div>;
}

function StatusRow({ label, value }: { label: string; value: string | number }) {
  return <div className="status-row"><span>{label}</span><strong>{value}</strong></div>;
}

function InvestigationsPage() {
  return <EndpointPanel endpoint="/api/v1/investigations" title="Investigation registry" description="Searchable records, descriptions, source links, and availability are populated only from returned API records." />;
}

function AnalyticsPage() {
  return (
    <>
      <div className="notice-strip"><Info size={16} /><p>Charts use ingested records only. Derived summaries are labeled, and units are shown only when the source provides them.</p></div>
      <Suspense fallback={<div className="route-loading">Loading chart module…</div>}>
        <div className="chart-grid">
          <ScientificChart title="Flame behavior over time" endpoint="/api/v1/analytics/combustion" />
          <ScientificChart title="Mean smoke obscuration drop by material" endpoint="/api/v1/analytics/materials" />
          <ScientificChart title="PSI-115 NumDen by source gravity label" endpoint="/api/v1/analytics/microgravity" />
          <ScientificChart title="Stored records by completed dataset" endpoint="/api/v1/analytics/overview" />
        </div>
      </Suspense>
      <EndpointPanel endpoint="/api/v1/experiments" title="Experimental conditions" description="Experiment-level conditions and comparisons returned by the API." />
    </>
  );
}

function MaterialsPage() {
  return (
    <>
      <MaterialComparison />
      <Suspense fallback={<div className="route-loading">Loading chart module…</div>}><ScientificChart title="Mean derived smoke obscuration drop by material" endpoint="/api/v1/analytics/materials" /></Suspense>
      <section className="panel limitation-panel"><ShieldAlert size={18} /><div><strong>Research limitation</strong><p>The comparison uses available derived smoke summaries and discloses its evidence coverage. It is not a certified spacecraft material-safety assessment.</p></div><span className="not-ready">NOT A SAFETY RATING</span></section>
    </>
  );
}

function MaterialComparison() {
  const materials = useApiResource<MaterialRecord[]>("/api/v1/materials");
  const [selected, setSelected] = useState<string[]>([]);
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<ApiFailure | null>(null);
  const rows = Array.isArray(materials.data) ? materials.data : [];

  const compare = async () => {
    if (selected.length < 2 || pending) return;
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const response = await postApi<unknown>("/api/v1/ranking/materials", { materials: selected });
      setResult(typeof response === "string" ? response : JSON.stringify(response, null, 2));
    } catch (cause) {
      setError(cause instanceof ApiFailure ? cause : new ApiFailure("Material ranking request failed.", "request-failed"));
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="panel data-panel material-compare">
      <div className="panel-heading"><div><span className="eyebrow">MATERIAL EVIDENCE</span><h2>Compare supported materials</h2><p>Select at least two records returned by the materials endpoint.</p></div><span className="endpoint-chip">GET /api/v1/materials</span></div>
      <ResourceState resource={materials} />
      {materials.data !== null && !Array.isArray(materials.data) && !materials.error && <div className="state-box error-state" role="alert">The API returned an unexpected material list format.</div>}
      {materials.data && rows.length === 0 && !materials.error && <div className="state-box">No material records are available for comparison.</div>}
      {rows.length > 0 && (
        <>
          <label className="material-select">MATERIALS
            <select multiple size={Math.min(5, rows.length)} value={selected} onChange={(event) => setSelected(Array.from(event.target.selectedOptions, (option) => option.value))}>
              {rows.map((material) => <option key={material.id} value={material.name}>{material.name}{material.category ? ` · ${material.category}` : ""}</option>)}
            </select>
          </label>
          <div className="compare-actions"><button className="primary-button" onClick={() => void compare()} disabled={selected.length < 2 || pending}>{pending ? "REQUESTING…" : "REQUEST EVIDENCE COMPARISON"} <ArrowRight size={14} /></button><span>Ranking is not safety certification.</span></div>
          {error && <ErrorState error={error} retry={() => void compare()} />}
          {result && <pre className="answer-output">{result}</pre>}
          <div className="panel-footnote">Comparison is requested from <code>POST /api/v1/ranking/materials</code>. No values are inferred by the interface.</div>
        </>
      )}
    </section>
  );
}

function SmokePage() {
  return (
    <>
      <Suspense fallback={<div className="route-loading">Loading chart module…</div>}><ScientificChart title="Derived obscuration drop by test" endpoint="/api/v1/analytics/smoke" /></Suspense>
      <EndpointPanel endpoint="/api/v1/datasets" title="Smoke data coverage" description="Dataset registry records, provenance, and availability returned by the backend." />
      <div className="data-integrity"><Info size={16} /><span>Measurement scope</span><p>Smoke response fields, units, and source references will be displayed as received; no units or values are assumed.</p></div>
    </>
  );
}

function LabPage() {
  return <><FlameViz /><div className="lab-caption"><span className="sim-tag">SIMULATED VISUALIZATION</span><p>Illustrative rendering for interface exploration only. It is not experimental footage, temperature measurement, or a validated physical combustion model.</p></div></>;
}

function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [operation, setOperation] = useState<"analyze" | "compare" | "research-summary">("analyze");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<ResearchAssistantResponse | null>(null);
  const [failure, setFailure] = useState<ApiFailure | null>(null);
  const [submittedPrompt, setSubmittedPrompt] = useState("");

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const prompt = question.trim();
    if (!prompt || pending) return;
    setPending(true);
    setFailure(null);
    setResult(null);
    setSubmittedPrompt(prompt);
    const path = `/api/v1/ai/${operation}`;
    try {
      const data = await postApi<ResearchAssistantResponse>(path, { question: prompt });
      setResult(data);
    } catch (error) {
      setFailure(error instanceof ApiFailure ? error : new ApiFailure(`Request failed for ${path}.`, "request-failed"));
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="assistant-layout">
      <div className="assistant-context"><span className="eyebrow">SOURCE-FIRST MODE</span><h2>Ask a research question.</h2><p>Questions use the ingested evidence. Gemini is optional; without a key, the assistant returns a local evidence summary.</p>
        <div className="assistant-prompts"><span>EXAMPLE QUESTIONS</span><button onClick={() => setQuestion("Compare flame extinction behavior in available experiments.")}>Compare flame extinction behavior in available experiments.</button><button onClick={() => setQuestion("Summarize available smoke detection measurements.")}>Summarize available smoke detection measurements.</button></div>
        <div className="context-warning"><ShieldAlert size={17} /><span>Scientific output requires cited sources and disclosed uncertainty.</span></div>
      </div>
      <div className="assistant-main">
        <div className="assistant-header"><span className="assistant-light" /> RESEARCH ASSISTANT <span className="endpoint-chip">SOURCE-GROUNDED API</span></div>
        <div className="assistant-transcript" aria-live="polite">
          {!submittedPrompt && <div className="assistant-empty"><MessageGlyph /><strong>Ready for a source-grounded query</strong><span>No conversation history is fabricated.</span></div>}
          {submittedPrompt && <div className="prompt-message"><span>YOUR QUERY</span><p>{submittedPrompt}</p></div>}
          {pending && <div className="state-box"><span className="assistant-light" /> Sending request to research service…</div>}
          {failure && <ErrorState error={failure} retry={() => {
            const form = document.getElementById("assistant-form");
            if (form instanceof HTMLFormElement) form.requestSubmit();
          }} />}
          {result && <div className="assistant-answer">
            <span className="assistant-answer-provider">{result.provider === "gemini" ? "GEMINI RESPONSE" : "LOCAL EVIDENCE SUMMARY"}</span>
            <p>{result.answer}</p>
            {result.provider === "local-evidence" && <p className="assistant-setup-note">To enable Gemini-generated answers, add GEMINI_API_KEY to backend/.env and restart the backend.</p>}
            {result.warning && <p className="assistant-warning">{result.warning}</p>}
            {result.sources.length > 0 && <details className="assistant-sources">
              <summary>Sources ({result.sources.length})</summary>
              <ul>{result.sources.map((source) => <li key={`${source.psi_id}:${source.filename}`}>
                <span>{source.psi_id} · {source.filename}</span>
                <span>{source.is_derived ? "DERIVED" : "SOURCE FILE"}</span>
              </li>)}</ul>
            </details>}
          </div>}
        </div>
        <form id="assistant-form" className="assistant-form" onSubmit={(event) => void submit(event)}>
          <label className="select-operation">REQUEST TYPE
            <select value={operation} onChange={(event) => setOperation(event.target.value as typeof operation)}>
              <option value="analyze">Analyze</option><option value="compare">Compare</option><option value="research-summary">Research summary</option>
            </select>
          </label>
          <div className="assistant-input"><label className="sr-only" htmlFor="research-question">Ask about available research</label><textarea id="research-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about available research…" rows={2} />
            <button type="submit" className="send-button" disabled={!question.trim() || pending} aria-label="Send research question"><Send size={17} /></button>
          </div>
          <span className="assistant-disclaimer">Answers depend on backend availability, source coverage, and model limitations.</span>
        </form>
      </div>
    </section>
  );
}

function MessageGlyph() {
  return <div className="message-glyph"><FileText size={22} /></div>;
}

function ReportsPage() {
  const overview = useApiResource<DatasetRow[]>("/api/v1/datasets");
  return (
    <section className="panel reports-panel">
      <div className="panel-heading"><div><span className="eyebrow">EXPORT CENTER</span><h2>Dataset provenance export</h2><p>Download the ingested dataset registry and provenance fields.</p></div><FileText size={21} /></div>
      <ResourceState resource={overview} emptyLabel="No report data returned by the backend." />
      {overview.data && overview.data.length > 0 && <button className="primary-button" onClick={() => downloadCsv(overview.data ?? [])}><Download size={15} /> DOWNLOAD CSV</button>}
      {overview.data?.length === 0 && <button className="primary-button" disabled title="No records are available to export"><Download size={15} /> NO DATA TO EXPORT</button>}
      <p className="panel-footnote">CSV contains only fields returned by <code>/api/v1/datasets</code>; local filesystem paths are not exposed.</p>
    </section>
  );
}

function downloadCsv(rows: DatasetRow[]) {
  if (!rows.length) return;
  const columns = Object.keys(rows[0]);
  const escape = (value: unknown) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const csv = [columns.map(escape).join(","), ...rows.map((row) => columns.map((column) => escape(row[column])).join(","))].join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "zyntara-api-report.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}

function AboutPage() {
  return (
    <div className="about-grid">
      <section className="panel about-mission"><span className="eyebrow">MISSION STATEMENT</span><h2>Fire behavior.<br /><span>Reimagined beyond Earth.</span></h2><p>ZYNTARA is a research interface for investigating combustion behavior in microgravity. It prioritizes provenance, measurable evidence, and transparent limitations.</p></section>
      <section className="panel"><span className="eyebrow">EVIDENCE RULES</span><div className="rule-list"><StatusRow label="Measurements" value="Backend only" /><StatusRow label="Visualization" value="Clearly labeled illustrative" /><StatusRow label="Missing route" value="Shown as unavailable" /><StatusRow label="Safety ranking" value="Not certified" /></div></section>
      <section className="panel about-links"><span className="eyebrow">EXPLORE THE WORKSPACE</span><Link to="/app/investigations">Investigation data <ArrowRight size={14} /></Link><Link to="/app/analytics">Scientific analytics <ArrowRight size={14} /></Link><Link to="/app/lab">Microgravity visualization <ArrowRight size={14} /></Link></section>
      <section className="panel about-note"><Info size={17} /><p>Workspace APIs use the ingested records and preserve measured, simulated, and derived labels. Gemini-generated responses require a key configured in the backend environment; without it, the assistant reports local evidence availability. No output is a certified spacecraft material-safety assessment.</p></section>
    </div>
  );
}

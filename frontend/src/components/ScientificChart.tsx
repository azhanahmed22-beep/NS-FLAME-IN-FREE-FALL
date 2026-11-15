import { useRef } from "react";
import { Brush, Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download } from "lucide-react";
import { useApiResource } from "../hooks/useApiResource";
import type { ChartResponse } from "../types/api";
import { ResourceState } from "./DataStates";

export default function ScientificChart({ title, endpoint }: { title: string; endpoint: string }) {
  const resource = useApiResource<ChartResponse>(endpoint);
  const chartRef = useRef<HTMLDivElement>(null);
  const points = Array.isArray(resource.data?.points) ? resource.data.points : [];
  const validPoints = points.filter((point) =>
    typeof point.label === "string" && Number.isFinite(point.value),
  );

  const downloadCsv = () => {
    if (!validPoints.length) return;
    const csv = ["label,value", ...validPoints.map((point) => `"${point.label.replaceAll('"', '""')}",${point.value}`)].join("\r\n");
    downloadFile(csv, "text/csv;charset=utf-8", "zyntara-chart-data.csv");
  };

  const downloadSvg = () => {
    const svg = chartRef.current?.querySelector("svg");
    if (!svg) return;
    downloadFile(new XMLSerializer().serializeToString(svg), "image/svg+xml;charset=utf-8", "zyntara-chart.svg");
  };

  return (
    <section className="panel chart-panel">
      <div className="panel-heading compact">
        <div><span className="eyebrow">API DATA</span><h3>{title}</h3></div>
        {resource.data?.unit && <span className="unit-tag">{resource.data.unit}</span>}
      </div>
      {validPoints.length > 0 && <div className="chart-actions">
        <button className="quiet-button" onClick={downloadCsv}><Download size={13} /> CSV</button>
        <button className="quiet-button" onClick={downloadSvg}><Download size={13} /> SVG</button>
      </div>}
      <div className="chart-area" ref={chartRef}>
        <ResourceState resource={resource} emptyLabel="This endpoint returned no measurements." />
        {validPoints && validPoints.length > 0 && (
          <>
            <p className="sr-only">Line chart showing {validPoints.length} data points. Source: {resource.data?.source ?? "not provided"}.</p>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={validPoints} margin={{ top: 10, right: 12, bottom: validPoints.length > 12 ? 22 : 4, left: 0 }}>
                <CartesianGrid stroke="#253447" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: "#8292a7", fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: "#8292a7", fontSize: 10 }} tickLine={false} axisLine={false} width={44} label={resource.data?.unit ? { value: resource.data.unit, angle: -90, position: "insideLeft", fill: "#8292a7", fontSize: 9 } : undefined} />
                <Tooltip contentStyle={{ background: "#0d1724", border: "1px solid #29394c", borderRadius: 4 }} />
                <Line type="monotone" dataKey="value" stroke="#52d9ef" strokeWidth={2} dot={{ r: 2, fill: "#52d9ef" }} />
                {validPoints.length > 12 && <Brush dataKey="label" height={18} travellerWidth={8} stroke="#42d9f5" fill="#101927" />}
              </LineChart>
            </ResponsiveContainer>
            {resource.data?.source && <p className="chart-source">Source: {resource.data.source}</p>}
          </>
        )}
        {!resource.loading && !resource.error && resource.data && !Array.isArray(resource.data.points) && (
          <div className="state-box error-state" role="alert">The API returned an unexpected chart format; a points list was expected.</div>
        )}
        {!resource.loading && !resource.error && resource.data && Array.isArray(resource.data.points) && validPoints.length === 0 && (
          <div className="state-box">This endpoint returned no valid measurements.</div>
        )}
      </div>
    </section>
  );
}

function downloadFile(contents: string, type: string, filename: string) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

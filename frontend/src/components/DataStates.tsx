import { AlertCircle, LoaderCircle, RefreshCw, WifiOff } from "lucide-react";
import type { ApiResource } from "../hooks/useApiResource";
import type { DatasetRow } from "../types/api";

export function LoadingState({ label = "Loading research data" }: { label?: string }) {
  return <div className="state-box" role="status"><LoaderCircle className="spin" size={18} /><span>{label}…</span></div>;
}

export function ErrorState({ error, retry }: { error: Error; retry: () => void }) {
  const isOffline = "kind" in error && error.kind === "offline";
  return (
    <div className="state-box error-state" role="alert">
      {isOffline ? <WifiOff size={18} /> : <AlertCircle size={18} />}
      <div><strong>{isOffline ? "API connection unavailable" : "Data request unavailable"}</strong><p>{error.message}</p></div>
      <button className="quiet-button" onClick={retry}><RefreshCw size={14} /> Retry</button>
    </div>
  );
}

export function ResourceState<T>({ resource, emptyLabel = "No records returned by this endpoint." }: {
  resource: ApiResource<T>;
  emptyLabel?: string;
}) {
  if (resource.loading) return <LoadingState />;
  if (resource.error) return <ErrorState error={resource.error} retry={resource.reload} />;
  if (resource.data === null) return <div className="state-box">{emptyLabel}</div>;
  return null;
}

export function DataTable({ rows }: { rows: DatasetRow[] }) {
  if (rows.length === 0) return <div className="state-box">No records returned by this endpoint.</div>;
  const columns = Object.keys(rows[0] ?? {});
  return (
    <div className="table-scroll">
      <table>
        <thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr></thead>
        <tbody>{rows.map((row, index) => (
          <tr key={String(row.id ?? index)}>{columns.map((column) => <td key={column}>{formatValue(row[column])}</td>)}</tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

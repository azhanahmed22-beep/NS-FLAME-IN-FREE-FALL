import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useApiResource } from "../hooks/useApiResource";
import type { DatasetRow } from "../types/api";
import { DataTable, ResourceState } from "./DataStates";

interface EndpointPanelProps {
  endpoint: string;
  title: string;
  description: string;
}

export default function EndpointPanel({ endpoint, title, description }: EndpointPanelProps) {
  const resource = useApiResource<DatasetRow[]>(endpoint);
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [filterBy, setFilterBy] = useState("");
  const [filterValue, setFilterValue] = useState("");
  const rows = Array.isArray(resource.data) ? resource.data : null;
  const columns = rows?.length ? Object.keys(rows[0]) : [];
  const filterOptions = useMemo(() => {
    if (!rows || !filterBy) return [];
    return Array.from(new Set(rows.map((row) => String(row[filterBy] ?? "—")))).sort();
  }, [rows, filterBy]);
  const filtered = useMemo(() => {
    if (!rows) return [];
    const term = query.trim().toLowerCase();
    return rows
      .filter((row) => JSON.stringify(row).toLowerCase().includes(term))
      .filter((row) => !filterBy || !filterValue || String(row[filterBy] ?? "—") === filterValue)
      .slice()
      .sort((left, right) => {
        if (!sortBy) return 0;
        const leftValue = String(left[sortBy] ?? "");
        const rightValue = String(right[sortBy] ?? "");
        return leftValue.localeCompare(rightValue, undefined, { numeric: true, sensitivity: "base" });
      });
  }, [rows, query, filterBy, filterValue, sortBy]);

  return (
    <section className="panel data-panel">
      <div className="panel-heading">
        <div><span className="eyebrow">BACKEND DATA</span><h2>{title}</h2><p>{description}</p></div>
        <span className="endpoint-chip">{endpoint}</span>
      </div>
      <ResourceState resource={resource} />
      {rows && !resource.error && rows.length > 0 && (
        <div className="data-controls">
          <label className="search-field">
            <Search size={16} /><span className="sr-only">Search records</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search returned records" />
          </label>
          <label className="filter-field">FILTER
            <select value={filterBy} onChange={(event) => { setFilterBy(event.target.value); setFilterValue(""); }}>
              <option value="">All fields</option>{columns.map((column) => <option key={column} value={column}>{column.replaceAll("_", " ")}</option>)}
            </select>
            {filterBy && <select aria-label={`Filter by ${filterBy}`} value={filterValue} onChange={(event) => setFilterValue(event.target.value)}>
              <option value="">All values</option>{filterOptions.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>}
          </label>
          <label className="filter-field">SORT
            <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="">API order</option>{columns.map((column) => <option key={column} value={column}>{column.replaceAll("_", " ")}</option>)}
            </select>
          </label>
        </div>
      )}
      {resource.data !== null && !Array.isArray(resource.data) && !resource.error && (
        <div className="state-box error-state" role="alert">The API returned an unexpected response shape; a record list was expected.</div>
      )}
      {rows && !resource.error && <DataTable rows={filtered} />}
      <p className="panel-footnote">Only values returned by the connected API appear here. Missing routes are reported without sample data.</p>
    </section>
  );
}

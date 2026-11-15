export interface HealthResponse {
  status: string;
}

export interface SystemStatus {
  database: string;
  investigations: number | null;
  dataset_versions: {
    completed: number | null;
    failed: number | null;
    processing: number | null;
  };
  ingestion_issues: number | null;
}

export interface Investigation {
  id: number;
  psi_id: string;
  acronym: string | null;
  title: string | null;
  research_area: string | null;
  doi: string | null;
  page_url: string | null;
  availability_status: string;
}

export interface MaterialRecord {
  id: number;
  name: string;
  category?: string | null;
}

export interface DatasetRow {
  [key: string]: unknown;
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface ChartResponse {
  points: ChartPoint[];
  unit?: string;
  source?: string;
}

export interface ResearchAssistantSource {
  psi_id: string;
  filename: string;
  is_derived: boolean;
  status: string;
}

export interface ResearchAssistantResponse {
  provider: "gemini" | "local-evidence";
  operation: string;
  answer: string;
  sources: ResearchAssistantSource[];
  warning: string | null;
}

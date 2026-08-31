// Mirrors backend/state/schema.py and backend/models/enums.py — keep in sync
// by hand; there is no shared codegen between the two in this project.
// See anchor.md/ARCHITECTURE.md > API STRUCTURE for the SSE event envelope.

export type VentureStatus = "draft" | "running" | "completed" | "failed";

export type AgentName =
  | "planner"
  | "market_research"
  | "competitor"
  | "customer"
  | "financial_risk"
  | "executive_decision"
  | "report_generator";

export type AgentRunStatus = "pending" | "running" | "completed" | "failed";

export type FindingCategory =
  | "market"
  | "competitor"
  | "customer"
  | "financial"
  | "marketing"
  | "risk";

export type FindingSourceType = "tavily" | "firecrawl" | "llm";

// Mirrors backend/state/schema.py::ResearchFinding
export interface ResearchFinding {
  category: FindingCategory;
  source_type: FindingSourceType;
  source_url: string | null;
  title: string | null;
  content: string;
}

// Mirrors backend/state/schema.py::VentureState
export interface VentureState {
  venture_id: string;
  title: string;
  one_liner: string;
  description: string;
  target_market: string | null;
  industry: string | null;

  research_plan: string | null;
  iteration_count: number;

  market_findings: ResearchFinding[];
  competitor_findings: ResearchFinding[];
  customer_findings: ResearchFinding[];
  financial_findings: ResearchFinding[];
  marketing_findings: ResearchFinding[];
  risk_findings: ResearchFinding[];

  venture_score: number | null;
  decision_feedback: string | null;

  summary: string | null;
  sections: Record<string, string>;
  recommendations: string[];

  error: string | null;
}

// One SSE event streamed from GET /api/v1/ventures/{id}/validate — see
// anchor.md/ARCHITECTURE.md > API STRUCTURE. `state_delta` carries only the
// VentureState fields that changed in this step, not the full state.
// "workflow"/"failed" is a sentinel the backend sends when the run itself
// throws (not a real agent) — state_delta then carries {"error": string}.
export interface VentureStreamEvent {
  agent: AgentName | "workflow";
  status: AgentRunStatus;
  state_delta: Partial<VentureState> & { error?: string };
}

// --- REST API shapes (backend/api/v1/ventures.py) ---
// Distinct from VentureState above: these mirror the DB row (Venture/Report
// ORM models via their Pydantic response models), not the LangGraph state.

// Mirrors backend/api/v1/ventures.py::VentureResponse
export interface VentureRecord {
  id: string;
  title: string;
  one_liner: string;
  description: string;
  target_market: string | null;
  industry: string | null;
  status: VentureStatus;
  venture_score: number | null;
  iteration_count: number;
  created_at: string;
  updated_at: string;
}

// Mirrors backend/api/v1/ventures.py::FindingResponse
export interface FindingRecord {
  id: string;
  category: FindingCategory;
  source_type: FindingSourceType;
  source_url: string | null;
  title: string | null;
  content: string;
  created_at: string;
}

// Mirrors backend/api/v1/ventures.py::ReportResponse
export interface VentureReport {
  id: string;
  venture_id: string;
  version: number;
  venture_score: number;
  summary: string;
  sections: Record<string, string>;
  recommendations: string[];
  created_at: string;
  findings: Record<string, FindingRecord[]>;
}

// Mirrors backend/api/v1/ventures.py::VentureCreateRequest
export interface VentureCreateInput {
  title: string;
  one_liner: string;
  description: string;
  target_market?: string;
  industry?: string;
}

// Mirrors backend/utils/responses.py's standard envelope
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  message: string | null;
}

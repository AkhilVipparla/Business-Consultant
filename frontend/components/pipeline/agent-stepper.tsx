// Agent Pipeline Stepper — see anchor.md/UI_UX_GUIDELINES.md > Component Patterns.
//
// Simplification: shows each agent's latest known status only (Pending /
// Running / Completed / Failed) — does not show the "iteration N" badge
// UI_UX_GUIDELINES.md describes for loop-back passes, since the SSE payload
// doesn't currently carry a per-event iteration number for every agent (only
// the Executive Decision Agent's own event includes iteration_count). Worth
// revisiting if the backend starts including it on every event.

import type { AgentName, AgentRunStatus } from "@/types/venture";

const STEP_ORDER: { key: AgentName; label: string }[] = [
  { key: "planner", label: "Planner" },
  { key: "market_research", label: "Market Research" },
  { key: "competitor", label: "Competitor" },
  { key: "customer", label: "Customer" },
  { key: "financial_risk", label: "Financial/Risk" },
  { key: "executive_decision", label: "Executive Decision" },
  { key: "report_generator", label: "Report Generator" },
];

interface AgentStepperProps {
  steps: Partial<Record<AgentName, AgentRunStatus>>;
}

function statusClasses(status: AgentRunStatus | undefined): string {
  switch (status) {
    case "running":
      return "border-terracotta text-terracotta animate-pulse";
    case "completed":
      return "border-olive bg-olive text-cream";
    case "failed":
      return "border-error bg-error text-cream";
    default:
      return "border-border text-muted";
  }
}

export function AgentStepper({ steps }: AgentStepperProps) {
  return (
    <ol className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-3">
      {STEP_ORDER.map(({ key, label }) => {
        const status = steps[key];
        return (
          <li
            key={key}
            className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${statusClasses(status)}`}
          >
            {status === "completed" ? <span aria-hidden>✓</span> : null}
            {status === "failed" ? <span aria-hidden>✕</span> : null}
            {label}
          </li>
        );
      })}
    </ol>
  );
}

"use client";

import { useParams } from "next/navigation";

import { AgentStepper } from "@/components/pipeline/agent-stepper";
import { ScoreBadge } from "@/components/report/score-badge";
import { SectionCard } from "@/components/report/section-card";
import { useVentureStream } from "@/hooks/useVentureStream";
import type { ResearchFinding, VentureState } from "@/types/venture";

// Fixed display order for the 6 categories per anchor.md/DECISIONS.md
// Decision 011 — matches backend/models/enums.py::FindingCategory, and the
// report dashboard's own SECTION_ORDER (app/ventures/[id]/report/page.tsx).
const SECTION_ORDER = ["market", "competitor", "customer", "financial", "marketing", "risk"];

// Maps a display category to the VentureState field the live stream
// accumulates its findings into (state/schema.py field names).
const FINDINGS_FIELD: Record<string, keyof VentureState> = {
  market: "market_findings",
  competitor: "competitor_findings",
  customer: "customer_findings",
  financial: "financial_findings",
  marketing: "marketing_findings",
  risk: "risk_findings",
};

// Client Component — needs the browser's EventSource API, unlike the report
// dashboard (a Server Component, since it's just a one-time data fetch).
export default function VenturePipelinePage() {
  const params = useParams<{ id: string }>();
  const ventureId = params.id;

  const { steps, state, isDone, error } = useVentureStream(ventureId);

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-heading text-3xl font-bold text-charcoal">
        {isDone && !error ? "Validation complete" : "Validating your idea…"}
      </h1>
      <p className="mt-2 text-muted">
        VentureMind AI is researching this venture live. This page updates in real time.
      </p>

      <div className="mt-8">
        <AgentStepper steps={steps} />
      </div>

      {error ? (
        <p role="alert" className="mt-6 text-sm text-error">
          {error}
        </p>
      ) : null}

      {isDone && !error ? (
        <div className="mt-8 space-y-4">
          {state.venture_score != null ? <ScoreBadge score={state.venture_score} /> : null}

          {state.summary ? <p className="text-lg text-charcoal">{state.summary}</p> : null}

          <div className="space-y-4">
            {SECTION_ORDER.filter((category) => state.sections?.[category]).map((category) => (
              <SectionCard
                key={category}
                category={category}
                narrative={state.sections![category]}
                findings={(state[FINDINGS_FIELD[category]] as ResearchFinding[] | undefined) ?? []}
              />
            ))}
          </div>

          {state.recommendations && state.recommendations.length > 0 ? (
            <div className="rounded-md border border-border bg-surface p-6">
              <h3 className="font-heading text-xl font-semibold text-charcoal">Recommendations</h3>
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-charcoal">
                {state.recommendations.map((recommendation) => (
                  <li key={recommendation}>{recommendation}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}

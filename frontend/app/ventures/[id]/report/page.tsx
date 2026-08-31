import { notFound } from "next/navigation";

import { ScoreBadge } from "@/components/report/score-badge";
import { SectionCard } from "@/components/report/section-card";
import { getVenture, getVentureReport } from "@/lib/api";

// Fixed display order for the 6 categories per anchor.md/DECISIONS.md
// Decision 011 — matches backend/models/enums.py::FindingCategory.
const SECTION_ORDER = ["market", "competitor", "customer", "financial", "marketing", "risk"];

// Server Component: data is fetched at request time, not client-side, so
// the report is part of the initial HTML rather than behind a loading spinner.
export default async function VentureReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const [venture, report] = await Promise.all([getVenture(id), getVentureReport(id)]).catch(
    () => {
      notFound();
    },
  );

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-heading text-3xl font-bold text-charcoal">{venture.title}</h1>
      <p className="mt-2 text-muted">{venture.one_liner}</p>

      <div className="mt-6">
        <ScoreBadge score={report.venture_score} />
      </div>

      <p className="mt-6 text-lg text-charcoal">{report.summary}</p>

      <div className="mt-8 space-y-4">
        {SECTION_ORDER.filter((category) => report.sections[category]).map((category) => (
          <SectionCard
            key={category}
            category={category}
            narrative={report.sections[category]}
            findings={report.findings[category] ?? []}
          />
        ))}
      </div>

      {report.recommendations.length > 0 ? (
        <div className="mt-8 rounded-md border border-border bg-surface p-6">
          <h3 className="font-heading text-xl font-semibold text-charcoal">Recommendations</h3>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-charcoal">
            {report.recommendations.map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </main>
  );
}

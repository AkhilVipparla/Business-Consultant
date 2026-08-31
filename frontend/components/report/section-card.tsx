// Accepts both the persisted-report shape (FindingRecord, with an id/
// created_at from the DB) and the raw live-stream shape (ResearchFinding,
// which doesn't have those yet since it hasn't been persisted) — only
// source_url/title are actually rendered here.
interface FindingLike {
  source_url: string | null;
  title: string | null;
}

interface SectionCardProps {
  category: string;
  narrative: string;
  findings: FindingLike[];
}

const CATEGORY_LABELS: Record<string, string> = {
  market: "Market",
  competitor: "Competitor",
  customer: "Customer",
  financial: "Financial",
  marketing: "Marketing",
  risk: "Risk",
};

export function SectionCard({ category, narrative, findings }: SectionCardProps) {
  return (
    <div className="rounded-md border border-border bg-surface p-6">
      <h3 className="font-heading text-xl font-semibold text-charcoal">
        {CATEGORY_LABELS[category] ?? category}
      </h3>
      <p className="mt-2 text-charcoal">{narrative}</p>

      {findings.length > 0 ? (
        <div className="mt-4 border-t border-border pt-4">
          <p className="text-sm font-medium text-muted">Sources</p>
          <ul className="mt-2 space-y-1.5">
            {findings.map((finding, index) => (
              <li key={`${index}-${finding.source_url ?? finding.title ?? "source"}`} className="text-sm">
                {finding.source_url ? (
                  <a
                    href={finding.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-terracotta underline hover:no-underline"
                  >
                    {finding.title || finding.source_url}
                  </a>
                ) : (
                  <span className="text-muted">{finding.title || "Untitled source"}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

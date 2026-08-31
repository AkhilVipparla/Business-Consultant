// Venture Score Badge — see anchor.md/UI_UX_GUIDELINES.md > Component Patterns.

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "lg";
}

function scoreTier(score: number): { label: string; colorClass: string } {
  if (score >= 70) return { label: "Strong", colorClass: "bg-olive/15 text-olive" };
  if (score >= 40) return { label: "Promising", colorClass: "bg-warning/15 text-warning" };
  return { label: "Needs Work", colorClass: "bg-error/15 text-error" };
}

export function ScoreBadge({ score, size = "lg" }: ScoreBadgeProps) {
  const { label, colorClass } = scoreTier(score);
  const sizeClass = size === "lg" ? "px-5 py-2 text-2xl" : "px-3 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full font-semibold ${sizeClass} ${colorClass}`}
    >
      {Math.round(score)}
      <span className="font-medium">{label}</span>
    </span>
  );
}

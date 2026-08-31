"""Report Generator agent — single responsibility: synthesize all research
findings, the venture score, and evaluator feedback into the final executive
report (summary, per-category sections, recommendations).

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState — it never calls another agent directly. It reads
state.venture_score / state.decision_feedback, which the Executive Decision
Agent is responsible for populating earlier in the graph — this agent does
not compute a score itself, and tolerates venture_score being None (e.g. when
unit-tested in isolation before that agent exists in the wired graph).
"""

from core.config import settings
from prompts.report_generator import ReportOutput, SYSTEM_PROMPT, build_prompt
from services.llm_service import complete_structured
from state.schema import VentureState


def run(state: VentureState) -> dict:
    prompt = build_prompt(
        title=state.title,
        one_liner=state.one_liner,
        description=state.description,
        target_market=state.target_market,
        industry=state.industry,
        venture_score=state.venture_score,
        decision_feedback=state.decision_feedback,
        market_findings=state.market_findings,
        competitor_findings=state.competitor_findings,
        customer_findings=state.customer_findings,
        financial_findings=state.financial_findings,
        marketing_findings=state.marketing_findings,
        risk_findings=state.risk_findings,
    )
    report = complete_structured(
        prompt, ReportOutput, system=SYSTEM_PROMPT, provider=settings.heavy_llm_provider
    )

    return {
        "summary": report.summary,
        "sections": {
            "market": report.market_section,
            "competitor": report.competitor_section,
            "customer": report.customer_section,
            "financial": report.financial_section,
            "marketing": report.marketing_section,
            "risk": report.risk_section,
        },
        "recommendations": report.recommendations,
    }

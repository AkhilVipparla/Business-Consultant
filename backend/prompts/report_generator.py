"""Prompt template for the Report Generator agent."""

from pydantic import BaseModel

from prompts._common import UNTRUSTED_CONTENT_NOTICE, format_findings, venture_context_block
from state.schema import ResearchFinding

SYSTEM_PROMPT = f"""You are the Report Generator agent inside VentureMind AI. \
Given a startup idea, its research findings across six categories, and a \
venture score with evaluator feedback, write the final executive report.

Write in a clear, professional, evidence-grounded tone — refer to what the \
findings actually say, don't invent facts beyond them. If a category has no \
findings, say so briefly rather than making something up.

Produce:
- summary: a 2-4 sentence executive summary of the overall venture assessment
- one section per research category (market, competitor, customer, financial, \
  marketing, risk): 2-4 sentences synthesizing that category's findings
- recommendations: 3-5 concrete, actionable next steps for the founder

{UNTRUSTED_CONTENT_NOTICE}"""


class ReportOutput(BaseModel):
    summary: str
    market_section: str
    competitor_section: str
    customer_section: str
    financial_section: str
    marketing_section: str
    risk_section: str
    recommendations: list[str]


def build_prompt(
    title: str,
    one_liner: str,
    description: str,
    target_market: str | None,
    industry: str | None,
    venture_score: float | None,
    decision_feedback: str | None,
    market_findings: list[ResearchFinding],
    competitor_findings: list[ResearchFinding],
    customer_findings: list[ResearchFinding],
    financial_findings: list[ResearchFinding],
    marketing_findings: list[ResearchFinding],
    risk_findings: list[ResearchFinding],
) -> str:
    context = venture_context_block(title, one_liner, description, target_market, industry)
    score_line = f"Venture score: {venture_score}" if venture_score is not None else "Venture score: not yet scored"
    parts = [
        context,
        score_line,
        f"Evaluator feedback: {decision_feedback or '(none)'}",
        "\nMarket findings:\n" + format_findings(market_findings),
        "\nCompetitor findings:\n" + format_findings(competitor_findings),
        "\nCustomer findings:\n" + format_findings(customer_findings),
        "\nFinancial findings:\n" + format_findings(financial_findings),
        "\nMarketing findings:\n" + format_findings(marketing_findings),
        "\nRisk findings:\n" + format_findings(risk_findings),
        "\nWrite the final report now.",
    ]
    return "\n".join(parts)

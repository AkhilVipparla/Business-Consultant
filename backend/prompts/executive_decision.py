"""Prompt template for the Executive Decision Agent.

Per anchor.md/DECISIONS.md Decision 011/012: this agent scores the venture
and writes feedback; the ROUTING decision (loop back or proceed) is
deterministic Python logic in graph/workflow.py, not something the LLM
decides — keeps that control flow predictable and testable.
"""

from pydantic import BaseModel, Field

from prompts._common import UNTRUSTED_CONTENT_NOTICE, format_findings, venture_context_block
from state.schema import ResearchFinding

SYSTEM_PROMPT = f"""You are the Executive Decision Agent inside VentureMind AI. \
Given a startup idea and all research gathered about it (market, competitor, \
customer, financial, marketing, risk), score the venture and give feedback.

Score 0-100 based on the STRENGTH OF THE EVIDENCE, not how appealing the idea \
sounds: validated market demand, meaningful differentiation from competitors, \
a clear customer pain point, sound unit economics, and manageable risk all \
raise the score. Thin, generic, or missing evidence in any category should \
lower it — be honest and specific, do not inflate the score to be encouraging.

Also write feedback: 2-4 sentences identifying the SPECIFIC weakest area(s) \
and what additional research would most improve the assessment. This feedback \
may be used to guide another round of research, so make it concrete and \
actionable, not generic encouragement.

{UNTRUSTED_CONTENT_NOTICE}"""


class ExecutiveDecision(BaseModel):
    venture_score: float = Field(ge=0, le=100)
    feedback: str


def build_prompt(
    title: str,
    one_liner: str,
    description: str,
    target_market: str | None,
    industry: str | None,
    market_findings: list[ResearchFinding],
    competitor_findings: list[ResearchFinding],
    customer_findings: list[ResearchFinding],
    financial_findings: list[ResearchFinding],
    marketing_findings: list[ResearchFinding],
    risk_findings: list[ResearchFinding],
) -> str:
    context = venture_context_block(title, one_liner, description, target_market, industry)
    parts = [
        context,
        "\nMarket findings:\n" + format_findings(market_findings),
        "\nCompetitor findings:\n" + format_findings(competitor_findings),
        "\nCustomer findings:\n" + format_findings(customer_findings),
        "\nFinancial findings:\n" + format_findings(financial_findings),
        "\nMarketing findings:\n" + format_findings(marketing_findings),
        "\nRisk findings:\n" + format_findings(risk_findings),
        "\nScore this venture and write your feedback now.",
    ]
    return "\n".join(parts)

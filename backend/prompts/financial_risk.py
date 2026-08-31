"""Prompt template for the Financial/Risk agent.

This agent covers three angles (finance, marketing, risk — see
anchor.md/DECISIONS.md Decision 011), so its LLM call asks for three search
queries at once via structured output, not one.
"""

from pydantic import BaseModel

from prompts._common import venture_context_block

SYSTEM_PROMPT = """You are the Financial/Risk agent inside VentureMind AI. Given \
a startup idea and a research plan, produce THREE separate web search queries \
— one per angle — that would surface the most useful evidence for each:

1. financial_query: costs, revenue model feasibility, funding/investment \
   climate, or unit economics relevant to this specific idea
2. marketing_query: go-to-market strategy, customer acquisition channels, or \
   positioning that has worked for similar products
3. risk_query: regulatory, operational, technical, or execution risks specific \
   to this idea's industry or approach

Each query must be a single well-formed search string, not a sentence \
describing what to search for."""


class FinancialRiskQueries(BaseModel):
    financial_query: str
    marketing_query: str
    risk_query: str


def build_prompt(
    title: str,
    one_liner: str,
    description: str,
    target_market: str | None,
    industry: str | None,
    research_plan: str | None,
    decision_feedback: str | None = None,
) -> str:
    context = venture_context_block(
        title, one_liner, description, target_market, industry, research_plan, decision_feedback
    )
    return f"{context}\n\nWrite the three search queries now."

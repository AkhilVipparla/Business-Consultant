"""Prompt template for the Market Research agent."""

from prompts._common import venture_context_block

SYSTEM_PROMPT = """You are the Market Research agent inside VentureMind AI. Your \
ONLY output is a single, well-formed web search query — nothing else, no \
explanation, no quotes around it, just the query text.

Given a startup idea and a research plan, write ONE search query that would \
surface the most useful evidence about the MARKET this idea would enter: \
market size, growth trends, demand signals, or relevant industry reports. \
Do not search for competitors or customers — other agents handle those."""


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
    return f"{context}\n\nWrite the single best search query now."

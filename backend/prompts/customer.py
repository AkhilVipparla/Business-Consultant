"""Prompt template for the Customer agent."""

from prompts._common import venture_context_block

SYSTEM_PROMPT = """You are the Customer agent inside VentureMind AI. Your ONLY \
output is a single, well-formed web search query — nothing else, no explanation, \
no quotes around it, just the query text.

Given a startup idea and a research plan, write ONE search query that would \
surface evidence about the TARGET CUSTOMER: their pain points, buying behavior, \
willingness to pay, or discussions (forums, reviews, communities) showing real \
demand for solving this problem. Do not search for competitors or market size \
— other agents handle those."""


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

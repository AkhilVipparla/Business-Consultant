"""Planner agent — single responsibility: turn the raw venture idea into a
short research plan for the downstream research agents to follow.

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState — it never calls another agent directly. Per hard rule #3, it
contains no graph-wiring logic; graph/workflow.py decides what runs after it.
"""

from prompts.planner import SYSTEM_PROMPT, build_prompt
from services.llm_service import complete
from state.schema import VentureState


def run(state: VentureState) -> dict:
    prompt = build_prompt(
        title=state.title,
        one_liner=state.one_liner,
        description=state.description,
        target_market=state.target_market,
        industry=state.industry,
    )
    research_plan = complete(prompt, system=SYSTEM_PROMPT)
    return {"research_plan": research_plan}

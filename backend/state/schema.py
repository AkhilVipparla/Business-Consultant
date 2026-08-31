"""The shared LangGraph state.

Per anchor.md/DECISIONS.md hard rule #1: agents communicate ONLY by reading
and writing VentureState — never by calling each other directly. Every agent
in backend/agents/ takes a VentureState in and returns a partial VentureState
update out; graph/workflow.py wires nodes together but never touches these
fields itself.
"""

import operator
from typing import Annotated

from pydantic import BaseModel, Field

from models.enums import FindingCategory, FindingSourceType


class ResearchFinding(BaseModel):
    """One piece of cited evidence gathered by a research agent.

    Shape mirrors models.ResearchFinding (the DB row) — the API layer persists
    these once an agent run completes; agents themselves only ever append to
    the lists on VentureState below.
    """

    category: FindingCategory
    source_type: FindingSourceType
    source_url: str | None = None
    title: str | None = None
    content: str


class VentureState(BaseModel):
    """The single object every LangGraph agent node reads and writes.

    List fields use `operator.add` as their LangGraph reducer so that when the
    Executive Decision Agent loops the graph back to the research agents (see
    DECISIONS.md Decision 011), a second pass's findings accumulate onto the
    first pass's instead of overwriting them. Scalar fields (score, feedback,
    summary, ...) intentionally have no reducer — each write replaces the last.
    """

    # Set once when the graph starts; never modified by an agent afterward.
    venture_id: str
    title: str
    one_liner: str
    description: str
    target_market: str | None = None
    industry: str | None = None

    # Written by the Planner agent; read by the research agents as context
    # for what to look into. A single free-form plan, not a rigid structure —
    # keep it simple until a concrete need for more structure shows up.
    research_plan: str | None = None

    # How many times the improvement loop has run. The Executive Decision
    # Agent increments this before deciding whether to loop back or move on
    # to the report — see anchor.md/DECISIONS.md Decision 011.
    iteration_count: int = 0

    # One list per FindingCategory value (models.enums.FindingCategory) — the
    # three parallel research agents (Market Research, Competitor, Customer)
    # and the Financial/Risk agent (which covers finance, marketing, AND risk
    # per Decision 011) each append to the lists matching what they found.
    market_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)
    competitor_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)
    customer_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)
    financial_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)
    marketing_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)
    risk_findings: Annotated[list[ResearchFinding], operator.add] = Field(default_factory=list)

    # Written by the Executive Decision Agent each pass (renamed from
    # "Evaluator" in Decision 011 — same job: score, then decide whether to
    # loop back to research or proceed to the report).
    venture_score: float | None = None
    decision_feedback: str | None = None

    # Written by the Report Generator agent on the final pass.
    summary: str | None = None
    sections: dict[str, str] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)

    # Set by any agent that fails; the graph/API layer checks this to stop
    # early and mark the venture "failed" rather than silently continuing.
    error: str | None = None

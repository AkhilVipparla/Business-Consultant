"""LangGraph StateGraph wiring.

Per anchor.md/DECISIONS.md hard rule #3, this module contains ONLY graph
structure (nodes, edges, routing) — never business logic. Agent behavior
lives in agents/; the loop's threshold and iteration cap live in
core/config.py (see Decision 012) so they're tunable without touching this
file.

Flow (see DECISIONS.md Decision 011/012):
    planner -> [market_research, competitor, customer] (parallel)
             -> financial_risk (join)
             -> executive_decision
                 -> score < threshold AND budget left -> back to the 3
                    research agents (with decision_feedback in context)
                 -> otherwise -> report_generator -> END
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents import (
    competitor_agent,
    customer_agent,
    executive_decision_agent,
    financial_risk_agent,
    market_research_agent,
    planner_agent,
    report_generator_agent,
)
from core.config import settings
from state.schema import VentureState

RESEARCH_NODES = ["market_research", "competitor", "customer"]


def _route_after_decision(state: VentureState) -> list[str] | str:
    score = state.venture_score
    has_budget = state.iteration_count <= settings.max_iterations
    if score is not None and score < settings.score_threshold and has_budget:
        return RESEARCH_NODES
    return "report_generator"


def build_graph() -> CompiledStateGraph:
    g = StateGraph(VentureState)

    g.add_node("planner", planner_agent.run)
    g.add_node("market_research", market_research_agent.run)
    g.add_node("competitor", competitor_agent.run)
    g.add_node("customer", customer_agent.run)
    g.add_node("financial_risk", financial_risk_agent.run)
    g.add_node("executive_decision", executive_decision_agent.run)
    g.add_node("report_generator", report_generator_agent.run)

    g.add_edge(START, "planner")
    for node in RESEARCH_NODES:
        g.add_edge("planner", node)
        g.add_edge(node, "financial_risk")
    g.add_edge("financial_risk", "executive_decision")

    g.add_conditional_edges(
        "executive_decision",
        _route_after_decision,
        {**{node: node for node in RESEARCH_NODES}, "report_generator": "report_generator"},
    )
    g.add_edge("report_generator", END)

    return g.compile()


graph = build_graph()

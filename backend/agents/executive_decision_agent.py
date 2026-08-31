"""Executive Decision Agent — single responsibility: score the venture and
write feedback, based only on what the research agents actually found.

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState. The loop-or-proceed ROUTING decision is NOT made here — it's
deterministic logic in graph/workflow.py (see Decision 011/012), so that
control flow stays predictable rather than up to the LLM.
"""

from core.config import settings
from prompts.executive_decision import ExecutiveDecision, SYSTEM_PROMPT, build_prompt
from services.llm_service import complete_structured
from state.schema import VentureState


def run(state: VentureState) -> dict:
    prompt = build_prompt(
        title=state.title,
        one_liner=state.one_liner,
        description=state.description,
        target_market=state.target_market,
        industry=state.industry,
        market_findings=state.market_findings,
        competitor_findings=state.competitor_findings,
        customer_findings=state.customer_findings,
        financial_findings=state.financial_findings,
        marketing_findings=state.marketing_findings,
        risk_findings=state.risk_findings,
    )
    decision = complete_structured(
        prompt, ExecutiveDecision, system=SYSTEM_PROMPT, provider=settings.heavy_llm_provider
    )

    return {
        "venture_score": decision.venture_score,
        "decision_feedback": decision.feedback,
        "iteration_count": state.iteration_count + 1,
    }

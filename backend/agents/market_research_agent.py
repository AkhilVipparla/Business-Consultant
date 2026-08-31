"""Market Research agent — single responsibility: gather evidence about the
market this venture would enter (size, trends, demand signals).

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState — it never calls another agent directly. Findings always come
straight from Tavily's own title/url/content — the LLM only ever picks the
search query, never invents a citation.
"""

from models.enums import FindingCategory, FindingSourceType
from prompts.market_research import SYSTEM_PROMPT, build_prompt
from services import tavily_service
from services.llm_service import complete
from state.schema import ResearchFinding, VentureState

MAX_RESULTS = 4


def run(state: VentureState) -> dict:
    prompt = build_prompt(
        title=state.title,
        one_liner=state.one_liner,
        description=state.description,
        target_market=state.target_market,
        industry=state.industry,
        research_plan=state.research_plan,
        decision_feedback=state.decision_feedback,
    )
    query = complete(prompt, system=SYSTEM_PROMPT).strip()

    results = tavily_service.search(query, max_results=MAX_RESULTS)

    findings = [
        ResearchFinding(
            category=FindingCategory.MARKET,
            source_type=FindingSourceType.TAVILY,
            source_url=r.url,
            title=r.title,
            content=r.content,
        )
        for r in results
        if r.content
    ]
    return {"market_findings": findings}

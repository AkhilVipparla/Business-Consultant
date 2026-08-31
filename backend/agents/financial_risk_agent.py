"""Financial/Risk agent — single responsibility: gather evidence about
financial feasibility, marketing strategy, and risk factors for this venture.
One agent, three finding categories — see anchor.md/DECISIONS.md Decision 011.

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState — it never calls another agent directly. Findings always come
straight from Tavily/Firecrawl's own title/url/content — the LLM only ever
picks the search queries, never invents a citation.
"""

from models.enums import FindingCategory, FindingSourceType
from prompts.financial_risk import SYSTEM_PROMPT, FinancialRiskQueries, build_prompt
from services import firecrawl_service, tavily_service
from services.llm_service import complete_structured
from state.schema import ResearchFinding, VentureState

MAX_RESULTS_PER_QUERY = 3


def _findings_for(category: FindingCategory, query: str) -> list[tuple[ResearchFinding, float]]:
    results = tavily_service.search(query, max_results=MAX_RESULTS_PER_QUERY)
    return [
        (
            ResearchFinding(
                category=category,
                source_type=FindingSourceType.TAVILY,
                source_url=r.url,
                title=r.title,
                content=r.content,
            ),
            r.score or 0.0,
        )
        for r in results
        if r.content
    ]


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
    queries = complete_structured(prompt, FinancialRiskQueries, system=SYSTEM_PROMPT)

    scored: list[tuple[ResearchFinding, float]] = []
    scored += _findings_for(FindingCategory.FINANCIAL, queries.financial_query)
    scored += _findings_for(FindingCategory.MARKETING, queries.marketing_query)
    scored += _findings_for(FindingCategory.RISK, queries.risk_query)

    # Firecrawl-scrape only the single best-scoring result across all three
    # angles — keeps this agent's tool-call cost bounded (see SECURITY.md AI
    # Agent Security) rather than scraping once per category.
    if scored:
        best_finding, _ = max(scored, key=lambda pair: pair[1])
        if best_finding.source_url:
            scraped = None
            try:
                scraped = firecrawl_service.scrape(best_finding.source_url)
            except firecrawl_service.FirecrawlScrapeError:
                pass
            if scraped and scraped.markdown:
                scored.append(
                    (
                        ResearchFinding(
                            category=best_finding.category,
                            source_type=FindingSourceType.FIRECRAWL,
                            source_url=scraped.url,
                            title=scraped.title,
                            content=scraped.markdown,
                        ),
                        0.0,
                    )
                )

    return {
        "financial_findings": [f for f, _ in scored if f.category == FindingCategory.FINANCIAL],
        "marketing_findings": [f for f, _ in scored if f.category == FindingCategory.MARKETING],
        "risk_findings": [f for f, _ in scored if f.category == FindingCategory.RISK],
    }

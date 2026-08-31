"""Customer agent — single responsibility: gather evidence about the target
customer's persona, pain points, and buying behavior (see anchor.md/DECISIONS.md
Decision 011).

Per anchor.md/DECISIONS.md hard rule #1, this function only reads/writes
VentureState — it never calls another agent directly. Findings always come
straight from Tavily/Firecrawl's own title/url/content — the LLM only ever
picks the search query, never invents a citation. The Firecrawl scrape is an
optional depth enrichment on top of Tavily's results: if it fails for any
reason, the agent still returns what Tavily found rather than failing outright.
"""

from models.enums import FindingCategory, FindingSourceType
from prompts.customer import SYSTEM_PROMPT, build_prompt
from services import firecrawl_service, tavily_service
from services.llm_service import complete
from state.schema import ResearchFinding, VentureState

MAX_RESULTS = 4
MAX_SCRAPES = 1


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
            category=FindingCategory.CUSTOMER,
            source_type=FindingSourceType.TAVILY,
            source_url=r.url,
            title=r.title,
            content=r.content,
        )
        for r in results
        if r.content
    ]

    for r in results[:MAX_SCRAPES]:
        if not r.url:
            continue
        try:
            scraped = firecrawl_service.scrape(r.url)
        except firecrawl_service.FirecrawlScrapeError:
            continue
        if scraped.markdown:
            findings.append(
                ResearchFinding(
                    category=FindingCategory.CUSTOMER,
                    source_type=FindingSourceType.FIRECRAWL,
                    source_url=scraped.url,
                    title=scraped.title,
                    content=scraped.markdown,
                )
            )

    return {"customer_findings": findings}

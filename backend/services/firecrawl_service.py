"""Firecrawl page scraping — the ONLY place agent code may call Firecrawl from."""

from firecrawl import Firecrawl
from pydantic import BaseModel

from core.config import settings
from core.logging import logger

_client: Firecrawl | None = None

# Cap how much scraped content ever reaches a prompt — a single page can be
# far larger than needed and directly drives LLM cost/context on a
# zero-budget project. See anchor.md/SECURITY.md > AI Agent Security.
MAX_MARKDOWN_CHARS = 8000


class FirecrawlScrapeError(RuntimeError):
    """Raised when a Firecrawl scrape fails or FIRECRAWL_API_KEY is missing."""


class ScrapeResult(BaseModel):
    url: str
    title: str | None = None
    markdown: str


def _get_client() -> Firecrawl:
    global _client
    if _client is None:
        if not settings.firecrawl_api_key:
            raise FirecrawlScrapeError(
                "FIRECRAWL_API_KEY is not set — copy backend/.env.example to backend/.env and fill it in"
            )
        _client = Firecrawl(api_key=settings.firecrawl_api_key)
    return _client


def scrape(url: str) -> ScrapeResult:
    """Scrape one specific URL and return its main content as markdown.

    Callers (agents) choose which URL to scrape — this service does not
    follow links or crawl; it fetches exactly the one page it's given.
    """
    client = _get_client()
    logger.info("Firecrawl scrape: {}", url)
    try:
        doc = client.scrape(url, formats=["markdown"], only_main_content=True)
    except Exception as exc:  # noqa: BLE001
        logger.error("Firecrawl scrape failed for {}: {}", url, exc)
        raise FirecrawlScrapeError(f"Firecrawl scrape failed: {exc}") from exc

    metadata = doc.metadata
    if metadata is not None and metadata.error:
        raise FirecrawlScrapeError(f"Firecrawl scrape of {url} returned an error: {metadata.error}")

    markdown = doc.markdown or ""
    if len(markdown) > MAX_MARKDOWN_CHARS:
        markdown = markdown[:MAX_MARKDOWN_CHARS]

    return ScrapeResult(
        url=(metadata.url if metadata and metadata.url else url),
        title=metadata.title if metadata else None,
        markdown=markdown,
    )

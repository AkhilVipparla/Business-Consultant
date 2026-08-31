"""Tavily web search — the ONLY place agent code may call Tavily from."""

from pydantic import BaseModel
from tavily import TavilyClient

from core.config import settings
from core.logging import logger

_client: TavilyClient | None = None


class TavilySearchError(RuntimeError):
    """Raised when a Tavily search fails or TAVILY_API_KEY is missing."""


class TavilySearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        if not settings.tavily_api_key:
            raise TavilySearchError(
                "TAVILY_API_KEY is not set — copy backend/.env.example to backend/.env and fill it in"
            )
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def search(query: str, max_results: int = 5) -> list[TavilySearchResult]:
    """Run a Tavily web search and return normalized results.

    Callers (agents) are responsible for turning these into ResearchFinding
    rows with the right `category` — this service knows nothing about
    VentureState or the DB schema, only about talking to Tavily.
    """
    client = _get_client()
    logger.info("Tavily search: {!r} (max_results={})", query, max_results)
    try:
        raw = client.search(query=query, search_depth="basic", max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        logger.error("Tavily search failed for {!r}: {}", query, exc)
        raise TavilySearchError(f"Tavily search failed: {exc}") from exc

    results = raw.get("results", []) if isinstance(raw, dict) else []
    return [
        TavilySearchResult(
            title=r.get("title") or "",
            url=r.get("url") or "",
            content=r.get("content") or "",
            score=r.get("score"),
        )
        for r in results
    ]

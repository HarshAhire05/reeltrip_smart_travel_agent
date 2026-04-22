"""
Tavily web search wrapper.
Wraps the synchronous Tavily client in asyncio.to_thread() to avoid blocking.
"""
from tavily import TavilyClient
from config import get_settings
import asyncio
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

_client: TavilyClient | None = None


def _get_client() -> TavilyClient | None:
    global _client
    if _client is None and settings.TAVILY_API_KEY:
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


async def search_tavily(
    query: str,
    max_results: int = 5,
    depth: str = "basic",
) -> list[dict] | None:
    """
    Search the web using Tavily.
    Returns list of result dicts with 'title', 'content', 'url' keys.
    Returns None on failure (never crashes).

    Args:
        query: Search query (3-8 words work best)
        max_results: Maximum number of results
        depth: "basic" (cheaper) or "advanced" (more thorough)
    """
    client = _get_client()
    if not client:
        logger.warning("Tavily not configured, skipping web search")
        return None

    try:
        result = await asyncio.to_thread(
            client.search,
            query=query,
            search_depth=depth,
            max_results=max_results,
            include_answer=True,
        )

        return result.get("results", [])

    except Exception as e:
        logger.error(f"Tavily search failed for '{query}': {e}")
        return None

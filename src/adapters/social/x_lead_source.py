from __future__ import annotations

from src.adapters.social.duckduckgo_site_search import DuckDuckGoSiteSearch, DuckDuckGoSiteSearchError
from src.domain.prospecting import SocialPost


class XLeadSourceError(RuntimeError):
    """Raised when X prospecting requests fail."""


class XLeadSource:
    def __init__(
        self,
        user_agent: str = "trade-prospecting-bot/0.1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.search = DuckDuckGoSiteSearch(
            site_domains=("x.com", "twitter.com"),
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
        )

    def search_recent_posts(self, search_term: str, limit: int) -> list[SocialPost]:
        try:
            results = self.search.search(search_term, limit)
        except DuckDuckGoSiteSearchError as exc:
            raise XLeadSourceError("Unable to load X search results.") from exc

        return [
            SocialPost(
                source="x",
                external_id=result.url,
                title=result.title,
                body=result.snippet,
                author="unknown",
                permalink=result.url,
                created_at=result.published_at,
            )
            for result in results
        ]

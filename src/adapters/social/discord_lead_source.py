from __future__ import annotations

from src.adapters.social.duckduckgo_site_search import DuckDuckGoSiteSearch, DuckDuckGoSiteSearchError
from src.domain.prospecting import SocialPost


class DiscordLeadSourceError(RuntimeError):
    """Raised when Discord prospecting requests fail."""


class DiscordLeadSource:
    def __init__(
        self,
        user_agent: str = "trade-prospecting-bot/0.1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.search = DuckDuckGoSiteSearch(
            site_domains=("discord.com",),
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
        )

    def search_recent_posts(self, search_term: str, limit: int) -> list[SocialPost]:
        try:
            results = self.search.search(search_term, limit)
        except DuckDuckGoSiteSearchError as exc:
            raise DiscordLeadSourceError("Unable to load Discord search results.") from exc

        return [
            SocialPost(
                source="discord",
                external_id=result.url,
                title=result.title,
                body=result.snippet,
                author="unknown",
                permalink=result.url,
                created_at=result.published_at,
            )
            for result in results
        ]

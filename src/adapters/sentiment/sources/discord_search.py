from __future__ import annotations

from src.adapters.sentiment.sources.google_news_rss import SentimentSignal
from src.adapters.social.duckduckgo_site_search import DuckDuckGoSiteSearch, DuckDuckGoSiteSearchError


class DiscordDiscussionSourceError(RuntimeError):
    """Raised when Discord sentiment requests fail."""


class DiscordDiscussionSource:
    def __init__(
        self,
        user_agent: str = "brivoly-etf-sentiment-bot/0.1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.search = DuckDuckGoSiteSearch(
            site_domains=("discord.com",),
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
        )

    def collect_signals(self, query: str, limit: int) -> list[SentimentSignal]:
        try:
            results = self.search.search(query, limit)
        except DuckDuckGoSiteSearchError as exc:
            raise DiscordDiscussionSourceError("Unable to load Discord discussion results.") from exc

        return [
            SentimentSignal(
                source="discord",
                channel="public_search",
                query=query,
                title=result.title,
                summary=result.snippet,
                url=result.url,
                published_at=result.published_at.isoformat(),
            )
            for result in results
        ]

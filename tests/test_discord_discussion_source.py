from __future__ import annotations

import httpx

from src.adapters.sentiment.sources.discord_search import DiscordDiscussionSource, DiscordDiscussionSourceError


def test_discord_discussion_source_parses_public_search_results(monkeypatch) -> None:
    def fake_get(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert "site:discord.com" in kwargs["params"]["q"]
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            text=(
                '<html><body>'
                '<a class="result__a" href="https://discord.com/channels/1/2/3">Semiconductor chatter</a>'
                '<div class="result__snippet">Retail tone looks euphoric</div>'
                "</body></html>"
            ),
        )

    monkeypatch.setattr("src.adapters.social.duckduckgo_site_search.httpx.get", fake_get)

    signals = DiscordDiscussionSource().collect_signals("semiconductor ETF", 5)

    assert signals[0].source == "discord"
    assert signals[0].title == "Semiconductor chatter"
    assert signals[0].summary == "Retail tone looks euphoric"


def test_discord_discussion_source_raises_on_http_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.social.duckduckgo_site_search.httpx.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("boom")),  # type: ignore[no-untyped-def]
    )

    try:
        DiscordDiscussionSource().collect_signals("query", 5)
    except DiscordDiscussionSourceError as exc:
        assert str(exc) == "Unable to load Discord discussion results."
    else:
        raise AssertionError("Expected DiscordDiscussionSourceError")

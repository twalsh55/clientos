from __future__ import annotations

import httpx

from src.adapters.social.discord_lead_source import DiscordLeadSource, DiscordLeadSourceError


def test_discord_lead_source_parses_public_search_results(monkeypatch) -> None:
    def fake_get(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert url == "https://html.duckduckgo.com/html/"
        assert "site:discord.com" in kwargs["params"]["q"]
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            text=(
                '<html><body>'
                '<a class="result__a" href="https://discord.com/channels/1/2/3">Discord forum result</a>'
                '<div class="result__snippet">People discussing manual reporting pain</div>'
                "</body></html>"
            ),
        )

    monkeypatch.setattr("src.adapters.social.duckduckgo_site_search.httpx.get", fake_get)

    posts = DiscordLeadSource().search_recent_posts("manual reporting", 5)

    assert posts[0].source == "discord"
    assert posts[0].title == "Discord forum result"
    assert posts[0].body == "People discussing manual reporting pain"
    assert posts[0].permalink == "https://discord.com/channels/1/2/3"


def test_discord_lead_source_raises_on_http_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.social.duckduckgo_site_search.httpx.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ReadTimeout("boom")),  # type: ignore[no-untyped-def]
    )

    try:
        DiscordLeadSource().search_recent_posts("query", 5)
    except DiscordLeadSourceError as exc:
        assert str(exc) == "Unable to load Discord search results."
    else:
        raise AssertionError("Expected DiscordLeadSourceError")

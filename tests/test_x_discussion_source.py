from __future__ import annotations

import httpx

from src.adapters.sentiment.sources.x_search import XDiscussionSource, XDiscussionSourceError


def test_x_discussion_source_parses_public_search_results(monkeypatch) -> None:
    def fake_get(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert "site:x.com" in kwargs["params"]["q"]
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            text=(
                '<html><body>'
                '<a class="result__a" href="https://twitter.com/market/status/1">Macro thread</a>'
                '<div class="result__snippet">ETF fear rising after CPI</div>'
                "</body></html>"
            ),
        )

    monkeypatch.setattr("src.adapters.social.duckduckgo_site_search.httpx.get", fake_get)

    signals = XDiscussionSource().collect_signals("ETF fear", 5)

    assert signals[0].source == "x"
    assert signals[0].channel == "public_search"
    assert signals[0].title == "Macro thread"
    assert signals[0].summary == "ETF fear rising after CPI"
    assert signals[0].url == "https://twitter.com/market/status/1"


def test_x_discussion_source_raises_on_http_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.social.duckduckgo_site_search.httpx.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("boom")),  # type: ignore[no-untyped-def]
    )

    try:
        XDiscussionSource().collect_signals("query", 5)
    except XDiscussionSourceError as exc:
        assert str(exc) == "Unable to load X discussion results."
    else:
        raise AssertionError("Expected XDiscussionSourceError")

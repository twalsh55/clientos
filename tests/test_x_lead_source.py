from __future__ import annotations

from datetime import UTC, datetime

import httpx

from src.adapters.social.x_lead_source import XLeadSource, XLeadSourceError


def test_x_lead_source_parses_public_search_results(monkeypatch) -> None:
    def fake_get(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert url == "https://html.duckduckgo.com/html/"
        assert "site:x.com" in kwargs["params"]["q"]
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            text=(
                '<html><body>'
                '<a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fx.com%2Fops%2Fstatus%2F1">Tweet title</a>'
                '<div class="result__snippet">Spreadsheet-heavy ops thread</div>'
                "</body></html>"
            ),
        )

    monkeypatch.setattr("src.adapters.social.duckduckgo_site_search.httpx.get", fake_get)
    fixed_now = datetime(2026, 5, 16, tzinfo=UTC)
    source = XLeadSource()
    source.search.now = lambda: fixed_now  # type: ignore[method-assign]

    posts = source.search_recent_posts("spreadsheet workflow", 5)

    assert posts[0].source == "x"
    assert posts[0].title == "Tweet title"
    assert posts[0].body == "Spreadsheet-heavy ops thread"
    assert posts[0].permalink == "https://x.com/ops/status/1"
    assert posts[0].created_at == fixed_now


def test_x_lead_source_raises_on_http_and_shape_errors(monkeypatch) -> None:
    def failing_get(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise httpx.ConnectError("boom")

    monkeypatch.setattr("src.adapters.social.duckduckgo_site_search.httpx.get", failing_get)
    try:
        XLeadSource().search_recent_posts("query", 5)
    except XLeadSourceError as exc:
        assert str(exc) == "Unable to load X search results."
    else:
        raise AssertionError("Expected XLeadSourceError")


def test_x_lead_source_filters_non_x_domains(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.social.duckduckgo_site_search.httpx.get",
        lambda *args, **kwargs: httpx.Response(  # type: ignore[no-untyped-def]
            200,
            request=httpx.Request("GET", "https://html.duckduckgo.com/html/"),
            text=(
                '<html><body>'
                '<a class="result__a" href="https://example.com/post">Ignore me</a>'
                '<div class="result__snippet">Nope</div>'
                "</body></html>"
            ),
        ),
    )

    assert XLeadSource().search_recent_posts("query", 5) == []

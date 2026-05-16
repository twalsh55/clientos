from __future__ import annotations

from src.adapters.social.duckduckgo_site_search import _normalize_result_url, _url_matches_allowed_domains


def test_normalize_result_url_handles_empty_protocol_relative_and_redirect_urls() -> None:
    assert _normalize_result_url("") == ""
    assert _normalize_result_url("//x.com/user/status/1") == "https://x.com/user/status/1"
    assert (
        _normalize_result_url("https://duckduckgo.com/l/?uddg=https%3A%2F%2Fdiscord.com%2Fchannels%2F1%2F2%2F3")
        == "https://discord.com/channels/1/2/3"
    )


def test_url_matches_allowed_domains_rejects_missing_host_and_accepts_subdomains() -> None:
    assert _url_matches_allowed_domains("/relative/path", ("x.com",)) is False
    assert _url_matches_allowed_domains("https://mobile.twitter.com/post", ("x.com", "twitter.com")) is True

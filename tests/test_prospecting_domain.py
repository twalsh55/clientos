from __future__ import annotations

from datetime import UTC, datetime

from src.domain.prospecting import SocialPost, score_social_post


def build_post(title: str, body: str) -> SocialPost:
    return SocialPost(
        source="reddit",
        external_id="abc123",
        title=title,
        body=body,
        author="alice",
        permalink="https://example.com/post",
        created_at=datetime(2026, 5, 14, tzinfo=UTC),
    )


def test_score_social_post_returns_ranked_match() -> None:
    post = build_post(
        "I wish there was a better workflow tool for invoice reconciliation?",
        "We still use spreadsheets and manual CSV checks. How are you solving this? I wish there was a tool for this.",
    )

    match = score_social_post(post, "i wish there was a tool for")

    assert match is not None
    assert match.score >= 8
    assert "asks a question" in match.reasons
    assert "mentions spreadsheet" in match.reasons
    assert "matched query i wish there was a tool for" in match.reasons


def test_score_social_post_filters_low_intent_posts() -> None:
    post = build_post("Daily status update", "A routine update with no workflow pain.")
    assert score_social_post(post, "spreadsheet workflow problem") is None


def test_score_social_post_filters_excluded_topics() -> None:
    post = build_post("Hiring for fintech role", "This is a job opening for a trading startup.")
    assert score_social_post(post, "portfolio risk dashboard") is None

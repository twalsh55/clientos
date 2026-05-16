from __future__ import annotations

from datetime import date

import pandas as pd

from src.adapters.sentiment.runtime import (
    DEFAULT_ETF_PROMPT_FILE,
    ETFSnapshot,
    _annualized_volatility_pct,
    _average_metric,
    _build_risk_flags,
    _classify_market_mood,
    _drawdown_from_high_pct,
    _return_pct,
    build_etf_market_snapshot,
    build_etf_sentiment_agent_from_env,
    collect_etf_sentiment_config_errors,
    load_etf_sentiment_prompt,
    parse_positive_int,
    run_etf_sentiment_job,
)


def test_load_etf_sentiment_prompt_uses_env_override(tmp_path, monkeypatch) -> None:
    prompt_file = tmp_path / "etf.md"
    prompt_file.write_text("Prompt body", encoding="utf-8")
    monkeypatch.setenv("ETF_SENTIMENT_PROMPT_FILE", str(prompt_file))

    assert load_etf_sentiment_prompt() == "Prompt body"


def test_load_etf_sentiment_prompt_rejects_missing_and_empty_files(tmp_path, monkeypatch) -> None:
    missing_file = tmp_path / "missing.md"
    monkeypatch.setenv("ETF_SENTIMENT_PROMPT_FILE", str(missing_file))
    try:
        load_etf_sentiment_prompt()
    except ValueError as exc:
        assert str(exc) == f"Unable to load ETF sentiment prompt file: {missing_file}"
    else:
        raise AssertionError("Expected missing prompt file to fail")

    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   ", encoding="utf-8")
    monkeypatch.setenv("ETF_SENTIMENT_PROMPT_FILE", str(empty_file))
    try:
        load_etf_sentiment_prompt()
    except ValueError as exc:
        assert str(exc) == f"ETF sentiment prompt file is empty: {empty_file}"
    else:
        raise AssertionError("Expected empty prompt file to fail")


def test_build_etf_sentiment_agent_from_env_switches_modes(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert build_etf_sentiment_agent_from_env().__class__.__name__ == "TemplateETFSentimentAgent"

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ETF_SENTIMENT_OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("ETF_SENTIMENT_OPENAI_MAX_OUTPUT_TOKENS", "123")
    agent = build_etf_sentiment_agent_from_env()
    assert agent.__class__.__name__ == "OpenAIETFSentimentAgent"
    assert agent.model == "gpt-5-mini"  # type: ignore[attr-defined]
    assert agent.max_output_tokens == 123  # type: ignore[attr-defined]


def test_build_etf_market_snapshot_computes_summary(monkeypatch) -> None:
    dates = pd.bdate_range("2025-01-01", periods=30)
    data = pd.DataFrame(
        {
            "VT": [100 + i for i in range(30)],
            "SPY": [200 + (i * 0.5) for i in range(30)],
            "QQQ": [300 + (i * 2.0) for i in range(30)],
            "EEM": [50 - (i * 0.2) for i in range(30)],
            "SOXX": [400 + (i * 3.0) for i in range(30)],
            "XLK": [150 + (i * 1.8) for i in range(30)],
            "ITA": [120 + (i * 0.8) for i in range(30)],
            "XLE": [90 + (i * 1.5) for i in range(30)],
            "SCHD": [70 + (i * 0.4) for i in range(30)],
            "QUAL": [80 + (i * 0.6) for i in range(30)],
            "IWM": [60 + (i * 0.3) for i in range(30)],
            "BND": [73 - (i * 0.1) for i in range(30)],
            "GLD": [180 + (i * 0.2) for i in range(30)],
            "VGK": [65 + (i * 0.4) for i in range(30)],
            "INDA": [40 + (i * 0.9) for i in range(30)],
            "MCHI": [45 - (i * 0.1) for i in range(30)],
        },
        index=dates,
    )

    class FakeAdapter:
        def load_close_data(self, tickers: list[str], start_date: date, end_date: date) -> pd.DataFrame:
            assert "VT" in tickers
            assert start_date < end_date
            return data[tickers]

    monkeypatch.delenv("ETF_SENTIMENT_LOOKBACK_DAYS", raising=False)
    snapshot = build_etf_market_snapshot(market_data=FakeAdapter(), as_of=date(2025, 2, 20))  # type: ignore[arg-type]

    assert snapshot["overview"]["tracked_etf_count"] == 16
    assert snapshot["overview"]["market_mood"] in {"constructive", "optimistic"}
    assert snapshot["leaders"][0]["ticker"] == "INDA"
    assert snapshot["laggards"][0]["ticker"] in {"EEM", "MCHI", "BND"}
    assert snapshot["etfs"][0]["label"] == "Global Equities"
    assert "yfinance proxies" in snapshot["data_note"]


def test_build_etf_market_snapshot_rejects_missing_data(monkeypatch) -> None:
    class EmptyAdapter:
        def load_close_data(self, tickers: list[str], start_date: date, end_date: date) -> pd.DataFrame:
            return pd.DataFrame()

    try:
        build_etf_market_snapshot(market_data=EmptyAdapter(), as_of=date(2025, 2, 20))  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == "Unable to load ETF market snapshot. Check ticker symbols or network connectivity."
    else:
        raise AssertionError("Expected empty snapshot to fail")

    class MissingColumnsAdapter:
        def load_close_data(self, tickers: list[str], start_date: date, end_date: date) -> pd.DataFrame:
            return pd.DataFrame({"OTHER": [1.0, 2.0]}, index=pd.bdate_range("2025-01-01", periods=2))

    try:
        build_etf_market_snapshot(market_data=MissingColumnsAdapter(), as_of=date(2025, 2, 20))  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == "Unable to build ETF sentiment snapshot from downloaded market data."
    else:
        raise AssertionError("Expected missing columns to fail")


def test_build_etf_market_snapshot_skips_empty_series_columns() -> None:
    dates = pd.bdate_range("2025-01-01", periods=30)
    data = pd.DataFrame(
        {
            "VT": [None] * 30,
            "SPY": [200 + i for i in range(30)],
            "QQQ": [300 + i for i in range(30)],
            "EEM": [50 + i for i in range(30)],
            "SOXX": [400 + i for i in range(30)],
            "XLK": [150 + i for i in range(30)],
            "ITA": [120 + i for i in range(30)],
            "XLE": [90 + i for i in range(30)],
            "SCHD": [70 + i for i in range(30)],
            "QUAL": [80 + i for i in range(30)],
            "IWM": [60 + i for i in range(30)],
            "BND": [73 + i for i in range(30)],
            "GLD": [180 + i for i in range(30)],
            "VGK": [65 + i for i in range(30)],
            "INDA": [40 + i for i in range(30)],
            "MCHI": [45 + i for i in range(30)],
        },
        index=dates,
    )

    class FakeAdapter:
        def load_close_data(self, tickers: list[str], start_date: date, end_date: date) -> pd.DataFrame:
            return data[tickers]

    snapshot = build_etf_market_snapshot(market_data=FakeAdapter(), as_of=date(2025, 2, 20))  # type: ignore[arg-type]
    assert snapshot["overview"]["tracked_etf_count"] == 15


def test_collect_etf_sentiment_config_errors_reports_missing_and_invalid_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ETF_SENTIMENT_PROMPT_FILE", str(tmp_path / "missing.md"))
    monkeypatch.setenv("ETF_SENTIMENT_LOOKBACK_DAYS", "0")
    monkeypatch.setenv("ETF_SENTIMENT_OPENAI_MAX_OUTPUT_TOKENS", "abc")

    assert collect_etf_sentiment_config_errors() == [
        f"Missing ETF sentiment prompt file: {tmp_path / 'missing.md'}",
        "ETF_SENTIMENT_LOOKBACK_DAYS must be greater than zero",
        "ETF_SENTIMENT_OPENAI_MAX_OUTPUT_TOKENS must be an integer",
    ]


def test_collect_etf_sentiment_config_errors_allows_defaults(monkeypatch) -> None:
    monkeypatch.delenv("ETF_SENTIMENT_PROMPT_FILE", raising=False)
    monkeypatch.delenv("ETF_SENTIMENT_LOOKBACK_DAYS", raising=False)
    monkeypatch.delenv("ETF_SENTIMENT_OPENAI_MAX_OUTPUT_TOKENS", raising=False)
    assert DEFAULT_ETF_PROMPT_FILE.is_file()
    assert collect_etf_sentiment_config_errors() == []


def test_parse_positive_int_validates_values(monkeypatch) -> None:
    monkeypatch.setenv("ETF_SENTIMENT_LOOKBACK_DAYS", "15")
    assert parse_positive_int("ETF_SENTIMENT_LOOKBACK_DAYS", default=10) == 15

    monkeypatch.setenv("ETF_SENTIMENT_LOOKBACK_DAYS", "bad")
    try:
        parse_positive_int("ETF_SENTIMENT_LOOKBACK_DAYS", default=10)
    except ValueError as exc:
        assert str(exc) == "ETF_SENTIMENT_LOOKBACK_DAYS must be an integer."
    else:
        raise AssertionError("Expected integer validation failure")

    monkeypatch.setenv("ETF_SENTIMENT_LOOKBACK_DAYS", "-1")
    try:
        parse_positive_int("ETF_SENTIMENT_LOOKBACK_DAYS", default=10)
    except ValueError as exc:
        assert str(exc) == "ETF_SENTIMENT_LOOKBACK_DAYS must be greater than zero."
    else:
        raise AssertionError("Expected positive validation failure")


def test_etf_sentiment_helper_functions_cover_edge_cases() -> None:
    short_series = pd.Series([1.0])
    zero_baseline_series = pd.Series([0.0, 1.0])
    growing_series = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    flat_series = pd.Series([100.0] * 21)
    empty_series = pd.Series(dtype=float)

    assert _return_pct(short_series, periods=1) is None
    assert _return_pct(zero_baseline_series, periods=1) is None
    assert _return_pct(growing_series, periods=1) == 0.9615384615384581
    assert _drawdown_from_high_pct(empty_series, periods=10) is None
    assert _drawdown_from_high_pct(pd.Series([0.0]), periods=10) is None
    assert _drawdown_from_high_pct(growing_series, periods=10) == 0.0
    assert _annualized_volatility_pct(flat_series, periods=20) == 0.0
    assert _annualized_volatility_pct(pd.Series([100.0, 101.0]), periods=20) is None
    assert _average_metric([], "five_day_return_pct") is None
    assert _classify_market_mood(None, 1.0) == "neutral"
    assert _classify_market_mood(2.1, 4.1) == "optimistic"
    assert _classify_market_mood(-2.1, -4.1) == "fearful"
    assert _classify_market_mood(1.0, 1.0) == "constructive"
    assert _classify_market_mood(-1.0, 1.0) == "cautious"
    assert _classify_market_mood(0.1, 0.1) == "neutral"

    flags = _build_risk_flags(
        [
            ETFSnapshot("AI / Technology", "XLK", 1.0, 1.0, 2.0, 8.5, -2.0, 31.0),
            ETFSnapshot("Bonds", "BND", 1.0, 1.0, 2.0, 1.0, -5.0, 10.0),
        ]
    )
    assert flags == [
        "Potential crowding near highs in: AI / Technology",
        "Defensive assets are strengthening: Bonds",
        "Elevated 20d realized volatility in: AI / Technology",
    ]


def test_run_etf_sentiment_job_builds_and_executes(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeAgent:
        def generate_briefing(self, prompt: str, market_snapshot: dict[str, object]) -> str:
            calls.append((prompt, market_snapshot))
            return "ETF Sentiment Brief"

    monkeypatch.setattr("src.adapters.sentiment.runtime.load_etf_sentiment_prompt", lambda: "Prompt body")
    monkeypatch.setattr("src.adapters.sentiment.runtime.build_etf_market_snapshot", lambda: {"overview": {"market_mood": "neutral"}})
    monkeypatch.setattr("src.adapters.sentiment.runtime.build_etf_sentiment_agent_from_env", lambda: FakeAgent())

    assert run_etf_sentiment_job() == "ETF Sentiment Brief"
    assert calls == [("Prompt body", {"overview": {"market_mood": "neutral"}})]

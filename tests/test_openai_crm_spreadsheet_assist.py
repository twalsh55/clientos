from __future__ import annotations

import httpx
import pytest

from src.adapters.llm.openai_crm_spreadsheet_assist import (
    OpenAICRMSpreadsheetAssistAgent,
    OpenAICRMSpreadsheetAssistError,
)


def test_openai_crm_spreadsheet_assist_uses_api_and_returns_mapping(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, headers, json, timeout: float):  # type: ignore[no-untyped-def]
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "output_text": '{"field_mapping":{"Person":"lead_name","Organisation":"company_name","Followup":"next_follow_up_at","Context":"notes"}}'
            },
        )

    monkeypatch.setattr("src.adapters.llm.openai_crm_spreadsheet_assist.httpx.post", fake_post)

    mapping = OpenAICRMSpreadsheetAssistAgent(api_key="secret").suggest_field_mapping(
        prompt="Focus on owner and next follow-up.",
        preferred_formats=["csv"],
        source_label="CSV upload",
        headers=["Person", "Organisation", "Followup", "Context"],
        sample_rows=[{"Person": "Taylor Brooks", "Organisation": "Beacon Ridge", "Followup": "2024-05-09", "Context": "Imported"}],
    )

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["json"]["model"] == "gpt-4.1-mini"
    assert mapping["Person"] == "lead_name"
    assert mapping["Context"] == "notes"


def test_openai_crm_spreadsheet_assist_rejects_missing_headers_and_transport_failures(monkeypatch) -> None:
    agent = OpenAICRMSpreadsheetAssistAgent(api_key="secret")

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="headers are required"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", [], [])

    monkeypatch.setattr(
        "src.adapters.llm.openai_crm_spreadsheet_assist.httpx.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.HTTPError("boom")),  # type: ignore[no-untyped-def]
    )
    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="Unable to use AI to interpret this spreadsheet layout right now"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])


def test_openai_crm_spreadsheet_assist_validates_response_shapes(monkeypatch) -> None:
    responses = iter(
        [
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={
                    "output": [
                        {
                            "content": [
                                {"text": '{"field_mapping":{"Person":"lead_name","Organisation":null}}'}
                            ]
                        }
                    ]
                },
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output_text": "not-json"},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output_text": '{"field_mapping":"bad"}'},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output_text": '{"field_mapping":{"Person":"unsupported_field"}}'},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output_text": '{"field_mapping":{"Person":123}}'},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output": "bad"},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
                json={"output": ["bad", {"content": "bad"}, {"content": ["bad", {"no_text": "x"}]}]},
            ),
        ]
    )

    monkeypatch.setattr("src.adapters.llm.openai_crm_spreadsheet_assist.httpx.post", lambda *args, **kwargs: next(responses))
    agent = OpenAICRMSpreadsheetAssistAgent(api_key="secret")

    mapping = agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person", "Organisation"], [{"Person": "Taylor"}])
    assert mapping["Person"] == "lead_name"
    assert mapping["Organisation"] is None

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="invalid payload"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="invalid payload"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="unsupported field mapping"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="invalid payload"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="invalid payload"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

    with pytest.raises(OpenAICRMSpreadsheetAssistError, match="invalid payload"):
        agent.suggest_field_mapping("prompt", [], "CSV upload", ["Person"], [{"Person": "Taylor"}])

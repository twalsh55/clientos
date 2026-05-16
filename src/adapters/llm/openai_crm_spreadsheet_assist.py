from __future__ import annotations

import json

import httpx

from src.application.crm_import import CANONICAL_IMPORT_FIELDS


class OpenAICRMSpreadsheetAssistError(RuntimeError):
    """Raised when AI spreadsheet mapping assistance fails."""


class OpenAICRMSpreadsheetAssistAgent:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1-mini",
        timeout_seconds: float = 30.0,
        max_output_tokens: int = 800,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens

    def suggest_field_mapping(
        self,
        prompt: str,
        preferred_formats: list[str],
        source_label: str,
        headers: list[str],
        sample_rows: list[dict[str, str]],
    ) -> dict[str, str | None]:
        if not headers:
            raise OpenAICRMSpreadsheetAssistError("Spreadsheet headers are required.")

        allowed_fields = ", ".join(CANONICAL_IMPORT_FIELDS)
        instructions = (
            "You rescue messy CRM spreadsheet imports by mapping unknown headers to canonical CRM fields. "
            "Return JSON only in the form "
            '{"field_mapping":{"Original Header":"lead_name","Other Header":null}}. '
            "Only use these canonical fields: "
            f"{allowed_fields}. "
            "Use null when a header should stay unmapped. "
            "Infer from both the header names and the sample row values. "
            "Be conservative and avoid guessing when evidence is weak. "
            f"User-specific intake prompt: {prompt.strip() or 'Focus on follow-up-critical CRM fields.'} "
            f"User's common formats: {', '.join(preferred_formats) if preferred_formats else 'not provided'}."
        )
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "source_label": source_label,
                                    "headers": headers,
                                    "sample_rows": sample_rows,
                                }
                            ),
                        }
                    ],
                }
            ],
            "max_output_tokens": self.max_output_tokens,
            "store": False,
        }
        try:
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenAICRMSpreadsheetAssistError("Unable to use AI to interpret this spreadsheet layout right now.") from exc

        content = _extract_text_from_response(body)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an invalid payload.") from exc

        raw_mapping = parsed.get("field_mapping")
        if not isinstance(raw_mapping, dict):
            raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an invalid payload.")

        normalized: dict[str, str | None] = {}
        for header in headers:
            candidate = raw_mapping.get(header)
            if candidate is None:
                normalized[header] = None
                continue
            if not isinstance(candidate, str):
                raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an invalid payload.")
            mapped = candidate.strip()
            if mapped and mapped not in CANONICAL_IMPORT_FIELDS:
                raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an unsupported field mapping.")
            normalized[header] = mapped or None
        return normalized


def _extract_text_from_response(payload: dict[str, object]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = payload.get("output", [])
    if not isinstance(output, list):
        raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an invalid payload.")

    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for content_item in content:
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                parts.append(text)

    content = "\n".join(part.strip() for part in parts if part.strip()).strip()
    if not content:
        raise OpenAICRMSpreadsheetAssistError("AI spreadsheet assistance returned an invalid payload.")
    return content

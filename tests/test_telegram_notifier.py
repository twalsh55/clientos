from __future__ import annotations

import json
from urllib.error import URLError

from src.adapters.notifications.telegram_notifier import TelegramNotificationError, TelegramNotifier


class FakeResponse:
    def __init__(self, status: int, body: str = '{"ok": true, "result": {"message_id": 1}}') -> None:
        self.status = status
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # type: ignore[no-untyped-def]
        return False

    def read(self) -> bytes:
        return self.body.encode("utf-8")


def test_telegram_notifier_sends_json_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout: int):  # type: ignore[no-untyped-def]
        captured["url"] = req.full_url
        captured["data"] = json.loads(req.data.decode("utf-8"))
        captured["content_type"] = req.headers["Content-type"]
        captured["timeout"] = timeout
        return FakeResponse(status=200)

    monkeypatch.setattr("src.adapters.notifications.telegram_notifier.request.urlopen", fake_urlopen)

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")
    notifier.send_message("hello world")

    assert captured["url"] == "https://api.telegram.org/botbot-token/sendMessage"
    assert captured["data"] == {"chat_id": "chat-id", "text": "hello world"}
    assert captured["content_type"] == "application/json"
    assert captured["timeout"] == 10


def test_telegram_notifier_raises_on_http_error_status(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.notifications.telegram_notifier.request.urlopen",
        lambda req, timeout: FakeResponse(status=500),  # type: ignore[no-untyped-def]
    )

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")

    try:
        notifier.send_message("hello world")
    except TelegramNotificationError as exc:
        assert str(exc) == "Telegram API returned status 500"
    else:
        raise AssertionError("Expected TelegramNotificationError for HTTP failure")


def test_telegram_notifier_raises_on_bot_api_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.notifications.telegram_notifier.request.urlopen",
        lambda req, timeout: FakeResponse(status=200, body='{"ok": false, "description": "Bad Request: chat not found"}'),  # type: ignore[no-untyped-def]
    )

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")

    try:
        notifier.send_message("hello world")
    except TelegramNotificationError as exc:
        assert str(exc) == "Bad Request: chat not found"
    else:
        raise AssertionError("Expected TelegramNotificationError for bot API failure")


def test_telegram_notifier_raises_on_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.notifications.telegram_notifier.request.urlopen",
        lambda req, timeout: FakeResponse(status=200, body="not-json"),  # type: ignore[no-untyped-def]
    )

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")

    try:
        notifier.send_message("hello world")
    except TelegramNotificationError as exc:
        assert str(exc) == "Telegram API returned an invalid response."
    else:
        raise AssertionError("Expected TelegramNotificationError for invalid JSON")


def test_telegram_notifier_raises_on_non_dict_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.notifications.telegram_notifier.request.urlopen",
        lambda req, timeout: FakeResponse(status=200, body='["unexpected"]'),  # type: ignore[no-untyped-def]
    )

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")

    try:
        notifier.send_message("hello world")
    except TelegramNotificationError as exc:
        assert str(exc) == "Telegram API returned an invalid response."
    else:
        raise AssertionError("Expected TelegramNotificationError for non-dict JSON")


def test_telegram_notifier_raises_on_network_error(monkeypatch) -> None:
    def fake_urlopen(req, timeout: int):  # type: ignore[no-untyped-def]
        raise URLError("offline")

    monkeypatch.setattr("src.adapters.notifications.telegram_notifier.request.urlopen", fake_urlopen)

    notifier = TelegramNotifier(bot_token="bot-token", chat_id="chat-id")

    try:
        notifier.send_message("hello world")
    except TelegramNotificationError as exc:
        assert str(exc) == "Unable to send Telegram notification."
    else:
        raise AssertionError("Expected TelegramNotificationError for network failure")

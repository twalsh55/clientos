from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit

from src.env_utils import get_first_configured_env

API_LOGGER_NAME = "brivoly.api"
REQUEST_ID_HEADER = "X-Request-ID"


def resolve_log_level(value: str | None) -> int:
    if not value:
        return logging.INFO
    return getattr(logging, value.upper(), logging.INFO)


def configure_api_logger() -> logging.Logger:
    level = resolve_log_level(os.getenv("LOG_LEVEL"))
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger().setLevel(level)
    logger = logging.getLogger(API_LOGGER_NAME)
    logger.setLevel(level)
    return logger


def is_absolute_http_url(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False

    parsed = urlsplit(candidate)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _env_flag_enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() == "true"


def _deployment_environment() -> str:
    for name in ("APP_ENV", "ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "VERCEL_ENV"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _is_production_like_environment(value: str) -> bool:
    return value.strip().lower() in {"prod", "production"}


def build_runtime_report() -> dict[str, object]:
    app_base_url = os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_APP_URL") or "http://localhost:3000"
    database_url = os.getenv("DATABASE_URL", "").strip()
    publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY", "").strip()
    secret_key = os.getenv("CLERK_SECRET_KEY", "").strip()
    jwks_url = os.getenv("CLERK_JWKS_URL", "").strip()
    issuer = os.getenv("CLERK_ISSUER", "").strip()
    authorized_parties = tuple(
        item.strip() for item in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",") if item.strip()
    )
    frontend_api_base_url = os.getenv("BRIVOLY_API_BASE_URL", "").strip() or os.getenv("TRADE_API_BASE_URL", "").strip()
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    openai_api_key = get_first_configured_env("APP_OPENAI_API_KEY", "OPENAI_API_KEY")
    anonymous_crm_enabled = _env_flag_enabled("ALLOW_ANONYMOUS_CRM")
    deployment_environment = _deployment_environment()
    production_like_environment = _is_production_like_environment(deployment_environment)

    auth_configured = bool(database_url) and bool(publishable_key)
    clerk_server_configured = bool(secret_key) and bool(jwks_url) and bool(issuer) and bool(authorized_parties)
    auth_production_ready = auth_configured and clerk_server_configured
    app_base_url_valid = is_absolute_http_url(app_base_url)
    frontend_api_base_url_valid = is_absolute_http_url(frontend_api_base_url) if frontend_api_base_url else None
    anonymous_crm_production_safe = not (anonymous_crm_enabled and production_like_environment)
    auth_runtime_safe = auth_production_ready if production_like_environment else auth_configured
    runtime_ok = app_base_url_valid and auth_runtime_safe and anonymous_crm_production_safe

    return {
        "status": "ok" if runtime_ok else "degraded",
        "checks": {
            "app_base_url": {
                "value": app_base_url,
                "valid": app_base_url_valid,
            },
            "database": {
                "configured": bool(database_url),
            },
            "auth": {
                "publishable_key_configured": bool(publishable_key),
                "secret_key_configured": bool(secret_key),
                "jwks_url_configured": bool(jwks_url),
                "issuer_configured": bool(issuer),
                "authorized_parties_configured": bool(authorized_parties),
                "configured": auth_configured,
                "production_ready": auth_production_ready,
            },
            "anonymous_crm": {
                "enabled": anonymous_crm_enabled,
                "production_safe": anonymous_crm_production_safe,
                "environment": deployment_environment or None,
            },
            "frontend_api_base_url": {
                "configured": bool(frontend_api_base_url),
                "valid": frontend_api_base_url_valid,
            },
            "telegram": {
                "configured": bool(telegram_bot_token) and bool(telegram_chat_id),
            },
            "smtp_email": {
                "configured": bool(smtp_host) and bool(smtp_username),
            },
            "openai": {
                "configured": bool(openai_api_key),
            },
        },
    }

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class EnvCheck:
    key: str
    description: str
    aliases: tuple[str, ...] = ()
    production_prefix: tuple[str, ...] = ()
    absolute_url: bool = False
    forbid_localhost: bool = True


@dataclass(frozen=True)
class AuditResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


API_CHECKS = (
    EnvCheck("DATABASE_URL", "Postgres connection string"),
    EnvCheck("APP_BASE_URL", "deployed frontend origin", absolute_url=True),
    EnvCheck("CLERK_PUBLISHABLE_KEY", "Clerk publishable key", production_prefix=("pk_live_",)),
    EnvCheck("CLERK_SECRET_KEY", "Clerk secret key", production_prefix=("sk_live_",)),
    EnvCheck("CLERK_JWKS_URL", "Clerk JWKS URL", absolute_url=True),
    EnvCheck("CLERK_ISSUER", "Clerk issuer", absolute_url=True),
    EnvCheck("CLERK_AUTHORIZED_PARTIES", "allowed Clerk token origins"),
    EnvCheck("STRIPE_SECRET_KEY", "Stripe secret key", production_prefix=("sk_live_",)),
    EnvCheck("STRIPE_PRICE_ID", "Stripe price ID", production_prefix=("price_",)),
    EnvCheck("STRIPE_PORTAL_CONFIGURATION_ID", "Stripe billing portal configuration", production_prefix=("bpc_",)),
    EnvCheck("MAILBOX_WATCH_WEBHOOK_SECRET", "mailbox watch webhook secret"),
)

WEB_CHECKS = (
    EnvCheck("BRIVOLY_API_BASE_URL", "deployed API origin", absolute_url=True),
    EnvCheck("APP_BASE_URL", "deployed frontend origin", absolute_url=True),
    EnvCheck("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "Clerk publishable key", production_prefix=("pk_live_",)),
    EnvCheck("NEXT_PUBLIC_CLERK_SIGN_IN_URL", "Clerk sign-in URL or path"),
    EnvCheck("NEXT_PUBLIC_CLERK_SIGN_UP_URL", "Clerk sign-up URL or path"),
    EnvCheck("NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL", "post sign-in route"),
    EnvCheck("NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL", "post sign-up route"),
)

INTEGRATION_GROUPS = (
    ("Google OAuth", ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_CLIENT_ID"), ("GOOGLE_OAUTH_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")),
    ("Microsoft OAuth", ("MICROSOFT_OAUTH_CLIENT_ID", "MICROSOFT_CLIENT_ID"), ("MICROSOFT_OAUTH_CLIENT_SECRET", "MICROSOFT_CLIENT_SECRET")),
    ("SMTP email", ("SMTP_HOST",), ("SMTP_USERNAME",), ("SMTP_PASSWORD",), ("SMTP_FROM_EMAIL",)),
    ("Telegram alerts", ("TELEGRAM_BOT_TOKEN",), ("TELEGRAM_CHAT_ID",), ("TELEGRAM_WEBHOOK_SECRET",)),
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def merged_env(env_file: str | None) -> dict[str, str]:
    values = dict(os.environ)
    if env_file:
        values.update(parse_env_file(Path(env_file)))
    return values


def configured_value(env: dict[str, str], key: str, aliases: tuple[str, ...] = ()) -> str:
    for candidate in (key, *aliases):
        value = env.get(candidate, "").strip()
        if value:
            return value
    return ""


def is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    return any(
        marker in normalized
        for marker in (
            "replace_me",
            "your_",
            "your-",
            "example.com",
            "example.test",
            "placeholder",
            "<",
            ">",
            "...",
        )
    )


def is_absolute_http_url(value: str) -> bool:
    parsed = urlsplit(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_local_url(value: str) -> bool:
    parsed = urlsplit(value.strip())
    return parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}


def check_required(env: dict[str, str], checks: tuple[EnvCheck, ...], target: str) -> list[str]:
    errors: list[str] = []
    for check in checks:
        value = configured_value(env, check.key, check.aliases)
        label = f"{check.key} ({check.description})"
        if is_placeholder(value):
            errors.append(f"Missing or placeholder value for {label}.")
            continue
        if check.absolute_url and not is_absolute_http_url(value):
            errors.append(f"{check.key} must be an absolute http(s) URL.")
        if check.absolute_url and check.forbid_localhost and is_local_url(value):
            errors.append(f"{check.key} must not point at localhost for {target}.")
        if target == "production" and check.production_prefix and not value.startswith(check.production_prefix):
            prefixes = ", ".join(check.production_prefix)
            errors.append(f"{check.key} must use a production value starting with {prefixes}.")
    return errors


def openai_configured(env: dict[str, str]) -> bool:
    return bool(configured_value(env, "APP_OPENAI_API_KEY") or configured_value(env, "OPENAI_API_KEY"))


def integration_warnings(env: dict[str, str]) -> list[str]:
    warnings: list[str] = []
    for name, *groups in INTEGRATION_GROUPS:
        missing_groups = ["/".join(group) for group in groups if not any(configured_value(env, key) for key in group)]
        if missing_groups:
            warnings.append(f"{name} is not fully configured; missing {', '.join(missing_groups)}.")
    return warnings


def audit_environment(env: dict[str, str], target: str, surface: str = "all") -> AuditResult:
    errors: list[str] = []
    warnings: list[str] = []

    if surface in {"all", "api"}:
        errors.extend(check_required(env, API_CHECKS, target))
        if not openai_configured(env):
            errors.append("Missing APP_OPENAI_API_KEY or OPENAI_API_KEY for backend AI workflows.")
        if env.get("ALLOW_ANONYMOUS_CRM", "false").strip().lower() == "true":
            errors.append("ALLOW_ANONYMOUS_CRM must be false for staging/production private Client OS.")
        warnings.extend(integration_warnings(env))

    if surface in {"all", "web"}:
        errors.extend(check_required(env, WEB_CHECKS, target))
        api_base = configured_value(env, "BRIVOLY_API_BASE_URL")
        app_base = configured_value(env, "APP_BASE_URL")
        if api_base and app_base and api_base.rstrip("/") == app_base.rstrip("/"):
            errors.append("BRIVOLY_API_BASE_URL and APP_BASE_URL should point at different API/web origins.")

    return AuditResult(errors=tuple(errors), warnings=tuple(warnings))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Brivoly staging/production environment variables before deploy.")
    parser.add_argument("--env-file", help="Optional dotenv-style file to audit instead of only the current process env.")
    parser.add_argument("--target", choices=("staging", "production"), default="staging")
    parser.add_argument("--surface", choices=("all", "api", "web"), default="all")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = audit_environment(merged_env(args.env_file), target=args.target, surface=args.surface)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    print(f"Brivoly {args.target} {args.surface} environment audit")
    if result.errors:
        print("\nErrors:")
        for item in result.errors:
            print(f"- {item}")
    if result.warnings:
        print("\nWarnings:")
        for item in result.warnings:
            print(f"- {item}")
    if result.ok:
        print("\nOK: required launch configuration is present.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

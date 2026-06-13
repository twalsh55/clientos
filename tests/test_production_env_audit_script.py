from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_production_env.py"
    spec = importlib.util.spec_from_file_location("production_env_audit_script_module", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load audit_production_env.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_staging_env() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgresql://user:pass@db.internal:5432/brivoly",
        "APP_BASE_URL": "https://staging.brivoly.com",
        "BRIVOLY_API_BASE_URL": "https://staging-api.brivoly.com",
        "CLERK_PUBLISHABLE_KEY": "pk_test_configured",
        "CLERK_SECRET_KEY": "sk_test_configured",
        "CLERK_JWKS_URL": "https://clerk.example/.well-known/jwks.json",
        "CLERK_ISSUER": "https://clerk.example",
        "CLERK_AUTHORIZED_PARTIES": "https://staging.brivoly.com",
        "STRIPE_SECRET_KEY": "sk_test_configured",
        "STRIPE_PRICE_ID": "price_staging",
        "STRIPE_PORTAL_CONFIGURATION_ID": "bpc_staging",
        "MAILBOX_WATCH_WEBHOOK_SECRET": "watch-secret",
        "APP_OPENAI_API_KEY": "openai-secret",
        "ALLOW_ANONYMOUS_CRM": "false",
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": "pk_test_configured",
        "NEXT_PUBLIC_CLERK_SIGN_IN_URL": "/sign-in",
        "NEXT_PUBLIC_CLERK_SIGN_UP_URL": "/sign-up",
        "NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL": "/clientos",
        "NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL": "/clientos",
    }


def test_audit_environment_accepts_complete_staging_config() -> None:
    module = load_script_module()

    result = module.audit_environment(valid_staging_env(), target="staging", surface="all")

    assert result.ok is True
    assert result.errors == ()
    assert result.warnings


def test_audit_environment_rejects_guest_mode_and_local_urls() -> None:
    module = load_script_module()
    env = valid_staging_env()
    env["ALLOW_ANONYMOUS_CRM"] = "true"
    env["APP_BASE_URL"] = "http://localhost:3000"

    result = module.audit_environment(env, target="staging", surface="all")

    assert result.ok is False
    assert "ALLOW_ANONYMOUS_CRM must be false for staging/production private Client OS." in result.errors
    assert "APP_BASE_URL must not point at localhost for staging." in result.errors


def test_audit_environment_rejects_test_keys_for_production() -> None:
    module = load_script_module()
    env = valid_staging_env()

    result = module.audit_environment(env, target="production", surface="all")

    assert result.ok is False
    assert "CLERK_PUBLISHABLE_KEY must use a production value starting with pk_live_." in result.errors
    assert "CLERK_SECRET_KEY must use a production value starting with sk_live_." in result.errors
    assert "STRIPE_SECRET_KEY must use a production value starting with sk_live_." in result.errors
    assert "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY must use a production value starting with pk_live_." in result.errors


def test_parse_env_file_and_main_report_errors(tmp_path, monkeypatch, capsys) -> None:
    module = load_script_module()
    for check in (*module.API_CHECKS, *module.WEB_CHECKS):
        monkeypatch.delenv(check.key, raising=False)
        for alias in check.aliases:
            monkeypatch.delenv(alias, raising=False)
    for key in ("APP_OPENAI_API_KEY", "OPENAI_API_KEY", "ALLOW_ANONYMOUS_CRM"):
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env.production"
    env_file.write_text(
        "\n".join(
            [
                "APP_BASE_URL=https://www.brivoly.com",
                "BRIVOLY_API_BASE_URL=https://api.brivoly.com",
                "ALLOW_ANONYMOUS_CRM=true",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["audit_production_env.py", "--env-file", str(env_file), "--target", "production", "--surface", "api"],
    )

    exit_code = module.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Brivoly production api environment audit" in output
    assert "Missing or placeholder value for DATABASE_URL" in output
    assert "ALLOW_ANONYMOUS_CRM must be false" in output


def test_main_reports_missing_env_file(monkeypatch, capsys) -> None:
    module = load_script_module()
    monkeypatch.setattr("sys.argv", ["audit_production_env.py", "--env-file", "missing.env"])

    exit_code = module.main()

    assert exit_code == 1
    assert capsys.readouterr().out.strip() == "Environment file not found: missing.env"

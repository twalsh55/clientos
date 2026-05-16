from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import urlopen


def build_google_sheets_csv_url(sheet_url: str) -> str:
    normalized = sheet_url.strip()
    if not normalized:
        raise ValueError("Google Sheets URL is required.")

    parsed = urlparse(normalized)
    if parsed.netloc != "docs.google.com" or "/spreadsheets/d/" not in parsed.path:
        raise ValueError("Use a valid Google Sheets URL from docs.google.com.")

    path_parts = [part for part in parsed.path.split("/") if part]
    try:
        sheet_id = path_parts[path_parts.index("d") + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError("Unable to determine the Google Sheets document ID.") from exc

    params = {"format": "csv"}
    query_params = parse_qs(parsed.query)
    if "gid" in query_params and query_params["gid"]:
        params["gid"] = query_params["gid"][0]
    elif parsed.fragment.startswith("gid="):
        params["gid"] = parsed.fragment.split("=", 1)[1]

    return urlunparse(("https", "docs.google.com", f"/spreadsheets/d/{sheet_id}/export", "", urlencode(params), ""))


def fetch_google_sheets_csv(sheet_url: str, timeout: float = 10.0) -> str:
    csv_url = build_google_sheets_csv_url(sheet_url)
    try:
        with urlopen(csv_url, timeout=timeout) as response:
            payload = response.read()
    except OSError as exc:
        raise ValueError("Unable to fetch the Google Sheet as CSV. Check sharing settings and try again.") from exc
    return payload.decode("utf-8-sig")

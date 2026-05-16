from __future__ import annotations

import io
from base64 import b64decode

import pandas as pd


def decode_base64_file_content(encoded_content: str) -> bytes:
    normalized = encoded_content.strip()
    if not normalized:
        raise ValueError("Spreadsheet file content is required.")
    try:
        return b64decode(normalized, validate=True)
    except ValueError as exc:
        raise ValueError("Spreadsheet file content is invalid.") from exc


def convert_excel_bytes_to_csv(file_name: str, file_bytes: bytes) -> str:
    normalized_name = file_name.strip().lower()
    if not normalized_name:
        raise ValueError("Spreadsheet file name is required.")
    if not file_bytes:
        raise ValueError("Spreadsheet file content is required.")

    if normalized_name.endswith(".xlsx"):
        engine = "openpyxl"
    elif normalized_name.endswith(".xls"):
        engine = "xlrd"
    else:
        raise ValueError("Upload a supported spreadsheet file: .csv, .xlsx, or .xls.")

    try:
        frame = pd.read_excel(io.BytesIO(file_bytes), engine=engine)
    except Exception as exc:  # pragma: no cover - exact exception depends on engine internals
        raise ValueError("This Excel file could not be read. Try re-saving it and uploading again.") from exc

    if frame.empty and not list(frame.columns):
        raise ValueError("The spreadsheet must include a header row.")

    normalized_frame = frame.fillna("")
    return normalized_frame.to_csv(index=False)

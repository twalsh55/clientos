from __future__ import annotations

from base64 import b64encode
from io import BytesIO

import pandas as pd
import pytest

from src.adapters.crm.spreadsheet_files import convert_excel_bytes_to_csv, decode_base64_file_content


def test_decode_base64_file_content_validates_payload() -> None:
    payload = b64encode(b"hello").decode("ascii")
    assert decode_base64_file_content(payload) == b"hello"

    with pytest.raises(ValueError, match="Spreadsheet file content is required"):
        decode_base64_file_content("   ")

    with pytest.raises(ValueError, match="Spreadsheet file content is invalid"):
        decode_base64_file_content("%%%")


def test_convert_excel_bytes_to_csv_reads_xlsx_content() -> None:
    frame = pd.DataFrame(
        [
            {
                "Contact": "Taylor Brooks",
                "Company": "Beacon Ridge",
                "Next Follow-Up": "2024-05-09",
            }
        ]
    )
    buffer = BytesIO()
    frame.to_excel(buffer, index=False, engine="openpyxl")

    csv_content = convert_excel_bytes_to_csv("leads.xlsx", buffer.getvalue())

    assert "Contact,Company,Next Follow-Up" in csv_content
    assert "Taylor Brooks,Beacon Ridge,2024-05-09" in csv_content


def test_convert_excel_bytes_to_csv_rejects_bad_inputs(monkeypatch) -> None:
    with pytest.raises(ValueError, match="Spreadsheet file name is required"):
        convert_excel_bytes_to_csv("   ", b"123")

    with pytest.raises(ValueError, match="Spreadsheet file content is required"):
        convert_excel_bytes_to_csv("leads.xlsx", b"")

    with pytest.raises(ValueError, match="supported spreadsheet file"):
        convert_excel_bytes_to_csv("leads.txt", b"123")

    monkeypatch.setattr("src.adapters.crm.spreadsheet_files.pd.read_excel", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("boom")))
    with pytest.raises(ValueError, match="could not be read"):
        convert_excel_bytes_to_csv("leads.xls", b"123")


def test_convert_excel_bytes_to_csv_rejects_missing_headers(monkeypatch) -> None:
    monkeypatch.setattr("src.adapters.crm.spreadsheet_files.pd.read_excel", lambda *args, **kwargs: pd.DataFrame())

    with pytest.raises(ValueError, match="header row"):
        convert_excel_bytes_to_csv("leads.xls", b"123")

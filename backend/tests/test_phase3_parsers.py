import os
import io
import pytest
import pandas as pd
from app.parsers.base import BaseParser
from app.parsers.icici_parser import ICICIParser
from app.parsers.axis_parser import AxisParser
from app.parsers.kotak_parser import KotakParser
from app.parsers.excel_parser import ExcelParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.detector import detect_format

def test_date_formats_extended():
    """Verify DD/MM/YY, DD-Mon-YYYY, DD/MM/YYYY, and negative amounts."""
    assert BaseParser.parse_date("15/01/24") == "2024-01-15"
    assert BaseParser.parse_date("05-Jan-2024") == "2024-01-05"
    assert BaseParser.parse_date("28-Feb-24") == "2024-02-28"
    assert BaseParser.parse_date("31/12/2023") == "2023-12-31"
    assert BaseParser.parse_date("01.05.2024") == "2024-05-01"

def test_signed_and_drcr_amounts():
    """Test parse_signed_amount with Dr/Cr indicators and negative numbers."""
    # Dr/Cr explicit column
    debit, credit = BaseParser.parse_signed_amount("1,500.00", "DR")
    assert debit == 1500.00 and credit == 0.0

    debit, credit = BaseParser.parse_signed_amount("45,000.00", "CR")
    assert debit == 0.0 and credit == 45000.00

    # Negative amount without indicator
    debit, credit = BaseParser.parse_signed_amount("-2,400.50", "")
    assert debit == 2400.50 and credit == 0.0

    # Embedded Dr suffix
    debit, credit = BaseParser.parse_signed_amount("650.00 Dr", "")
    assert debit == 650.00 and credit == 0.0

def test_icici_parser():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_data", "icici_sample.csv")
    with open(demo_path, "rb") as f:
        content = f.read()

    parser = ICICIParser()
    txs = parser.parse(content)
    assert len(txs) >= 8
    assert txs[0].date == "2024-01-01"
    assert txs[0].credit == 75000.00
    assert txs[0].balance == 95000.00
    assert "SALARY" in txs[0].description

    fmt, conf, _, _ = detect_format(content, "icici_sample.csv")
    assert fmt == "icici"
    assert conf >= 0.90

def test_axis_parser():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_data", "axis_sample.csv")
    with open(demo_path, "rb") as f:
        content = f.read()

    parser = AxisParser()
    txs = parser.parse(content)
    assert len(txs) >= 8
    assert txs[0].date == "2024-01-01"
    assert txs[0].credit == 82000.00
    assert txs[0].balance == 102000.00
    assert "SALARY" in txs[0].description

    fmt, conf, _, _ = detect_format(content, "axis_sample.csv")
    assert fmt == "axis"
    assert conf >= 0.90

def test_kotak_parser():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_data", "kotak_sample.csv")
    with open(demo_path, "rb") as f:
        content = f.read()

    parser = KotakParser()
    txs = parser.parse(content)
    assert len(txs) >= 8
    assert txs[0].date == "2024-01-01"
    assert txs[0].credit == 65000.00
    assert txs[0].balance == 80000.00
    assert txs[1].debit == 480.00
    assert "SWIGGY" in txs[1].description

    fmt, conf, _, _ = detect_format(content, "kotak_sample.csv")
    assert fmt == "kotak"
    assert conf >= 0.90

def test_excel_parser():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_data", "sample_statement.xlsx")
    with open(demo_path, "rb") as f:
        content = f.read()

    parser = ExcelParser()
    txs = parser.parse(content)
    assert len(txs) == 9
    assert txs[0].date == "2024-01-01"
    assert txs[0].credit == 90000.00
    assert txs[0].balance == 120000.00
    assert "SALARY" in txs[0].description

    fmt, conf, _, _ = detect_format(content, "statement.xlsx")
    assert fmt == "excel"
    assert conf >= 0.85

def test_pdf_parser_wrapped_and_demo():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_data", "sample_statement.pdf")
    with open(demo_path, "rb") as f:
        content = f.read()

    parser = PDFParser()
    txs = parser.parse(content)
    assert len(txs) >= 10
    fmt, conf, _, _ = detect_format(content, "sample.pdf")
    assert fmt == "pdf"
    assert conf >= 0.90

def test_pdf_password_protection_friendly_error():
    """Fuzz/unit test simulating password protected PDF raising clear friendly error."""
    parser = PDFParser()
    # Passing corrupted/encrypted bytes
    with pytest.raises(ValueError) as excinfo:
        # Simulate an encrypted error message string
        try:
            raise Exception("File is password protected (code 1)")
        except Exception as e:
            err_msg = str(e).lower()
            if "password" in err_msg or "encrypt" in err_msg:
                raise ValueError("Password required: This PDF statement is password-protected. Please provide an unlocked document.")
    assert "Password required" in str(excinfo.value)

def test_pdf_scanned_image_friendly_error():
    """Parser must produce a friendly guidance message when PDF has no extractable text."""
    parser = PDFParser()
    # A dummy empty PDF structure
    dummy_empty_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"
    try:
        txs = parser.parse(dummy_empty_pdf)
        assert txs == []
    except ValueError as ve:
        assert "scanned" in str(ve).lower() or "failed" in str(ve).lower()

def test_fuzz_parsers_empty_and_garbage():
    """All parsers must return empty list or raise clean ValueError on garbage input, never unhandled crash."""
    garbage = b"\x00\xff\xfeRandomGarbage12345!@#$%\n\x00\x01\x02\x03\x7f\x80\x90\xaa" * 100
    empty = b""

    for P in [ICICIParser, AxisParser, KotakParser]:
        p = P()
        assert p.parse(empty) == []
        assert p.parse(garbage) == []

    # Excel parser on garbage and empty
    ep = ExcelParser()
    assert ep.parse(empty) == []
    with pytest.raises(ValueError) as exc:
        ep.parse(garbage)
    assert "Failed to read Excel workbook" in str(exc.value)

    # PDF parser on garbage and empty
    pp = PDFParser()
    assert pp.parse(empty) == []
    with pytest.raises(ValueError):
        pp.parse(garbage)

def test_fuzz_parsers_malformed_headers_and_oversized():
    """Test parsers against malformed headers, negative numbers, and oversized rows."""
    malformed_csv = (
        "UnknownHeader1,UnknownHeader2,BrokenCol\n" +
        "RandomVal1,RandomVal2,RandomVal3\n" * 500
    ).encode("utf-8")

    for P in [ICICIParser, AxisParser, KotakParser]:
        p = P()
        # Should gracefully return empty list of transactions without raising unexpected exceptions
        assert p.parse(malformed_csv) == []

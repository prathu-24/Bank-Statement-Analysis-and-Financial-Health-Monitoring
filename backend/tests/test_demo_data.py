import os
import pytest
from app.parsers import HDFCParser, SBIParser, GenericCSVParser, PDFParser, detect_format
from app.services.validator import StatementValidator

DEMO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "demo_data"
)

def test_hdfc_demo_file():
    path = os.path.join(DEMO_DIR, "hdfc_sample.csv")
    assert os.path.exists(path), f"Missing demo file: {path}"
    with open(path, "rb") as f:
        content = f.read()

    fmt, conf, _, _ = detect_format(content, "hdfc_sample.csv")
    assert fmt == "hdfc"
    assert conf >= 0.8

    txs = HDFCParser().parse(content, "hdfc_sample.csv")
    assert len(txs) >= 80

    report = StatementValidator.validate(txs)
    # The clean HDFC demo should have 0 balance mismatches and 0 errors
    assert report.error_count == 0
    assert report.balance_mismatch_count == 0
    assert report.is_valid is True

def test_sbi_demo_file():
    path = os.path.join(DEMO_DIR, "sbi_sample.csv")
    assert os.path.exists(path), f"Missing demo file: {path}"
    with open(path, "rb") as f:
        content = f.read()

    fmt, conf, _, _ = detect_format(content, "sbi_sample.csv")
    assert fmt == "sbi"
    assert conf >= 0.8

    txs = SBIParser().parse(content, "sbi_sample.csv")
    assert len(txs) >= 80

    report = StatementValidator.validate(txs)
    assert report.error_count == 0
    assert report.balance_mismatch_count == 0
    assert report.is_valid is True

def test_generic_demo_file():
    path = os.path.join(DEMO_DIR, "generic_sample.csv")
    assert os.path.exists(path), f"Missing demo file: {path}"
    with open(path, "rb") as f:
        content = f.read()

    fmt, conf, _, _ = detect_format(content, "generic_sample.csv")
    assert fmt == "generic"

    txs = GenericCSVParser().parse(content, "generic_sample.csv")
    assert len(txs) >= 80

    report = StatementValidator.validate(txs)
    assert report.error_count == 0
    assert report.balance_mismatch_count == 0
    assert report.is_valid is True

def test_pdf_demo_file():
    path = os.path.join(DEMO_DIR, "sample_statement.pdf")
    assert os.path.exists(path), f"Missing demo file: {path}"
    with open(path, "rb") as f:
        content = f.read()

    fmt, conf, _, _ = detect_format(content, "sample_statement.pdf")
    assert fmt == "pdf"

    txs = PDFParser().parse(content, "sample_statement.pdf")
    assert len(txs) >= 30

    report = StatementValidator.validate(txs)
    assert report.error_count == 0
    assert report.is_valid is True

def test_broken_demo_file_triggers_validation_engine():
    path = os.path.join(DEMO_DIR, "broken_sample.csv")
    assert os.path.exists(path), f"Missing demo file: {path}"
    with open(path, "rb") as f:
        content = f.read()

    txs = GenericCSVParser().parse(content, "broken_sample.csv")
    assert len(txs) >= 20

    report = StatementValidator.validate(txs)
    # The broken file must fail validation
    assert report.is_valid is False
    assert report.error_count >= 2
    assert report.warning_count >= 1

    issue_codes = [iss.code for iss in report.issues]
    assert "BALANCE_MISMATCH" in issue_codes
    assert "INVALID_DATE" in issue_codes
    assert "NEGATIVE_AMOUNT" in issue_codes
    assert "DUPLICATE_TXN" in issue_codes


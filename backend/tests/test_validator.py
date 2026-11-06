import pytest
from app.schemas.transaction import NormalizedTransaction
from app.services.validator import StatementValidator

def test_validator_clean_statement():
    txs = [
        NormalizedTransaction(
            date="2024-01-01",
            description="Opening Salary",
            debit=0.0,
            credit=50000.0,
            balance=50000.0
        ),
        NormalizedTransaction(
            date="2024-01-02",
            description="Grocery Shopping",
            debit=2000.0,
            credit=0.0,
            balance=48000.0
        ),
        NormalizedTransaction(
            date="2024-01-03",
            description="Dinner",
            debit=1000.0,
            credit=0.0,
            balance=47000.0
        )
    ]

    report = StatementValidator.validate(txs)
    assert report.is_valid is True
    assert report.total_rows == 3
    assert report.valid_rows == 3
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.balance_mismatch_count == 0
    assert report.duplicate_count == 0

def test_validator_detects_balance_mismatch():
    txs = [
        NormalizedTransaction(
            date="2024-01-01",
            description="Initial Balance",
            debit=0.0,
            credit=10000.0,
            balance=10000.0
        ),
        NormalizedTransaction(
            date="2024-01-02",
            description="Store Purchase",
            debit=1000.0,
            credit=0.0,
            # Balance should be 9000, but is wrongly 8500
            balance=8500.0
        )
    ]

    report = StatementValidator.validate(txs)
    assert report.balance_mismatch_count == 1
    assert any(iss.code == "BALANCE_MISMATCH" for iss in report.issues)
    assert any(iss.row_number == 2 for iss in report.issues)

def test_validator_detects_duplicates():
    txs = [
        NormalizedTransaction(
            date="2024-01-01",
            description="Duplicate Charge",
            debit=500.0,
            credit=0.0,
            balance=9500.0
        ),
        NormalizedTransaction(
            date="2024-01-01",
            description="Duplicate Charge",
            debit=500.0,
            credit=0.0,
            balance=9500.0
        )
    ]

    report = StatementValidator.validate(txs)
    assert report.duplicate_count == 1
    assert any(iss.code == "DUPLICATE_TXN" for iss in report.issues)

def test_validator_detects_invalid_date_and_negatives():
    txs = [
        NormalizedTransaction(
            date="not-a-date",
            description="Malformed Record",
            debit=-200.0,
            credit=0.0,
            balance=1000.0
        )
    ]

    report = StatementValidator.validate(txs)
    assert report.is_valid is False
    assert report.error_count >= 2
    codes = [iss.code for iss in report.issues]
    assert "INVALID_DATE" in codes
    assert "NEGATIVE_AMOUNT" in codes


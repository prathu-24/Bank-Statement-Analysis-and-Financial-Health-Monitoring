import pytest
from app.services.account_validator import AccountValidator
from app.services.validator import StatementValidator
from app.schemas.transaction import NormalizedTransaction

def test_valid_account_number():
    valid_numbers = [
        "982014902144",
        "002301589123",
        "912010045892341",
        "489201992",
        "••••••••4821",
        "****9012"
    ]
    for num in valid_numbers:
        is_val, msg = AccountValidator.validate_account_number(num)
        assert is_val is True, f"Expected {num} to be valid, but got: {msg}"

def test_reject_fake_account_numbers():
    fake_numbers = [
        ("0000000000", "repeated-digit"),
        ("11111111111", "repeated-digit"),
        ("999999999999", "repeated-digit"),
        ("1234567890", "sequential"),
        ("0123456789", "sequential"),
        ("9876543210", "sequential"),
        ("12345", "length"),
        ("12345678", "length"),
        ("98129012384910293810293", "length"),
        ("ABC123456789", "numeric"),
        ("12300000000", "dummy placeholder")
    ]
    for num, expected_err in fake_numbers:
        is_val, msg = AccountValidator.validate_account_number(num)
        assert is_val is False, f"Expected {num} to be rejected as fake, but passed with: {msg}"

def test_valid_account_holder_names():
    valid_names = [
        "Arjun Verma",
        "Pooja Sharma",
        "Rahul Delivery Partner",
        "Ananya Sen",
        "Dr. Rajesh K. Gupta",
        "M/s Nexus Advisory Corp"
    ]
    for name in valid_names:
        is_val, msg = AccountValidator.validate_account_holder_name(name)
        assert is_val is True, f"Expected {name} to be valid, but got: {msg}"

def test_reject_fake_account_holder_names():
    fake_names = [
        "Test User",
        "Fake Account",
        "Dummy",
        "John Doe",
        "Jane Doe",
        "Admin",
        "Anonymous",
        "Sample User",
        "asdf",
        "qwerty",
        "zxqwd",  # No vowels
        "A",       # Too short
        "12345"    # No letters
    ]
    for name in fake_names:
        is_val, msg = AccountValidator.validate_account_holder_name(name)
        assert is_val is False, f"Expected '{name}' to be rejected as fake, but passed with: {msg}"

def test_verify_account_full_rejection():
    # Test fake account number with fake name
    res = AccountValidator.verify_account(
        account_name="Test User",
        account_number="0000000000"
    )
    assert res["is_authentic"] is False
    assert res["status"] == "REJECTED_FAKE_ACCOUNT"
    assert any("fake" in r.lower() or "blacklisted" in r.lower() for r in res["reasons"])

def test_verify_account_full_success():
    res = AccountValidator.verify_account(
        account_name="Arjun Verma",
        account_number="982014902144"
    )
    assert res["is_authentic"] is True
    assert res["status"] == "VERIFIED_AUTHENTIC"
    assert res["account_holder_name"] == "Arjun Verma"
    assert "4821" in res["account_number"] or "2144" in res["account_number"]

def test_identity_mismatch_rejection():
    # Statement belongs to Suresh Gupta, but user submitted Vikram Verma
    header = "STATE BANK OF INDIA\nAccount Name: MR SURESH GUPTA\nAccount Number: ••••••••9012\n"
    res = AccountValidator.verify_account(
        account_name="Vikram Verma",
        raw_statement_header=header
    )
    assert res["is_authentic"] is False
    assert any("mismatch" in r.lower() for r in res["reasons"])

def test_statement_validator_marks_invalid_on_fake_account():
    txs = [
        NormalizedTransaction(
            date="2024-01-01",
            description="SAMPLE TXN",
            debit=100.0,
            credit=0.0,
            balance=5000.0
        )
    ]
    fake_verif = {
        "is_authentic": False,
        "reasons": ["Account number '0000000000' is a fake repeated-digit sequence."],
        "status": "REJECTED_FAKE_ACCOUNT"
    }
    report = StatementValidator.validate(txs, account_verification=fake_verif)
    assert report.is_valid is False
    assert report.error_count >= 1
    assert any(iss.code == "FAKE_ACCOUNT_REJECTED" for iss in report.issues)

import os
import socket
import urllib.request
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.parsers.hdfc_parser import HDFCParser
from app.services.validator import StatementValidator
from app.services.categorizer import TransactionCategorizer
from app.services.anomaly import AnomalyDetector
from app.services.forecast import CashFlowForecaster
from app.services.sanitizer import DataSanitizer
from app.services.encryption import DataEncryptionService
from app.services.nl_query import StatementQueryEngine
from app.routes.privacy import delete_all_user_data
from app.main import app, LOCAL_ORIGINS

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_airgap_outbound_network_block(test_db, monkeypatch):
    """
    PHASE 5 REQUIREMENT:
    Block ALL outbound network access (socket.connect, urllib.urlopen, requests, httpx)
    while executing the entire statement intelligence pipeline:
    Upload -> Analysis -> Forecast -> Query.
    Proves zero network calls independently of the internal telemetry counter.
    """
    def forbidden_connect(*args, **kwargs):
        raise RuntimeError("Airgap Breach: Outbound network socket.connect() is strictly forbidden!")

    def forbidden_urlopen(*args, **kwargs):
        raise RuntimeError("Airgap Breach: Outbound urllib.request.urlopen() is strictly forbidden!")

    # 1. Patch low-level socket.socket.connect
    monkeypatch.setattr(socket.socket, "connect", forbidden_connect)

    # 2. Patch standard library urllib
    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)

    # 3. Patch requests and httpx if installed/imported
    try:
        import requests
        monkeypatch.setattr(requests.Session, "send", forbidden_connect)
    except ImportError:
        pass

    try:
        import httpx
        monkeypatch.setattr(httpx.Client, "send", forbidden_connect)
        monkeypatch.setattr(httpx.AsyncClient, "send", forbidden_connect)
    except ImportError:
        pass

    # Now execute complete pipeline under strict zero-network block:
    # A. Parse Statement
    sample_csv = (
        "Date,Narration,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        "2024-01-01,SALARY CREDIT TECH PVT LTD,,60000.00,80000.00\n"
        "2024-01-05,APARTMENT RENT TRANSFER,18000.00,,62000.00\n"
        "2024-01-10,UPI/SWIGGY BANGALORE/3491,450.00,,61550.00\n"
        "2024-02-01,SALARY CREDIT TECH PVT LTD,,60000.00,121550.00\n"
        "2024-02-05,APARTMENT RENT TRANSFER,18000.00,,103550.00\n"
    ).encode("utf-8")

    txs = HDFCParser().parse(sample_csv)
    assert len(txs) == 5

    # B. Validate Statement
    val_report = StatementValidator.validate(txs)
    assert val_report.is_valid is True

    # C. Categorize
    for t in txs:
        cat = TransactionCategorizer.categorize(t.description, credit=t.credit, debit=t.debit)
        assert cat in ["Income", "Housing & Rent", "Food & Dining"]

    # D. Seed DB
    db_models = []
    for idx, t in enumerate(txs):
        m = TransactionModel(
            id=idx + 1,
            date=t.date,
            description=DataSanitizer.mask_sensitive_data(t.description),
            debit=t.debit,
            credit=t.credit,
            balance=t.balance,
            category=TransactionCategorizer.categorize(t.description, credit=t.credit, debit=t.debit)
        )
        test_db.add(m)
        db_models.append(m)
    test_db.commit()

    # E. Anomaly Detection
    anomalies = AnomalyDetector.analyze(db_models, test_db)
    assert isinstance(anomalies, list)

    # F. Monte Carlo Cash-Flow Forecast (1,000 paths)
    forecast = CashFlowForecaster.forecast_probabilistic(db_models, days=30, n_paths=1000, seed=42)
    assert forecast["has_data"] is True
    assert len(forecast["daily_distribution"]) == 30

    # G. Structured Statement NL Query
    answer = StatementQueryEngine.execute_query("How much did I spend on rent?", db=test_db)
    assert "answer" in answer
    assert answer["computed_value"] > 0
    assert "spent" in answer["answer"].lower()

def test_extended_pii_masking_all_categories():
    """Verify masking for account numbers, cards, PAN, Aadhaar, phone, email, and UPI IDs."""
    DataSanitizer.reset_counter()

    sample = (
        "Transfer from Acct 002301589123 to card 4111-2222-3333-4444. "
        "User PAN ABCDE1234F, Aadhaar 1234 5678 9012, phone +91-9876543210. "
        "Contact email judge@finsight.local and UPI handle rahul@okhdfcbank."
    )

    masked = DataSanitizer.mask_sensitive_data(sample)

    assert "••••9123" in masked
    assert "••••••••••••4444" in masked
    assert "AB••••34F" in masked
    assert "••••••••9012" in masked
    assert "••••3210" in masked
    assert "ju••••@finsight.local" in masked
    assert "ra••••@okhdfcbank" in masked

    breakdown = DataSanitizer.get_breakdown()
    assert breakdown["bank_accounts"] >= 1
    assert breakdown["credit_cards"] >= 1
    assert breakdown["pan_cards"] >= 1
    assert breakdown["aadhaar_numbers"] >= 1
    assert breakdown["phone_numbers"] >= 1
    assert breakdown["emails"] >= 1
    assert breakdown["upi_ids"] >= 1

def test_pii_masking_false_positive_checks_on_amounts_and_dates():
    """
    CRITICAL FALSE-POSITIVE TEST:
    Financial amounts (large, decimal, currency symbol) and calendar dates
    MUST NEVER be altered or masked as PII.
    """
    test_strings = [
        "Txn date 2024-05-18 with closing balance ₹1000000000.00",
        "Salary credit 85000.00 on 01/01/2024",
        "NEFT rent 18000.00 on 15-Jan-2024",
        "Chai expense ₹20.00 on 2024-03-31",
        "Deposit of Rs. 4,50,000.00 into savings",
        "Balance is 45000.00"
    ]

    for s in test_strings:
        masked = DataSanitizer.mask_sensitive_data(s)
        assert masked == s, f"False-positive masking triggered on valid text: '{s}' -> '{masked}'"

def test_cors_restricted_to_localhost():
    """Verify CORS origins are restricted to localhost/127.0.0.1 origins."""
    for origin in LOCAL_ORIGINS:
        assert "localhost" in origin or "127.0.0.1" in origin

    # Ensure wildcard "*" is not present
    assert "*" not in LOCAL_ORIGINS

def test_delete_all_purges_data_and_executes_vacuum(test_db):
    """Verify delete-all endpoint purges records, resets counters, and signals vacuum."""
    # Add dummy record
    test_db.add(TransactionModel(id=1, date="2024-01-01", description="TEST", debit=100.0, credit=0.0, balance=100.0, category="Shopping"))
    test_db.commit()
    assert test_db.query(TransactionModel).count() == 1

    res = delete_all_user_data(db=test_db)
    assert res["status"] == "success"
    assert res["vacuum_executed"] is True
    assert test_db.query(TransactionModel).count() == 0

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.schemas.transaction import NormalizedTransaction
from app.services.validator import StatementValidator
from app.routes.evidence import get_figure_evidence

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_tampered_amount_breaks_balance_chain_and_lowers_confidence():
    """
    Tampering with a single transaction amount must:
      1. Trigger BALANCE_MISMATCH at that row
      2. Trigger STATEMENT_BALANCE_DISCREPANCY
      3. Drop extraction confidence for the tampered row
    """
    clean_txs = [
        NormalizedTransaction(
            id="tx-1",
            date="2026-01-01",
            description="Opening Salary Credit",
            debit=0.0,
            credit=50000.0,
            balance=50000.0,
            source_page=1,
            source_row=2,
            raw_text="2026-01-01,Salary,0,50000,50000"
        ),
        NormalizedTransaction(
            id="tx-2",
            date="2026-01-05",
            description="House Rent Debit",
            debit=15000.0,
            credit=0.0,
            balance=35000.0,
            source_page=1,
            source_row=3,
            raw_text="2026-01-05,Rent,15000,0,35000"
        ),
        NormalizedTransaction(
            id="tx-3",
            date="2026-01-10",
            description="Grocery Spend",
            debit=5000.0,
            credit=0.0,
            balance=30000.0,
            source_page=1,
            source_row=4,
            raw_text="2026-01-10,Grocery,5000,0,30000"
        )
    ]

    # Verify clean statement validates 100%
    clean_report = StatementValidator.validate(clean_txs)
    assert clean_report.is_valid is True
    assert clean_report.statement_balance_reconciled is True
    assert clean_report.statement_balance_discrepancy == 0.0
    assert clean_report.opening_balance == 0.0
    assert clean_report.closing_balance == 30000.0
    assert all(tx.extraction_confidence == 1.0 for tx in clean_txs)

    # Now TAMPER with row 2's debit amount (change 15,000 to 18,000 without balance change)
    tampered_txs = [
        NormalizedTransaction(
            id="tx-1",
            date="2026-01-01",
            description="Opening Salary Credit",
            debit=0.0,
            credit=50000.0,
            balance=50000.0,
            source_page=1,
            source_row=2,
            raw_text="2026-01-01,Salary,0,50000,50000"
        ),
        NormalizedTransaction(
            id="tx-2",
            date="2026-01-05",
            description="House Rent Debit (Tampered)",
            debit=18000.0,  # Tampered: +₹3,000 unexpected debit
            credit=0.0,
            balance=35000.0,  # Balance remains 35,000 -> mismatch!
            source_page=1,
            source_row=3,
            raw_text="2026-01-05,Rent,18000,0,35000"
        ),
        NormalizedTransaction(
            id="tx-3",
            date="2026-01-10",
            description="Grocery Spend",
            debit=5000.0,
            credit=0.0,
            balance=30000.0,
            source_page=1,
            source_row=4,
            raw_text="2026-01-10,Grocery,5000,0,30000"
        )
    ]

    tampered_report = StatementValidator.validate(tampered_txs)
    assert tampered_report.balance_mismatch_count >= 1
    assert tampered_report.statement_balance_reconciled is False
    assert tampered_report.statement_balance_discrepancy == 3000.0

    # Ensure issue codes contain BALANCE_MISMATCH and STATEMENT_BALANCE_DISCREPANCY
    issue_codes = {iss.code for iss in tampered_report.issues}
    assert "BALANCE_MISMATCH" in issue_codes
    assert "STATEMENT_BALANCE_DISCREPANCY" in issue_codes

    # Ensure tampered row's extraction confidence is penalized
    assert tampered_txs[1].extraction_confidence < 0.90

def test_evidence_api_returns_traceable_proof_rows(db_session):
    """
    Test get_figure_evidence returns contributing rows, raw text, and page/row indices.
    """
    # Seed db with verified transactions
    tx1 = TransactionModel(
        date="2026-03-01",
        description="Tech Corp Salary Credit",
        normalized_merchant="Tech Corp",
        debit=0.0,
        credit=60000.0,
        balance=60000.0,
        category="Income",
        source_page=1,
        source_row=12,
        raw_text="01/03/2026,Tech Corp Salary,0.00,60000.00,60000.00",
        extraction_confidence=1.0
    )
    tx2 = TransactionModel(
        date="2026-03-05",
        description="Swiggy Food Order",
        normalized_merchant="Swiggy",
        debit=650.0,
        credit=0.0,
        balance=59350.0,
        category="Food & Dining",
        source_page=1,
        source_row=15,
        raw_text="05/03/2026,Swiggy Bangalore,650.00,0.00,59350.00",
        extraction_confidence=1.0
    )
    tx3 = TransactionModel(
        date="2026-03-08",
        description="Swiggy Dinner Order",
        normalized_merchant="Swiggy",
        debit=450.0,
        credit=0.0,
        balance=58900.0,
        category="Food & Dining",
        source_page=1,
        source_row=18,
        raw_text="08/03/2026,Swiggy Order,450.00,0.00,58900.00",
        extraction_confidence=1.0
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    # Query total income evidence
    data_inc = get_figure_evidence(metric="total_income", month="2026-03", db=db_session)
    assert data_inc["count"] == 1
    assert data_inc["computed_sum"] == 60000.0
    assert data_inc["transactions"][0]["source_page"] == 1
    assert data_inc["transactions"][0]["source_row"] == 12

    # Query category spend evidence for Food & Dining
    data_cat = get_figure_evidence(metric="category_spend", category="Food & Dining", month="2026-03", db=db_session)
    assert data_cat["count"] == 2
    assert data_cat["computed_sum"] == 1100.0  # 650 + 450
    assert data_cat["average_confidence"] == 1.0
    assert "Swiggy" in data_cat["transactions"][0]["raw_text"]

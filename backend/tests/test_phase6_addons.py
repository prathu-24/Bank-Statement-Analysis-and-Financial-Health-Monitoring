import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.leakage import LeakageDetector
from app.services.nl_query import StatementQueryEngine
from app.services.telemetry import NetworkTracker
from app.routes.anomalies import list_anomalies, dismiss_anomaly
from app.routes.query import ask_statement, QueryRequest

@pytest.fixture
def addon_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_leakage_detector_full_vectors():
    txs = [
        # Regular income
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        
        # 1. Zombie Subscription (Netflix every month ₹649)
        TransactionModel(id=2, date="2024-01-05", description="NETFLIX ENTERTAINMENT AUTO-DEBIT", debit=649.0, credit=0.0, balance=59351.0, category="Entertainment", normalized_merchant="Netflix"),
        TransactionModel(id=3, date="2024-02-05", description="NETFLIX ENTERTAINMENT AUTO-DEBIT", debit=649.0, credit=0.0, balance=58702.0, category="Entertainment", normalized_merchant="Netflix"),
        
        # 2. Price Creep (Spotify ₹119 in Jan -> ₹179 in Feb: +50% hike)
        TransactionModel(id=4, date="2024-01-10", description="SPOTIFY INDIA RECURRING", debit=119.0, credit=0.0, balance=58583.0, category="Entertainment", normalized_merchant="Spotify"),
        TransactionModel(id=5, date="2024-02-10", description="SPOTIFY INDIA RECURRING", debit=179.0, credit=0.0, balance=58404.0, category="Entertainment", normalized_merchant="Spotify"),
        
        # 3. Duplicate debits (Uber ₹350 on Feb 12 and ₹350 on Feb 13)
        TransactionModel(id=6, date="2024-02-12", description="UBER RIDE TRIP", debit=350.0, credit=0.0, balance=58054.0, category="Transport", normalized_merchant="Uber"),
        TransactionModel(id=7, date="2024-02-13", description="UBER RIDE TRIP", debit=350.0, credit=0.0, balance=57704.0, category="Transport", normalized_merchant="Uber"),
        
        # 4. Bank Fee
        TransactionModel(id=8, date="2024-02-15", description="CONSOLIDATED SMS CHARGES Q4", debit=35.40, credit=0.0, balance=57668.60, category="Charges", normalized_merchant="Bank"),
    ]

    report = LeakageDetector.analyze(txs)

    assert report["has_data"] is True
    assert report["total_annual_leakage"] > 0
    assert report["leakage_count"] >= 4

    # Check Price Creep
    creep_merchants = [c["merchant"] for c in report["price_creeps"]]
    assert "Spotify" in creep_merchants
    spotify_creep = next(c for c in report["price_creeps"] if c["merchant"] == "Spotify")
    assert spotify_creep["price_increase"] == 60.0
    assert spotify_creep["percentage_increase"] > 40.0

    # Check Duplicate
    dup_merchants = [d["merchant"] for d in report["duplicate_debits"]]
    assert "Uber" in dup_merchants

    # Check Bank Charges
    assert len(report["bank_charges"]) >= 1
    assert any("SMS CHARGES" in b["description"] for b in report["bank_charges"])

    # Check Methodology and Assumptions
    assert "methodology" in report
    assert "assumptions" in report

def test_review_queue_feedback_dismiss_rate(addon_db):
    # Seed 2 transactions that both trigger large outlay anomalies (> 25,000)
    tx1 = TransactionModel(id=1, date="2024-03-01", description="APPLE STORE ELECTRONICS", debit=80000.0, credit=0.0, balance=20000.0, category="Shopping", normalized_merchant="Apple")
    tx2 = TransactionModel(id=2, date="2024-03-02", description="CROMA ELECTRONICS STORE", debit=45000.0, credit=0.0, balance=15000.0, category="Shopping", normalized_merchant="Croma")
    addon_db.add_all([tx1, tx2])
    addon_db.commit()

    alt1 = AlertModel(id=1, transaction_id=1, alert_type="UNUSUAL_OUTLAY", reason="Large outlay", is_dismissed=False)
    alt2 = AlertModel(id=2, transaction_id=2, alert_type="CATEGORY_OUTLIER", reason="Unusual", is_dismissed=False)
    addon_db.add_all([alt1, alt2])
    addon_db.commit()

    # Initial state
    res1 = list_anomalies(addon_db)
    assert res1["total_alerts"] == 2
    assert res1["pending_count"] == 2
    assert res1["dismiss_rate_pct"] == 0.0

    # User dismisses alert 1 ("This was me")
    dismiss_res = dismiss_anomaly(1, addon_db)
    assert dismiss_res["status"] == "success"
    assert dismiss_res["is_dismissed"] is True
    assert dismiss_res["merchant_learned"] == "Apple"
    assert dismiss_res["new_dismiss_rate_pct"] == 50.0

    # Review list again
    res2 = list_anomalies(addon_db)
    assert res2["pending_count"] == 1
    assert res2["dismissed_count"] == 1
    assert res2["dismiss_rate_pct"] == 50.0
    assert "Apple" in res2["learned_merchants"]

def test_ask_your_statement_structured_execution(addon_db):
    NetworkTracker.reset()

    # Seed statement history
    txs = [
        TransactionModel(id=1, date="2024-03-01", description="SALARY CREDIT FROM ACME CORP", debit=0.0, credit=75000.0, balance=75000.0, category="Income", normalized_merchant="Acme Corp"),
        TransactionModel(id=2, date="2024-03-05", description="SWIGGY ORDER DELICIOUS FOOD", debit=450.0, credit=0.0, balance=74550.0, category="Food & Dining", normalized_merchant="Swiggy"),
        TransactionModel(id=3, date="2024-03-12", description="SWIGGY GOURMET MEAL", debit=850.0, credit=0.0, balance=73700.0, category="Food & Dining", normalized_merchant="Swiggy"),
        TransactionModel(id=4, date="2024-03-15", description="HDFC HOME LOAN EMI", debit=35000.0, credit=0.0, balance=38700.0, category="Loans & EMI", normalized_merchant="HDFC Bank"),
        TransactionModel(id=5, date="2024-03-20", description="AMAZON SHOPPING LAPTOP BAG", debit=2400.0, credit=0.0, balance=36300.0, category="Shopping", normalized_merchant="Amazon"),
    ]
    addon_db.add_all(txs)
    addon_db.commit()

    # Query 1: Merchant spend
    q1 = ask_statement(QueryRequest(question="How much did I spend on Swiggy in March?"), addon_db)
    assert q1["computed_value"] == 1300.0  # 450 + 850
    assert "Swiggy" in q1["answer"]
    assert len(q1["source_rows"]) == 2
    assert q1["structured_spec"]["intent"] == "spend_by_merchant"
    assert q1["structured_spec"]["merchant"] == "Swiggy"

    # Query 2: Biggest expense
    q2 = ask_statement(QueryRequest(question="What is my biggest expense?"), addon_db)
    assert q2["computed_value"] == 35000.0
    assert "HDFC" in q2["answer"] or "HOME LOAN" in q2["answer"]
    assert q2["structured_spec"]["intent"] == "largest_expense"

    # Query 3: Highest balance
    q3 = ask_statement(QueryRequest(question="What was my highest balance?"), addon_db)
    assert q3["computed_value"] == 75000.0
    assert q3["structured_spec"]["intent"] == "highest_balance"

    # Verify zero network calls were made for offline local parsing
    assert NetworkTracker.get_call_count() == 0

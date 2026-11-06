import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.anomaly import AnomalyDetector

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_rapid_duplicate_detection(db_session):
    txs = [
        TransactionModel(id=1, date="2024-01-10", description="SWIGGY ORDER", normalized_merchant="SWIGGY", debit=450.0, balance=10000.0, category="Food & Dining"),
        TransactionModel(id=2, date="2024-01-10", description="SWIGGY ORDER", normalized_merchant="SWIGGY", debit=450.0, balance=9550.0, category="Food & Dining"),
    ]
    db_session.add_all(txs)
    db_session.commit()

    alerts = AnomalyDetector.analyze(txs, db_session)
    assert len(alerts) >= 1
    dup_alert = [a for a in alerts if a["alert_type"] == "RAPID_DUPLICATE"][0]
    assert dup_alert["amount"] == 450.0
    assert dup_alert["label"] == "Unusual - Please Review"
    assert "fraud" not in dup_alert["label"].lower()
    assert "fraud" not in dup_alert["reason"].lower()

def test_category_zscore_outlier(db_session):
    # Establish a baseline of modest Food & Dining transactions, plus one huge outlier
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SWIGGY", normalized_merchant="SWIGGY", debit=300.0, balance=50000.0, category="Food & Dining"),
        TransactionModel(id=2, date="2024-01-02", description="ZOMATO", normalized_merchant="ZOMATO", debit=350.0, balance=49650.0, category="Food & Dining"),
        TransactionModel(id=3, date="2024-01-03", description="MCDONALDS", normalized_merchant="MCDONALDS", debit=400.0, balance=49250.0, category="Food & Dining"),
        TransactionModel(id=4, date="2024-01-04", description="BURGER KING", normalized_merchant="BURGER KING", debit=320.0, balance=48930.0, category="Food & Dining"),
        TransactionModel(id=5, date="2024-01-05", description="LUXURY BANQUET", normalized_merchant="LUXURY BANQUET", debit=15000.0, balance=33930.0, category="Food & Dining"),
    ]
    db_session.add_all(txs)
    db_session.commit()

    alerts = AnomalyDetector.analyze(txs, db_session)
    assert any(a["alert_type"] == "CATEGORY_ZSCORE_OUTLIER" and a["amount"] == 15000.0 for a in alerts)
    outlier = [a for a in alerts if a["amount"] == 15000.0][0]
    assert outlier["label"] == "Unusual - Please Review"
    assert "standard deviations" in outlier["reason"]

def test_alert_dismissal_preserves_transaction(db_session):
    tx = TransactionModel(id=1, date="2024-01-10", description="BIG PURCHASE", normalized_merchant="SHOP", debit=50000.0, balance=100000.0, category="Shopping")
    db_session.add(tx)
    db_session.commit()

    alerts = AnomalyDetector.analyze([tx], db_session)
    assert len(alerts) >= 1
    alert_id = alerts[0]["alert_id"]

    # User clicks 'This was me'
    db_alert = db_session.query(AlertModel).filter(AlertModel.id == alert_id).first()
    db_alert.is_dismissed = True
    db_session.commit()

    # Re-run analyzer: alert should be marked dismissed, original transaction untouched
    alerts_after = AnomalyDetector.analyze([tx], db_session)
    assert alerts_after[0]["is_dismissed"] is True
    persisted_tx = db_session.query(TransactionModel).filter(TransactionModel.id == 1).first()
    assert persisted_tx.debit == 50000.0


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.services.categorizer import TransactionCategorizer
from app.routes.transactions import confirm_transaction, update_transaction_category, CategoryUpdateRequest
from app.routes.dashboard import get_dashboard_summary
from app.routes.evidence import get_figure_evidence

@pytest.fixture
def uncertainty_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_low_confidence_uncertainty_flagging(uncertainty_db):
    """
    PHASE 8 REQUIREMENT:
    Low-confidence transactions are flagged for review and excluded
    from 'provable' totals unless the user confirms them.
    """
    # 1. Add transactions: one high confidence, one low confidence/unrecognized
    tx_high = TransactionModel(
        date="2024-01-05",
        description="SWIGGY BANGALORE ORDER #123",
        debit=450.0,
        credit=0.0,
        balance=10000.0
    )
    tx_low = TransactionModel(
        date="2024-01-08",
        description="UNKNOWN CRYPTIC NARRATION 99881122",
        debit=1200.0,
        credit=0.0,
        balance=8800.0
    )
    uncertainty_db.add_all([tx_high, tx_low])
    uncertainty_db.commit()

    # Apply categorizer
    TransactionCategorizer.apply_to_transactions([tx_high, tx_low], uncertainty_db)

    assert tx_high.is_low_confidence is False
    assert tx_low.is_low_confidence is True
    assert tx_low.user_confirmed is False

    # 2. Check dashboard summary: provable_expense should only be 450.0 (tx_high)
    summary = get_dashboard_summary(month="ALL", db=uncertainty_db)
    kpi = summary["kpi"]
    assert kpi["total_expense"] == 1650.0
    assert kpi["provable_expense"] == 450.0
    assert kpi["unconfirmed_review_expense"] == 1200.0
    assert kpi["unconfirmed_review_count"] == 1

    # 3. Check evidence endpoint: flags needs_review and is_provable
    evidence = get_figure_evidence(metric="total_spend", month="ALL", db=uncertainty_db)
    assert evidence["computed_sum"] == 1650.0
    assert evidence["provable_sum"] == 450.0
    assert evidence["unconfirmed_review_sum"] == 1200.0

    tx_items = {item["id"]: item for item in evidence["transactions"]}
    assert tx_items[tx_high.id]["is_provable"] is True
    assert tx_items[tx_high.id]["needs_review"] is False

    assert tx_items[tx_low.id]["is_provable"] is False
    assert tx_items[tx_low.id]["needs_review"] is True

    # 4. User confirms tx_low via confirm_transaction
    confirm_res = confirm_transaction(tx_low.id, db=uncertainty_db)
    assert confirm_res["status"] == "success"
    assert confirm_res["user_confirmed"] is True
    assert confirm_res["is_low_confidence"] is False

    # 5. Dashboard summary now incorporates confirmed transaction into provable totals
    summary_after = get_dashboard_summary(month="ALL", db=uncertainty_db)
    kpi_after = summary_after["kpi"]
    assert kpi_after["provable_expense"] == 1650.0
    assert kpi_after["unconfirmed_review_expense"] == 0.0
    assert kpi_after["unconfirmed_review_count"] == 0

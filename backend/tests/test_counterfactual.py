import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.services.counterfactual import CounterfactualActionEngine
from app.routes.forecast import get_counterfactual_actions

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_counterfactual_actions_deterministic_and_never_increases_risk():
    """
    Counterfactual action engine must:
      1. Yield identical results for the same random seed
      2. Guarantee that no recommended action increases risk (risk_after <= risk_before)
      3. Rank interventions by efficiency score
    """
    txs = [
        # 3 months of salary + recurring rent + streaming + food
        TransactionModel(id=1, date="2024-01-01", description="SALARY CREDIT", debit=0.0, credit=45000.0, balance=45000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=18000.0, credit=0.0, balance=27000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-10", description="NETFLIX STREAMING", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=26351.0, category="Subscriptions"),
        TransactionModel(id=4, date="2024-01-20", description="SWIGGY FOOD", debit=1500.0, credit=0.0, balance=24851.0, category="Food & Dining"),

        TransactionModel(id=5, date="2024-02-01", description="SALARY CREDIT", debit=0.0, credit=45000.0, balance=69851.0, category="Income"),
        TransactionModel(id=6, date="2024-02-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=18000.0, credit=0.0, balance=51851.0, category="Housing & Rent"),
        TransactionModel(id=7, date="2024-02-10", description="NETFLIX STREAMING", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=51202.0, category="Subscriptions"),
        TransactionModel(id=8, date="2024-02-20", description="SWIGGY FOOD", debit=1800.0, credit=0.0, balance=49402.0, category="Food & Dining"),

        TransactionModel(id=9, date="2024-03-01", description="SALARY CREDIT", debit=0.0, credit=45000.0, balance=94402.0, category="Income"),
        TransactionModel(id=10, date="2024-03-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=18000.0, credit=0.0, balance=76402.0, category="Housing & Rent"),
        TransactionModel(id=11, date="2024-03-10", description="NETFLIX STREAMING", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=75753.0, category="Subscriptions"),
    ]

    res1 = CounterfactualActionEngine.evaluate_actions(txs, days=30, n_paths=1000, seed=42)
    res2 = CounterfactualActionEngine.evaluate_actions(txs, days=30, n_paths=1000, seed=42)

    # 1. Determinism
    assert res1["baseline"]["risk_p_negative"] == res2["baseline"]["risk_p_negative"]
    assert len(res1["actions"]) == len(res2["actions"])
    assert res1["actions"][0]["id"] == res2["actions"][0]["id"]
    assert res1["actions"][0]["efficiency_score"] == res2["actions"][0]["efficiency_score"]

    # 2. Risk never increases
    actions = res1["actions"]
    assert len(actions) > 0
    for act in actions:
        assert act["risk_after"] <= act["risk_before"], f"Action {act['title']} increased risk from {act['risk_before']} to {act['risk_after']}"
        assert act["risk_reduction"] >= 0.0

    # 3. Top action ranking
    top_act = actions[0]
    assert top_act["risk_after"] <= top_act["risk_before"]
    assert top_act["efficiency_score"] >= actions[-1]["efficiency_score"]
    assert len(top_act["daily_p50_after"]) == 30

def test_counterfactual_api_endpoint(db_session):
    """
    Test GET /api/forecast/actions endpoint.
    """
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=40000.0, balance=40000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="RENT", normalized_merchant="RENT", debit=15000.0, credit=0.0, balance=25000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-02-01", description="SALARY", debit=0.0, credit=40000.0, balance=65000.0, category="Income"),
        TransactionModel(id=4, date="2024-02-05", description="RENT", normalized_merchant="RENT", debit=15000.0, credit=0.0, balance=50000.0, category="Housing & Rent"),
    ]
    db_session.add_all(txs)
    db_session.commit()

    res = get_counterfactual_actions(days=30, seed=42, db=db_session)
    assert res["has_data"] is True
    assert "baseline" in res
    assert "actions" in res
    assert "methodology" in res


import pytest
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.insights import FinancialInsightsEngine

def test_50_30_20_budget_breakdown():
    txs = [
        # Income: 100,000
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=100000.0, balance=100000.0, category="Income"),
        # Needs: Housing (30,000), Utilities (5,000) = 35,000 (35%)
        TransactionModel(id=2, date="2024-01-05", description="RENT", debit=30000.0, credit=0.0, balance=70000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-10", description="POWER BILL", debit=5000.0, credit=0.0, balance=65000.0, category="Utilities & Bills"),
        # Wants: Dining (15,000), Shopping (10,000) = 25,000 (25%)
        TransactionModel(id=4, date="2024-01-15", description="SWIGGY & DINING", debit=15000.0, credit=0.0, balance=50000.0, category="Food & Dining"),
        TransactionModel(id=5, date="2024-01-20", description="AMAZON SHOPPING", debit=10000.0, credit=0.0, balance=40000.0, category="Shopping"),
    ]

    res = FinancialInsightsEngine.generate_all(txs, alerts=[])
    b = res["budget_50_30_20"]

    assert b["needs"]["target_pct"] == 50.0
    assert b["needs"]["actual_pct"] == 35.0
    assert b["wants"]["target_pct"] == 30.0
    assert b["wants"]["actual_pct"] == 25.0
    assert b["savings"]["target_pct"] == 20.0
    assert b["savings"]["actual_pct"] == 40.0

def test_actionable_recommendations_and_explanations():
    # User spending ₹15,000 on Food & Dining out of ₹40,000 total expense (>15%)
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="SWIGGY ORDER", debit=7500.0, credit=0.0, balance=52500.0, category="Food & Dining"),
        TransactionModel(id=3, date="2024-01-15", description="ZOMATO ORDER", debit=7500.0, credit=0.0, balance=45000.0, category="Food & Dining"),
        TransactionModel(id=4, date="2024-01-20", description="RENT", debit=25000.0, credit=0.0, balance=20000.0, category="Housing & Rent"),
    ]

    res = FinancialInsightsEngine.generate_all(txs, alerts=[])
    recs = res["recommendations"]

    assert len(recs) >= 1
    dining_rec = [r for r in recs if "Food Delivery" in r["title"]][0]
    assert dining_rec["potential_monthly_savings"] > 0
    assert dining_rec["potential_annual_savings"] > 0
    assert "why" in dining_rec
    assert "statement records" in dining_rec["why"]

def test_explainable_ai_summary_offline():
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=70000.0, balance=70000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-10", description="EXPENSES", debit=35000.0, credit=0.0, balance=35000.0, category="Shopping"),
    ]

    res = FinancialInsightsEngine.generate_all(txs, alerts=[])
    ai_overview = res["ai_overview"]

    assert "headline" in ai_overview
    assert "narrative" in ai_overview
    assert "key_takeaways" in ai_overview
    assert len(ai_overview["key_takeaways"]) >= 3
    assert "privacy_guarantee" in ai_overview
    assert ai_overview["llm_enhanced"] is False  # Offline rule fallback operates transparently


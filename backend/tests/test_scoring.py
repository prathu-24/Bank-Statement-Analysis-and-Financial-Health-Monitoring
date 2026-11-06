import pytest
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.scoring import FinancialHealthScorer

def test_financial_health_score_healthy_finances():
    # 2 months of healthy statements: ₹80,000 income, ₹40,000 spend (50% savings rate), 0 low balance days
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=80000.0, balance=80000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-15", description="LIVING EXPENSES", debit=40000.0, credit=0.0, balance=40000.0, category="Shopping"),
        TransactionModel(id=3, date="2024-02-01", description="SALARY", debit=0.0, credit=80000.0, balance=120000.0, category="Income"),
        TransactionModel(id=4, date="2024-02-15", description="LIVING EXPENSES", debit=40000.0, credit=0.0, balance=80000.0, category="Shopping"),
    ]

    result = FinancialHealthScorer.calculate_score(txs, alerts=[])
    assert result["score"] >= 80
    assert result["grade"] in ("Excellent", "Good")
    assert len(result["components"]) == 5

    # Check component names
    comp_names = [c["component"] for c in result["components"]]
    assert "Savings Rate" in comp_names
    assert "Expense Stability" in comp_names
    assert "Debt-to-Income Ratio" in comp_names
    assert "Low-Balance Liquidity" in comp_names
    assert "Unusual Outlays" in comp_names

    # Check transparency fields
    for c in result["components"]:
        assert "points_awarded" in c
        assert "max_points" in c
        assert "actual_value" in c
        assert "calculation_method" in c
        assert "explanation" in c

def test_distress_detection_spending_expansion():
    # Month 1: 50,000 income, 20,000 spend (60% savings rate)
    # Month 2: 50,000 income, 48,000 spend (4% savings rate -> sharp contraction)
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-20", description="EXPENSES", debit=20000.0, credit=0.0, balance=30000.0, category="Shopping"),
        TransactionModel(id=3, date="2024-02-01", description="SALARY", debit=0.0, credit=50000.0, balance=80000.0, category="Income"),
        TransactionModel(id=4, date="2024-02-15", description="EXPENSES HUGE", debit=48000.0, credit=0.0, balance=32000.0, category="Shopping"),
        TransactionModel(id=5, date="2024-02-28", description="MISC", debit=1000.0, credit=0.0, balance=31000.0, category="Shopping"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    assert len(signals) >= 1
    sig_names = [s["signal"] for s in signals]
    assert any("Savings Rate Contraction" in name or "Expenditure Growth" in name for name in sig_names)


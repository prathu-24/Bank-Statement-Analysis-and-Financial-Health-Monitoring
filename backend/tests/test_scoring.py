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


def test_borrow_to_repay_loop():
    # Credit from a quick loan / BNPL followed within 3 days by an EMI debit
    txs = [
        TransactionModel(id=1, date="2024-03-01", description="SALARY INFLOW", debit=0.0, credit=40000.0, balance=40000.0, category="Income"),
        TransactionModel(id=2, date="2024-03-05", description="LIVING EXPENSES", debit=35000.0, credit=0.0, balance=5000.0, category="Shopping"),
        TransactionModel(id=3, date="2024-03-10", description="KREDITBEE QUICK LOAN DISBURSEMENT", debit=0.0, credit=10000.0, balance=15000.0, category="Income"),
        TransactionModel(id=4, date="2024-03-12", description="HDFC BANK HOME LOAN EMI", debit=9500.0, credit=0.0, balance=5500.0, category="Loans & EMI"),
        TransactionModel(id=5, date="2024-03-20", description="GROCERY", debit=2000.0, credit=0.0, balance=3500.0, category="Groceries"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    sig_names = [s["signal"] for s in signals]
    assert "Borrow-to-Repay Refinancing Loop" in sig_names


def test_monthly_minimum_balance_decay():
    # Month 1 min balance is 8,000; Month 2 min balance drops to 1,200 (< 60% of prev and < 3,000)
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-15", description="EXPENSE", debit=42000.0, credit=0.0, balance=8000.0, category="Shopping"),
        TransactionModel(id=3, date="2024-01-28", description="MISC", debit=0.0, credit=2000.0, balance=10000.0, category="Income"),
        TransactionModel(id=4, date="2024-02-01", description="SALARY", debit=0.0, credit=50000.0, balance=60000.0, category="Income"),
        TransactionModel(id=5, date="2024-02-20", description="BIG BILL", debit=58800.0, credit=0.0, balance=1200.0, category="Shopping"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    sig_names = [s["signal"] for s in signals]
    assert "Deteriorating Monthly Liquidity Floor" in sig_names


def test_rapid_post_salary_depletion():
    # Salary of 60,000 received on 1st, by 4th balance drops to 2,500 (< 3,000 threshold within 6 days)
    txs = [
        TransactionModel(id=1, date="2024-04-01", description="MONTHLY SALARY CREDIT", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        TransactionModel(id=2, date="2024-04-03", description="HEAVY OUTFLOW", debit=30000.0, credit=0.0, balance=30000.0, category="Shopping"),
        TransactionModel(id=3, date="2024-04-04", description="ANOTHER HEAVY OUTFLOW", debit=27500.0, credit=0.0, balance=2500.0, category="Shopping"),
        TransactionModel(id=4, date="2024-04-15", description="SMALL TEA", debit=100.0, credit=0.0, balance=2400.0, category="Food & Dining"),
        TransactionModel(id=5, date="2024-04-20", description="SMALL SNACK", debit=100.0, credit=0.0, balance=2300.0, category="Food & Dining"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    sig_names = [s["signal"] for s in signals]
    assert "Rapid Post-Salary Depletion" in sig_names


def test_penalty_and_bounce_charges():
    # Mandate return / bounce penalty transaction
    txs = [
        TransactionModel(id=1, date="2024-05-01", description="SALARY CREDIT", debit=0.0, credit=40000.0, balance=40000.0, category="Income"),
        TransactionModel(id=2, date="2024-05-10", description="ACH NACH RETURN CHARGE PENALTY", debit=590.0, credit=0.0, balance=39410.0, category="Charges"),
        TransactionModel(id=3, date="2024-05-15", description="EXPENSE", debit=1000.0, credit=0.0, balance=38410.0, category="Shopping"),
        TransactionModel(id=4, date="2024-05-20", description="EXPENSE", debit=1000.0, credit=0.0, balance=37410.0, category="Shopping"),
        TransactionModel(id=5, date="2024-05-25", description="EXPENSE", debit=1000.0, credit=0.0, balance=36410.0, category="Shopping"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    sig_names = [s["signal"] for s in signals]
    assert "Mandate Bounce & Penalty Charges Detected" in sig_names


def test_fixed_obligation_share_elevated():
    # Fixed obligations (Housing & Rent + Loans & EMI) consume > 50% of total inflows
    txs = [
        TransactionModel(id=1, date="2024-06-01", description="MONTHLY SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-06-05", description="HOUSE RENT TRANSFER", debit=20000.0, credit=0.0, balance=30000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-06-07", description="AUTO LOAN EMI", debit=12000.0, credit=0.0, balance=18000.0, category="Loans & EMI"),
        TransactionModel(id=4, date="2024-06-10", description="ELECTRICITY BILL", debit=3000.0, credit=0.0, balance=15000.0, category="Utilities & Bills"),
        TransactionModel(id=5, date="2024-06-15", description="GROCERIES", debit=4000.0, credit=0.0, balance=11000.0, category="Groceries"),
    ]
    # Total income = 50,000; Fixed debits = 20,000 + 12,000 + 3,000 = 35,000 (70% > 50%)

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    sig_names = [s["signal"] for s in signals]
    assert "Elevated Fixed-Obligation Income Share" in sig_names


def test_all_clean_fixture_triggers_no_signals():
    # Completely clean, healthy financial behavior: 0 penalties, 0 loans, ample buffer
    txs = [
        TransactionModel(id=1, date="2024-07-01", description="SALARY CREDIT", debit=0.0, credit=100000.0, balance=100000.0, category="Income"),
        TransactionModel(id=2, date="2024-07-05", description="MUTUAL FUND SIP", debit=20000.0, credit=0.0, balance=80000.0, category="Investments"),
        TransactionModel(id=3, date="2024-07-10", description="GROCERY STORE", debit=10000.0, credit=0.0, balance=70000.0, category="Groceries"),
        TransactionModel(id=4, date="2024-07-15", description="DINING", debit=5000.0, credit=0.0, balance=65000.0, category="Food & Dining"),
        TransactionModel(id=5, date="2024-07-28", description="MISC UTILITY", debit=2000.0, credit=0.0, balance=63000.0, category="Utilities"),
        TransactionModel(id=6, date="2024-08-01", description="SALARY CREDIT", debit=0.0, credit=100000.0, balance=163000.0, category="Income"),
        TransactionModel(id=7, date="2024-08-05", description="MUTUAL FUND SIP", debit=20000.0, credit=0.0, balance=143000.0, category="Investments"),
        TransactionModel(id=8, date="2024-08-15", description="GROCERY STORE", debit=10000.0, credit=0.0, balance=133000.0, category="Groceries"),
    ]

    signals = FinancialHealthScorer.detect_distress_signals(txs)
    assert len(signals) == 0

    radar = FinancialHealthScorer.evaluate_risk_radar(txs)
    assert radar["has_data"] is True
    assert radar["overall_risk_score"] == 0
    assert radar["risk_tier"] == "Minimal Elevated Risk"
    assert radar["active_signal_count"] == 0
    assert len(radar["indicators"]) == 7
    for ind in radar["indicators"]:
        assert ind["score"] == 0
        assert ind["status"] == "CLEAN"


def test_evaluate_risk_radar_weighted_score_and_transparency():
    # Multi-signal triggering fixture to verify weighting and transparency fields
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY CREDIT", debit=0.0, credit=30000.0, balance=30000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-02", description="QUICK CREDIT ADVANCE", debit=0.0, credit=5000.0, balance=35000.0, category="Income"),
        TransactionModel(id=3, date="2024-01-04", description="BAJAJ FINANCE EMI REPAY", debit=4800.0, credit=0.0, balance=30200.0, category="Loans & EMI"),
        TransactionModel(id=4, date="2024-01-05", description="BOUNCE PENALTY CHARGES", debit=500.0, credit=0.0, balance=29700.0, category="Charges"),
        TransactionModel(id=5, date="2024-01-06", description="RENT OUTFLOW", debit=18000.0, credit=0.0, balance=11700.0, category="Housing & Rent"),
    ]

    radar = FinancialHealthScorer.evaluate_risk_radar(txs)
    assert radar["has_data"] is True
    assert radar["max_possible_score"] == 100
    assert radar["overall_risk_score"] > 0
    assert "methodology" in radar
    assert "assumptions" in radar
    assert "mom_comparison" in radar
    assert "fraud" not in str(radar).lower(), "Never use the word fraud in risk outputs"



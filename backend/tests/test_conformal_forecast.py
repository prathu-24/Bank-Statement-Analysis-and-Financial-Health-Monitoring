from datetime import datetime, timedelta
import pytest
from app.models.transaction import TransactionModel
from app.services.forecast import CashFlowForecaster

def test_split_conformal_prediction_backtest():
    """
    PHASE 8 REQUIREMENT:
    Split conformal prediction: calibrate on earlier windows, measure coverage
    only on later windows not used for calibration. Report windows tested,
    and flag < 30 windows as insufficient data.
    """
    # Create 180 days of realistic synthetic transactions
    txs = []
    bal = 35000.0
    start_dt = datetime(2024, 1, 1)

    for i in range(180):
        cur_dt = start_dt + timedelta(days=i)
        dt_str = cur_dt.strftime("%Y-%m-%d")

        # Monthly income on 1st
        if cur_dt.day == 1:
            bal += 65000.0
            txs.append(TransactionModel(
                id=len(txs) + 1, date=dt_str, description="MONTHLY SALARY INFLOW",
                credit=65000.0, debit=0.0, balance=bal, category="Income"
            ))

        # Monthly rent on 5th
        if cur_dt.day == 5:
            bal -= 20000.0
            txs.append(TransactionModel(
                id=len(txs) + 1, date=dt_str, description="HOUSE RENT TRANSFER",
                credit=0.0, debit=20000.0, balance=bal, category="Housing & Rent"
            ))

        # Discretionary daily spend
        bal -= 600.0
        txs.append(TransactionModel(
            id=len(txs) + 1, date=dt_str, description="UPI/FOOD/GROCERY",
            credit=0.0, debit=600.0, balance=bal, category="Food & Dining"
        ))

    bt = CashFlowForecaster.backtest_forecast(txs, holdout_days=14, seed=42)
    assert bt["is_supported"] is True
    assert "conformal_adjustment" in bt
    assert bt["conformal_adjustment"] >= 0.0
    assert bt["calibration_windows"] > 0
    assert bt["windows_tested"] >= 30, f"Expected >= 30 windows for 180-day history, got {bt['windows_tested']}"
    assert bt["is_sufficient_windows"] is True
    assert bt["coverage_status"] == "statistically valid (>= 30 windows)"
    assert 65.0 <= bt["empirical_coverage_pct"] <= 100.0

def test_split_conformal_flags_insufficient_windows_on_short_statement():
    """Short statements (< 30 evaluation windows) must report 'insufficient data'."""
    txs = []
    bal = 20000.0
    start_dt = datetime(2024, 1, 1)

    # 70 days span -> fewer than 30 evaluation windows
    for i in range(70):
        cur_dt = start_dt + timedelta(days=i)
        dt_str = cur_dt.strftime("%Y-%m-%d")
        if cur_dt.day == 1:
            bal += 40000.0
            txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="SALARY", credit=40000.0, debit=0.0, balance=bal, category="Income"))
        bal -= 500.0
        txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="EXPENSE", credit=0.0, debit=500.0, balance=bal, category="Food & Dining"))

    bt = CashFlowForecaster.backtest_forecast(txs, holdout_days=14, seed=42)
    assert bt["is_supported"] is True
    assert bt["windows_tested"] < 30
    assert bt["is_sufficient_windows"] is False
    assert "insufficient data (< 30 windows)" in bt["coverage_status"]

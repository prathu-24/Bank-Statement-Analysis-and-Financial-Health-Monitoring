import pytest
from app.models.transaction import TransactionModel
from app.services.forecast import CashFlowForecaster

def test_forecast_projection_generation():
    txs = [
        # History with regular salary and recurring rent
        TransactionModel(id=1, date="2024-01-01", description="TECH CORP SALARY", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=15000.0, credit=0.0, balance=45000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-20", description="GROCERY STORE", debit=2000.0, credit=0.0, balance=43000.0, category="Shopping"),
        TransactionModel(id=4, date="2024-02-01", description="TECH CORP SALARY", debit=0.0, credit=60000.0, balance=103000.0, category="Income"),
        TransactionModel(id=5, date="2024-02-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=15000.0, credit=0.0, balance=88000.0, category="Housing & Rent"),
    ]

    forecast = CashFlowForecaster.forecast(txs, days=30)
    assert forecast["has_data"] is True
    assert forecast["starting_balance"] == 88000.0
    assert len(forecast["daily_projection"]) == 30
    assert "daily_discretionary_burn" in forecast["assumptions"]
    assert "disclaimer" in forecast

def test_forecast_detects_crunch_point():
    # Account with low remaining balance (e.g. ₹5,000) and an impending rent payment of ₹15,000 on the 5th
    txs = [
        TransactionModel(id=1, date="2024-01-05", description="RENT PAYMENT", normalized_merchant="RENT", debit=15000.0, credit=0.0, balance=20000.0, category="Housing & Rent"),
        TransactionModel(id=2, date="2024-02-05", description="RENT PAYMENT", normalized_merchant="RENT", debit=15000.0, credit=0.0, balance=5000.0, category="Housing & Rent"),
    ]

    forecast = CashFlowForecaster.forecast(txs, days=30)
    # Starting at 5,000 with 15,000 rent due in ~30 days and daily burn, it will dip below 3,000 safety floor
    assert len(forecast["crunch_points"]) > 0
    assert any(cp["is_below_safety"] for cp in forecast["daily_projection"])
    assert forecast["primary_crunch_alert"] is not None

def test_forecast_probabilistic_deterministic_and_monotonic_bounds():
    """
    Probabilistic Monte Carlo forecast must:
      1. Be 100% deterministic given the same seed
      2. Guarantee p10 <= p50 <= p90 across all projection days
      3. Supply risk probabilities and danger dates
    """
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="TECH CORP SALARY", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=15000.0, credit=0.0, balance=45000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-15", description="SWIGGY ORDER", debit=800.0, credit=0.0, balance=44200.0, category="Food & Dining"),
        TransactionModel(id=4, date="2024-02-01", description="TECH CORP SALARY", debit=0.0, credit=60000.0, balance=104200.0, category="Income"),
        TransactionModel(id=5, date="2024-02-05", description="APARTMENT RENT", normalized_merchant="APARTMENT RENT", debit=15000.0, credit=0.0, balance=89200.0, category="Housing & Rent"),
    ]

    res1 = CashFlowForecaster.forecast_probabilistic(txs, days=30, n_paths=1000, seed=42)
    res2 = CashFlowForecaster.forecast_probabilistic(txs, days=30, n_paths=1000, seed=42)

    # 1. Determinism
    assert res1["daily_distribution"][0]["p50"] == res2["daily_distribution"][0]["p50"]
    assert res1["daily_distribution"][-1]["p90"] == res2["daily_distribution"][-1]["p90"]
    assert res1["risk_metrics"]["p_negative_pre_payday"] == res2["risk_metrics"]["p_negative_pre_payday"]

    # 2. Monotonic percentile bounds: p10 <= p50 <= p90
    dist = res1["daily_distribution"]
    assert len(dist) == 30
    for day_item in dist:
        p10 = day_item["p10"]
        p50 = day_item["p50"]
        p90 = day_item["p90"]
        assert p10 <= p50, f"Violation p10 ({p10}) > p50 ({p50}) on date {day_item['date']}"
        assert p50 <= p90, f"Violation p50 ({p50}) > p90 ({p90}) on date {day_item['date']}"

    # 3. Risk payload check
    assert "p_negative_30d" in res1["risk_metrics"]
    assert "methodology" in res1
    assert "assumptions" in res1

def test_forecast_backtest_insufficient_history():
    """
    Backtesting requires at least 60 days of recorded history.
    """
    short_txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-20", description="RENT", debit=15000.0, credit=0.0, balance=35000.0, category="Housing & Rent")
    ]
    bt = CashFlowForecaster.backtest_forecast(short_txs, holdout_days=30, seed=42)
    assert bt["is_supported"] is False
    assert "minimum 60 days" in bt["reason"].lower()

def test_forecast_backtest_sufficient_history():
    """
    Backtesting on 90 days of synthetic transactions must report empirical coverage and MAE.
    """
    from datetime import datetime, timedelta
    txs = []
    bal = 20000.0
    start_dt = datetime(2024, 1, 1)

    for i in range(90):
        cur_dt = start_dt + timedelta(days=i)
        dt_str = cur_dt.strftime("%Y-%m-%d")

        # Salary on 1st of month
        if cur_dt.day == 1:
            bal += 50000.0
            txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="SALARY CREDIT", debit=0.0, credit=50000.0, balance=bal, category="Income"))

        # Rent on 5th
        if cur_dt.day == 5:
            bal -= 15000.0
            txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="RENT PAYMENT", normalized_merchant="RENT", debit=15000.0, credit=0.0, balance=bal, category="Housing & Rent"))

        # Discretionary daily spend
        bal -= 400.0
        txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="DAILY COFFEE", debit=400.0, credit=0.0, balance=bal, category="Food & Dining"))

    bt = CashFlowForecaster.backtest_forecast(txs, holdout_days=30, seed=42)
    assert bt["is_supported"] is True
    assert bt["evaluated_days_count"] > 0
    assert 0.0 <= bt["empirical_coverage_pct"] <= 100.0
    assert bt["mean_absolute_error"] >= 0.0


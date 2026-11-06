import pytest
from datetime import datetime, timedelta
from app.models.transaction import TransactionModel
from app.services.forecast import CashFlowForecaster
from app.services.counterfactual import CounterfactualActionEngine

def test_p10_p50_p90_monotonic_guarantee():
    """Verify that p10 <= p50 <= p90 holds across all simulated days for any seed."""
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY CREDIT", debit=0.0, credit=60000.0, balance=60000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="APARTMENT RENT", debit=18000.0, credit=0.0, balance=42000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-15", description="SWIGGY DINING", debit=750.0, credit=0.0, balance=41250.0, category="Food & Dining"),
        TransactionModel(id=4, date="2024-02-01", description="SALARY CREDIT", debit=0.0, credit=60000.0, balance=101250.0, category="Income"),
        TransactionModel(id=5, date="2024-02-05", description="APARTMENT RENT", debit=18000.0, credit=0.0, balance=83250.0, category="Housing & Rent"),
    ]

    for seed in [42, 100, 999]:
        res = CashFlowForecaster.forecast_probabilistic(txs, days=30, n_paths=500, seed=seed)
        for item in res["daily_distribution"]:
            assert item["p10"] <= item["p50"], f"p10 ({item['p10']}) > p50 ({item['p50']}) on day {item['day']}"
            assert item["p50"] <= item["p90"], f"p50 ({item['p50']}) > p90 ({item['p90']}) on day {item['day']}"

def test_seed_42_reproducibility():
    """Verify seed=42 produces bit-for-bit identical results."""
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="RENT", debit=15000.0, credit=0.0, balance=35000.0, category="Housing & Rent"),
    ]

    res_a = CashFlowForecaster.forecast_probabilistic(txs, days=30, n_paths=1000, seed=42)
    res_b = CashFlowForecaster.forecast_probabilistic(txs, days=30, n_paths=1000, seed=42)

    assert res_a["daily_distribution"][0]["p50"] == res_b["daily_distribution"][0]["p50"]
    assert res_a["daily_distribution"][-1]["p10"] == res_b["daily_distribution"][-1]["p10"]
    assert res_a["daily_distribution"][-1]["p90"] == res_b["daily_distribution"][-1]["p90"]
    assert res_a["risk_metrics"]["p_negative_pre_payday"] == res_b["risk_metrics"]["p_negative_pre_payday"]

def test_low_confidence_flag_under_3_months():
    """If statement history is under 90 days (3 months), low_confidence is True and interval is widened."""
    # 45 days history (< 90 days)
    short_txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-15", description="RENT", debit=15000.0, credit=0.0, balance=35000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-02-15", description="GROCERY", debit=2000.0, credit=0.0, balance=33000.0, category="Shopping"),
    ]

    res = CashFlowForecaster.forecast_probabilistic(short_txs, days=30, n_paths=500, seed=42)
    assert res["low_confidence"] is True
    assert "< 90 days" in res["confidence_reason"]

    # 120 days history (>= 90 days)
    long_txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=50000.0, balance=50000.0, category="Income"),
        TransactionModel(id=2, date="2024-02-01", description="SALARY", debit=0.0, credit=50000.0, balance=75000.0, category="Income"),
        TransactionModel(id=3, date="2024-03-01", description="SALARY", debit=0.0, credit=50000.0, balance=100000.0, category="Income"),
        TransactionModel(id=4, date="2024-05-01", description="SALARY", debit=0.0, credit=50000.0, balance=125000.0, category="Income"),
    ]
    res_long = CashFlowForecaster.forecast_probabilistic(long_txs, days=30, n_paths=500, seed=42)
    assert res_long["low_confidence"] is False

def test_rolling_origin_backtest_with_naive_comparison():
    """Rolling-origin backtests evaluate multiple cutoffs and compare against naive moving average."""
    txs = []
    bal = 30000.0
    start_dt = datetime(2024, 1, 1)

    for day in range(120):
        dt = start_dt + timedelta(days=day)
        dt_str = dt.strftime("%Y-%m-%d")

        # Monthly salary
        if dt.day == 1:
            bal += 65000.0
            txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="SALARY CORP", debit=0.0, credit=65000.0, balance=bal, category="Income"))

        # Monthly rent
        if dt.day == 5:
            bal -= 20000.0
            txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="RENT APARTMENT", normalized_merchant="RENT", debit=20000.0, credit=0.0, balance=bal, category="Housing & Rent"))

        # Daily expense
        bal -= 500.0
        txs.append(TransactionModel(id=len(txs)+1, date=dt_str, description="FOOD OUTLAY", debit=500.0, credit=0.0, balance=bal, category="Food & Dining"))

    bt = CashFlowForecaster.backtest_forecast(txs, holdout_days=30, seed=42)
    assert bt["is_supported"] is True
    assert bt["cutoffs_tested"] >= 2
    assert "rolling_cutoffs" in bt
    assert len(bt["rolling_cutoffs"]) >= 2

    # Check metrics
    assert 0.0 <= bt["empirical_coverage_pct"] <= 100.0
    assert bt["mean_absolute_error"] > 0
    assert "naive_baseline_mae" in bt
    assert bt["naive_baseline_mae"] > 0
    assert "mae_improvement_pct" in bt

def test_top_counterfactual_action_lowers_shortage_risk():
    """Counterfactual top action reduces shortage risk or keeps it at 0."""
    txs = [
        TransactionModel(id=1, date="2024-01-01", description="SALARY", debit=0.0, credit=35000.0, balance=35000.0, category="Income"),
        TransactionModel(id=2, date="2024-01-05", description="APARTMENT RENT", normalized_merchant="RENT", debit=25000.0, credit=0.0, balance=10000.0, category="Housing & Rent"),
        TransactionModel(id=3, date="2024-01-10", description="GYM MEMBERSHIP", normalized_merchant="GYM", debit=4000.0, credit=0.0, balance=6000.0, category="Subscriptions"),
        TransactionModel(id=4, date="2024-02-01", description="SALARY", debit=0.0, credit=35000.0, balance=41000.0, category="Income"),
        TransactionModel(id=5, date="2024-02-05", description="APARTMENT RENT", normalized_merchant="RENT", debit=25000.0, credit=0.0, balance=16000.0, category="Housing & Rent"),
        TransactionModel(id=6, date="2024-02-10", description="GYM MEMBERSHIP", normalized_merchant="GYM", debit=4000.0, credit=0.0, balance=12000.0, category="Subscriptions"),
    ]

    res = CounterfactualActionEngine.evaluate_actions(txs, days=30, n_paths=800, seed=42)
    assert res["has_data"] is True
    actions = res["actions"]
    assert len(actions) > 0
    top = actions[0]
    assert top["risk_after"] <= top["risk_before"]
    assert top["risk_reduction"] >= 0.0

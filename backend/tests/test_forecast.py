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


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.services.forecast import CashFlowForecaster

router = APIRouter(prefix="/api/forecast", tags=["Cash-Flow Forecasting"])

@router.get("")
def get_cash_flow_forecast(
    days: int = Query(30, ge=7, le=90, description="Projection horizon in days"),
    db: Session = Depends(get_db)
):
    """
    Simulates a 30-day cash flow projection using:
      - Latest closing balance
      - Historical trailing discretionary daily burn rate
      - Detected recurring commitments (EMIs, rent, subscriptions)
      - Expected regular salary inflows
    Attaches probabilistic Monte Carlo distribution (p10, p50, p90) and backtest summary.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    forecast_data = CashFlowForecaster.forecast(transactions, days=days)

    # Attach probabilistic model and backtest while preserving existing contract
    if forecast_data.get("has_data"):
        probabilistic_data = CashFlowForecaster.forecast_probabilistic(transactions, days=days, n_paths=2000, seed=42)
        forecast_data["probabilistic"] = probabilistic_data
        backtest_data = CashFlowForecaster.backtest_forecast(transactions, holdout_days=min(30, days), seed=42)
        forecast_data["backtest"] = backtest_data

    return forecast_data

@router.get("/probabilistic")
def get_probabilistic_forecast(
    days: int = Query(30, ge=7, le=90, description="Horizon in days"),
    n_paths: int = Query(2000, ge=100, le=5000, description="Monte Carlo sample paths"),
    seed: int = Query(42, description="Random seed for deterministic reproducibility"),
    db: Session = Depends(get_db)
):
    """
    Returns multi-path probabilistic cash flow distributions (p10, p50, p90).
    Calculates pre-payday balance breach probabilities and first-breach date clustering.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    return CashFlowForecaster.forecast_probabilistic(transactions, days=days, n_paths=n_paths, seed=seed)

@router.get("/backtest")
def get_forecast_backtest(
    holdout_days: int = Query(30, ge=7, le=60, description="Holdout window days"),
    seed: int = Query(42, description="Random seed"),
    db: Session = Depends(get_db)
):
    """
    Performs walk-forward historical backtesting on statement history.
    Reports empirical 80% interval coverage and MAE.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    return CashFlowForecaster.backtest_forecast(transactions, holdout_days=holdout_days, seed=seed)


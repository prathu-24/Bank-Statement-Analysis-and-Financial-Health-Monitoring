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
    Highlights potential cash shortages and impending payment crunch dates.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    forecast_data = CashFlowForecaster.forecast(transactions, days=days)
    return forecast_data


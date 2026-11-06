from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.scoring import FinancialHealthScorer

router = APIRouter(prefix="/api/health", tags=["Financial Health"])

@router.get("/score")
def get_financial_health_score(db: Session = Depends(get_db)):
    """
    Computes transparent 100-point Financial Health Score across 5 components:
      - Savings rate (30 pts)
      - Expense stability (20 pts)
      - Debt-to-income ratio (25 pts)
      - Low-balance days (15 pts)
      - Unusual activity count (10 pts)
    Provides mathematical formulas, measured values, and plain-language explanations.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    alerts = db.query(AlertModel).all()

    score_data = FinancialHealthScorer.calculate_score(transactions, alerts)
    return score_data

@router.get("/distress")
def get_distress_signals(db: Session = Depends(get_db)):
    """
    Scans for early financial distress signals:
      - Declining savings rate
      - Increasing EMI share of income
      - Repeated low-balance days
      - Spending expanding faster than income
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    signals = FinancialHealthScorer.detect_distress_signals(transactions)

    return {
        "signals_count": len(signals),
        "has_critical_distress": any(s["severity"] == "HIGH" for s in signals),
        "signals": signals
    }


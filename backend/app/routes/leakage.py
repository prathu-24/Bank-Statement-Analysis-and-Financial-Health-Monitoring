from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.transaction import TransactionModel
from app.services.leakage import LeakageDetector

router = APIRouter(prefix="/api/leakage", tags=["Financial Leakage"])

@router.get("")
def get_financial_leakage(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Identifies hidden recurring leakage:
      - Zombie & underutilized subscriptions
      - Price creep across recurring charges
      - Duplicate charges within 48 hours
      - Avoidable bank & penalty fees
      - Estimated annualized rupee waste
    """
    transactions = db.query(TransactionModel).all()
    return LeakageDetector.analyze(transactions)


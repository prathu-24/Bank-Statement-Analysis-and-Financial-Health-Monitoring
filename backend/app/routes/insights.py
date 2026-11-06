from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.insights import FinancialInsightsEngine

router = APIRouter(prefix="/api/insights", tags=["AI Insights & Recommendations"])

@router.get("")
def get_financial_insights(db: Session = Depends(get_db)):
    """
    Generates actionable financial suggestions, 50/30/20 budget analysis,
    personalized historical spending models, and an Explainable AI Executive Summary.
    Operates 100% offline with zero cloud dependency.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    alerts = db.query(AlertModel).all()

    insights_data = FinancialInsightsEngine.generate_all(transactions, alerts)
    return insights_data

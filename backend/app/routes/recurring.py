from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.services.recurring import RecurringPaymentDetector

router = APIRouter(prefix="/api/recurring", tags=["Recurring Payments"])

@router.get("")
def get_recurring_commitments(db: Session = Depends(get_db)):
    """
    Detects repeating subscriptions, EMIs, and utility obligations.
    Identifies cadence (Weekly, Monthly, Yearly) and flags forgotten subscriptions.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    detected = RecurringPaymentDetector.detect(transactions)

    # Compute summary
    monthly_total = 0.0
    annual_total = 0.0
    forgotten_count = 0
    forgotten_monthly_savings = 0.0
    subscriptions_count = 0

    for item in detected:
        freq = item["frequency"]
        avg = item["average_amount"]
        annual = item["estimated_annual_cost"]

        annual_total += annual

        # Normalize to monthly
        if freq == "Weekly":
            m_equiv = avg * 4.33
        elif freq == "Bi-Weekly":
            m_equiv = avg * 2.16
        elif freq == "Yearly":
            m_equiv = avg / 12.0
        elif freq == "Quarterly":
            m_equiv = avg / 3.0
        else:
            m_equiv = avg

        monthly_total += m_equiv

        if item["classification"] == "Subscription":
            subscriptions_count += 1

        if item["is_potentially_forgotten"]:
            forgotten_count += 1
            forgotten_monthly_savings += m_equiv

    return {
        "summary": {
            "total_monthly_commitment": round(monthly_total, 2),
            "total_annual_commitment": round(annual_total, 2),
            "total_commitments_count": len(detected),
            "subscriptions_count": subscriptions_count,
            "potential_forgotten_count": forgotten_count,
            "potential_annual_savings": round(forgotten_monthly_savings * 12, 2)
        },
        "commitments": detected
    }


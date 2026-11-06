from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.models.category_override import CategoryOverrideModel
from app.services.anomaly import AnomalyDetector
from app.services.categorizer import TransactionCategorizer

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies & Review"])

@router.get("")
def list_anomalies(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detects unusual transactions using explainable statistical models (IQR, Category Z-scores, duplicates).
    Strictly uses the label 'Unusual - Please Review' (never 'fraud').
    Computes review queue metrics, dismiss rates, and learned merchant exceptions.
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    alerts = AnomalyDetector.analyze(transactions, db)

    pending_count = sum(1 for a in alerts if not a["is_dismissed"])
    dismissed_count = sum(1 for a in alerts if a["is_dismissed"])
    total_alerts = len(alerts)
    dismiss_rate_pct = round((dismissed_count / total_alerts * 100), 1) if total_alerts > 0 else 0.0

    # Collect recognized merchants from dismissals
    dismissed_alert_ids = [a["alert_id"] for a in alerts if a["is_dismissed"] and a.get("alert_id")]
    learned_merchants = set()
    if dismissed_alert_ids:
        dismissed_tx_ids = [
            a.transaction_id for a in db.query(AlertModel).filter(AlertModel.id.in_(dismissed_alert_ids)).all()
        ]
        if dismissed_tx_ids:
            for tx in db.query(TransactionModel).filter(TransactionModel.id.in_(dismissed_tx_ids)).all():
                m = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
                if m:
                    learned_merchants.add(m)

    return {
        "pending_count": pending_count,
        "dismissed_count": dismissed_count,
        "total_alerts": total_alerts,
        "dismiss_rate_pct": dismiss_rate_pct,
        "learned_merchants_count": len(learned_merchants),
        "learned_merchants": sorted(list(learned_merchants)),
        "alerts": alerts,
        "methodology": "Statistical review queue (Z-score >= 1.75, IQR outlier, rapid 48-hr duplicates). 'This was me' dismissals teach the system to lower outlier sensitivity for recognized merchants.",
        "assumptions": {
            "label": "Unusual - Please Review (Not a fraud verdict)",
            "user_feedback_adaptive": True
        }
    }

@router.post("/{alert_id}/dismiss")
def dismiss_anomaly(alert_id: int, db: Session = Depends(get_db)):
    """
    Allows the user to mark an unusual transaction alert as 'This was me'.
    Dismisses the alert, lowers sensitivity for that merchant, and adjusts the review queue.
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found.")

    alert.is_dismissed = True
    alert.dismissed_at = datetime.utcnow()
    db.commit()

    # Identify transaction and merchant to reinforce model learning
    merchant = "Recognized Merchant"
    tx = db.query(TransactionModel).filter(TransactionModel.id == alert.transaction_id).first()
    if tx:
        merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)

    # Recalculate dismiss rate
    total = db.query(AlertModel).count()
    dismissed = db.query(AlertModel).filter(AlertModel.is_dismissed == True).count()
    rate = round((dismissed / total * 100), 1) if total > 0 else 100.0

    return {
        "status": "success",
        "message": f"Alert marked as 'This was me'. Sensitivity for '{merchant}' adjusted.",
        "alert_id": alert_id,
        "is_dismissed": True,
        "merchant_learned": merchant,
        "new_dismiss_rate_pct": rate
    }

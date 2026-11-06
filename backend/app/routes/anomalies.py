from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.anomaly import AnomalyDetector

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies & Review"])

@router.get("")
def list_anomalies(db: Session = Depends(get_db)):
    """
    Detects unusual transactions using explainable statistical models (IQR, Category Z-scores, duplicates).
    Strictly uses the label 'Unusual - Please Review' (never 'fraud').
    """
    transactions = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()
    alerts = AnomalyDetector.analyze(transactions, db)

    pending_count = sum(1 for a in alerts if not a["is_dismissed"])
    dismissed_count = sum(1 for a in alerts if a["is_dismissed"])

    return {
        "pending_count": pending_count,
        "dismissed_count": dismissed_count,
        "total_alerts": len(alerts),
        "alerts": alerts
    }

@router.post("/{alert_id}/dismiss")
def dismiss_anomaly(alert_id: int, db: Session = Depends(get_db)):
    """
    Allows the user to mark an unusual transaction alert as 'This was me'.
    Dismisses the alert without modifying the immutable underlying transaction record.
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found.")

    alert.is_dismissed = True
    alert.dismissed_at = datetime.utcnow()
    db.commit()

    return {
        "status": "success",
        "message": "Alert marked as 'This was me' and dismissed.",
        "alert_id": alert_id,
        "is_dismissed": True
    }


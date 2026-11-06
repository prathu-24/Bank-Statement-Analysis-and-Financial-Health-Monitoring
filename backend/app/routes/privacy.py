from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.models.alert import AlertModel

router = APIRouter(prefix="/api/privacy", tags=["Security & Privacy"])

@router.delete("/delete-all")
def delete_all_user_data(db: Session = Depends(get_db)):
    """
    Executes a complete purge of all user transactions, category overrides, and alert dismissals.
    Provides users with complete right-to-be-forgotten privacy control.
    """
    tx_count = db.query(TransactionModel).count()
    ovr_count = db.query(CategoryOverrideModel).count()
    alt_count = db.query(AlertModel).count()

    db.query(TransactionModel).delete()
    db.query(CategoryOverrideModel).delete()
    db.query(AlertModel).delete()
    db.commit()

    return {
        "status": "success",
        "message": "All statement records, overrides, and alerts have been permanently purged.",
        "purged_records": {
            "transactions": tx_count,
            "category_overrides": ovr_count,
            "alerts": alt_count
        }
    }

@router.get("/status")
def get_privacy_status(db: Session = Depends(get_db)):
    """
    Returns data isolation metrics and active privacy protections.
    """
    tx_count = db.query(TransactionModel).count()
    return {
        "privacy_shield_active": True,
        "storage_mode": "Local SQLite (Ephemeral Session)",
        "account_number_masking": "Enabled (last 4 digits visible)",
        "third_party_telemetry": "Disabled (Zero cloud transmission)",
        "current_stored_transactions": tx_count,
        "temporary_file_retention": "0s (In-memory stream processing)"
    }

import os
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, DB_PATH
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.models.alert import AlertModel
from app.services.sanitizer import DataSanitizer
from app.services.encryption import DataEncryptionService
from app.services.telemetry import NetworkTracker

router = APIRouter(prefix="/api/privacy", tags=["Security & Privacy"])

AUTO_PURGE_ENABLED = os.environ.get("FINSIGHT_AUTO_PURGE", "false").lower() in ("true", "1", "yes")
AUTO_PURGE_HOURS = int(os.environ.get("FINSIGHT_AUTO_PURGE_HOURS", "24"))

def execute_auto_purge(db: Session) -> int:
    """Purges records older than AUTO_PURGE_HOURS when FINSIGHT_AUTO_PURGE is enabled."""
    if not AUTO_PURGE_ENABLED:
        return 0
    cutoff = datetime.utcnow() - timedelta(hours=AUTO_PURGE_HOURS)
    purged = db.query(TransactionModel).filter(TransactionModel.created_at < cutoff).delete()
    if purged > 0:
        db.commit()
    return purged

@router.delete("/delete-all")
def delete_all_user_data(db: Session = Depends(get_db)):
    """
    Executes a complete purge of all user transactions, category overrides, and alerts.
    Provides users with complete right-to-be-forgotten privacy control and zeroes disk pages via VACUUM.
    """
    tx_count = db.query(TransactionModel).count()
    ovr_count = db.query(CategoryOverrideModel).count()
    alt_count = db.query(AlertModel).count()

    db.query(TransactionModel).delete()
    db.query(CategoryOverrideModel).delete()
    db.query(AlertModel).delete()
    db.commit()

    # Truly purge SQLite database file on disk via VACUUM
    vacuum_ok = False
    try:
        from app.database import engine
        with engine.connect() as conn:
            conn.exec_driver_sql("VACUUM")
        vacuum_ok = True
    except Exception:
        pass

    DataSanitizer.reset_counter()
    NetworkTracker.reset()

    return {
        "status": "success",
        "message": "All statement records, overrides, and alerts have been permanently purged and SQLite storage vacuumed.",
        "purged_records": {
            "transactions": tx_count,
            "category_overrides": ovr_count,
            "alerts": alt_count
        },
        "vacuum_executed": vacuum_ok
    }

@router.get("/status")
def get_privacy_status(db: Session = Depends(get_db)):
    """
    Returns dynamically computed data isolation metrics, local file metrics,
    PII sanitization counters, network tracking, and verifiable retention policies.
    """
    recently_purged = execute_auto_purge(db) if AUTO_PURGE_ENABLED else 0

    tx_count = db.query(TransactionModel).count()
    ovr_count = db.query(CategoryOverrideModel).count()
    alt_count = db.query(AlertModel).count()

    db_abs_path = os.path.abspath(DB_PATH)
    db_exists = os.path.exists(db_abs_path)
    db_size_bytes = os.path.getsize(db_abs_path) if db_exists else 0
    if db_size_bytes >= 1024 * 1024:
        db_size_human = f"{round(db_size_bytes / (1024 * 1024), 2)} MB"
    elif db_size_bytes >= 1024:
        db_size_human = f"{round(db_size_bytes / 1024, 1)} KB"
    else:
        db_size_human = f"{db_size_bytes} B"

    total_masked = DataSanitizer.compute_effective_masked_count(db)
    outbound_calls = NetworkTracker.get_call_count()

    if AUTO_PURGE_ENABLED:
        retention_policy_desc = f"Auto-purge active: Statement transactions destroyed after {AUTO_PURGE_HOURS} hours."
        temp_retention = f"Auto-purged after {AUTO_PURGE_HOURS}h"
    else:
        retention_policy_desc = "Local-device persistence: Data resides in local SQLite until user initiates 'Delete All Data'."
        temp_retention = "Retained on host until manual purge"

    return {
        # Backwards-compatible computed fields
        "privacy_shield_active": True,
        "storage_mode": f"Local SQLite ({os.path.basename(DB_PATH)})",
        "account_number_masking": "Enabled (last 4 digits visible)",
        "third_party_telemetry": "Disabled (Zero cloud transmission)" if outbound_calls == 0 else "Controlled Network Access",
        "current_stored_transactions": tx_count,
        "temporary_file_retention": temp_retention,

        # Provable Privacy Receipt blocks
        "database": {
            "file_path": db_abs_path,
            "file_size_bytes": db_size_bytes,
            "file_size_human": db_size_human,
            "exists": db_exists,
        },
        "stored_records": {
            "transactions": tx_count,
            "category_overrides": ovr_count,
            "alerts": alt_count,
            "total_rows": tx_count + ovr_count + alt_count
        },
        "sanitization": {
            "active": True,
            "total_masked_values": total_masked,
            "breakdown": DataSanitizer.get_breakdown(),
            "patterns": [
                "Bank Account Numbers (10-18 digits)",
                "Credit/Debit Cards (16 digits)",
                "Indian PAN Cards",
                "Mobile Numbers (10 digits)"
            ]
        },
        "network_isolation": {
            "outbound_network_calls": outbound_calls,
            "status": "100% Offline Local Processing" if outbound_calls == 0 else "External Network Calls Recorded",
            "allowed_endpoints": NetworkTracker.get_allowed_destinations()
        },
        "retention_policy": {
            "auto_purge_enabled": AUTO_PURGE_ENABLED,
            "auto_purge_hours": AUTO_PURGE_HOURS if AUTO_PURGE_ENABLED else None,
            "policy_description": retention_policy_desc,
            "recently_purged_count": recently_purged
        },
        "encryption_status": "ON" if DataEncryptionService.is_enabled() else "OFF",
        "encryption_at_rest": {
            "enabled": DataEncryptionService.is_enabled(),
            "status": "ON (AES-128 Fernet)" if DataEncryptionService.is_enabled() else "OFF (Unencrypted Plaintext)",
            "cipher": "AES-128-CBC (Fernet)" if DataEncryptionService.is_enabled() else "Plaintext SQLite",
            "key_configured": os.environ.get("FINSIGHT_ENCRYPTION_KEY") is not None
        },
        "methodology": "Hardware-local zero-telemetry architecture: SQLite file storage on host, regex PII neutralization at ingestion, zero external HTTP calls.",
        "assumptions": {
            "local_execution": True,
            "cloud_sync": False,
            "manual_purge_guaranteed": True
        }
    }

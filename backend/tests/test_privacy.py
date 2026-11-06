import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.models.alert import AlertModel
from app.services.sanitizer import DataSanitizer
from app.services.encryption import DataEncryptionService
from app.services.telemetry import NetworkTracker
from app.routes.privacy import get_privacy_status, delete_all_user_data, execute_auto_purge

@pytest.fixture
def privacy_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_data_sanitizer_counter_and_breakdown():
    DataSanitizer.reset_counter()
    assert DataSanitizer.get_masked_count() == 0

    # Test sample with 1 bank account, 1 credit card, 1 PAN card, 1 phone number
    sample = (
        "Transfer to A/C 12345678901234 from CARD 4111-2222-3333-4444. "
        "Verified with PAN ABCDE1234F and mobile +91-9876543210."
    )
    masked = DataSanitizer.mask_sensitive_data(sample)

    assert "••••1234" in masked
    assert "••••••••••••4444" in masked
    assert "AB••••34F" in masked
    assert "••••3210" in masked

    count = DataSanitizer.get_masked_count()
    assert count == 4

    breakdown = DataSanitizer.get_breakdown()
    assert breakdown["bank_accounts"] == 1
    assert breakdown["credit_cards"] == 1
    assert breakdown["pan_cards"] == 1
    assert breakdown["phone_numbers"] == 1

    DataSanitizer.reset_counter()
    assert DataSanitizer.get_masked_count() == 0

def test_data_encryption_service_cycle():
    # Without key
    orig_key = os.environ.get("FINSIGHT_ENCRYPTION_KEY")
    try:
        if "FINSIGHT_ENCRYPTION_KEY" in os.environ:
            del os.environ["FINSIGHT_ENCRYPTION_KEY"]
        assert DataEncryptionService.is_enabled() is False
        assert DataEncryptionService.encrypt("Secret statement line") == "Secret statement line"
        assert DataEncryptionService.decrypt("Secret statement line") == "Secret statement line"

        # With generated Fernet key
        test_key = DataEncryptionService.generate_key()
        os.environ["FINSIGHT_ENCRYPTION_KEY"] = test_key
        assert DataEncryptionService.is_enabled() is True

        secret = "UPI/23490234/MERCHANT PAYMENT/FOOD"
        encrypted = DataEncryptionService.encrypt(secret)
        assert encrypted.startswith("enc:")
        assert encrypted != secret

        decrypted = DataEncryptionService.decrypt(encrypted)
        assert decrypted == secret
    finally:
        if orig_key:
            os.environ["FINSIGHT_ENCRYPTION_KEY"] = orig_key
        elif "FINSIGHT_ENCRYPTION_KEY" in os.environ:
            del os.environ["FINSIGHT_ENCRYPTION_KEY"]

def test_network_tracker():
    NetworkTracker.reset()
    assert NetworkTracker.get_call_count() == 0

    NetworkTracker.record_call("https://api.example.com/check")
    assert NetworkTracker.get_call_count() == 1
    assert "https://api.example.com/check" in NetworkTracker.get_allowed_destinations()

    NetworkTracker.reset()
    assert NetworkTracker.get_call_count() == 0

def test_get_privacy_status_computed_receipt(privacy_db):
    # Seed transactions
    DataSanitizer.reset_counter()
    NetworkTracker.reset()

    tx1 = TransactionModel(
        date="2024-01-01",
        description=DataSanitizer.mask_sensitive_data("TRANSFER TO 998877665544"),
        debit=1500.0,
        credit=0.0,
        balance=10000.0,
        category="Shopping"
    )
    privacy_db.add(tx1)
    privacy_db.commit()

    status = get_privacy_status(privacy_db)

    # 1. Backwards compatibility checks
    assert status["privacy_shield_active"] is True
    assert status["current_stored_transactions"] == 1
    assert "Ephemeral Session" not in status["storage_mode"], "Must not make false ephemeral claims"

    # 2. Database block
    db_block = status["database"]
    assert "file_path" in db_block
    assert "file_size_bytes" in db_block
    assert "file_size_human" in db_block

    # 3. Stored records block
    stored_block = status["stored_records"]
    assert stored_block["transactions"] == 1
    assert stored_block["total_rows"] >= 1

    # 4. Sanitization block
    san_block = status["sanitization"]
    assert san_block["active"] is True
    assert san_block["total_masked_values"] >= 1
    assert len(san_block["patterns"]) == 4

    # 5. Network isolation block
    net_block = status["network_isolation"]
    assert net_block["outbound_network_calls"] == 0
    assert "100% Offline" in net_block["status"]

    # 6. Retention policy
    ret_block = status["retention_policy"]
    assert "policy_description" in ret_block
    assert "auto_purge_enabled" in ret_block

    # 7. Encryption block
    enc_block = status["encryption_at_rest"]
    assert "enabled" in enc_block
    assert "cipher" in enc_block

    # 8. Methodology & Assumptions
    assert "methodology" in status
    assert "assumptions" in status

def test_delete_all_user_data_purge(privacy_db):
    privacy_db.add(TransactionModel(date="2024-01-01", description="TEST", debit=100.0, balance=500.0))
    privacy_db.add(CategoryOverrideModel(merchant_pattern="TEST", category="Shopping"))
    privacy_db.add(AlertModel(transaction_id=1, alert_type="TEST", reason="TEST"))
    privacy_db.commit()

    res = delete_all_user_data(privacy_db)
    assert res["status"] == "success"
    assert res["purged_records"]["transactions"] == 1
    assert res["purged_records"]["category_overrides"] == 1
    assert res["purged_records"]["alerts"] == 1

    # Verify tables are completely empty
    assert privacy_db.query(TransactionModel).count() == 0
    assert privacy_db.query(CategoryOverrideModel).count() == 0
    assert privacy_db.query(AlertModel).count() == 0


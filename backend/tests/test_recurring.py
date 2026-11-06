import pytest
from app.models.transaction import TransactionModel
from app.services.recurring import RecurringPaymentDetector

def test_detect_monthly_subscription():
    txs = [
        TransactionModel(id=1, date="2024-01-05", description="NETFLIX SUBSCRIPTION", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=50000.0, category="Subscriptions"),
        TransactionModel(id=2, date="2024-02-05", description="NETFLIX SUBSCRIPTION", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=48000.0, category="Subscriptions"),
        TransactionModel(id=3, date="2024-03-05", description="NETFLIX SUBSCRIPTION", normalized_merchant="NETFLIX", debit=649.0, credit=0.0, balance=46000.0, category="Subscriptions"),
    ]

    detected = RecurringPaymentDetector.detect(txs)
    assert len(detected) == 1
    item = detected[0]
    assert item["merchant"] == "NETFLIX"
    assert item["frequency"] == "Monthly"
    assert item["average_amount"] == 649.0
    assert item["classification"] == "Subscription"
    assert item["transaction_count"] == 3
    assert item["next_expected_date"] == "2024-04-04"  # 30 days after March 5

def test_detect_monthly_emi():
    txs = [
        TransactionModel(id=1, date="2024-01-10", description="HDFC BANK HOME LOAN EMI", normalized_merchant="HDFC LOAN", debit=25000.0, credit=0.0, balance=60000.0, category="Loans & EMI"),
        TransactionModel(id=2, date="2024-02-10", description="HDFC BANK HOME LOAN EMI", normalized_merchant="HDFC LOAN", debit=25000.0, credit=0.0, balance=55000.0, category="Loans & EMI"),
    ]

    detected = RecurringPaymentDetector.detect(txs)
    assert len(detected) == 1
    assert detected[0]["classification"] == "EMI / Loan"
    assert detected[0]["average_amount"] == 25000.0
    assert detected[0]["estimated_annual_cost"] == 300000.0

def test_amount_variance_tolerance():
    # Broadband bill with slight fluctuation: 999, 1049 (within 10%)
    txs = [
        TransactionModel(id=1, date="2024-01-15", description="AIRTEL BROADBAND", normalized_merchant="AIRTEL", debit=999.0, credit=0.0, balance=30000.0, category="Utilities & Bills"),
        TransactionModel(id=2, date="2024-02-15", description="AIRTEL BROADBAND", normalized_merchant="AIRTEL", debit=1049.0, credit=0.0, balance=29000.0, category="Utilities & Bills"),
    ]

    detected = RecurringPaymentDetector.detect(txs)
    assert len(detected) == 1
    assert detected[0]["merchant"] == "AIRTEL"
    assert detected[0]["frequency"] == "Monthly"


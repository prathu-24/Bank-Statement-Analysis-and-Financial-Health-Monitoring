import pytest
from app.services.categorizer import TransactionCategorizer

def test_categorizer_rules():
    assert TransactionCategorizer.categorize("UPI/42314/SWIGGY BANGALORE", debit=350.0) == "Food & Dining"
    assert TransactionCategorizer.categorize("ZOMATO ORDER #12345", debit=520.0) == "Food & Dining"
    assert TransactionCategorizer.categorize("UBER TRIP MUMBAI", debit=240.0) == "Transport"
    assert TransactionCategorizer.categorize("NETFLIX SUBSCRIPTION", debit=649.0) == "Subscriptions"
    assert TransactionCategorizer.categorize("SPOTIFY PREMIUM MONTHLY", debit=119.0) == "Subscriptions"
    assert TransactionCategorizer.categorize("HDFC HOME LOAN EMI", debit=25000.0) == "Loans & EMI"
    assert TransactionCategorizer.categorize("MONTHLY HOUSE RENT", debit=15000.0) == "Housing & Rent"
    assert TransactionCategorizer.categorize("SALARY CREDIT TECH CORP", credit=85000.0) == "Income"
    assert TransactionCategorizer.categorize("RANDOM ABC UNKNOWN CHARGE", debit=50.0) == "Uncategorized"

def test_merchant_extraction():
    m1 = TransactionCategorizer.extract_normalized_merchant("UPI/34521401/ZOMATO/paytm@axis/Ref991")
    assert "ZOMATO" in m1

    m2 = TransactionCategorizer.extract_normalized_merchant("POS 48291 SWIGGY RESTAURANT BLR")
    assert "SWIGGY" in m2

    m3 = TransactionCategorizer.extract_normalized_merchant("NEFT-HDFC001-NETFLIX INDIA")
    assert "NETFLIX" in m3

def test_user_overrides_priority():
    # Normally "ZOMATO" is "Food & Dining", but user customizes to "Personal Discretionary"
    custom_overrides = {"ZOMATO": "Personal Discretionary"}
    cat = TransactionCategorizer.categorize(
        "UPI/123/ZOMATO/FOOD",
        debit=400.0,
        user_overrides=custom_overrides
    )
    assert cat == "Personal Discretionary"


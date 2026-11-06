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

def test_gig_worker_and_indian_rules():
    # Inflow from Swiggy/Uber to worker should be Income, not Food/Transport
    assert TransactionCategorizer.categorize("SWIGGY BUNDL TECH WEEKLY INFLOW", credit=9500.0) == "Income"
    assert TransactionCategorizer.categorize("UBER INDIA SYSTEMS DISBURSEMENT", credit=8200.0) == "Income"
    
    # Loans & EMI should override generic transport 'auto'
    assert TransactionCategorizer.categorize("BAJAJ AUTO FINANCE TWO WHEELER EMI", debit=3200.0) == "Loans & EMI"
    
    # Subscriptions & Storage
    assert TransactionCategorizer.categorize("GOOGLE STORAGE 100GB SUBSCRIPTION", debit=219.0) == "Subscriptions"
    
    # Education
    assert TransactionCategorizer.categorize("COLLEGE UNIVERSITY SEMESTER EXAM FEE", debit=9200.0) == "Education"
    assert TransactionCategorizer.categorize("URGENT TEXTBOOK PHOTOCOPY XEROX", debit=350.0) == "Education"

def test_confidence_and_review_fallback():
    cat, conf = TransactionCategorizer.categorize_with_confidence("SWIGGY BANGALORE", debit=450.0)
    assert cat == "Food & Dining"
    assert conf >= 0.90

    cat_unk, conf_unk = TransactionCategorizer.categorize_with_confidence("UNRECOGNIZED NOISE CHUNK 19283", debit=500.0)
    assert cat_unk == "Uncategorized – review"
    assert conf_unk < 0.50

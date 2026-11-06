import pytest
from app.parsers.base import BaseParser
from app.parsers.hdfc_parser import HDFCParser
from app.parsers.sbi_parser import SBIParser
from app.parsers.generic_csv_parser import GenericCSVParser
from app.parsers.detector import detect_format
from app.schemas.transaction import ColumnMapping

def test_base_parser_clean_amount():
    assert BaseParser.clean_amount("₹ 1,500.50") == 1500.50
    assert BaseParser.clean_amount("Rs. 25,000.00 Cr") == 25000.00
    assert BaseParser.clean_amount("350.00 Dr") == 350.00
    assert BaseParser.clean_amount("-") == 0.0
    assert BaseParser.clean_amount("") == 0.0
    assert BaseParser.clean_amount(None) == 0.0

def test_base_parser_parse_date():
    assert BaseParser.parse_date("15/01/2024") == "2024-01-15"
    assert BaseParser.parse_date("28-02-2024") == "2024-02-28"
    assert BaseParser.parse_date("2024-03-31") == "2024-03-31"
    assert BaseParser.parse_date("01-Jan-2024") == "2024-01-01"
    assert BaseParser.parse_date("invalid_date") is None

def test_hdfc_parser():
    sample_hdfc = (
        "HDFC BANK STATEMENT\n"
        "Account: XXXXXXXX1234\n"
        "Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        "01/01/24,SALARY CREDIT TECH CORP,REF1001,01/01/24,,75000.00,85000.00\n"
        "02/01/24,SWIGGY BANGALORE,REF1002,02/01/24,450.00,,84550.00\n"
        "05/01/24,NETFLIX INDIA,REF1003,05/01/24,649.00,,83901.00\n"
    ).encode('utf-8')

    parser = HDFCParser()
    txs = parser.parse(sample_hdfc)

    assert len(txs) == 3
    assert txs[0].date == "2024-01-01"
    assert txs[0].credit == 75000.00
    assert txs[0].debit == 0.0
    assert txs[0].balance == 85000.00
    assert "SALARY" in txs[0].description

    assert txs[1].date == "2024-01-02"
    assert txs[1].debit == 450.00
    assert txs[1].credit == 0.0
    assert txs[1].balance == 84550.00

def test_sbi_parser():
    sample_sbi = (
        "STATE BANK OF INDIA\n"
        "Txn Date,Value Date,Description,Ref No./Cheque No.,Debit,Credit,Balance\n"
        "10/01/2024,10/01/2024,TRANSFER TO ZOMATO,UPI123456,320.00,,50000.00\n"
        "15/01/2024,15/01/2024,RENT PAYMENT,NEFT998877,18000.00,,32000.00\n"
    ).encode('utf-8')

    parser = SBIParser()
    txs = parser.parse(sample_sbi)

    assert len(txs) == 2
    assert txs[0].date == "2024-01-10"
    assert txs[0].debit == 320.00
    assert txs[0].balance == 50000.00
    assert txs[1].debit == 18000.00
    assert txs[1].balance == 32000.00

def test_generic_csv_parser_and_mapping():
    sample_custom = (
        "TransactionDate,Memo,MoneyOut,MoneyIn,LedgerBalance\n"
        "2024-02-01,Groceries Supermarket,2400.00,,40000.00\n"
        "2024-02-05,Freelance Payment,,15000.00,55000.00\n"
    ).encode('utf-8')

    mapping = ColumnMapping(
        date_col="TransactionDate",
        description_col="Memo",
        debit_col="MoneyOut",
        credit_col="MoneyIn",
        balance_col="LedgerBalance"
    )

    parser = GenericCSVParser(mapping=mapping)
    txs = parser.parse(sample_custom)

    assert len(txs) == 2
    assert txs[0].date == "2024-02-01"
    assert txs[0].debit == 2400.00
    assert txs[1].credit == 15000.00
    assert txs[1].balance == 55000.00

def test_detector():
    hdfc_sample = b"HDFC BANK STATEMENT\nDate,Narration,Withdrawal Amt.,Deposit Amt.,Closing Balance\n01/01/24,ATM,500,,1000"
    sbi_sample = b"STATE BANK OF INDIA\nTxn Date,Description,Debit,Credit,Balance\n01/01/2024,ATM,500,,1000"
    generic_sample = b"Date,Description,Debit,Credit,Balance\n2024-01-01,Store,100,,900"

    fmt_h, conf_h, _, _ = detect_format(hdfc_sample, "statement.csv")
    assert fmt_h == "hdfc"
    assert conf_h > 0.8

    fmt_s, conf_s, _, _ = detect_format(sbi_sample, "sbi.csv")
    assert fmt_s == "sbi"
    assert conf_s > 0.8

    fmt_g, conf_g, _, _ = detect_format(generic_sample, "generic.csv")
    assert fmt_g == "generic"
    assert conf_g > 0.6


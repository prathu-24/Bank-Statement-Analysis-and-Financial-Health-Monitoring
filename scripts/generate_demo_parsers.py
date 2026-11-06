import os
import pandas as pd

def generate_samples():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demo_dir = os.path.join(base_dir, "demo_data")
    os.makedirs(demo_dir, exist_ok=True)

    # 1. ICICI Sample CSV
    # Headers: Transaction Date, Value Date, Cheque Number, Transaction Remarks, Withdrawal Amount (INR ), Deposit Amount (INR ), Balance (INR )
    # Date format: DD/MM/YYYY or DD-MM-YYYY
    icici_lines = [
        "ICICI BANK LTD",
        "Detailed Statement for Account: 002301589123",
        "Statement Period: 01/01/2024 to 30/03/2024",
        "Transaction Date,Value Date,Cheque Number,Transaction Remarks,Withdrawal Amount (INR ),Deposit Amount (INR ),Balance (INR )",
        "01/01/2024,01/01/2024,NA,INF/INFT/002934/SALARY JAN,0.00,75000.00,95000.00",
        "02/01/2024,02/01/2024,NA,UPI/Swiggy Bangalore/400291,450.00,0.00,94550.00",
        "04/01/2024,04/01/2024,NA,NEFT/RATN00001/RENT JAN 2024,18000.00,0.00,76550.00",
        "10/01/2024,10/01/2024,NA,ACH/HDFC LOAN/EMI4402,15000.00,0.00,61550.00",
        "15/01/2024,15/01/2024,NA,UPI/Blinkit Grocery Delhi/99201,1250.00,0.00,60300.00",
        "25/01/2024,25/01/2024,NA,BIL/Jio Fiber Prepaid/883921,899.00,0.00,59401.00",
        "01/02/2024,01/02/2024,NA,INF/INFT/004921/SALARY FEB,0.00,75000.00,134401.00",
        "05/02/2024,05/02/2024,NA,NEFT/RATN00001/RENT FEB 2024,18000.00,0.00,116401.00",
        "10/02/2024,10/02/2024,NA,ACH/HDFC LOAN/EMI4402,15000.00,0.00,101401.00",
        "28/02/2024,28/02/2024,NA,POS/ZOMATO RESTAURANT/55920,650.00,0.00,100751.00"
    ]
    with open(os.path.join(demo_dir, "icici_sample.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(icici_lines) + "\n")

    # 2. Axis Sample CSV
    # Headers: Tran Date, CHQNO, PARTICULARS, DR, CR, BAL
    # Date format: DD-MM-YYYY or DD-Mon-YYYY
    axis_lines = [
        "AXIS BANK LTD",
        "STATEMENT OF ACCOUNT FOR SAVINGS - 912010045892341",
        "Generated on: 01-04-2024",
        "Tran Date,CHQNO,PARTICULARS,DR,CR,BAL",
        "01-01-2024,CHQ001,SALARY CREDIT FROM INFOSYS TECH,0.00,82000.00,102000.00",
        "03-01-2024,,UPI/ZOMATO/ORDER48291,520.00,0.00,101480.00",
        "05-01-2024,NEFT491,NEFT TO SURESH LANDLORD RENT,20000.00,0.00,81480.00",
        "08-01-2024,,UPI/UBER TRIP/RIDE9931,340.00,0.00,81140.00",
        "10-01-2024,ACH201,ACH DEBIT AXIS AUTO LOAN EMI,12500.00,0.00,68640.00",
        "15-01-2024,,POS/STARBUCKS COFFEE/4412,480.00,0.00,68160.00",
        "01-02-2024,CHQ002,SALARY CREDIT FROM INFOSYS TECH,0.00,82000.00,150160.00",
        "05-02-2024,NEFT492,NEFT TO SURESH LANDLORD RENT,20000.00,0.00,130160.00",
        "10-02-2024,ACH202,ACH DEBIT AXIS AUTO LOAN EMI,12500.00,0.00,117660.00",
        "20-02-2024,,UPI/AMAZON PAY/SHOPPING991,2499.00,0.00,115161.00"
    ]
    with open(os.path.join(demo_dir, "axis_sample.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(axis_lines) + "\n")

    # 3. Kotak Sample CSV
    # Headers: Transaction Date, Narration, Chq / Ref No., Amount, Dr / Cr, Balance
    # Uses Dr / Cr indicator column
    kotak_lines = [
        "KOTAK MAHINDRA BANK",
        "Account Statement for AC No: 489201992",
        "Period: 01/01/2024 to 28/02/2024",
        "Transaction Date,Narration,Chq / Ref No.,Amount,Dr / Cr,Balance",
        "01/01/2024,SALARY CREDIT BY WIPRO CORP,REF49021,65000.00,CR,80000.00",
        "02/01/2024,UPI/SWIGGY DEL/BANGALORE,REF11029,480.00,DR,79520.00",
        "05/01/2024,NEFT APARTMENT RENT SHARMA,REF99201,16000.00,DR,63520.00",
        "10/01/2024,ACH KOTAK HOME LOAN EMI,REF55192,14200.00,DR,49320.00",
        "18/01/2024,UPI/ZEPTO INSTANT GROCERY,REF77210,850.00,DR,48470.00",
        "01/02/2024,SALARY CREDIT BY WIPRO CORP,REF99204,65000.00,CR,113470.00",
        "05/02/2024,NEFT APARTMENT RENT SHARMA,REF33120,16000.00,DR,97470.00",
        "10/02/2024,ACH KOTAK HOME LOAN EMI,REF44912,14200.00,DR,83270.00",
        "14/02/2024,UPI/BOOKMYSHOW MOVIE TICKETS,REF88192,720.00,DR,82550.00"
    ]
    with open(os.path.join(demo_dir, "kotak_sample.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(kotak_lines) + "\n")

    # 4. Excel Sample (.xlsx)
    # Using openpyxl / pandas
    excel_records = [
        {"Txn Date": "01/01/2024", "Description": "SALARY CREDIT TECH SERVICES", "Debit": 0.0, "Credit": 90000.0, "Balance": 120000.0},
        {"Txn Date": "02/01/2024", "Description": "UPI/ZOMATO RESTAURANTS/4491", "Debit": 550.0, "Credit": 0.0, "Balance": 119450.0},
        {"Txn Date": "05/01/2024", "Description": "NEFT TRANSFER RENT PAYMENT", "Debit": 22000.0, "Credit": 0.0, "Balance": 97450.0},
        {"Txn Date": "10/01/2024", "Description": "ACH DEBIT HDFC PERSONAL LOAN", "Debit": 18500.0, "Credit": 0.0, "Balance": 78950.0},
        {"Txn Date": "15/01/2024", "Description": "UPI/SWIGGY INSTAMART GROCERIES", "Debit": 1420.0, "Credit": 0.0, "Balance": 77530.0},
        {"Txn Date": "01/02/2024", "Description": "SALARY CREDIT TECH SERVICES", "Debit": 0.0, "Credit": 90000.0, "Balance": 167530.0},
        {"Txn Date": "05/02/2024", "Description": "NEFT TRANSFER RENT PAYMENT", "Debit": 22000.0, "Credit": 0.0, "Balance": 145530.0},
        {"Txn Date": "10/02/2024", "Description": "ACH DEBIT HDFC PERSONAL LOAN", "Debit": 18500.0, "Credit": 0.0, "Balance": 127030.0},
        {"Txn Date": "20/02/2024", "Description": "NETFLIX DIGITAL SUBSCRIPTION", "Debit": 649.0, "Credit": 0.0, "Balance": 126381.0}
    ]
    df_excel = pd.DataFrame(excel_records)
    excel_path = os.path.join(demo_dir, "sample_statement.xlsx")
    df_excel.to_excel(excel_path, index=False, engine="openpyxl")

    print(f"Generated demo files in {demo_dir}:")
    print(" - icici_sample.csv")
    print(" - axis_sample.csv")
    print(" - kotak_sample.csv")
    print(" - sample_statement.xlsx")

if __name__ == "__main__":
    generate_samples()

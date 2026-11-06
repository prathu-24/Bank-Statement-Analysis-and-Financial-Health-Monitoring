import os
import csv
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
os.makedirs(DEMO_DIR, exist_ok=True)

def generate_base_transactions():
    """
    Generates 6 months (Jan 2024 - June 2024) of realistic, mathematically consistent transactions.
    """
    random.seed(42)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)

    running_balance = 25000.0  # Initial opening balance
    transactions = []

    current_date = start_date
    while current_date <= end_date:
        d_day = current_date.day
        d_month = current_date.month

        # 1. Monthly Salary on 1st of every month
        if d_day == 1:
            salary = 85000.0
            running_balance += salary
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "SALARY CREDIT TECH CORP PVT LTD",
                "ref": f"CMS{random.randint(100000, 999999)}",
                "debit": 0.0,
                "credit": salary,
                "balance": round(running_balance, 2)
            })

        # 2. Monthly Rent on 5th of every month
        if d_day == 5:
            rent = 18000.0
            running_balance -= rent
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "NEFT TO LANDLORD APARTMENT RENT",
                "ref": f"NEFT{random.randint(100000, 999999)}",
                "debit": rent,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # 3. Monthly EMI on 10th of every month
        if d_day == 10:
            emi = 24500.0
            running_balance -= emi
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "ACH HDFC BANK HOME LOAN EMI",
                "ref": f"ACH{random.randint(100000, 999999)}",
                "debit": emi,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # 4. Active Subscriptions
        # Netflix on 7th
        if d_day == 7:
            running_balance -= 649.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "POS NETFLIX ENTERTAINMENT MUMBAI",
                "ref": f"POS{random.randint(100000, 999999)}",
                "debit": 649.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # Spotify on 14th
        if d_day == 14:
            running_balance -= 119.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "UPI/SPOTIFY INDIA/PREMIUM MONTHLY",
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": 119.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # Amazon Prime on 18th
        if d_day == 18:
            running_balance -= 299.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "AMAZON PRIME DIGITAL MEMBERSHIP",
                "ref": f"AMZ{random.randint(100000, 999999)}",
                "debit": 299.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # 5. Potentially Forgotten Subscription: Cult.fit Gym Membership on 22nd
        if d_day == 22:
            running_balance -= 1499.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "CULT.FIT GYM FITNESS PASS MONTHLY",
                "ref": f"CLT{random.randint(100000, 999999)}",
                "debit": 1499.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # 6. Utilities on 25th: Airtel Broadband & Electricity
        if d_day == 25:
            bb = 1179.0
            running_balance -= bb
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "AIRTEL BROADBAND FIBER BILL",
                "ref": f"ART{random.randint(100000, 999999)}",
                "debit": bb,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # 7. Discretionary Daily Transactions (Swiggy, Uber, Groceries)
        if random.random() < 0.45:
            food_amt = random.choice([320.0, 450.0, 580.0, 640.0, 290.0])
            running_balance -= food_amt
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": f"UPI/SWIGGY BANGALORE/ORDER{random.randint(1000,9999)}",
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": food_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        if random.random() < 0.35:
            uber_amt = random.choice([180.0, 240.0, 310.0, 420.0])
            running_balance -= uber_amt
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": f"UBER TRIP MUMBAI CAB RIDE",
                "ref": f"UBR{random.randint(100000, 999999)}",
                "debit": uber_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # Duplicate Transaction on March 15 (2 Swiggy orders of identical amount on same day)
        if d_month == 3 and d_day == 15 and len(transactions) > 0 and transactions[-1]["desc"].startswith("UPI/SWIGGY"):
            dup_amt = transactions[-1]["debit"]
            running_balance -= dup_amt
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": transactions[-1]["desc"],
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": dup_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # Unusually Large Outlier Transaction on April 20 (Jewelry/Electronics purchase of ₹48,000)
        if d_month == 4 and d_day == 20:
            big_amt = 48000.0
            running_balance -= big_amt
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": "POS TANISHQ JEWELLERY BANGALORE",
                "ref": f"POS{random.randint(100000, 999999)}",
                "debit": big_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })

        # Potential Cash Shortage in final week of June (extra expenses bringing balance down to ₹1,450 before rent/EMI)
        if d_month == 6 and d_day == 28:
            shortage_spend = running_balance - 1450.0
            if shortage_spend > 0:
                running_balance -= shortage_spend
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": "EMERGENCY VEHICLE REPAIR SERVICE",
                    "ref": f"POS{random.randint(100000, 999999)}",
                    "debit": round(shortage_spend, 2),
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })

        current_date += timedelta(days=1)

    return transactions

def write_hdfc_csv(transactions):
    path = os.path.join(DEMO_DIR, "hdfc_sample.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("HDFC BANK LIMITED\n")
        f.write("ACCOUNT STATEMENT - SAVINGS ACCOUNT\n")
        f.write("Account Number: ••••••••4821\n")
        f.write("Statement Period: 01/01/24 to 30/06/24\n")
        f.write("Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance\n")
        writer = csv.writer(f)
        for tx in transactions:
            dt = datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d/%m/%y")
            debit_str = f"{tx['debit']:.2f}" if tx['debit'] > 0 else ""
            credit_str = f"{tx['credit']:.2f}" if tx['credit'] > 0 else ""
            writer.writerow([
                dt,
                tx["desc"],
                tx["ref"],
                dt,
                debit_str,
                credit_str,
                f"{tx['balance']:.2f}"
            ])
    print(f"Generated: {path}")

def write_sbi_csv(transactions):
    path = os.path.join(DEMO_DIR, "sbi_sample.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("STATE BANK OF INDIA\n")
        f.write("Account Name: MR ARJUN VERMA\n")
        f.write("Account Number: ••••••••9012\n")
        f.write("Txn Date,Value Date,Description,Ref No./Cheque No.,Debit,Credit,Balance\n")
        writer = csv.writer(f)
        for tx in transactions:
            dt = datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            debit_str = f"{tx['debit']:.2f}" if tx['debit'] > 0 else ""
            credit_str = f"{tx['credit']:.2f}" if tx['credit'] > 0 else ""
            writer.writerow([
                dt,
                dt,
                tx["desc"],
                tx["ref"],
                debit_str,
                credit_str,
                f"{tx['balance']:.2f}"
            ])
    print(f"Generated: {path}")

def write_generic_csv(transactions):
    path = os.path.join(DEMO_DIR, "generic_sample.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Debit", "Credit", "Balance"])
        for tx in transactions:
            debit_str = f"{tx['debit']:.2f}" if tx['debit'] > 0 else ""
            credit_str = f"{tx['credit']:.2f}" if tx['credit'] > 0 else ""
            writer.writerow([
                tx["date"],
                tx["desc"],
                debit_str,
                credit_str,
                f"{tx['balance']:.2f}"
            ])
    print(f"Generated: {path}")

def write_pdf_statement(transactions):
    path = os.path.join(DEMO_DIR, "sample_statement.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1e293b')
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )

    elements.append(Paragraph("<b>NATIONAL BANK OF INDIA</b> - Official Account Statement", title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Account Holder: Arjun Verma | Account: ••••••••8841 | IFSC: NATB0001234", meta_style))
    elements.append(Paragraph("Statement Period: 01/01/2024 to 30/06/2024 | Currency: INR", meta_style))
    elements.append(Spacer(1, 14))

    # Table data
    table_data = [["Date", "Description", "Debit", "Credit", "Balance"]]
    # Include first 45 representative transactions for a compact multi-page PDF
    for tx in transactions[:45]:
        dt = datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        deb = f"Rs.{tx['debit']:,.2f}" if tx['debit'] > 0 else "-"
        cred = f"Rs.{tx['credit']:,.2f}" if tx['credit'] > 0 else "-"
        bal = f"Rs.{tx['balance']:,.2f}"
        desc_p = tx["desc"][:32]
        table_data.append([dt, desc_p, deb, cred, bal])

    t = Table(table_data, colWidths=[70, 210, 80, 80, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    elements.append(t)
    doc.build(elements)
    print(f"Generated: {path}")

def write_broken_csv(transactions):
    path = os.path.join(DEMO_DIR, "broken_sample.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Debit", "Credit", "Balance"])

        # Take 30 rows and introduce deliberate errors for validation demonstrations
        subset = [dict(tx) for tx in transactions[:30]]

        # Error 1: Broken balance arithmetic at row 8
        subset[7]["balance"] = round(subset[7]["balance"] + 4500.0, 2)

        # Error 2: Invalid date format at row 14
        subset[13]["date"] = "invalid-date-31-02"

        # Error 3: Negative debit amount at row 20
        subset[19]["debit"] = -750.0

        # Warning 4: Duplicate transaction at row 24 (identical to row 23)
        subset[23] = dict(subset[22])

        for tx in subset:
            debit_str = f"{tx['debit']:.2f}" if tx['debit'] != 0.0 else ""
            credit_str = f"{tx['credit']:.2f}" if tx['credit'] != 0.0 else ""
            writer.writerow([
                tx["date"],
                tx["desc"],
                debit_str,
                credit_str,
                f"{tx['balance']:.2f}"
            ])
    print(f"Generated: {path}")

def main():
    print("Generating reproducible synthetic demo banking statements...")
    txs = generate_base_transactions()
    write_hdfc_csv(txs)
    write_sbi_csv(txs)
    write_generic_csv(txs)
    write_pdf_statement(txs)
    write_broken_csv(txs)
    print("All demo statements successfully created in /demo_data!")

if __name__ == "__main__":
    main()

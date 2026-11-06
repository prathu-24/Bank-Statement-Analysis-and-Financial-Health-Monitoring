import os
import csv
import json
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
os.makedirs(DEMO_DIR, exist_ok=True)

def generate_salaried_persona():
    """
    Persona 1: Salaried Professional (6 months: Jan 2024 - June 2024)
    Fixed monthly salary, rent, home loan EMI, subscriptions, plus planted anomalies.
    """
    random.seed(42)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)

    running_balance = 25000.0
    transactions = []
    ground_truth = {
        "persona": "Salaried Professional",
        "opening_balance": 25000.0,
        "date_range": "2024-01-01 to 2024-06-30",
        "planted_events": [
            {"event_type": "duplicate_charge", "date": "2024-03-15", "merchant": "Swiggy", "amount": 580.0},
            {"event_type": "spending_spike", "date": "2024-04-20", "merchant": "Tanishq", "amount": 48000.0},
            {"event_type": "forgotten_subscription", "merchant": "Cult.fit", "amount": 1499.0, "frequency": "Monthly"},
            {"event_type": "late_salary", "expected_date": "2024-05-01", "actual_date": "2024-05-06", "amount": 85000.0},
            {"event_type": "payday_shortfall", "date": "2024-06-28", "trough_balance": 1450.0}
        ],
        "true_categories": {}
    }

    current_date = start_date
    tx_id = 1
    while current_date <= end_date:
        d_day = current_date.day
        d_month = current_date.month

        # Salary on 1st (except May delayed to 6th)
        is_salary_day = (d_day == 1 and d_month != 5) or (d_day == 6 and d_month == 5)
        if is_salary_day:
            salary = 85000.0
            running_balance += salary
            desc = "SALARY CREDIT TECH CORP PVT LTD"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"CMS{random.randint(100000, 999999)}",
                "debit": 0.0,
                "credit": salary,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Income"
            tx_id += 1

        # Rent on 5th
        if d_day == 5:
            rent = 18000.0
            running_balance -= rent
            desc = "NEFT TO LANDLORD APARTMENT RENT"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"NEFT{random.randint(100000, 999999)}",
                "debit": rent,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Housing & Rent"
            tx_id += 1

        # EMI on 10th
        if d_day == 10:
            emi = 24500.0
            running_balance -= emi
            desc = "ACH HDFC BANK HOME LOAN EMI"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"ACH{random.randint(100000, 999999)}",
                "debit": emi,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Loans & EMI"
            tx_id += 1

        # Subscriptions: Netflix on 7th, Spotify on 14th, Prime on 18th
        if d_day == 7:
            running_balance -= 649.0
            desc = "POS NETFLIX ENTERTAINMENT MUMBAI"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"POS{random.randint(100000, 999999)}",
                "debit": 649.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Subscriptions"
            tx_id += 1

        if d_day == 14:
            running_balance -= 119.0
            desc = "UPI/SPOTIFY INDIA/PREMIUM MONTHLY"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": 119.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Subscriptions"
            tx_id += 1

        # Forgotten subscription: Cult.fit on 22nd
        if d_day == 22:
            running_balance -= 1499.0
            desc = "CULT.FIT GYM FITNESS PASS MONTHLY"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"CLT{random.randint(100000, 999999)}",
                "debit": 1499.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Subscriptions"
            tx_id += 1

        # Utilities on 25th: Airtel Broadband
        if d_day == 25:
            bb = 1179.0
            running_balance -= bb
            desc = "AIRTEL BROADBAND FIBER BILL"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"ART{random.randint(100000, 999999)}",
                "debit": bb,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Utilities & Bills"
            tx_id += 1

        # Discretionary: Swiggy Food
        if random.random() < 0.35:
            food_amt = random.choice([320.0, 450.0, 580.0, 640.0])
            running_balance -= food_amt
            desc = f"UPI/SWIGGY BANGALORE/ORDER{random.randint(1000,9999)}"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": food_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Food & Dining"
            tx_id += 1

        # Planted Duplicate on March 15 (2 Swiggy orders of ₹580)
        if d_month == 3 and d_day == 15:
            desc = "UPI/SWIGGY BANGALORE/ORDER7741"
            running_balance -= 580.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": "UPI884192",
                "debit": 580.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Food & Dining"
            tx_id += 1

            running_balance -= 580.0
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": "UPI884193",
                "debit": 580.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Food & Dining"
            tx_id += 1

        # Planted Spike on April 20 (Jewelry ₹48,000)
        if d_month == 4 and d_day == 20:
            spike_amt = 48000.0
            running_balance -= spike_amt
            desc = "POS TANISHQ JEWELLERY BANGALORE"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": "POS994821",
                "debit": spike_amt,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Shopping"
            tx_id += 1

        # Planted Payday shortfall on June 28 (Emergency vehicle repair)
        if d_month == 6 and d_day == 28:
            shortage_spend = running_balance - 1450.0
            if shortage_spend > 0:
                running_balance -= shortage_spend
                desc = "EMERGENCY VEHICLE REPAIR SERVICE"
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "ref": "POS334190",
                    "debit": round(shortage_spend, 2),
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })
                ground_truth["true_categories"][desc] = "Transportation"
                tx_id += 1

        current_date += timedelta(days=1)

    return transactions, ground_truth

def generate_gig_worker_persona():
    """
    Persona 2: Gig Economy Delivery Partner (6 months: Jan 2024 - June 2024)
    Irregular weekly payouts, daily fuel expenses, bike EMI, planted spike and shortfall.
    """
    random.seed(101)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)

    running_balance = 8000.0
    transactions = []
    ground_truth = {
        "persona": "Gig Economy Worker",
        "opening_balance": 8000.0,
        "date_range": "2024-01-01 to 2024-06-30",
        "planted_events": [
            {"event_type": "duplicate_charge", "date": "2024-02-18", "merchant": "HPCL Petrol", "amount": 450.0},
            {"event_type": "spending_spike", "date": "2024-05-12", "merchant": "Bike Engine Overhaul", "amount": 16500.0},
            {"event_type": "forgotten_subscription", "merchant": "Google One", "amount": 219.0, "frequency": "Monthly"},
            {"event_type": "late_salary", "description": "10-day payout delay in mid-June", "date": "2024-06-20"},
            {"event_type": "payday_shortfall", "date": "2024-06-25", "trough_balance": 450.0}
        ],
        "true_categories": {}
    }

    current_date = start_date
    tx_id = 1
    days_since_payout = 0

    while current_date <= end_date:
        d_day = current_date.day
        d_month = current_date.month

        # Irregular Payouts every 5 to 7 days (except mid-June delay)
        is_delayed_period = (d_month == 6 and 10 <= d_day <= 22)
        days_since_payout += 1

        if (days_since_payout >= 6 and not is_delayed_period) or (d_month == 6 and d_day == 23):
            payout = random.choice([6200.0, 7800.0, 8900.0, 11400.0, 9500.0])
            running_balance += payout
            desc = random.choice([
                "ZOMATO MEDIA PVT LTD WEEKLY PAYOUT",
                "UBER INDIA SYSTEMS DISBURSEMENT",
                "SWIGGY BUNDL TECH WEEKLY INFLOW"
            ])
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"CMS{random.randint(100000, 999999)}",
                "debit": 0.0,
                "credit": payout,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Income"
            days_since_payout = 0
            tx_id += 1

        # Two-wheeler EMI on 12th
        if d_day == 12:
            bike_emi = 3850.0
            running_balance -= bike_emi
            desc = "BAJAJ AUTO FINANCE TWO WHEELER EMI"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"ACH{random.randint(100000, 999999)}",
                "debit": bike_emi,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Loans & EMI"
            tx_id += 1

        # Daily Fuel Expense (every 2-3 days)
        if random.random() < 0.45:
            fuel = random.choice([250.0, 350.0, 420.0, 500.0])
            running_balance -= fuel
            desc = "UPI/HPCL PETROL PUMP FUEL DEBIT"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": fuel,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Transport"
            tx_id += 1

        # Forgotten subscription: Google One Storage ₹219 on 27th
        if d_day == 27:
            running_balance -= 219.0
            desc = "GOOGLE STORAGE 100GB SUBSCRIPTION"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"GOOG{random.randint(100000, 999999)}",
                "debit": 219.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Subscriptions"
            tx_id += 1

        # Planted Duplicate on Feb 18 (HPCL Fuel ₹450 duplicate)
        if d_month == 2 and d_day == 18:
            desc = "UPI/HPCL PETROL PUMP FUEL DEBIT"
            for _ in range(2):
                running_balance -= 450.0
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "ref": f"UPI{random.randint(100000, 999999)}",
                    "debit": 450.0,
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })
                ground_truth["true_categories"][desc] = "Transport"
                tx_id += 1

        # Planted Spending Spike on May 12 (Bike overhaul ₹16,500)
        if d_month == 5 and d_day == 12:
            running_balance -= 16500.0
            desc = "BIKE ENGINE OVERHAUL & TYRE REPAIR"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": "POS664210",
                "debit": 16500.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Transport"
            tx_id += 1

        # Planted Shortfall on June 25 (Balance drops to ₹450)
        if d_month == 6 and d_day == 25:
            drain = running_balance - 450.0
            if drain > 0:
                running_balance -= drain
                desc = "URGENT MEDICAL CLINIC EXPENSE"
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "ref": "UPI994012",
                    "debit": round(drain, 2),
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })
                ground_truth["true_categories"][desc] = "Healthcare"
                tx_id += 1

        current_date += timedelta(days=1)

    return transactions, ground_truth

def generate_student_persona():
    """
    Persona 3: College Student (6 months: Jan 2024 - June 2024)
    Parental transfer, PG rent, small UPI canteen/printout spends, planted spike and shortfall.
    """
    random.seed(303)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)

    running_balance = 3500.0
    transactions = []
    ground_truth = {
        "persona": "College Student",
        "opening_balance": 3500.0,
        "date_range": "2024-01-01 to 2024-06-30",
        "planted_events": [
            {"event_type": "duplicate_charge", "date": "2024-03-22", "merchant": "Campus Canteen", "amount": 140.0},
            {"event_type": "spending_spike", "date": "2024-01-25", "merchant": "Semester Exam Fee", "amount": 9200.0},
            {"event_type": "forgotten_subscription", "merchant": "Spotify Student", "amount": 59.0, "frequency": "Monthly"},
            {"event_type": "late_salary", "description": "Late allowance delayed to April 14", "date": "2024-04-14"},
            {"event_type": "payday_shortfall", "date": "2024-04-11", "trough_balance": 110.0}
        ],
        "true_categories": {}
    }

    current_date = start_date
    tx_id = 1
    while current_date <= end_date:
        d_day = current_date.day
        d_month = current_date.month

        # Monthly Parental allowance on 3rd (except April delayed to 14th)
        is_allowance_day = (d_day == 3 and d_month != 4) or (d_day == 14 and d_month == 4)
        if is_allowance_day:
            allowance = 15000.0
            running_balance += allowance
            desc = "IMPS INFLOW FROM FATHER MONTHLY ALLOWANCE"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"IMPS{random.randint(100000, 999999)}",
                "debit": 0.0,
                "credit": allowance,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Income"
            tx_id += 1

        # PG Room Rent on 5th
        if d_day == 5:
            rent = 6500.0
            running_balance -= rent
            desc = "UPI TO PG HOSTEL ROOM OWNER RENT"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": rent,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Housing & Rent"
            tx_id += 1

        # Spotify Student on 16th
        if d_day == 16:
            running_balance -= 59.0
            desc = "SPOTIFY INDIA STUDENT RECURRING"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": 59.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Subscriptions"
            tx_id += 1

        # Canteen / Tea / Snacks
        if random.random() < 0.60:
            canteen = random.choice([40.0, 60.0, 90.0, 120.0])
            running_balance -= canteen
            desc = "UPI/COLLEGE CAMPUS CANTEEN/CHAI"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": f"UPI{random.randint(100000, 999999)}",
                "debit": canteen,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Food & Dining"
            tx_id += 1

        # Planted Spike on Jan 25 (Semester Exam Fee ₹9,200)
        if d_month == 1 and d_day == 25:
            running_balance -= 9200.0
            desc = "COLLEGE UNIVERSITY SEMESTER EXAM FEE"
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "ref": "NETBANK99120",
                "debit": 9200.0,
                "credit": 0.0,
                "balance": round(running_balance, 2)
            })
            ground_truth["true_categories"][desc] = "Education"
            tx_id += 1

        # Planted Duplicate on March 22 (Canteen ₹140 duplicate)
        if d_month == 3 and d_day == 22:
            desc = "UPI/COLLEGE CAMPUS CANTEEN/SNACKS"
            for _ in range(2):
                running_balance -= 140.0
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "ref": f"UPI{random.randint(100000, 999999)}",
                    "debit": 140.0,
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })
                ground_truth["true_categories"][desc] = "Food & Dining"
                tx_id += 1

        # Planted Payday Shortfall on April 11 (Balance drops to ₹110 before allowance)
        if d_month == 4 and d_day == 11:
            drain = running_balance - 110.0
            if drain > 0:
                running_balance -= drain
                desc = "URGENT TEXTBOOK PHOTOCOPY XEROX"
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "ref": "UPI221094",
                    "debit": round(drain, 2),
                    "credit": 0.0,
                    "balance": round(running_balance, 2)
                })
                ground_truth["true_categories"][desc] = "Education"
                tx_id += 1

        current_date += timedelta(days=1)

    return transactions, ground_truth

def write_persona_files(name, transactions, truth):
    csv_path = os.path.join(DEMO_DIR, f"persona_{name}.csv")
    json_path = os.path.join(DEMO_DIR, f"persona_{name}_truth.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
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

    truth["total_transactions"] = len(transactions)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    print(f"Generated Persona [{name}]: {csv_path} and {json_path}")

def generate_base_transactions():
    """Legacy base statement generator for backward compatibility."""
    txs, _ = generate_salaried_persona()
    return txs

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

    table_data = [["Date", "Description", "Debit", "Credit", "Balance"]]
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

        subset = [dict(tx) for tx in transactions[:30]]
        subset[7]["balance"] = round(subset[7]["balance"] + 4500.0, 2)
        subset[13]["date"] = "invalid-date-31-02"
        subset[19]["debit"] = -750.0
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
    print("Generating comprehensive multi-persona evaluation banking datasets...")

    # Persona 1: Salaried Professional
    sal_txs, sal_truth = generate_salaried_persona()
    write_persona_files("salaried", sal_txs, sal_truth)

    # Persona 2: Gig Worker
    gig_txs, gig_truth = generate_gig_worker_persona()
    write_persona_files("gig_worker", gig_txs, gig_truth)

    # Persona 3: College Student
    stu_txs, stu_truth = generate_student_persona()
    write_persona_files("student", stu_txs, stu_truth)

    # Legacy demo statements
    write_hdfc_csv(sal_txs)
    write_sbi_csv(sal_txs)
    write_generic_csv(sal_txs)
    write_pdf_statement(sal_txs)
    write_broken_csv(sal_txs)
    print("All persona evaluation datasets & demo files successfully written to /demo_data!")

if __name__ == "__main__":
    main()

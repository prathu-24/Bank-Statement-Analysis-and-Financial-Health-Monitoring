import json
import os
from datetime import datetime, timedelta

def create_unseen_held_out_benchmark():
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
    os.makedirs(demo_dir, exist_ok=True)

    csv_path = os.path.join(demo_dir, "persona_unseen_held_out.csv")
    truth_path = os.path.join(demo_dir, "persona_unseen_held_out_truth.json")

    # Start balance
    bal = 125000.0
    start_date = datetime(2024, 1, 1)

    raw_tx_specs = [
        # Month 1 - Jan 2024
        ("2024-01-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-01-02", "UPI/THEOBROMA BANDRA/PASTRY ORDER", 640.0, 0.0, "Food & Dining"),
        ("2024-01-04", "TRANSFER TO LANDLADY SMT RADHA-RENT JAN", 22000.0, 0.0, "Housing & Rent"),
        ("2024-01-05", "UPI/CHAAYOS CONNAUGHT PLACE/TEA SNACKS", 320.0, 0.0, "Food & Dining"),
        ("2024-01-07", "BESCOM ELECTRICITY BILL BANGALORE", 2150.0, 0.0, "Utilities & Bills"),
        ("2024-01-09", "SHELL PETROL BUNK WHITEFIELD/FUEL", 2800.0, 0.0, "Transportation"),
        ("2024-01-11", "UPI/HALDIRAMS NAGPUR/DINNER", 1250.0, 0.0, "Food & Dining"),
        ("2024-01-13", "NATURES BASKET KORAMANGALA/ORGANIC GROCERY", 3450.0, 0.0, "Groceries"),
        ("2024-01-15", "DISNEY PLUS HOTSTAR ANNUAL VIP", 1499.0, 0.0, "Subscriptions"),
        ("2024-01-18", "FASTAG RECHARGE IHMCL HIGHWAY", 1000.0, 0.0, "Transportation"),
        ("2024-01-20", "MAX HEALTHCARE SAKET/OPD CONSULTATION", 1500.0, 0.0, "Healthcare"),
        ("2024-01-22", "MYNTRA DESIGNS PVT LTD/WINTER JACKET", 3499.0, 0.0, "Shopping"),
        ("2024-01-22", "MYNTRA DESIGNS PVT LTD/WINTER JACKET", 3499.0, 0.0, "Shopping"), # Planted duplicate
        ("2024-01-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-01-28", "UDEMY ONLINE LEARNING/DATA ENGINEERING", 899.0, 0.0, "Education"),

        # Month 2 - Feb 2024
        ("2024-02-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-02-02", "UPI/BARBEQUE NATION POWAI/FAMILY DINNER", 3800.0, 0.0, "Food & Dining"),
        ("2024-02-04", "TRANSFER TO LANDLADY SMT RADHA-RENT FEB", 22000.0, 0.0, "Housing & Rent"),
        ("2024-02-06", "MGL PIPED NATURAL GAS MUMBAI", 840.0, 0.0, "Utilities & Bills"),
        ("2024-02-08", "INDIAN OIL CORP PETROL PUMP", 2500.0, 0.0, "Transportation"),
        ("2024-02-10", "LE MARCHE GOURMET STORE/GROCERIES", 4200.0, 0.0, "Groceries"),
        ("2024-02-12", "APPLE.COM/BILL ICLOUD STORAGE 200GB", 219.0, 0.0, "Subscriptions"),
        ("2024-02-14", "NIC NATURAL ICE CREAM JUHU", 480.0, 0.0, "Food & Dining"),
        ("2024-02-17", "APOLLO HOSPITALS PHARMACY/MEDICINES", 1850.0, 0.0, "Healthcare"),
        ("2024-02-20", "RED_BUS INTERCITY VOLVO TICKET", 1450.0, 0.0, "Transportation"),
        ("2024-02-23", "WESTSIDE RETAIL TRENT LTD/CLOTHING SPIKE", 28500.0, 0.0, "Shopping"), # Planted spending spike
        ("2024-02-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-02-27", "OXFORD BOOK STORE KOLKATA/BOOKS", 1650.0, 0.0, "Education"),

        # Month 3 - Mar 2024
        ("2024-03-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-03-02", "UPI/THEOBROMA BANDRA/PASTRY ORDER", 580.0, 0.0, "Food & Dining"),
        ("2024-03-04", "TRANSFER TO LANDLADY SMT RADHA-RENT MAR", 22000.0, 0.0, "Housing & Rent"),
        ("2024-03-06", "BESCOM ELECTRICITY BILL BANGALORE", 1980.0, 0.0, "Utilities & Bills"),
        ("2024-03-09", "SHELL PETROL BUNK WHITEFIELD/FUEL", 2750.0, 0.0, "Transportation"),
        ("2024-03-12", "NATURES BASKET KORAMANGALA/ORGANIC GROCERY", 3890.0, 0.0, "Groceries"),
        ("2024-03-15", "YOUTUBE PREMIUM FAMILY MEMBERSHIP", 189.0, 0.0, "Subscriptions"),
        ("2024-03-18", "DR LAL PATHLABS/ANNUAL BLOOD CHECKUP", 2400.0, 0.0, "Healthcare"),
        ("2024-03-21", "HAMLEYS TOYS STORE PHOENIX", 3200.0, 0.0, "Shopping"),
        ("2024-03-24", "UPI/KALEVA SWEETS GOLE MARKET", 720.0, 0.0, "Food & Dining"),
        ("2024-03-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-03-28", "BRITISH COUNCIL LIBRARY ANNUAL PASS", 2200.0, 0.0, "Education"),
        ("2024-03-30", "MAKEMYTRIP HOLIDAY FLIGHT MUM-DEL", 6400.0, 0.0, "Transportation"),

        # Month 4 - Apr 2024
        ("2024-04-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-04-03", "UPI/CHAAYOS CONNAUGHT PLACE/TEA SNACKS", 360.0, 0.0, "Food & Dining"),
        ("2024-04-04", "TRANSFER TO LANDLADY SMT RADHA-RENT APR", 22000.0, 0.0, "Housing & Rent"),
        ("2024-04-07", "ADANI ELECTRICITY MUMBAI BILL", 2450.0, 0.0, "Utilities & Bills"),
        ("2024-04-10", "INDIAN OIL CORP PETROL PUMP", 2600.0, 0.0, "Transportation"),
        ("2024-04-13", "LE MARCHE GOURMET STORE/GROCERIES", 4100.0, 0.0, "Groceries"),
        ("2024-04-15", "APPLE.COM/BILL ICLOUD STORAGE 200GB", 219.0, 0.0, "Subscriptions"),
        ("2024-04-17", "MEDPLUS PHARMACY BANGALORE/MEDICINES", 1120.0, 0.0, "Healthcare"),
        ("2024-04-19", "IKEA HYDERABAD FURNITURE STORE", 7800.0, 0.0, "Shopping"),
        ("2024-04-22", "UPI/THEOBROMA BANDRA/PASTRY ORDER", 620.0, 0.0, "Food & Dining"),
        ("2024-04-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-04-27", "EDX ONLINE COURSE CERTIFICATION/CS50", 4100.0, 0.0, "Education"),
        ("2024-04-29", "FASTAG RECHARGE IHMCL HIGHWAY", 1000.0, 0.0, "Transportation"),

        # Month 5 - May 2024
        ("2024-05-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-05-02", "UPI/HALDIRAMS NAGPUR/DINNER", 1450.0, 0.0, "Food & Dining"),
        ("2024-05-04", "TRANSFER TO LANDLADY SMT RADHA-RENT MAY", 22000.0, 0.0, "Housing & Rent"),
        ("2024-05-06", "MGL PIPED NATURAL GAS MUMBAI", 890.0, 0.0, "Utilities & Bills"),
        ("2024-05-08", "SHELL PETROL BUNK WHITEFIELD/FUEL", 2900.0, 0.0, "Transportation"),
        ("2024-05-11", "NATURES BASKET KORAMANGALA/ORGANIC GROCERY", 3700.0, 0.0, "Groceries"),
        ("2024-05-15", "DISNEY PLUS HOTSTAR ANNUAL VIP", 1499.0, 0.0, "Subscriptions"),
        ("2024-05-18", "FORTIS HOSPITAL NOIDA/HEALTH CHECK", 3200.0, 0.0, "Healthcare"),
        ("2024-05-20", "TATA CLIQ LUXURY/DESIGNER APPAREL", 6800.0, 0.0, "Shopping"),
        ("2024-05-23", "UPI/BARBEQUE NATION POWAI/LUNCH", 2400.0, 0.0, "Food & Dining"),
        ("2024-05-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-05-27", "UDEMY ONLINE LEARNING/SYSTEM DESIGN", 799.0, 0.0, "Education"),
        ("2024-05-30", "RED_BUS INTERCITY VOLVO TICKET", 1350.0, 0.0, "Transportation"),

        # Month 6 - Jun 2024
        ("2024-06-01", "NEFT-CR-NEXUS ADVISORY CORP-CONSULTING FEE", 0.0, 95000.0, "Income"),
        ("2024-06-03", "UPI/THEOBROMA BANDRA/PASTRY ORDER", 540.0, 0.0, "Food & Dining"),
        ("2024-06-04", "TRANSFER TO LANDLADY SMT RADHA-RENT JUN", 22000.0, 0.0, "Housing & Rent"),
        ("2024-06-06", "BESCOM ELECTRICITY BILL BANGALORE", 2280.0, 0.0, "Utilities & Bills"),
        ("2024-06-09", "INDIAN OIL CORP PETROL PUMP", 2700.0, 0.0, "Transportation"),
        ("2024-06-12", "LE MARCHE GOURMET STORE/GROCERIES", 4350.0, 0.0, "Groceries"),
        ("2024-06-15", "APPLE.COM/BILL ICLOUD STORAGE 200GB", 219.0, 0.0, "Subscriptions"),
        ("2024-06-17", "APOLLO HOSPITALS PHARMACY/MEDICINES", 1620.0, 0.0, "Healthcare"),
        ("2024-06-19", "WESTSIDE RETAIL TRENT/SUMMER LINEN", 4200.0, 0.0, "Shopping"),
        ("2024-06-22", "UPI/CHAAYOS CONNAUGHT PLACE/CHAI SNACKS", 410.0, 0.0, "Food & Dining"),
        ("2024-06-25", "ACT FIBERNET BROADBAND BILL", 1179.0, 0.0, "Utilities & Bills"),
        ("2024-06-27", "OXFORD BOOK STORE KOLKATA/NOVELS", 1450.0, 0.0, "Education"),
        ("2024-06-29", "SHELL PETROL BUNK WHITEFIELD/FUEL", 2850.0, 0.0, "Transportation"),
        ("2024-06-30", "UPI/NIC NATURAL ICE CREAM JUHU", 390.0, 0.0, "Food & Dining"),
    ]

    # Calculate exact ledger reconciliation
    lines = ["Date,Description,Debit,Credit,Balance"]
    true_categories = {}
    running_balance = bal

    for date_str, desc, debit, credit, cat in raw_tx_specs:
        running_balance = round(running_balance + credit - debit, 2)
        deb_str = f"{debit:.2f}" if debit > 0 else ""
        cred_str = f"{credit:.2f}" if credit > 0 else ""
        bal_str = f"{running_balance:.2f}"
        lines.append(f"{date_str},{desc},{deb_str},{cred_str},{bal_str}")
        true_categories[desc] = cat

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    truth_dict = {
        "persona": "Unseen Held-Out Benchmark (Out-of-Sample)",
        "total_transactions": len(raw_tx_specs),
        "starting_balance": bal,
        "ending_balance": running_balance,
        "true_categories": true_categories,
        "planted_events": [
            {
                "event_type": "duplicate_charge",
                "date": "2024-01-22",
                "amount": 3499.0,
                "description": "MYNTRA DESIGNS PVT LTD/WINTER JACKET"
            },
            {
                "event_type": "spending_spike",
                "date": "2024-02-23",
                "amount": 28500.0,
                "description": "WESTSIDE RETAIL TRENT LTD/CLOTHING SPIKE"
            }
        ]
    }

    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth_dict, f, indent=2)

    print(f"Generated {len(raw_tx_specs)} unseen transactions in {csv_path}")

if __name__ == "__main__":
    create_unseen_held_out_benchmark()

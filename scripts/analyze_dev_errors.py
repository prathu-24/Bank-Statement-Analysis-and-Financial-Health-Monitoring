import json
import os
import pandas as pd
from collections import defaultdict

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from app.services.categorizer import TransactionCategorizer

def run_error_analysis():
    truth_path = "demo_data/persona_unseen_held_out_truth.json"
    csv_path = "demo_data/persona_unseen_held_out.csv"

    with open(truth_path) as f:
        truth = json.load(f)
    true_cats = truth["true_categories"]

    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    mid = len(df) // 2
    dev_df = df.iloc[:mid]

    misclassified = []
    cm = defaultdict(lambda: defaultdict(int))
    all_cats = set()

    for _, row in dev_df.iterrows():
        desc = row["Description"]
        credit = float(row["Credit"]) if pd.notna(row["Credit"]) and str(row["Credit"]).strip() else 0.0
        debit = float(row["Debit"]) if pd.notna(row["Debit"]) and str(row["Debit"]).strip() else 0.0
        actual = true_cats.get(desc, "Uncategorized")
        if actual == "Transportation":
            actual = "Transport"
        pred = TransactionCategorizer.categorize(desc, credit=credit, debit=debit)
        all_cats.add(actual)
        all_cats.add(pred)
        cm[actual][pred] += 1
        if pred != actual:
            misclassified.append({
                "date": row["Date"].strftime("%Y-%m-%d"),
                "description": desc,
                "debit": debit,
                "credit": credit,
                "true_category": actual,
                "predicted_category": pred
            })

    print(f"Total DEV rows: {len(dev_df)}")
    print(f"Total Misclassified: {len(misclassified)}")
    acc = round((len(dev_df) - len(misclassified)) / len(dev_df) * 100, 1)
    print(f"DEV Accuracy: {acc}%")

    print("\n--- TOP MISCLASSIFIED DESCRIPTIONS (DEV HALF ONLY) ---")
    for idx, m in enumerate(misclassified[:30], 1):
        print(f"{idx}. [{m['date']}] {m['description']} | True: {m['true_category']} -> Pred: {m['predicted_category']}")

    print("\n--- CONFUSION MATRIX (Rows: True, Columns: Predicted) ---")
    cats_sorted = sorted(list(all_cats))
    header = "True \\ Pred".ljust(22) + "".join([c[:9].rjust(11) for c in cats_sorted])
    print(header)
    print("-" * len(header))
    for true_c in cats_sorted:
        row_str = true_c[:20].ljust(22)
        for pred_c in cats_sorted:
            row_str += str(cm[true_c][pred_c]).rjust(11)
        print(row_str)

    return misclassified, cm, cats_sorted, len(dev_df), acc

if __name__ == "__main__":
    run_error_analysis()

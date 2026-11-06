from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from app.models.transaction import TransactionModel
from app.services.categorizer import TransactionCategorizer

class RecurringPaymentDetector:
    """
    Identifies recurring payments (subscriptions, EMIs, utilities) using:
      1. Merchant similarity & clustering
      2. Amount similarity within 10%
      3. Cadence detection (weekly, monthly, yearly intervals)
      4. Forgotten subscription heuristics
    """

    AMOUNT_VARIANCE_TOLERANCE = 0.12  # +/- 12%

    @classmethod
    def detect(cls, transactions: List[TransactionModel]) -> List[Dict[str, Any]]:
        # Consider only debits
        debits = [tx for tx in transactions if tx.debit > 0]
        if len(debits) < 2:
            return []

        # Group transactions by normalized merchant
        merchant_groups = defaultdict(list)
        for tx in debits:
            merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
            merchant_groups[merchant].append(tx)

        detected_recurring: List[Dict[str, Any]] = []

        for merchant, tx_list in merchant_groups.items():
            if len(tx_list) < 2:
                continue

            # Sort chronologically
            sorted_txs = sorted(tx_list, key=lambda x: x.date)

            # Check amount similarity
            amounts = [tx.debit for tx in sorted_txs]
            median_amt = statistics.median(amounts)
            if median_amt <= 0:
                continue

            # Filter transactions that fall within tolerance
            similar_txs = [
                tx for tx in sorted_txs
                if abs(tx.debit - median_amt) / median_amt <= cls.AMOUNT_VARIANCE_TOLERANCE
            ]

            if len(similar_txs) < 2:
                continue

            # Calculate intervals between consecutive occurrences (in days)
            dates = [datetime.strptime(tx.date, "%Y-%m-%d") for tx in similar_txs]
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

            if not intervals:
                continue

            median_interval = statistics.median(intervals)

            # Determine frequency
            frequency = None
            cycle_days = 30

            if 5 <= median_interval <= 9:
                frequency = "Weekly"
                cycle_days = 7
            elif 12 <= median_interval <= 17:
                frequency = "Bi-Weekly"
                cycle_days = 14
            elif 24 <= median_interval <= 35:
                frequency = "Monthly"
                cycle_days = 30
            elif 80 <= median_interval <= 100:
                frequency = "Quarterly"
                cycle_days = 90
            elif 350 <= median_interval <= 380:
                frequency = "Yearly"
                cycle_days = 365

            # If intervals have consistent regularity
            if frequency:
                avg_amount = round(statistics.mean([tx.debit for tx in similar_txs]), 2)
                last_date = dates[-1]
                next_date = last_date + timedelta(days=cycle_days)

                # Classification
                classification = cls._classify(merchant, similar_txs[0].description, avg_amount)

                # Estimated annual cost
                annual_cost = cls._calculate_annual_cost(avg_amount, frequency)

                # Forgotten subscription heuristic:
                # 1. Classified as subscription
                # 2. Occurred for at least 3 billing cycles
                # 3. Relatively small/recurring amount (< ₹2,500)
                is_potentially_forgotten = False
                if classification == "Subscription" and len(similar_txs) >= 3 and avg_amount <= 2500:
                    # If merchant is streaming, cloud, or app service
                    forgotten_keywords = ["gym", "prime", "hotstar", "zee5", "cloud", "saavn", "app", "magazine", "club"]
                    desc_low = merchant.lower() + " " + similar_txs[0].description.lower()
                    if any(k in desc_low for k in forgotten_keywords):
                        is_potentially_forgotten = True

                detected_recurring.append({
                    "id": f"rec-{merchant.lower().replace(' ', '-')}",
                    "merchant": merchant,
                    "category": similar_txs[0].category or "Subscriptions",
                    "average_amount": avg_amount,
                    "frequency": frequency,
                    "cycle_days": cycle_days,
                    "transaction_count": len(similar_txs),
                    "first_date": dates[0].strftime("%Y-%m-%d"),
                    "last_date": last_date.strftime("%Y-%m-%d"),
                    "next_expected_date": next_date.strftime("%Y-%m-%d"),
                    "estimated_annual_cost": annual_cost,
                    "classification": classification,
                    "is_potentially_forgotten": is_potentially_forgotten,
                    "confidence": min(0.98, round(0.70 + (len(similar_txs) * 0.05), 2)),
                    "transaction_ids": [tx.id for tx in similar_txs],
                    "explanation": (
                        f"Detected {len(similar_txs)} regular charges to {merchant} averaging {avg_amount:,.2f} "
                        f"with a {frequency.lower()} interval (median {int(median_interval)} days)."
                    )
                })

        # Sort by average amount descending
        detected_recurring.sort(key=lambda x: x["average_amount"], reverse=True)
        return detected_recurring

    @classmethod
    def _classify(cls, merchant: str, narration: str, amount: float) -> str:
        combined = (merchant + " " + narration).lower()
        if any(w in combined for w in ["emi", "loan", "bajaj", "mortgage", "housing"]):
            return "EMI / Loan"
        if any(w in combined for w in ["rent", "maintenance", "society"]):
            return "Housing / Rent"
        if any(w in combined for w in ["netflix", "spotify", "prime", "hotstar", "gym", "cult", "youtube", "music", "apple", "google play"]):
            return "Subscription"
        if any(w in combined for w in ["airtel", "jio", "broadband", "bescom", "power", "gas", "electricity"]):
            return "Utility Bill"
        return "Recurring Expense"

    @classmethod
    def _calculate_annual_cost(cls, amount: float, frequency: str) -> float:
        if frequency == "Weekly":
            return round(amount * 52, 2)
        elif frequency == "Bi-Weekly":
            return round(amount * 26, 2)
        elif frequency == "Monthly":
            return round(amount * 12, 2)
        elif frequency == "Quarterly":
            return round(amount * 4, 2)
        elif frequency == "Yearly":
            return round(amount, 2)
        return round(amount * 12, 2)


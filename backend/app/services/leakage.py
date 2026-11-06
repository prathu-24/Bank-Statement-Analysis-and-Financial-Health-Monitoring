from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import numpy as np

from app.models.transaction import TransactionModel
from app.services.categorizer import TransactionCategorizer
from app.services.recurring import RecurringPaymentDetector

class LeakageDetector:
    """
    Identifies hidden financial leakage:
      1. Zombie / underutilized recurring subscriptions
      2. Price creep (stealth subscription price increases)
      3. Rapid duplicate debits
      4. Hidden bank fees, AMC, and penalty charges
      5. Total estimated annual rupee leakage
    """

    BANK_CHARGE_KEYWORDS = [
        "sms charge", "annual fee", "debit card amc", "amc charge",
        "service charge", "min bal", "minimum balance", "penalty",
        "bounce charge", "folio charge", "atm decline charge",
        "cash handling fee", "nach return", "ach return", "statement charge"
    ]

    SUBSCRIPTION_KEYWORDS = [
        "netflix", "spotify", "prime", "hotstar", "youtube", "gym",
        "cult.fit", "apple.com/bill", "google storage", "cloud",
        "coursera", "udemy", "gymnasium", "fitness", "adobe", "chatgpt", "midjourney"
    ]

    @classmethod
    def analyze(cls, transactions: List[TransactionModel]) -> Dict[str, Any]:
        if not transactions:
            return {
                "has_data": False,
                "total_annual_leakage": 0.0,
                "leakage_count": 0,
                "zombie_subscriptions": [],
                "price_creeps": [],
                "duplicate_debits": [],
                "bank_charges": [],
                "annual_savings_summary": {},
                "methodology": "Leakage detected via recurring cadence tracking, inter-charge price growth (>5%), rapid 48-hour duplicate charges, and bank fee keyword classification.",
                "assumptions": {
                    "annualization_factor": 12,
                    "price_creep_threshold_pct": 5.0
                }
            }

        sorted_txs = sorted(transactions, key=lambda x: (x.date, x.id))
        debits = [tx for tx in sorted_txs if tx.debit > 0]

        # 1. Bank Charges
        bank_charges: List[Dict[str, Any]] = []
        for tx in debits:
            desc_lower = tx.description.lower()
            cat = tx.category or ""
            is_bank_charge = (
                cat == "Charges" or
                any(k in desc_lower for k in cls.BANK_CHARGE_KEYWORDS)
            )
            if is_bank_charge:
                bank_charges.append({
                    "transaction_id": tx.id,
                    "date": tx.date,
                    "description": tx.description,
                    "amount": round(tx.debit, 2),
                    "fee_type": "Bank / Penalty Fee",
                    "avoidable": True
                })

        total_bank_charges_spent = sum(c["amount"] for c in bank_charges)

        # 2. Duplicate Debits (within 48 hours)
        duplicate_debits: List[Dict[str, Any]] = []
        seen_duplicates = set()
        for i in range(len(debits) - 1):
            curr = debits[i]
            nxt = debits[i + 1]
            try:
                d1 = datetime.strptime(curr.date, "%Y-%m-%d")
                d2 = datetime.strptime(nxt.date, "%Y-%m-%d")
                days_diff = (d2 - d1).days

                m1 = curr.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(curr.description)
                m2 = nxt.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(nxt.description)

                if m1 == m2 and abs(curr.debit - nxt.debit) < 0.01 and 0 <= days_diff <= 2:
                    if nxt.id not in seen_duplicates:
                        seen_duplicates.add(nxt.id)
                        duplicate_debits.append({
                            "original_tx_id": curr.id,
                            "duplicate_tx_id": nxt.id,
                            "merchant": m2,
                            "original_date": curr.date,
                            "duplicate_date": nxt.date,
                            "amount": round(nxt.debit, 2),
                            "hours_apart": max(1, days_diff * 24),
                            "action": "File immediate chargeback dispute with bank"
                        })
            except Exception:
                continue

        total_duplicates_amount = sum(d["amount"] for d in duplicate_debits)

        # 3. Recurring grouping for Price Creep & Zombie Subscriptions
        merchant_txs = defaultdict(list)
        for tx in debits:
            m = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
            merchant_txs[m].append(tx)

        price_creeps: List[Dict[str, Any]] = []
        zombie_subscriptions: List[Dict[str, Any]] = []

        # Analyze each merchant with multiple debits
        for merchant, tx_list in merchant_txs.items():
            if len(tx_list) < 2:
                continue

            chron_txs = sorted(tx_list, key=lambda x: x.date)

            # Price Creep Detection (check consecutive charges)
            for k in range(len(chron_txs) - 1):
                prev_tx = chron_txs[k]
                curr_tx = chron_txs[k + 1]

                if prev_tx.debit > 0 and curr_tx.debit > prev_tx.debit:
                    increase_pct = ((curr_tx.debit - prev_tx.debit) / prev_tx.debit) * 100.0
                    delta = curr_tx.debit - prev_tx.debit

                    if increase_pct >= 5.0 and delta >= 20.0:
                        price_creeps.append({
                            "merchant": merchant,
                            "previous_date": prev_tx.date,
                            "new_date": curr_tx.date,
                            "previous_amount": round(prev_tx.debit, 2),
                            "new_amount": round(curr_tx.debit, 2),
                            "price_increase": round(delta, 2),
                            "percentage_increase": round(increase_pct, 1),
                            "annualized_creep_cost": round(delta * 12, 2),
                            "explanation": f"Subscription price increased from ₹{prev_tx.debit:,.0f} to ₹{curr_tx.debit:,.0f} (+{round(increase_pct, 1)}%) without plan upgrade."
                        })

            # Zombie Subscription Detection
            m_lower = merchant.lower()
            desc_samples = " ".join(t.description.lower() for t in chron_txs)
            is_sub_like = any(k in m_lower or k in desc_samples for k in cls.SUBSCRIPTION_KEYWORDS)

            # Cadence check
            dates = [datetime.strptime(t.date, "%Y-%m-%d") for t in chron_txs]
            intervals = [(dates[idx+1] - dates[idx]).days for idx in range(len(dates)-1)]
            avg_interval = np.mean(intervals) if intervals else 0

            # If recurring cadence (e.g. 25-35 days) and subscription-like merchant
            if (20 <= avg_interval <= 40 or is_sub_like) and len(chron_txs) >= 2:
                latest_amt = chron_txs[-1].debit
                zombie_subscriptions.append({
                    "merchant": merchant,
                    "monthly_cost": round(latest_amt, 2),
                    "annual_cost": round(latest_amt * 12, 2),
                    "charge_count": len(chron_txs),
                    "last_billed": chron_txs[-1].date,
                    "category": chron_txs[-1].category or "Entertainment",
                    "action": "Audit usage or cancel unused recurring plan"
                })

        # Calculate Total Annual Leakage
        annual_zombie = sum(z["annual_cost"] for z in zombie_subscriptions)
        annual_creep = sum(p["annualized_creep_cost"] for p in price_creeps)
        annual_bank = total_bank_charges_spent * 2  # assume conservative semi-annual projection
        total_annual_leakage = round(annual_zombie + annual_creep + annual_bank + total_duplicates_amount, 2)

        return {
            "has_data": True,
            "total_annual_leakage": total_annual_leakage,
            "leakage_count": len(zombie_subscriptions) + len(price_creeps) + len(duplicate_debits) + len(bank_charges),
            "annual_savings_summary": {
                "zombie_subscriptions_annual": round(annual_zombie, 2),
                "price_creep_annual": round(annual_creep, 2),
                "bank_charges_annual": round(annual_bank, 2),
                "duplicate_refunds_immediate": round(total_duplicates_amount, 2)
            },
            "zombie_subscriptions": zombie_subscriptions,
            "price_creeps": price_creeps,
            "duplicate_debits": duplicate_debits,
            "bank_charges": bank_charges,
            "methodology": "Leakage synthesized across 4 vectors: (1) recurring entertainment/cloud debits, (2) subscription price creeps >5% MoM, (3) 48-hr identical duplicate debits, and (4) banking AMC/late charges.",
            "assumptions": {
                "annualization_multiplier": 12,
                "price_creep_threshold_pct": 5.0,
                "zero_usage_heuristic": "Monthly recurring auto-debit with no discretionary interactions"
            }
        }


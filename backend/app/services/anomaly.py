from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session

from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.categorizer import TransactionCategorizer
from app.services.recurring import RecurringPaymentDetector

class AnomalyDetector:
    """
    Explainable statistical detector for atypical transactions.
    Rules & Statistical Models:
      1. Rapid Duplicate Detection (Identical merchant & amount on same day or consecutive days for major outlays)
      2. Known Recurring Exclusion (Prevents scheduled Rent, EMIs, and subscriptions from false alerting)
      3. Category-Specific Robust Outliers (Median & MAD / IQR with robust Z-scores)
      4. Global Robust Outlier Detection (Extreme spikes against overall discretionary spending, >= ₹5,000)
      5. Structured Severity Levels (LOW, MEDIUM, HIGH, CRITICAL)

    Strict Compliance:
      - Never uses the term 'fraud'
      - Labeled uniformly as 'Unusual - Please Review'
      - Persists user dismissals ('This was me') without mutating raw transaction data
    """

    LABEL = "Unusual - Please Review"

    @classmethod
    def analyze(cls, transactions: List[TransactionModel], db: Session) -> List[Dict[str, Any]]:
        debits = [tx for tx in transactions if tx.debit > 0]
        if not debits:
            return []

        # Fetch existing dismissed alerts
        existing_alerts = db.query(AlertModel).all()
        dismissed_map = {a.transaction_id: a.is_dismissed for a in existing_alerts}
        alert_db_map = {a.transaction_id: a for a in existing_alerts}

        alerts: List[Dict[str, Any]] = []
        flagged_tx_ids: Set[int] = set()

        # Sort chronologically
        sorted_txs = sorted(debits, key=lambda x: (x.date, x.id))

        # 1. Identify Known Recurring Commitments to Ignore (e.g. regular Rent, EMI, monthly bills)
        recurring_commitments = RecurringPaymentDetector.detect(transactions)
        recurring_tx_ids: Set[int] = set()
        for rec in recurring_commitments:
            recurring_tx_ids.update(rec.get("transaction_ids", []))

        # 2. Rapid Duplicate Detection (Double-swipes / duplicate debits)
        for i in range(len(sorted_txs) - 1):
            curr = sorted_txs[i]
            nxt = sorted_txs[i + 1]
            try:
                d1 = datetime.strptime(curr.date, "%Y-%m-%d")
                d2 = datetime.strptime(nxt.date, "%Y-%m-%d")
                days_diff = (d2 - d1).days

                m1 = curr.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(curr.description)
                m2 = nxt.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(nxt.description)

                same_amount = abs(curr.debit - nxt.debit) < 0.01

                # Condition A: Exactly on same day (days_diff == 0) with identical merchant & amount
                is_same_day_dup = (days_diff == 0 and m1 == m2 and same_amount)

                # Condition B: Consecutive day (days_diff == 1) for significant amounts (>= ₹1,000) or identical narration
                is_consecutive_dup = (
                    days_diff == 1 and m1 == m2 and same_amount and
                    (nxt.debit >= 1000.0 or curr.description.strip().lower() == nxt.description.strip().lower())
                )

                if (is_same_day_dup or is_consecutive_dup) and nxt.id not in flagged_tx_ids:
                    flagged_tx_ids.add(nxt.id)
                    severity = "CRITICAL" if nxt.debit >= 10000.0 else ("HIGH" if nxt.debit >= 500.0 else "MEDIUM")
                    alerts.append(cls._create_alert_dict(
                        nxt,
                        alert_type="RAPID_DUPLICATE",
                        severity=severity,
                        reason=f"Repeated charge of ₹{nxt.debit:,.2f} at {m2} within {days_diff} day(s) of row from {curr.date}.",
                        dismissed=dismissed_map.get(nxt.id, False),
                        db_alert=alert_db_map.get(nxt.id)
                    ))
            except Exception:
                continue

        # 3. Category-Specific Robust Outliers (Median & MAD)
        cat_amounts = defaultdict(list)
        for tx in sorted_txs:
            if tx.id not in recurring_tx_ids:
                cat = tx.category or "Uncategorized"
                cat_amounts[cat].append(tx.debit)

        cat_stats = {}
        for cat, vals in cat_amounts.items():
            if len(vals) >= 3:
                vals_arr = np.array(vals, dtype=np.float64)
                med = float(np.median(vals_arr))
                mad = float(np.median(np.abs(vals_arr - med)))
                mad_sigma = float(1.4826 * mad) if mad > 0 else float(np.std(vals_arr))
                if mad_sigma < 1.0:
                    q75, q25 = np.percentile(vals_arr, [75, 25])
                    iqr = q75 - q25
                    mad_sigma = float(iqr / 1.349) if iqr > 0 else float(max(10.0, np.std(vals_arr)))
                cat_stats[cat] = {
                    "median": med,
                    "sigma": max(1.0, mad_sigma)
                }

        for tx in sorted_txs:
            if tx.id in flagged_tx_ids or tx.id in recurring_tx_ids:
                continue

            cat = tx.category or "Uncategorized"
            merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)

            if cat in cat_stats:
                med_c = cat_stats[cat]["median"]
                sigma_c = cat_stats[cat]["sigma"]
                robust_z = (tx.debit - med_c) / sigma_c

                # Robust threshold: at least 3.0 robust std deviations AND at least 2.5x median AND >= ₹1,500 over median
                if robust_z >= 3.0 and tx.debit >= (med_c * 2.5) and (tx.debit - med_c) >= 1500.0:
                    flagged_tx_ids.add(tx.id)
                    severity = "CRITICAL" if robust_z >= 5.0 and tx.debit >= 25000.0 else ("HIGH" if robust_z >= 3.5 or tx.debit >= 10000.0 else "MEDIUM")
                    alerts.append(cls._create_alert_dict(
                        tx,
                        alert_type="CATEGORY_ZSCORE_OUTLIER",
                        severity=severity,
                        reason=f"Amount of ₹{tx.debit:,.2f} at {merchant} is {round(robust_z, 1)} standard deviations above your {cat} median of ₹{med_c:,.2f}.",
                        dismissed=dismissed_map.get(tx.id, False),
                        db_alert=alert_db_map.get(tx.id)
                    ))

        # 4. Global Non-Recurring Outlier Spikes (IQR / Extreme Discretionary Outlays, minimum ₹5,000)
        non_rec_debits = [tx.debit for tx in sorted_txs if tx.id not in recurring_tx_ids]
        if len(non_rec_debits) >= 4:
            q75, q25 = np.percentile(non_rec_debits, [75, 25])
            global_iqr = q75 - q25
            global_med = float(np.median(non_rec_debits))
            global_spike_bound = max(global_med * 4.0, q75 + (2.5 * global_iqr), 5000.0)
        else:
            global_spike_bound = 5000.0

        for tx in sorted_txs:
            if tx.id in flagged_tx_ids or tx.id in recurring_tx_ids:
                continue

            # Check if this non-recurring expenditure is an extreme spike
            if tx.debit >= global_spike_bound:
                flagged_tx_ids.add(tx.id)
                severity = "CRITICAL" if tx.debit >= 25000.0 else "HIGH"
                alerts.append(cls._create_alert_dict(
                    tx,
                    alert_type="UNUSUALLY_LARGE_AMOUNT",
                    severity=severity,
                    reason=f"Unusually large expenditure of ₹{tx.debit:,.2f} significantly exceeds your discretionary spending baseline.",
                    dismissed=dismissed_map.get(tx.id, False),
                    db_alert=alert_db_map.get(tx.id)
                ))

        # Sync detected alerts with DB
        for alt in alerts:
            tx_id = alt["transaction_id"]
            if tx_id not in alert_db_map:
                new_db_alert = AlertModel(
                    transaction_id=tx_id,
                    alert_type=alt["alert_type"],
                    reason=alt["reason"],
                    is_dismissed=False
                )
                db.add(new_db_alert)
                db.flush()
                alt["alert_id"] = new_db_alert.id
            else:
                alt["alert_id"] = alert_db_map[tx_id].id
        db.commit()

        alerts.sort(key=lambda x: x["date"], reverse=True)
        return alerts

    @classmethod
    def _create_alert_dict(
        cls,
        tx: TransactionModel,
        alert_type: str,
        severity: str,
        reason: str,
        dismissed: bool,
        db_alert: Any = None
    ) -> Dict[str, Any]:
        return {
            "alert_id": db_alert.id if db_alert else None,
            "transaction_id": tx.id,
            "date": tx.date,
            "description": tx.description,
            "merchant": tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description),
            "amount": tx.debit,
            "category": tx.category,
            "label": cls.LABEL,
            "alert_type": alert_type,
            "severity": severity,
            "reason": reason,
            "is_dismissed": dismissed,
            "why": (
                f"Statistical evaluation flagged this transaction because: {reason} "
                "This does not indicate confirmed wrongdoing or unauthorized access; please review if this expenditure was intended."
            )
        }

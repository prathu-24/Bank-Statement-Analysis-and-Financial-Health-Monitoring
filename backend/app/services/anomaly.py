from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session

from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.categorizer import TransactionCategorizer

class AnomalyDetector:
    """
    Explainable statistical detector for atypical transactions.
    Rules & Statistical Models:
      1. Rapid Duplicate Detection (Identical merchant & amount within 48 hours)
      2. Unusually Large Outlay (> ₹25,000 or > 2.5x 90th percentile)
      3. Category-Specific Outliers (Z-score >= 1.75 against category distribution)
      4. Global Interquartile Range (IQR) outliers (Debit > Q3 + 1.5*IQR)
      5. New Merchant Outlier (First appearance with above-median amount)

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
        amounts = [tx.debit for tx in sorted_txs]

        # 1. Rapid Duplicate Detection
        for i in range(len(sorted_txs) - 1):
            curr = sorted_txs[i]
            nxt = sorted_txs[i + 1]
            try:
                d1 = datetime.strptime(curr.date, "%Y-%m-%d")
                d2 = datetime.strptime(nxt.date, "%Y-%m-%d")
                days_diff = (d2 - d1).days

                m1 = curr.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(curr.description)
                m2 = nxt.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(nxt.description)

                if m1 == m2 and abs(curr.debit - nxt.debit) < 0.01 and 0 <= days_diff <= 2:
                    if nxt.id not in flagged_tx_ids:
                        flagged_tx_ids.add(nxt.id)
                        alerts.append(cls._create_alert_dict(
                            nxt,
                            alert_type="RAPID_DUPLICATE",
                            severity="HIGH",
                            reason=f"Repeated charge of ₹{nxt.debit:,.2f} at {m2} within {days_diff} day(s) of row from {curr.date}.",
                            dismissed=dismissed_map.get(nxt.id, False),
                            db_alert=alert_db_map.get(nxt.id)
                        ))
            except Exception:
                continue

        # 2. Category-Specific Z-Scores
        cat_amounts = defaultdict(list)
        for tx in sorted_txs:
            cat = tx.category or "Uncategorized"
            cat_amounts[cat].append(tx.debit)

        cat_stats = {}
        for cat, vals in cat_amounts.items():
            if len(vals) >= 3:
                cat_stats[cat] = {
                    "mean": float(np.mean(vals)),
                    "std": float(np.std(vals))
                }

        for tx in sorted_txs:
            if tx.id in flagged_tx_ids:
                continue

            cat = tx.category or "Uncategorized"
            merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)

            if cat in cat_stats:
                mean_c = cat_stats[cat]["mean"]
                std_c = cat_stats[cat]["std"]
                if std_c > 1.0:
                    z_score = (tx.debit - mean_c) / std_c
                    if z_score >= 1.75:
                        flagged_tx_ids.add(tx.id)
                        alerts.append(cls._create_alert_dict(
                            tx,
                            alert_type="CATEGORY_ZSCORE_OUTLIER",
                            severity="HIGH" if z_score >= 2.5 else "MEDIUM",
                            reason=f"Amount of ₹{tx.debit:,.2f} at {merchant} is {round(z_score, 1)} standard deviations above your {cat} average of ₹{mean_c:,.2f}.",
                            dismissed=dismissed_map.get(tx.id, False),
                            db_alert=alert_db_map.get(tx.id)
                        ))

        # 3. Global Statistical Outliers (IQR or Absolute Large Spikes)
        if len(amounts) >= 4:
            q75, q25 = np.percentile(amounts, [75, 25])
            iqr = q75 - q25
            iqr_upper_bound = q75 + (1.5 * iqr)
            median_spend = float(np.median(amounts))
        else:
            iqr_upper_bound = 20000.0
            median_spend = float(np.median(amounts))

        for tx in sorted_txs:
            if tx.id in flagged_tx_ids:
                continue

            # Unusually large absolute transaction
            if tx.debit >= 25000.0 or (len(amounts) >= 4 and tx.debit > iqr_upper_bound and tx.debit >= 5000.0):
                flagged_tx_ids.add(tx.id)
                alerts.append(cls._create_alert_dict(
                    tx,
                    alert_type="UNUSUALLY_LARGE_AMOUNT",
                    severity="HIGH" if tx.debit >= 30000.0 else "MEDIUM",
                    reason=f"Unusually large expenditure of ₹{tx.debit:,.2f} significantly exceeds your typical spending threshold.",
                    dismissed=dismissed_map.get(tx.id, False),
                    db_alert=alert_db_map.get(tx.id)
                ))

        # 4. New Merchant Outlier Detection
        seen_merchants: Set[str] = set()
        for tx in sorted_txs:
            if tx.id in flagged_tx_ids:
                seen_merchants.add(tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description))
                continue

            merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
            is_new = merchant not in seen_merchants

            if is_new and len(seen_merchants) >= 5 and tx.debit > (median_spend * 2.5) and tx.debit >= 3000:
                flagged_tx_ids.add(tx.id)
                alerts.append(cls._create_alert_dict(
                    tx,
                    alert_type="NEW_MERCHANT_SPIKE",
                    severity="MEDIUM",
                    reason=f"First-time merchant '{merchant}' with spending ₹{tx.debit:,.2f}, which is {round(tx.debit / max(1, median_spend), 1)}x higher than your median expense.",
                    dismissed=dismissed_map.get(tx.id, False),
                    db_alert=alert_db_map.get(tx.id)
                ))

            seen_merchants.add(merchant)

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

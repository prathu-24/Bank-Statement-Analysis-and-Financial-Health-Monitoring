from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.recurring import RecurringPaymentDetector

class FinancialHealthScorer:
    """
    Transparent 100-Point Financial Health Scoring Engine.
    
    Components:
      1. Savings Rate (30 pts)
      2. Expense Stability (20 pts)
      3. Debt-to-Income (DTI) Ratio (25 pts)
      4. Low-Balance Days (15 pts)
      5. Unusual Activity Count (10 pts)
    Total: 100 pts.
    """

    LOW_BALANCE_THRESHOLD = 3000.0  # INR

    @classmethod
    def calculate_score(
        cls,
        transactions: List[TransactionModel],
        alerts: List[AlertModel]
    ) -> Dict[str, Any]:
        if not transactions:
            return {
                "score": 0,
                "grade": "Insufficient Data",
                "is_preliminary": True,
                "components": [],
                "summary": "No transactions available to calculate financial health score."
            }

        sorted_txs = sorted(transactions, key=lambda x: x.date)
        total_income = sum(tx.credit for tx in sorted_txs)
        total_expense = sum(tx.debit for tx in sorted_txs)
        net_savings = total_income - total_expense

        # Group by month
        monthly_data = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "emi": 0.0})
        dates = []
        for tx in sorted_txs:
            dates.append(datetime.strptime(tx.date, "%Y-%m-%d"))
            m = tx.date[:7]
            monthly_data[m]["income"] += tx.credit
            monthly_data[m]["expense"] += tx.debit
            cat_low = (tx.category or "").lower()
            desc_low = tx.description.lower()
            if "loan" in cat_low or "emi" in cat_low or "loan" in desc_low or "emi" in desc_low:
                monthly_data[m]["emi"] += tx.debit

        data_days = (dates[-1] - dates[0]).days if len(dates) >= 2 else 1
        is_preliminary = data_days < 25

        components = []

        # -------------------------------------------------------------
        # 1. Savings Rate (Max 30 Points)
        # -------------------------------------------------------------
        if total_income > 0:
            savings_rate = (net_savings / total_income) * 100.0
        else:
            savings_rate = 0.0

        if savings_rate >= 30.0:
            sr_pts = 30
        elif savings_rate >= 20.0:
            sr_pts = 25
        elif savings_rate >= 10.0:
            sr_pts = 18
        elif savings_rate >= 0.0:
            sr_pts = 10
        else:
            sr_pts = 0

        components.append({
            "component": "Savings Rate",
            "actual_value": f"{round(savings_rate, 1)}%",
            "points_awarded": sr_pts,
            "max_points": 30,
            "calculation_method": "Net Savings / Total Income * 100 (Graded benchmark: >=30% = 30pts, 20-30% = 25pts, 10-20% = 18pts)",
            "explanation": f"You retained {round(savings_rate, 1)}% of net cash inflows. Benchmarked financial guidance recommends retaining at least 20% of net income."
        })

        # -------------------------------------------------------------
        # 2. Expense Stability (Max 20 Points)
        # -------------------------------------------------------------
        monthly_expenses = [d["expense"] for d in monthly_data.values() if d["expense"] > 0]
        if len(monthly_expenses) >= 2:
            mean_exp = float(np.mean(monthly_expenses))
            std_exp = float(np.std(monthly_expenses))
            cv = (std_exp / mean_exp) if mean_exp > 0 else 0.0

            if cv <= 0.15:
                es_pts = 20
                stab_label = "Highly predictable"
            elif cv <= 0.28:
                es_pts = 16
                stab_label = "Moderately consistent"
            elif cv <= 0.45:
                es_pts = 11
                stab_label = "Volatile month-to-month"
            else:
                es_pts = 6
                stab_label = "Highly unpredictable"
            cv_pct = f"{round(cv * 100, 1)}% CV"
        else:
            es_pts = 15
            stab_label = "Single month baseline"
            cv_pct = "N/A (1 month recorded)"

        components.append({
            "component": "Expense Stability",
            "actual_value": cv_pct,
            "points_awarded": es_pts,
            "max_points": 20,
            "calculation_method": "Coefficient of Variation (CV = Std Dev / Mean of monthly spending). Lower variation yields higher points.",
            "explanation": f"{stab_label} spending habits across statement periods. Stable expenses protect against cash shortages."
        })

        # -------------------------------------------------------------
        # 3. Debt-to-Income (DTI) Ratio (Max 25 Points)
        # -------------------------------------------------------------
        total_emi = sum(d["emi"] for d in monthly_data.values())
        if total_income > 0:
            dti = (total_emi / total_income) * 100.0
        else:
            dti = 0.0

        if dti <= 15.0:
            dti_pts = 25
            dti_label = "Minimal debt obligations"
        elif dti <= 30.0:
            dti_pts = 20
            dti_label = "Healthy debt burden"
        elif dti <= 40.0:
            dti_pts = 14
            dti_label = "Moderate debt load"
        elif dti <= 50.0:
            dti_pts = 8
            dti_label = "High debt strain"
        else:
            dti_pts = 2
            dti_label = "Critical debt exposure"

        components.append({
            "component": "Debt-to-Income Ratio",
            "actual_value": f"{round(dti, 1)}%",
            "points_awarded": dti_pts,
            "max_points": 25,
            "calculation_method": "Total EMI & Loan Repayments / Total Inflows * 100 (Thresholds: <=15% = 25pts, <=30% = 20pts, >50% = 2pts)",
            "explanation": f"{dti_label}. Loans and EMIs consume {round(dti, 1)}% of your net inflows (ideal threshold is under 30%)."
        })

        # -------------------------------------------------------------
        # 4. Low-Balance Days (Max 15 Points)
        # -------------------------------------------------------------
        # Count distinct calendar days where ending balance dipped below threshold
        day_balances = {}
        for tx in sorted_txs:
            day_balances[tx.date] = tx.balance

        low_days = sum(1 for bal in day_balances.values() if bal < cls.LOW_BALANCE_THRESHOLD)
        if low_days == 0:
            lb_pts = 15
        elif low_days <= 2:
            lb_pts = 12
        elif low_days <= 5:
            lb_pts = 8
        elif low_days <= 8:
            lb_pts = 4
        else:
            lb_pts = 0

        components.append({
            "component": "Low-Balance Liquidity",
            "actual_value": f"{low_days} day(s) < ₹{int(cls.LOW_BALANCE_THRESHOLD):,}",
            "points_awarded": lb_pts,
            "max_points": 15,
            "calculation_method": f"Count of calendar days with closing balance below emergency safety floor of ₹{int(cls.LOW_BALANCE_THRESHOLD):,}.",
            "explanation": f"Your account dipped below ₹{int(cls.LOW_BALANCE_THRESHOLD):,} on {low_days} day(s), indicating your liquidity buffer strength."
        })

        # -------------------------------------------------------------
        # 5. Unusual Activity Count (Max 10 Points)
        # -------------------------------------------------------------
        active_anomalies = [a for a in alerts if not a.is_dismissed]
        anomaly_count = len(active_anomalies)

        if anomaly_count == 0:
            ua_pts = 10
        elif anomaly_count == 1:
            ua_pts = 8
        elif anomaly_count == 2:
            ua_pts = 6
        elif anomaly_count == 3:
            ua_pts = 3
        else:
            ua_pts = 0

        components.append({
            "component": "Unusual Outlays",
            "actual_value": f"{anomaly_count} unverified alert(s)",
            "points_awarded": ua_pts,
            "max_points": 10,
            "calculation_method": "Deductions for un-dismissed statistical anomalies (duplicates, sudden spikes, or category deviations).",
            "explanation": f"{anomaly_count} unverified atypical transaction(s) detected. Dismissing verified alerts restores points."
        })

        total_score = sum(c["points_awarded"] for c in components)

        if total_score >= 85:
            grade = "Excellent"
        elif total_score >= 70:
            grade = "Good"
        elif total_score >= 50:
            grade = "Fair"
        else:
            grade = "Vulnerable"

        return {
            "score": total_score,
            "grade": grade,
            "is_preliminary": is_preliminary,
            "data_days_analyzed": data_days,
            "components": components,
            "summary": (
                f"Overall Financial Health Score is {total_score}/100 ({grade}). "
                f"{'Note: Preliminary assessment based on limited transaction history.' if is_preliminary else ''}"
            )
        }

    @classmethod
    def detect_distress_signals(cls, transactions: List[TransactionModel]) -> List[Dict[str, Any]]:
        """
        Evaluates early financial distress signals:
          - Declining savings rate
          - Increasing EMI share of income
          - Repeated low-balance days near month-end
          - Spending growth outpacing income growth
        """
        if not transactions or len(transactions) < 5:
            return []

        sorted_txs = sorted(transactions, key=lambda x: x.date)
        monthly_data = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "emi": 0.0, "days": set()})

        for tx in sorted_txs:
            m = tx.date[:7]
            monthly_data[m]["income"] += tx.credit
            monthly_data[m]["expense"] += tx.debit
            monthly_data[m]["days"].add(tx.date)
            cat_low = (tx.category or "").lower()
            if "loan" in cat_low or "emi" in cat_low:
                monthly_data[m]["emi"] += tx.debit

        months = sorted(list(monthly_data.keys()))
        signals: List[Dict[str, Any]] = []

        # 1. Repeated Low Balance Days
        low_balance_dates = [tx.date for tx in sorted_txs if tx.balance < cls.LOW_BALANCE_THRESHOLD]
        if len(low_balance_dates) >= 4:
            signals.append({
                "signal": "Chronic Low-Balance Liquidity Crunch",
                "severity": "HIGH",
                "evidence": f"Account balance dipped below ₹{int(cls.LOW_BALANCE_THRESHOLD):,} on {len(low_balance_dates)} separate days.",
                "explanation": "Operating close to minimum balance elevates the risk of overdrafts, bounced recurring mandates, and penalty fees.",
                "remedy": "Build an immediate liquid reserve buffer of at least 1 month's living expenses."
            })

        if len(months) >= 2:
            prev_m = months[-2]
            curr_m = months[-1]

            prev_inc = monthly_data[prev_m]["income"]
            curr_inc = monthly_data[curr_m]["income"]
            prev_exp = monthly_data[prev_m]["expense"]
            curr_exp = monthly_data[curr_m]["expense"]

            prev_sav_rate = ((prev_inc - prev_exp) / prev_inc * 100) if prev_inc > 0 else 0
            curr_sav_rate = ((curr_inc - curr_exp) / curr_inc * 100) if curr_inc > 0 else 0

            # 2. Declining Savings Rate
            if curr_sav_rate < prev_sav_rate - 8.0:
                signals.append({
                    "signal": "Accelerated Savings Rate Contraction",
                    "severity": "MEDIUM",
                    "evidence": f"Savings rate dropped from {round(prev_sav_rate, 1)}% in {prev_m} to {round(curr_sav_rate, 1)}% in {curr_m}.",
                    "explanation": "Outflows expanded faster than inflows, reducing your net cash margin.",
                    "remedy": "Audit discretionary Food and Shopping categories to restore savings margin above 20%."
                })

            # 3. Spending Outpacing Inflows
            if prev_exp > 0 and prev_inc > 0:
                exp_growth = ((curr_exp - prev_exp) / prev_exp) * 100
                inc_growth = ((curr_inc - prev_inc) / prev_inc) * 100

                if exp_growth - inc_growth > 15.0:
                    signals.append({
                        "signal": "Expenditure Growth Outpacing Inflows",
                        "severity": "HIGH",
                        "evidence": f"Monthly spending expanded by {round(exp_growth, 1)}% while income grew by only {round(inc_growth, 1)}%.",
                        "explanation": "Spending expansion exceeding income velocity leads directly to reserve depletion.",
                        "remedy": "Cap non-essential flexible spending for the next 30 days."
                    })

            # 4. Increasing EMI Share
            prev_dti = (monthly_data[prev_m]["emi"] / prev_inc * 100) if prev_inc > 0 else 0
            curr_dti = (monthly_data[curr_m]["emi"] / curr_inc * 100) if curr_inc > 0 else 0

            if curr_dti > prev_dti + 5.0 and curr_dti > 35.0:
                signals.append({
                    "signal": "Rising Debt-Service Pressure",
                    "severity": "HIGH",
                    "evidence": f"EMI obligations rose from {round(prev_dti, 1)}% to {round(curr_dti, 1)}% of net monthly income.",
                    "explanation": "Fixed loan obligations are consuming an alarming proportion of liquid cash flow.",
                    "remedy": "Avoid taking on additional credit card EMIs or personal loans."
                })

        return signals


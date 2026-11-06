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

    PENALTY_KEYWORDS = [
        "late fee", "penal", "penalty", "bounce", "ecs return",
        "nach bounce", "nach return", "ach return", "return charge",
        "cheque bounce", "overdue charge", "mandate reject"
    ]

    BORROW_KEYWORDS = [
        "loan", "kredit", "moneyview", "cashe", "bnpl", "paylater",
        "cred", "borrow", "advance", "personal loan", "bajaj finserv"
    ]

    DEBT_REPAY_KEYWORDS = [
        "emi", "loan", "repay", "credit card", "bill payment", "due payment"
    ]

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

        # 5. Borrow-to-Repay Loops (Refinancing debt with short-term credit)
        for i in range(len(sorted_txs)):
            tx_credit = sorted_txs[i]
            if tx_credit.credit <= 0:
                continue
            desc_c = tx_credit.description.lower()
            if any(k in desc_c for k in cls.BORROW_KEYWORDS) and "repay" not in desc_c:
                try:
                    d_c = datetime.strptime(tx_credit.date, "%Y-%m-%d")
                    # Look ahead 5 days for debt debit
                    for j in range(i + 1, min(len(sorted_txs), i + 20)):
                        tx_debit = sorted_txs[j]
                        if tx_debit.debit <= 0:
                            continue
                        d_d = datetime.strptime(tx_debit.date, "%Y-%m-%d")
                        diff_days = (d_d - d_c).days
                        if 0 <= diff_days <= 5:
                            desc_d = tx_debit.description.lower()
                            cat_d = (tx_debit.category or "").lower()
                            if any(k in desc_d for k in cls.DEBT_REPAY_KEYWORDS) or "loan" in cat_d:
                                signals.append({
                                    "signal": "Borrow-to-Repay Refinancing Loop",
                                    "severity": "HIGH",
                                    "evidence": f"Inflow of ₹{tx_credit.credit:,.2f} ({tx_credit.description}) on {tx_credit.date} followed within {diff_days} day(s) by debt service outflow of ₹{tx_debit.debit:,.2f} ({tx_debit.description}) on {tx_debit.date}.",
                                    "explanation": "Borrowing new credit shortly before fulfilling debt obligations reflects elevated liquidity recycling risk.",
                                    "remedy": "Freeze taking on short-term BNPL advances to service existing commitments."
                                })
                                break
                except Exception:
                    pass

        # 6. Monthly Minimum-Balance Trend
        if len(months) >= 2:
            min_balances = {}
            for m in months:
                bals = [tx.balance for tx in sorted_txs if tx.date.startswith(m)]
                if bals:
                    min_balances[m] = min(bals)

            if len(min_balances) >= 2:
                m_prev = months[-2]
                m_curr = months[-1]
                prev_min = min_balances[m_prev]
                curr_min = min_balances[m_curr]

                if curr_min < prev_min * 0.60 and curr_min < cls.LOW_BALANCE_THRESHOLD:
                    signals.append({
                        "signal": "Deteriorating Monthly Liquidity Floor",
                        "severity": "HIGH" if curr_min < 1500 else "MEDIUM",
                        "evidence": f"Minimum monthly closing balance fell from ₹{prev_min:,.2f} in {m_prev} to ₹{curr_min:,.2f} in {m_curr}.",
                        "explanation": "A systematically decaying minimum balance floor indicates cash depletion between pay cycles.",
                        "remedy": "Replenish emergency cash reserves to restore minimum liquidity buffer above ₹3,000."
                    })

        # 7. Days of Buffer After Salary Arrival
        salary_txs = [
            tx for tx in sorted_txs
            if tx.credit >= 20000.0 or "salary" in tx.description.lower()
        ]
        for sal in salary_txs[-2:]:
            try:
                d_sal = datetime.strptime(sal.date, "%Y-%m-%d")
                subsequent_txs = [
                    tx for tx in sorted_txs
                    if tx.date > sal.date and (datetime.strptime(tx.date, "%Y-%m-%d") - d_sal).days <= 10
                ]
                for sub_tx in subsequent_txs:
                    if sub_tx.balance < cls.LOW_BALANCE_THRESHOLD or sub_tx.balance < (sal.credit * 0.20):
                        days_drained = (datetime.strptime(sub_tx.date, "%Y-%m-%d") - d_sal).days
                        if days_drained <= 6:
                            signals.append({
                                "signal": "Rapid Post-Salary Depletion",
                                "severity": "HIGH",
                                "evidence": f"Account balance dropped to ₹{sub_tx.balance:,.2f} within {days_drained} day(s) of receiving salary (₹{sal.credit:,.2f} on {sal.date}).",
                                "explanation": "Clustered payments immediately following payday exhaust liquid funds, creating mid-month cash vulnerability.",
                                "remedy": "Stagger non-essential deductions across mid-month to preserve working liquidity."
                            })
                            break
            except Exception:
                pass

        # 8. Penalty or Late-Fee Debits
        penalty_txs = [
            tx for tx in sorted_txs
            if tx.debit > 0 and any(k in tx.description.lower() for k in cls.PENALTY_KEYWORDS)
        ]
        if penalty_txs:
            tot_penalty = sum(t.debit for t in penalty_txs)
            signals.append({
                "signal": "Mandate Bounce & Penalty Charges Detected",
                "severity": "HIGH",
                "evidence": f"Found {len(penalty_txs)} penalty/bounce transaction(s) totaling ₹{tot_penalty:,.2f} on statement.",
                "explanation": "Bank penalty fees and mandate rejections indicate timing mismatches or insufficient balance at clearance.",
                "remedy": "Align recurring debit mandates with confirmed salary credit dates to eliminate bounce penalties."
            })

        # 9. Fixed-Obligation Share of Income
        fixed_categories = {"Housing & Rent", "Loans & EMI", "Utilities & Bills"}
        fixed_debits = sum(tx.debit for tx in sorted_txs if tx.category in fixed_categories)
        total_income = sum(tx.credit for tx in sorted_txs)
        if total_income > 0:
            fixed_ratio = (fixed_debits / total_income) * 100
            if fixed_ratio > 50.0:
                signals.append({
                    "signal": "Elevated Fixed-Obligation Income Share",
                    "severity": "HIGH" if fixed_ratio > 65.0 else "MEDIUM",
                    "evidence": f"Fixed obligations (Rent, EMIs, Utilities) consume {round(fixed_ratio, 1)}% of total verified inflows (healthy ceiling is under 45%).",
                    "explanation": "High fixed overhead reduces discretion to absorb emergency expenses without taking on additional debt.",
                    "remedy": "Prioritize clearing high-interest installment debts to reduce fixed monthly commitments."
                })

        return signals

    @classmethod
    def evaluate_risk_radar(cls, transactions: List[TransactionModel]) -> Dict[str, Any]:
        """
        Debt-Spiral Radar & Transparent Risk Indicator Scoring Engine.
        Synthesizes 7 discrete risk dimensions into a weighted score (0 to 100).
        Strictly labeled as 'Elevated Risk Indicators' (never a verdict).
        """
        if not transactions or len(transactions) < 2:
            return {
                "has_data": False,
                "overall_risk_score": 0,
                "risk_tier": "Insufficient History",
                "indicators": [],
                "mom_comparison": {
                    "previous_month_score": 0,
                    "current_month_score": 0,
                    "score_delta": 0,
                    "trend": "STABLE"
                },
                "methodology": "Multi-dimensional weighted radar evaluating borrow-to-repay loops, liquidity floor trends, buffer drain days, penalty fees, and fixed obligations.",
                "assumptions": {
                    "label": "Elevated Risk Indicators (Probabilistic estimate, not a verdict)",
                    "penalty_keywords": cls.PENALTY_KEYWORDS
                }
            }

        signals = cls.detect_distress_signals(transactions)
        signal_names = {s["signal"] for s in signals}

        indicators = [
            {
                "id": "borrow_to_repay",
                "name": "Borrow-to-Repay Loops",
                "max_points": 20,
                "score": 20 if "Borrow-to-Repay Refinancing Loop" in signal_names else 0,
                "status": "ELEVATED" if "Borrow-to-Repay Refinancing Loop" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Borrow-to-Repay Refinancing Loop"), "No borrowing before debt payments detected.")
            },
            {
                "id": "liquidity_floor",
                "name": "Monthly Balance Floor Trend",
                "max_points": 15,
                "score": 15 if "Deteriorating Monthly Liquidity Floor" in signal_names else 0,
                "status": "ELEVATED" if "Deteriorating Monthly Liquidity Floor" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Deteriorating Monthly Liquidity Floor"), "Minimum monthly closing balance is stable or expanding.")
            },
            {
                "id": "post_salary_buffer",
                "name": "Days of Buffer After Salary",
                "max_points": 15,
                "score": 15 if "Rapid Post-Salary Depletion" in signal_names else 0,
                "status": "ELEVATED" if "Rapid Post-Salary Depletion" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Rapid Post-Salary Depletion"), "Account maintains liquid buffer beyond 7 days post-payday.")
            },
            {
                "id": "penalty_charges",
                "name": "Mandate Bounces & Penalty Charges",
                "max_points": 15,
                "score": 15 if "Mandate Bounce & Penalty Charges Detected" in signal_names else 0,
                "status": "ELEVATED" if "Mandate Bounce & Penalty Charges Detected" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Mandate Bounce & Penalty Charges Detected"), "Zero penalty or mandate bounce debits detected.")
            },
            {
                "id": "fixed_obligations",
                "name": "Fixed-Obligation Income Share",
                "max_points": 15,
                "score": 15 if "Elevated Fixed-Obligation Income Share" in signal_names else 0,
                "status": "ELEVATED" if "Elevated Fixed-Obligation Income Share" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Elevated Fixed-Obligation Income Share"), "Fixed commitments comfortably within 45% of income.")
            },
            {
                "id": "savings_contraction",
                "name": "Accelerated Savings Contraction",
                "max_points": 10,
                "score": 10 if "Accelerated Savings Rate Contraction" in signal_names else 0,
                "status": "ELEVATED" if "Accelerated Savings Rate Contraction" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Accelerated Savings Rate Contraction"), "Savings rate trajectory is stable or expanding.")
            },
            {
                "id": "spending_expansion",
                "name": "Expenditure Growth Outpacing Inflows",
                "max_points": 10,
                "score": 10 if "Expenditure Growth Outpacing Inflows" in signal_names else 0,
                "status": "ELEVATED" if "Expenditure Growth Outpacing Inflows" in signal_names else "CLEAN",
                "evidence": next((s["evidence"] for s in signals if s["signal"] == "Expenditure Growth Outpacing Inflows"), "Expense velocity remains disciplined relative to income.")
            }
        ]

        total_risk = sum(ind["score"] for ind in indicators)

        # MoM Risk Score Delta Comparison
        sorted_txs = sorted(transactions, key=lambda x: x.date)
        months_set = sorted(list(set(tx.date[:7] for tx in sorted_txs if tx.date)))
        curr_m_score = total_risk
        prev_m_score = total_risk

        if len(months_set) >= 2:
            prev_month = months_set[-2]
            prev_month_txs = [tx for tx in sorted_txs if tx.date.startswith(prev_month)]
            if prev_month_txs:
                prev_signals = cls.detect_distress_signals(prev_month_txs)
                prev_names = {s["signal"] for s in prev_signals}
                prev_m_score = (
                    (20 if "Borrow-to-Repay Refinancing Loop" in prev_names else 0) +
                    (15 if "Deteriorating Monthly Liquidity Floor" in prev_names else 0) +
                    (15 if "Rapid Post-Salary Depletion" in prev_names else 0) +
                    (15 if "Mandate Bounce & Penalty Charges Detected" in prev_names else 0) +
                    (15 if "Elevated Fixed-Obligation Income Share" in prev_names else 0) +
                    (10 if "Accelerated Savings Rate Contraction" in prev_names else 0) +
                    (10 if "Expenditure Growth Outpacing Inflows" in prev_names else 0)
                )

        score_delta = curr_m_score - prev_m_score
        trend = "INCREASED_RISK" if score_delta > 5 else "DECREASED_RISK" if score_delta < -5 else "STABLE"

        tier = "Critical Risk Elevation" if total_risk >= 50 else "Moderate Risk Indicators" if total_risk >= 25 else "Minimal Elevated Risk"

        return {
            "has_data": True,
            "overall_risk_score": total_risk,
            "max_possible_score": 100,
            "risk_tier": tier,
            "active_signal_count": len([ind for ind in indicators if ind["score"] > 0]),
            "indicators": indicators,
            "signals": signals,
            "mom_comparison": {
                "previous_month_score": prev_m_score,
                "current_month_score": curr_m_score,
                "score_delta": score_delta,
                "trend": trend
            },
            "methodology": "Multi-dimensional weighted radar evaluating borrow-to-repay loops (20pts), liquidity floor trend (15pts), buffer drain days (15pts), penalty fees (15pts), and fixed obligations (15pts).",
            "assumptions": {
                "wording": "Elevated risk indicators (estimates, not verdicts)",
                "penalty_keywords": cls.PENALTY_KEYWORDS
            }
        }


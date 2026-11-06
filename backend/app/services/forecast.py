from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from app.models.transaction import TransactionModel
from app.services.recurring import RecurringPaymentDetector

class CashFlowForecaster:
    """
    30-Day Predictive Cash-Flow Engine.
    Simulates daily liquidity trajectory using:
      1. Verified closing balance as starting point
      2. Trailing daily discretionary spend rate
      3. Scheduled recurring obligations (EMIs, rent, utilities, subscriptions)
      4. Expected salary/income recurrence
      5. Crunch-point detection (low balance / negative balance risks)
    """

    SAFETY_FLOOR = 3000.0  # Alert floor in INR

    @classmethod
    def forecast(
        cls,
        transactions: List[TransactionModel],
        days: int = 30
    ) -> Dict[str, Any]:
        if not transactions:
            return {
                "has_data": False,
                "starting_balance": 0.0,
                "daily_projection": [],
                "crunch_points": [],
                "assumptions": {},
                "summary": "No transaction history available to simulate cash flow."
            }

        sorted_txs = sorted(transactions, key=lambda x: (x.date, x.id))
        latest_tx = sorted_txs[-1]
        start_date = datetime.strptime(latest_tx.date, "%Y-%m-%d")
        current_balance = round(latest_tx.balance, 2)

        # 1. Detect recurring payments
        recurring_commitments = RecurringPaymentDetector.detect(sorted_txs)

        # 2. Compute Trailing Discretionary Daily Burn
        # Look back up to 60 days from latest date
        lookback_date = start_date - timedelta(days=60)
        recent_debits = [
            tx for tx in sorted_txs
            if tx.debit > 0 and datetime.strptime(tx.date, "%Y-%m-%d") >= lookback_date
        ]

        # Identify which transactions were part of recurring commitments to exclude from discretionary
        recurring_tx_ids = set()
        for rec in recurring_commitments:
            recurring_tx_ids.update(rec.get("transaction_ids", []))

        discretionary_txs = [tx for tx in recent_debits if tx.id not in recurring_tx_ids]
        discretionary_total = sum(tx.debit for tx in discretionary_txs)

        # Calculate active days in lookback period
        unique_days = len(set(tx.date for tx in recent_debits))
        divisor = max(14, unique_days)
        daily_discretionary = round(discretionary_total / divisor, 2) if divisor > 0 else 500.0
        # Sanity bound: daily burn between ₹100 and ₹5,000
        daily_discretionary = max(100.0, min(5000.0, daily_discretionary))

        # 3. Detect Salary / Regular Income Recurrence
        credits = [tx for tx in sorted_txs if tx.credit > 0]
        income_txs = [
            tx for tx in credits
            if "salary" in tx.description.lower() or tx.category == "Income" or tx.credit >= 20000.0
        ]

        expected_income_events = []
        if income_txs:
            # Group by day of month
            salary_days = [datetime.strptime(tx.date, "%Y-%m-%d").day for tx in income_txs]
            median_day = int(statistics.median(salary_days))
            typical_salary = round(statistics.median([tx.credit for tx in income_txs]), 2)

            # Project salary credits in the next 30 days
            for d in range(1, days + 1):
                proj_date = start_date + timedelta(days=d)
                # Check if projected date matches salary day (or adjusted for month length)
                if proj_date.day == median_day or (median_day > 28 and proj_date.day in (28, 29, 30, 31) and (proj_date + timedelta(days=1)).month != proj_date.month):
                    expected_income_events.append({
                        "date": proj_date.strftime("%Y-%m-%d"),
                        "amount": typical_salary,
                        "description": f"Expected Salary / Regular Income (₹{typical_salary:,.2f})"
                    })

        # 4. Map Recurring Commitments into the Projection Horizon
        scheduled_obligations = defaultdict(list)
        for rec in recurring_commitments:
            # Project dates from last_date using cycle_days
            last_dt = datetime.strptime(rec["last_date"], "%Y-%m-%d")
            cycle_days = rec.get("cycle_days", 30)
            avg_amt = rec["average_amount"]
            merchant = rec["merchant"]

            # Step forward
            curr_dt = last_dt + timedelta(days=cycle_days)
            end_horizon = start_date + timedelta(days=days)

            while curr_dt <= end_horizon:
                if curr_dt > start_date:
                    date_str = curr_dt.strftime("%Y-%m-%d")
                    scheduled_obligations[date_str].append({
                        "merchant": merchant,
                        "amount": avg_amt,
                        "classification": rec["classification"],
                        "description": f"{merchant} ({rec['classification']})"
                    })
                curr_dt += timedelta(days=cycle_days)

        # 5. Daily Simulation
        daily_projection = []
        running_balance = current_balance
        crunch_points = []
        total_projected_inflow = 0.0
        total_projected_outflow = 0.0

        for d in range(1, days + 1):
            target_date = start_date + timedelta(days=d)
            date_str = target_date.strftime("%Y-%m-%d")

            day_inflow = 0.0
            day_outflow = 0.0
            events = []

            # Check expected salary/income
            for inc in expected_income_events:
                if inc["date"] == date_str:
                    day_inflow += inc["amount"]
                    events.append(f"+ ₹{inc['amount']:,.0f} {inc['description']}")

            # Check scheduled obligations
            if date_str in scheduled_obligations:
                for ob in scheduled_obligations[date_str]:
                    day_outflow += ob["amount"]
                    events.append(f"- ₹{ob['amount']:,.0f} {ob['description']}")

            # Apply daily discretionary spending
            day_outflow += daily_discretionary
            events.append(f"- ₹{daily_discretionary:,.0f} Estimated Discretionary Outlays")

            running_balance = round(running_balance + day_inflow - day_outflow, 2)
            total_projected_inflow += day_inflow
            total_projected_outflow += day_outflow

            # Evaluate Crunch Points
            if running_balance < cls.SAFETY_FLOOR:
                # Find primary upcoming scheduled payment triggering crunch
                triggering_payment = ""
                if date_str in scheduled_obligations:
                    top_ob = max(scheduled_obligations[date_str], key=lambda x: x["amount"])
                    triggering_payment = f"before your ₹{top_ob['amount']:,.0f} {top_ob['merchant']} payment"

                is_negative = running_balance < 0
                crunch_points.append({
                    "date": date_str,
                    "day_offset": d,
                    "projected_balance": running_balance,
                    "severity": "CRITICAL" if is_negative else "WARNING",
                    "trigger": triggering_payment,
                    "message": (
                        f"Potential cash shortage: Your projected balance may dip to ₹{running_balance:,.2f} on {target_date.strftime('%b %d')}"
                        + (f" ({triggering_payment})." if triggering_payment else ".")
                    )
                })

            daily_projection.append({
                "date": date_str,
                "day_number": d,
                "projected_balance": running_balance,
                "inflow": round(day_inflow, 2),
                "outflow": round(day_outflow, 2),
                "events": events,
                "is_below_safety": running_balance < cls.SAFETY_FLOOR,
                "is_negative": running_balance < 0
            })

        # Synthesize primary crunch highlight
        primary_crunch = None
        if crunch_points:
            # Pick first or most severe crunch point
            primary_crunch = min(crunch_points, key=lambda x: x["projected_balance"])

        return {
            "has_data": True,
            "starting_balance": current_balance,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": (start_date + timedelta(days=days)).strftime("%Y-%m-%d"),
            "projection_days": days,
            "safety_floor": cls.SAFETY_FLOOR,
            "ending_projected_balance": running_balance,
            "total_projected_inflow": round(total_projected_inflow, 2),
            "total_projected_outflow": round(total_projected_outflow, 2),
            "net_projected_cashflow": round(total_projected_inflow - total_projected_outflow, 2),
            "daily_projection": daily_projection,
            "crunch_points": crunch_points,
            "primary_crunch_alert": primary_crunch,
            "assumptions": {
                "starting_balance": current_balance,
                "daily_discretionary_burn": daily_discretionary,
                "expected_income_count": len(expected_income_events),
                "scheduled_obligations_count": sum(len(v) for v in scheduled_obligations.values()),
                "methodology": "Linear daily cash burn simulation combining historical discretionary burn rates with detected recurring payment schedules."
            },
            "disclaimer": "Projections are mathematical scenario simulations based on historical recurring cadence. They do not constitute deterministic or legally binding guarantees."
        }


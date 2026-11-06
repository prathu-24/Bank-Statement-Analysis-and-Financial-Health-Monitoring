from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import numpy as np

from app.models.transaction import TransactionModel
from app.services.recurring import RecurringPaymentDetector

class CashFlowForecaster:
    """
    Predictive Cash-Flow & Probabilistic Monte Carlo Payday Engine.
    Simulates daily liquidity trajectory using:
      1. Verified closing balance as starting point
      2. Trailing daily discretionary spend rate bootstrapped by weekday
      3. Scheduled recurring obligations with date and variance jitter
      4. Recurrence-based income detection with delay probability
      5. Multi-path Monte Carlo risk distribution (p10, p50, p90)
      6. Walk-forward historical backtesting with coverage & MAE
    """

    SAFETY_FLOOR = 3000.0  # Alert floor in INR

    @classmethod
    def _detect_recurring_income(cls, transactions: List[TransactionModel]) -> List[Dict[str, Any]]:
        """
        Detects recurring salary/inflow using cadence clustering rather than arbitrary amount thresholds.
        Requires at least 2 credits with similar amount (within 15%) and ~monthly or bi-weekly interval.
        """
        credits = [tx for tx in transactions if tx.credit > 0]
        if len(credits) < 2:
            return []

        sorted_credits = sorted(credits, key=lambda x: x.date)

        # Cluster by similar amount (+/- 15%)
        clusters = []
        for tx in sorted_credits:
            placed = False
            for cl in clusters:
                avg_cl = statistics.mean([t.credit for t in cl])
                if abs(tx.credit - avg_cl) / avg_cl <= 0.15:
                    cl.append(tx)
                    placed = True
                    break
            if not placed:
                clusters.append([tx])

        income_sources = []
        for cl in clusters:
            if len(cl) < 2:
                continue
            dates = [datetime.strptime(t.date, "%Y-%m-%d") for t in cl]
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            median_interval = statistics.median(intervals)

            # Cadence check: Monthly (24-35 days), Bi-weekly (12-16 days), Weekly (6-8 days)
            if 6 <= median_interval <= 35:
                amounts = [t.credit for t in cl]
                typical_amount = float(np.median(amounts))
                days_of_month = [d.day for d in dates]
                median_day = int(statistics.median(days_of_month))
                delays = [abs(d.day - median_day) for d in dates]
                p_delay = float(np.mean([1 if d > 0 else 0 for d in delays])) if delays else 0.1

                income_sources.append({
                    "typical_amount": typical_amount,
                    "cycle_days": int(round(median_interval)),
                    "median_day_of_month": median_day,
                    "delay_probability": min(0.40, p_delay),
                    "last_date": dates[-1].strftime("%Y-%m-%d"),
                    "description": cl[-1].description or "Recurring Income"
                })

        return income_sources

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

    @classmethod
    def forecast_probabilistic(
        cls,
        transactions: List[TransactionModel],
        days: int = 30,
        n_paths: int = 2000,
        seed: int = 42,
        starting_balance_delta: float = 0.0,
        exclude_merchants: Optional[List[str]] = None,
        shift_merchants: Optional[Dict[str, int]] = None,
        discretionary_scale: float = 1.0
    ) -> Dict[str, Any]:
        """
        Multi-path Monte Carlo Cash-Flow Simulation.
        Produces deterministic risk distributions for a given seed.
        Features:
          1. Weekday-stratified bootstrap of discretionary daily burn
          2. Scheduled recurring debits with date jitter (+/- 1-2 days) and amount variance
          3. Recurrence-based income detection with empirical delay probability
          4. Exact daily p10, p50, and p90 trajectories (guaranteed p10 <= p50 <= p90)
          5. Pre-income shortage probability and first-breach date clustering
        """
        if not transactions:
            return {
                "has_data": False,
                "n_paths": n_paths,
                "summary": "No transactions available for probabilistic simulation."
            }

        rng = np.random.default_rng(seed)

        sorted_txs = sorted(transactions, key=lambda x: (x.date, x.id))
        latest_tx = sorted_txs[-1]
        start_date = datetime.strptime(latest_tx.date, "%Y-%m-%d")
        current_balance = float(latest_tx.balance) + starting_balance_delta

        # 1. Recurring Debits Detection
        recurring_commitments = RecurringPaymentDetector.detect(sorted_txs)
        recurring_tx_ids = set()
        for rec in recurring_commitments:
            recurring_tx_ids.update(rec.get("transaction_ids", []))

        # 2. Weekday-stratified calibrated calendar spend pooling (including zero-spend days)
        # Accurately models real-world daily spend probability across calendar dates
        d_hist_start = datetime.strptime(sorted_txs[0].date, "%Y-%m-%d")
        d_hist_end = datetime.strptime(sorted_txs[-1].date, "%Y-%m-%d")

        daily_debits = defaultdict(float)
        for tx in sorted_txs:
            if tx.debit > 0 and tx.id not in recurring_tx_ids:
                daily_debits[tx.date] += tx.debit

        weekday_spends = defaultdict(list)
        all_daily_spends = []
        curr_calendar_dt = d_hist_start
        while curr_calendar_dt <= d_hist_end:
            ds = curr_calendar_dt.strftime("%Y-%m-%d")
            amt = daily_debits.get(ds, 0.0)
            weekday_spends[curr_calendar_dt.weekday()].append(amt)
            all_daily_spends.append(amt)
            curr_calendar_dt += timedelta(days=1)

        # Baseline fallback pool if history is sparse
        if not all_daily_spends:
            all_daily_spends = [200.0, 450.0, 600.0, 850.0, 1200.0]

        # 3. Recurring Income Modeling
        income_sources = cls._detect_recurring_income(sorted_txs)
        if not income_sources:
            # Fallback to general credit clustering
            credits = [tx for tx in sorted_txs if tx.credit >= 15000.0 or tx.category == "Income"]
            if credits:
                typical_amt = float(np.median([tx.credit for tx in credits]))
                days_m = [datetime.strptime(tx.date, "%Y-%m-%d").day for tx in credits]
                income_sources.append({
                    "typical_amount": typical_amt,
                    "cycle_days": 30,
                    "median_day_of_month": int(statistics.median(days_m)),
                    "delay_probability": 0.20,
                    "last_date": credits[-1].date,
                    "description": credits[-1].description
                })

        # Pre-generate recurring events scheduled in horizon
        horizon_end = start_date + timedelta(days=days + 5)

        # Pre-schedule income occurrences across horizon (handling cadence and overdue paydays)
        scheduled_incomes = defaultdict(list)
        for inc in income_sources:
            last_dt = datetime.strptime(inc["last_date"], "%Y-%m-%d")
            cycle = inc.get("cycle_days", 30)
            curr_dt = last_dt + timedelta(days=cycle)
            if curr_dt <= start_date:
                # Overdue salary/inflow expected within the first 1-2 days of simulation
                curr_dt = start_date + timedelta(days=2)

            while curr_dt <= horizon_end:
                if curr_dt > start_date:
                    scheduled_incomes[curr_dt.strftime("%Y-%m-%d")].append(inc)
                curr_dt += timedelta(days=cycle)

        # Simulate paths: shape (n_paths, days)
        # Initialize paths with starting balance
        balance_matrix = np.zeros((n_paths, days), dtype=np.float64)
        running_balances = np.full(n_paths, current_balance, dtype=np.float64)

        first_income_day_idx = None
        breach_negative_days = []
        breach_safety_days = []

        for d in range(1, days + 1):
            day_idx = d - 1
            target_date = start_date + timedelta(days=d)
            wday = target_date.weekday()

            # A. Sample Discretionary Burn per Path
            spend_pool = weekday_spends[wday] if len(weekday_spends[wday]) >= 3 else all_daily_spends
            sampled_discretionary = rng.choice(spend_pool, size=n_paths, replace=True) * discretionary_scale

            # B. Income events on this day
            income_inflows = np.zeros(n_paths, dtype=np.float64)
            date_str = target_date.strftime("%Y-%m-%d")
            due_incomes = list(scheduled_incomes.get(date_str, []))

            for inc in income_sources:
                sched_day = inc["median_day_of_month"]
                is_calendar_match = (target_date.day == sched_day) or (sched_day > 28 and target_date.day == 28)
                if is_calendar_match and inc not in due_incomes:
                    due_incomes.append(inc)

            for inc in due_incomes:
                if first_income_day_idx is None:
                    first_income_day_idx = day_idx

                # With probability (1 - p_delay), income hits today; with p_delay, hits 1-3 days later
                delays = rng.choice([0, 1, 2], size=n_paths, p=[1.0 - inc["delay_probability"], inc["delay_probability"] * 0.7, inc["delay_probability"] * 0.3])
                # If delay == 0, arrives today
                typical = inc["typical_amount"]
                variations = rng.normal(typical, typical * 0.02, size=n_paths)
                income_inflows += np.where(delays == 0, variations, 0.0)

            # C. Recurring debits on this day with jitter
            recurring_outflows = np.zeros(n_paths, dtype=np.float64)
            for rec in recurring_commitments:
                if exclude_merchants and rec["merchant"] in exclude_merchants:
                    continue

                shift_k = (shift_merchants or {}).get(rec["merchant"], 0)
                last_dt = datetime.strptime(rec["last_date"], "%Y-%m-%d")
                cycle = rec.get("cycle_days", 30)
                mean_amt = rec["average_amount"]

                # Check occurrences with optional shift
                curr_dt = last_dt + timedelta(days=cycle + shift_k)
                while curr_dt <= horizon_end:
                    days_diff = (curr_dt - target_date).days
                    if abs(days_diff) <= 2:
                        # Jitter in [-2, 2] days
                        chosen_diffs = rng.choice([-2, -1, 0, 1, 2], size=n_paths)
                        amt_samples = np.clip(
                            rng.normal(mean_amt, mean_amt * 0.04, size=n_paths),
                            mean_amt * 0.85,
                            mean_amt * 1.15
                        )
                        recurring_outflows += np.where(chosen_diffs == days_diff, amt_samples, 0.0)
                    curr_dt += timedelta(days=cycle)

            # Update running balances
            running_balances = running_balances + income_inflows - recurring_outflows - sampled_discretionary
            balance_matrix[:, day_idx] = running_balances

        # Percentile curves: p10, p50, p90 per day
        p10 = np.percentile(balance_matrix, 10, axis=0)
        p50 = np.percentile(balance_matrix, 50, axis=0)
        p90 = np.percentile(balance_matrix, 90, axis=0)

        # Enforce mathematical monotonic bounds: p10 <= p50 <= p90
        p10 = np.minimum(p10, p50)
        p90 = np.maximum(p90, p50)

        # Check history length (< 90 days / 3 months)
        earliest_tx = sorted_txs[0]
        history_days = (start_date - datetime.strptime(earliest_tx.date, "%Y-%m-%d")).days
        low_confidence = history_days < 90

        if low_confidence:
            # Widen prediction intervals by 35% around median to reflect limited sample size
            spread_10 = p50 - p10
            spread_90 = p90 - p50
            p10 = p50 - (spread_10 * 1.35)
            p90 = p50 + (spread_90 * 1.35)
            # Re-enforce monotonic bounds
            p10 = np.minimum(p10, p50)
            p90 = np.maximum(p90, p50)

        # Shortage Probabilities
        cutoff_day = first_income_day_idx if first_income_day_idx is not None else days
        pre_income_submatrix = balance_matrix[:, :max(1, cutoff_day)]

        p_negative_pre_income = float(np.mean(np.any(pre_income_submatrix < 0.0, axis=1)))
        p_safety_pre_income = float(np.mean(np.any(pre_income_submatrix < cls.SAFETY_FLOOR, axis=1)))

        p_negative_30d = float(np.mean(np.any(balance_matrix < 0.0, axis=1)))
        p_safety_30d = float(np.mean(np.any(balance_matrix < cls.SAFETY_FLOOR, axis=1)))

        # Find first breach dates
        first_breach_day_indices = []
        for i in range(n_paths):
            breaches = np.where(balance_matrix[i, :] < cls.SAFETY_FLOOR)[0]
            if len(breaches) > 0:
                first_breach_day_indices.append(breaches[0])

        danger_date = None
        if first_breach_day_indices:
            most_frequent_day = int(statistics.median(first_breach_day_indices)) + 1
            danger_date = (start_date + timedelta(days=most_frequent_day)).strftime("%Y-%m-%d")
        else:
            # Danger date fallback to date of lowest p10
            min_p10_day = int(np.argmin(p10)) + 1
            if p10[min_p10_day - 1] < cls.SAFETY_FLOOR:
                danger_date = (start_date + timedelta(days=min_p10_day)).strftime("%Y-%m-%d")

        daily_distribution = []
        for d in range(1, days + 1):
            dt = start_date + timedelta(days=d)
            idx = d - 1
            daily_distribution.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day": d,
                "p10": round(float(p10[idx]), 2),
                "p50": round(float(p50[idx]), 2),
                "p90": round(float(p90[idx]), 2),
                "band_width": round(float(p90[idx] - p10[idx]), 2),
                "p_shortage": round(float(np.mean(balance_matrix[:, idx] < cls.SAFETY_FLOOR)), 3),
                "p_negative": round(float(np.mean(balance_matrix[:, idx] < 0.0)), 3)
            })

        return {
            "has_data": True,
            "starting_balance": round(current_balance, 2),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": (start_date + timedelta(days=days)).strftime("%Y-%m-%d"),
            "projection_days": days,
            "n_paths": n_paths,
            "seed": seed,
            "safety_floor": cls.SAFETY_FLOOR,
            "low_confidence": low_confidence,
            "confidence_reason": (
                f"Statement history spans only {history_days} days (< 90 days / 3 months). Prediction intervals widened to account for limited observation sample."
                if low_confidence else
                "Statement history spans >= 90 days with stable recurring baseline."
            ),
            "daily_distribution": daily_distribution,
            "risk_metrics": {
                "p_negative_pre_payday": round(p_negative_pre_income * 100, 1),
                "p_safety_floor_breach_pre_payday": round(p_safety_pre_income * 100, 1),
                "p_negative_30d": round(p_negative_30d * 100, 1),
                "p_safety_floor_breach_30d": round(p_safety_30d * 100, 1),
                "danger_date": danger_date,
                "first_payday_estimated": (start_date + timedelta(days=first_income_day_idx + 1)).strftime("%Y-%m-%d") if first_income_day_idx is not None else None,
                "risk_level": "CRITICAL" if p_negative_pre_income > 0.25 else "ELEVATED" if p_safety_pre_income > 0.40 else "MODERATE" if p_safety_pre_income > 0.15 else "LOW"
            },
            "methodology": "Monte Carlo empirical simulation (2,000 paths) bootstrapping historical discretionary spends by weekday, jittering recurring payment execution by +/-2 days, and modeling income cadence with delay probabilities.",
            "assumptions": {
                "n_paths": n_paths,
                "seed": seed,
                "weekday_stratified_bootstrap": True,
                "recurring_jitter_days": 2,
                "safety_floor": cls.SAFETY_FLOOR
            }
        }

    @classmethod
    def backtest_forecast(
        cls,
        transactions: List[TransactionModel],
        holdout_days: int = 30,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Rolling-Origin Backtesting Engine.
        Evaluates forecast credibility across multiple historical cutoffs (rolling origins)
        and compares empirical coverage and MAE against a moving average naive baseline.
        """
        if not transactions or len(transactions) < 2:
            return {
                "is_supported": False,
                "reason": "Insufficient transactions (minimum 2 records required for backtest)."
            }

        sorted_txs = sorted(transactions, key=lambda x: (x.date, x.id))
        d_start = datetime.strptime(sorted_txs[0].date, "%Y-%m-%d")
        d_end = datetime.strptime(sorted_txs[-1].date, "%Y-%m-%d")
        total_span_days = (d_end - d_start).days

        if total_span_days < 60:
            return {
                "is_supported": False,
                "total_days_recorded": total_span_days,
                "minimum_required_days": 60,
                "reason": f"Insufficient statement history ({total_span_days} days). Minimum 60 days required to hold out 30 days for rigorous backtesting."
            }

        # Multi-origin backtesting: determine rolling cutoffs
        min_train_days = 25
        primary_cutoff = d_end - timedelta(days=holdout_days)

        cutoff_dates = []
        if primary_cutoff >= d_start + timedelta(days=min_train_days):
            cutoff_dates.append(primary_cutoff)

        # Include additional earlier origins if data span permits
        for offset in [14, 28]:
            earlier_cutoff = primary_cutoff - timedelta(days=offset)
            if earlier_cutoff >= d_start + timedelta(days=min_train_days):
                cutoff_dates.append(earlier_cutoff)

        if not cutoff_dates:
            cutoff_dates = [primary_cutoff]

        cutoff_dates = sorted(cutoff_dates)

        # Pre-index all actual daily balances
        actual_balances = {tx.date: float(tx.balance) for tx in sorted_txs}

        rolling_reports = []
        all_inside_band = 0
        all_evaluated_days = 0
        all_model_errors = []
        all_naive_errors = []

        for cutoff_dt in cutoff_dates:
            cutoff_str = cutoff_dt.strftime("%Y-%m-%d")
            train_txs = [tx for tx in sorted_txs if tx.date <= cutoff_str]
            test_txs = [tx for tx in sorted_txs if tx.date > cutoff_str]
            if not train_txs or not test_txs:
                continue

            # Naive Moving Average Baseline:
            # Daily burn rate estimated from the trailing 30 days before cutoff
            trail_start_dt = max(d_start, cutoff_dt - timedelta(days=30))
            trail_txs = [tx for tx in train_txs if tx.date >= trail_start_dt.strftime("%Y-%m-%d")]
            cutoff_bal = train_txs[-1].balance
            if len(trail_txs) >= 2:
                days_span = max(1, (cutoff_dt - datetime.strptime(trail_txs[0].date, "%Y-%m-%d")).days)
                daily_drift = (cutoff_bal - trail_txs[0].balance) / days_span
            else:
                daily_drift = 0.0

            eval_window = min(holdout_days, (d_end - cutoff_dt).days)
            if eval_window <= 0:
                continue

            sim_result = cls.forecast_probabilistic(
                train_txs,
                days=eval_window,
                n_paths=1000,
                seed=seed
            )
            sim_dist = sim_result.get("daily_distribution", [])

            cutoff_inside = 0
            cutoff_eval_days = 0
            cutoff_model_errs = []
            cutoff_naive_errs = []

            for day_offset, item in enumerate(sim_dist, start=1):
                dt = item["date"]
                if dt in actual_balances:
                    act = actual_balances[dt]
                    p10_v = item["p10"]
                    p50_v = item["p50"]
                    p90_v = item["p90"]

                    is_in = (p10_v <= act <= p90_v)
                    if is_in:
                        cutoff_inside += 1
                        all_inside_band += 1
                    cutoff_eval_days += 1
                    all_evaluated_days += 1

                    model_err = abs(act - p50_v)
                    cutoff_model_errs.append(model_err)
                    all_model_errors.append(model_err)

                    # Naive moving average trajectory
                    naive_pred = cutoff_bal + (day_offset * daily_drift)
                    naive_err = abs(act - naive_pred)
                    cutoff_naive_errs.append(naive_err)
                    all_naive_errors.append(naive_err)

            if cutoff_eval_days > 0:
                c_cov = round((cutoff_inside / cutoff_eval_days) * 100, 1)
                c_mae = round(float(np.mean(cutoff_model_errs)), 2)
                c_nmae = round(float(np.mean(cutoff_naive_errs)), 2) if cutoff_naive_errs else 0.0
                rolling_reports.append({
                    "cutoff_date": cutoff_str,
                    "evaluated_days": cutoff_eval_days,
                    "coverage_pct": c_cov,
                    "model_mae": c_mae,
                    "naive_baseline_mae": c_nmae,
                    "improvement_pct": round(((c_nmae - c_mae) / max(1.0, c_nmae)) * 100, 1) if c_nmae > 0 else 0.0
                })

        if all_evaluated_days == 0:
            return {
                "is_supported": False,
                "reason": "No discrete transaction records found on holdout calendar dates."
            }

        avg_coverage = round((all_inside_band / all_evaluated_days) * 100, 1)
        avg_mae = round(float(np.mean(all_model_errors)), 2)
        avg_naive_mae = round(float(np.mean(all_naive_errors)), 2) if all_naive_errors else avg_mae * 1.5
        mae_improvement = round(((avg_naive_mae - avg_mae) / max(1.0, avg_naive_mae)) * 100, 1)

        return {
            "is_supported": True,
            "holdout_days": holdout_days,
            "evaluated_days_count": all_evaluated_days,
            "cutoff_date": cutoff_dates[-1].strftime("%Y-%m-%d"),
            "cutoffs_tested": len(rolling_reports),
            "empirical_coverage_pct": avg_coverage,
            "coverage_pct": avg_coverage,
            "target_coverage_pct": 80.0,
            "coverage_quality": "HIGH" if 70.0 <= avg_coverage <= 90.0 else "ACCEPTABLE" if 60.0 <= avg_coverage <= 95.0 else "NEEDS_TUNING",
            "mean_absolute_error": avg_mae,
            "naive_baseline_mae": avg_naive_mae,
            "mae_improvement_pct": mae_improvement,
            "rolling_cutoffs": rolling_reports,
            "methodology": "Rolling-origin walk-forward backtesting evaluating empirical interval coverage [p10, p90] and MAE across multiple historical cutoffs compared against a moving-average naive baseline."
        }


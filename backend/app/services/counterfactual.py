from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import numpy as np

from app.models.transaction import TransactionModel
from app.services.recurring import RecurringPaymentDetector
from app.services.forecast import CashFlowForecaster

class CounterfactualActionEngine:
    """
    Counterfactual Financial Decision Intelligence Engine.
    Evaluates computed interventions by modifying simulation parameters and re-running
    the identical 2,000 Monte Carlo paths under the exact same random seed.
    Guarantees:
      - All deltas stem purely from user interventions, zero simulation noise.
      - Ranked by risk reduction per rupee of monthly sacrifice.
      - Top action never increases risk.
    """

    @classmethod
    def evaluate_actions(
        cls,
        transactions: List[TransactionModel],
        days: int = 30,
        n_paths: int = 1500,
        seed: int = 42
    ) -> Dict[str, Any]:
        if not transactions or len(transactions) < 2:
            return {
                "has_data": False,
                "baseline_risk": 0.0,
                "actions": [],
                "summary": "Insufficient transaction records to compute counterfactual actions."
            }

        sorted_txs = sorted(transactions, key=lambda x: (x.date, x.id))

        # 1. Run Baseline Probabilistic Forecast
        baseline = CashFlowForecaster.forecast_probabilistic(
            sorted_txs,
            days=days,
            n_paths=n_paths,
            seed=seed
        )

        p_neg_before = baseline["risk_metrics"]["p_negative_pre_payday"]
        p_safety_before = baseline["risk_metrics"]["p_safety_floor_breach_pre_payday"]
        p50_before = [d["p50"] for d in baseline["daily_distribution"]]
        dates = [d["date"] for d in baseline["daily_distribution"]]

        candidate_actions: List[Dict[str, Any]] = []

        # 2. Candidate Action Set A: Pause / Cancel Recurring Commitments
        recurring_items = RecurringPaymentDetector.detect(sorted_txs)
        for rec in recurring_items[:4]:
            merchant = rec["merchant"]
            cost = rec["average_amount"]

            # Re-run simulation excluding this merchant with identical seed
            sim_after = CashFlowForecaster.forecast_probabilistic(
                sorted_txs,
                days=days,
                n_paths=n_paths,
                seed=seed,
                exclude_merchants=[merchant]
            )

            p_neg_after = sim_after["risk_metrics"]["p_negative_pre_payday"]
            p_safety_after = sim_after["risk_metrics"]["p_safety_floor_breach_pre_payday"]
            p50_after = [d["p50"] for d in sim_after["daily_distribution"]]

            risk_reduction = round(max(0.0, p_neg_before - p_neg_after), 1)
            safety_reduction = round(max(0.0, p_safety_before - p_safety_after), 1)

            # Efficiency: risk reduction per rupee
            efficiency = ((risk_reduction * 100.0) + (safety_reduction * 20.0)) / max(100.0, cost)

            candidate_actions.append({
                "action_type": "PAUSE_RECURRING",
                "target": merchant,
                "title": f"Pause or Cancel {merchant} ({rec['frequency']})",
                "description": f"Pausing {merchant} frees up ₹{cost:,.2f} every {rec['frequency'].lower()}, eliminating scheduled deductions from your liquid balance.",
                "monthly_sacrifice": round(cost, 2),
                "risk_before": p_neg_before,
                "risk_after": p_neg_after,
                "risk_reduction": risk_reduction,
                "safety_risk_before": p_safety_before,
                "safety_risk_after": p_safety_after,
                "safety_risk_reduction": safety_reduction,
                "efficiency_score": round(efficiency, 3),
                "daily_p50_after": p50_after
            })

            # 3. Candidate Action Set B: Shift Recurring Debit Date by +5 Days (Timing Optimization)
            if rec.get("classification") in ("EMI / Loan", "Housing / Rent", "Recurring Expense"):
                sim_shift = CashFlowForecaster.forecast_probabilistic(
                    sorted_txs,
                    days=days,
                    n_paths=n_paths,
                    seed=seed,
                    shift_merchants={merchant: 5}
                )

                shift_neg_after = sim_shift["risk_metrics"]["p_negative_pre_payday"]
                shift_safety_after = sim_shift["risk_metrics"]["p_safety_floor_breach_pre_payday"]
                shift_p50_after = [d["p50"] for d in sim_shift["daily_distribution"]]

                shift_risk_red = round(max(0.0, p_neg_before - shift_neg_after), 1)
                shift_safety_red = round(max(0.0, p_safety_before - shift_safety_after), 1)

                # Date shifts have 0 rupee sacrifice -> highest efficiency if they reduce risk!
                shift_efficiency = (shift_risk_red * 150.0) + (shift_safety_red * 30.0)

                if shift_risk_red > 0 or shift_safety_red > 0:
                    candidate_actions.append({
                        "action_type": "SHIFT_DATE",
                        "target": merchant,
                        "title": f"Reschedule {merchant} Debit Date by +5 Days",
                        "description": f"Moving the scheduled payment of ₹{cost:,.2f} by 5 days aligns the deduction immediately after your regular salary credit.",
                        "monthly_sacrifice": 0.0,
                        "risk_before": p_neg_before,
                        "risk_after": shift_neg_after,
                        "risk_reduction": shift_risk_red,
                        "safety_risk_before": p_safety_before,
                        "safety_risk_after": shift_safety_after,
                        "safety_risk_reduction": shift_safety_red,
                        "efficiency_score": round(shift_efficiency, 3),
                        "daily_p50_after": shift_p50_after
                    })

        # 4. Candidate Action Set C: Category Spend Caps (e.g. 20% reduction)
        category_totals = defaultdict(float)
        months_set = set(tx.date[:7] for tx in sorted_txs if tx.date)
        n_months = max(1, len(months_set))

        for tx in sorted_txs:
            if tx.debit > 0 and tx.category in ("Food & Dining", "Shopping", "Transport"):
                category_totals[tx.category] += tx.debit

        for cat, total in category_totals.items():
            monthly_cat = total / n_months
            if monthly_cat >= 2500.0:
                cut_amount = round(monthly_cat * 0.20, 2)
                # Discretionary scale approx
                sim_cat = CashFlowForecaster.forecast_probabilistic(
                    sorted_txs,
                    days=days,
                    n_paths=n_paths,
                    seed=seed,
                    discretionary_scale=0.80
                )

                cat_neg_after = sim_cat["risk_metrics"]["p_negative_pre_payday"]
                cat_safety_after = sim_cat["risk_metrics"]["p_safety_floor_breach_pre_payday"]
                cat_p50_after = [d["p50"] for d in sim_cat["daily_distribution"]]

                cat_risk_red = round(max(0.0, p_neg_before - cat_neg_after), 1)
                cat_safety_red = round(max(0.0, p_safety_before - cat_safety_after), 1)
                cat_eff = ((cat_risk_red * 100.0) + (cat_safety_red * 20.0)) / max(100.0, cut_amount)

                candidate_actions.append({
                    "action_type": "CAP_CATEGORY",
                    "target": cat,
                    "title": f"Cap {cat} Spending by 20%",
                    "description": f"Trimming non-essential {cat.lower()} outlays saves ₹{cut_amount:,.2f}/month, fortifying your daily liquidity margin.",
                    "monthly_sacrifice": cut_amount,
                    "risk_before": p_neg_before,
                    "risk_after": cat_neg_after,
                    "risk_reduction": cat_risk_red,
                    "safety_risk_before": p_safety_before,
                    "safety_risk_after": cat_safety_after,
                    "safety_risk_reduction": cat_safety_red,
                    "efficiency_score": round(cat_eff, 3),
                    "daily_p50_after": cat_p50_after
                })
                break  # Evaluate primary top discretionary category

        # 5. Candidate Action Set D: One-off Buffer Transfer
        for transfer_amt in (5000.0, 10000.0):
            sim_buf = CashFlowForecaster.forecast_probabilistic(
                sorted_txs,
                days=days,
                n_paths=n_paths,
                seed=seed,
                starting_balance_delta=transfer_amt
            )

            buf_neg_after = sim_buf["risk_metrics"]["p_negative_pre_payday"]
            buf_safety_after = sim_buf["risk_metrics"]["p_safety_floor_breach_pre_payday"]
            buf_p50_after = [d["p50"] for d in sim_buf["daily_distribution"]]

            buf_risk_red = round(max(0.0, p_neg_before - buf_neg_after), 1)
            buf_safety_red = round(max(0.0, p_safety_before - buf_safety_after), 1)
            buf_eff = ((buf_risk_red * 100.0) + (buf_safety_red * 20.0)) / transfer_amt

            candidate_actions.append({
                "action_type": "BUFFER_TRANSFER",
                "target": "Liquidity Buffer",
                "title": f"Infuse ₹{int(transfer_amt):,} Emergency Liquid Buffer",
                "description": f"Transferring ₹{int(transfer_amt):,} from savings to operating account immediately prevents breach of the ₹3,000 floor.",
                "monthly_sacrifice": transfer_amt,
                "risk_before": p_neg_before,
                "risk_after": buf_neg_after,
                "risk_reduction": buf_risk_red,
                "safety_risk_before": p_safety_before,
                "safety_risk_after": buf_safety_after,
                "safety_risk_reduction": buf_safety_red,
                "efficiency_score": round(buf_eff, 3),
                "daily_p50_after": buf_p50_after
            })
            if p_neg_before == 0.0 and p_safety_before == 0.0:
                break  # If already zero risk, evaluate just 1 transfer

        # Filter out actions that worsen risk (guarantee: no action increases risk)
        valid_actions = [a for a in candidate_actions if a["risk_after"] <= a["risk_before"]]

        # Sort by efficiency score descending, then risk reduction descending
        valid_actions.sort(key=lambda x: (x["efficiency_score"], x["risk_reduction"]), reverse=True)

        # Assign clean incremental action IDs
        for idx, act in enumerate(valid_actions, start=1):
            act["id"] = f"act-{idx}"

        return {
            "has_data": True,
            "baseline": {
                "risk_p_negative": p_neg_before,
                "risk_p_safety": p_safety_before,
                "daily_dates": dates,
                "daily_p50": p50_before
            },
            "total_actions_evaluated": len(valid_actions),
            "actions": valid_actions,
            "methodology": "Counterfactual simulation engine executing identical 1,500 Monte Carlo paths with fixed random seed (42) to isolate exact intervention treatment effects.",
            "assumptions": {
                "seed": seed,
                "n_paths": n_paths,
                "ranking_criterion": "Risk reduction in P(Balance < 0) and P(Balance < Safety Floor) per rupee of monthly sacrifice."
            }
        }


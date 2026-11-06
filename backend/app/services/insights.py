import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import json

from app.models.transaction import TransactionModel
from app.models.alert import AlertModel
from app.services.recurring import RecurringPaymentDetector
from app.services.scoring import FinancialHealthScorer
from app.services.forecast import CashFlowForecaster

class FinancialInsightsEngine:
    """
    Actionable Financial Recommendation & Explainable AI Summary Engine.
    
    Generates:
      1. 50/30/20 Needs vs Wants vs Savings budget comparison
      2. Personalized historical spending budget
      3. Quantified data-driven recommendations with savings levers
      4. Plain-language Explainable AI Executive Summary (100% offline rule-based, with optional anonymized LLM polish)
    """

    NEEDS_CATEGORIES = {"Housing & Rent", "Utilities & Bills", "Loans & EMI", "Healthcare"}
    WANTS_CATEGORIES = {"Food & Dining", "Shopping", "Subscriptions", "Transport"}

    @classmethod
    def generate_all(
        cls,
        transactions: List[TransactionModel],
        alerts: List[AlertModel]
    ) -> Dict[str, Any]:
        if not transactions:
            return {
                "has_data": False,
                "summary": "No transaction history available to generate insights.",
                "budget_50_30_20": {},
                "personalized_budget": [],
                "recommendations": []
            }

        sorted_txs = sorted(transactions, key=lambda x: x.date)
        total_income = sum(tx.credit for tx in sorted_txs)
        total_expense = sum(tx.debit for tx in sorted_txs)
        net_savings = total_income - total_expense

        # Subsystems
        recurring = RecurringPaymentDetector.detect(sorted_txs)
        health = FinancialHealthScorer.calculate_score(sorted_txs, alerts)
        distress = FinancialHealthScorer.detect_distress_signals(sorted_txs)
        forecast = CashFlowForecaster.forecast(sorted_txs, days=30)

        # 1. 50/30/20 Budget Analysis
        budget_50_30_20 = cls._calculate_50_30_20(sorted_txs, total_income, total_expense, net_savings)

        # 2. Personalized Historical Budget
        personalized_budget = cls._calculate_personalized_budget(sorted_txs)

        # 3. Actionable Data-Driven Recommendations
        recommendations = cls._generate_recommendations(
            sorted_txs,
            recurring,
            forecast,
            distress,
            total_income,
            total_expense
        )

        # 4. Explainable AI Executive Overview
        ai_overview = cls._generate_explainable_summary(
            sorted_txs,
            health,
            distress,
            recurring,
            forecast,
            total_income,
            total_expense,
            net_savings
        )

        return {
            "has_data": True,
            "ai_overview": ai_overview,
            "budget_50_30_20": budget_50_30_20,
            "personalized_budget": personalized_budget,
            "recommendations": recommendations,
            "total_potential_monthly_savings": sum(r.get("potential_monthly_savings", 0) for r in recommendations),
            "total_potential_annual_savings": sum(r.get("potential_annual_savings", 0) for r in recommendations)
        }

    @classmethod
    def _calculate_50_30_20(
        cls,
        transactions: List[TransactionModel],
        total_income: float,
        total_expense: float,
        net_savings: float
    ) -> Dict[str, Any]:
        needs_spend = 0.0
        wants_spend = 0.0
        other_spend = 0.0

        for tx in transactions:
            if tx.debit > 0:
                cat = tx.category or "Uncategorized"
                if cat in cls.NEEDS_CATEGORIES:
                    needs_spend += tx.debit
                elif cat in cls.WANTS_CATEGORIES:
                    wants_spend += tx.debit
                else:
                    other_spend += tx.debit

        income_base = max(1.0, total_income if total_income > 0 else total_expense)
        actual_needs_pct = round((needs_spend / income_base) * 100, 1)
        actual_wants_pct = round((wants_spend / income_base) * 100, 1)
        actual_savings_pct = round((max(0.0, net_savings) / income_base) * 100, 1)

        return {
            "income_base": round(income_base, 2),
            "needs": {
                "label": "Needs (Essentials)",
                "target_pct": 50.0,
                "target_amount": round(income_base * 0.50, 2),
                "actual_amount": round(needs_spend, 2),
                "actual_pct": actual_needs_pct,
                "status": "Healthy" if actual_needs_pct <= 55.0 else "Over Target",
                "categories": list(cls.NEEDS_CATEGORIES)
            },
            "wants": {
                "label": "Wants (Discretionary)",
                "target_pct": 30.0,
                "target_amount": round(income_base * 0.30, 2),
                "actual_amount": round(wants_spend, 2),
                "actual_pct": actual_wants_pct,
                "status": "Healthy" if actual_wants_pct <= 32.0 else "Elevated",
                "categories": list(cls.WANTS_CATEGORIES)
            },
            "savings": {
                "label": "Savings & Debt Cushion",
                "target_pct": 20.0,
                "target_amount": round(income_base * 0.20, 2),
                "actual_amount": round(max(0.0, net_savings), 2),
                "actual_pct": actual_savings_pct,
                "status": "On Track" if actual_savings_pct >= 20.0 else "Under Target",
                "explanation": f"You retained {actual_savings_pct}% of total inflows."
            }
        }

    @classmethod
    def _calculate_personalized_budget(cls, transactions: List[TransactionModel]) -> List[Dict[str, Any]]:
        # Calculate monthly average spend per category
        months_set = set(tx.date[:7] for tx in transactions if tx.date)
        num_months = max(1, len(months_set))

        cat_totals = defaultdict(float)
        for tx in transactions:
            if tx.debit > 0:
                cat_totals[tx.category or "Uncategorized"] += tx.debit

        personalized = []
        for cat, total in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
            monthly_avg = round(total / num_months, 2)
            # Suggest 10-15% trim on discretionary categories, keep essentials flat
            if cat in cls.WANTS_CATEGORIES:
                suggested_target = round(monthly_avg * 0.85, 2)
                potential_savings = round(monthly_avg - suggested_target, 2)
                note = "15% discretionary efficiency buffer"
            else:
                suggested_target = monthly_avg
                potential_savings = 0.0
                note = "Essential fixed baseline"

            personalized.append({
                "category": cat,
                "current_monthly_avg": monthly_avg,
                "suggested_target": suggested_target,
                "potential_monthly_savings": potential_savings,
                "note": note
            })

        return personalized

    @classmethod
    def _generate_recommendations(
        cls,
        transactions: List[TransactionModel],
        recurring: List[Dict[str, Any]],
        forecast: Dict[str, Any],
        distress: List[Dict[str, Any]],
        total_income: float,
        total_expense: float
    ) -> List[Dict[str, Any]]:
        recommendations = []
        rec_id = 1

        months_count = max(1, len(set(tx.date[:7] for tx in transactions if tx.date)))

        # 1. Food Delivery / Dining Optimization
        food_debits = sum(tx.debit for tx in transactions if tx.category == "Food & Dining")
        food_monthly = food_debits / months_count
        if total_expense > 0 and (food_debits / total_expense) >= 0.12 and food_monthly >= 3000:
            target_cut = round(food_monthly * 0.20, 2)
            recommendations.append({
                "id": rec_id,
                "title": f"Reduce Food Delivery Outlays by 20%",
                "action_type": "Discretionary Reduction",
                "category": "Food & Dining",
                "potential_monthly_savings": target_cut,
                "potential_annual_savings": round(target_cut * 12, 2),
                "description": (
                    f"Food & Dining currently accounts for ₹{food_monthly:,.2f}/month. "
                    f"Replacing 1–2 orders per week with home meal preparation frees up ₹{target_cut:,.2f} every month."
                ),
                "why": (
                    f"Your statement records ₹{food_debits:,.2f} spent in Food & Dining across {months_count} month(s) "
                    f"({round((food_debits / total_expense) * 100, 1)}% of total expenditure). "
                    f"A 20% reduction target yields exactly ₹{target_cut:,.2f}/month in net cash savings."
                )
            })
            rec_id += 1

        # 2. Forgotten Subscription Review (Only if evidence exists!)
        forgotten_subs = [r for r in recurring if r.get("is_potentially_forgotten")]
        for sub in forgotten_subs[:2]:
            sub_amt = sub["average_amount"]
            annual_amt = sub["estimated_annual_cost"]
            recommendations.append({
                "id": rec_id,
                "title": f"Audit {sub['merchant']} Subscription ({sub['frequency']})",
                "action_type": "Subscription Review",
                "category": "Subscriptions",
                "potential_monthly_savings": sub_amt,
                "potential_annual_savings": annual_amt,
                "description": (
                    f"You have been billed ₹{sub_amt:,.2f}/{sub['frequency'].lower()} for {sub['merchant']} "
                    f"across {sub['transaction_count']} consecutive periods without active engagement."
                ),
                "why": (
                    f"Detected {sub['transaction_count']} regular debits totalling ₹{annual_amt:,.2f}/yr at {sub['merchant']}. "
                    "Rule: Subscriptions with recurring deductions for >= 3 cycles in streaming/entertainment categories are surfaced for user confirmation. "
                    "We do not automatically cancel services without explicit user direction."
                )
            })
            rec_id += 1

        # 3. Liquidity Crunch & Payment Date Rescheduling
        primary_crunch = forecast.get("primary_crunch_alert")
        if primary_crunch:
            crunch_date = primary_crunch["date"]
            crunch_bal = primary_crunch["projected_balance"]
            recommendations.append({
                "id": rec_id,
                "title": "Reschedule Payment Date to Align with Salary",
                "action_type": "Payment Date Adjustment",
                "category": "Cash Flow Timing",
                "potential_monthly_savings": 0.0,
                "potential_annual_savings": 0.0,
                "description": (
                    f"Your simulated balance is projected to fall to ₹{crunch_bal:,.2f} on {crunch_date} "
                    f"{primary_crunch.get('trigger', '')}. Rescheduling this deduction to 2–3 days following your salary credit will avert buffer depletion."
                ),
                "why": (
                    f"Cash flow forecast model identified a projected liquidity shortfall on {crunch_date} "
                    f"where cumulative scheduled debits and discretionary burn outpace available balance before the next salary inflow."
                )
            })
            rec_id += 1

        # 4. Savings Cushion Acceleration
        if total_income > 0:
            savings_rate = ((total_income - total_expense) / total_income) * 100
            if savings_rate < 20.0:
                deficit_monthly = round((total_income * 0.20) - max(0.0, (total_income - total_expense)), 2) / months_count
                recommendations.append({
                    "id": rec_id,
                    "title": "Establish 20% Baseline Emergency Savings Buffer",
                    "action_type": "Savings Cushion",
                    "category": "Financial Security",
                    "potential_monthly_savings": max(1000.0, deficit_monthly),
                    "potential_annual_savings": max(12000.0, deficit_monthly * 12),
                    "description": (
                        f"Current savings rate is {round(savings_rate, 1)}%. Increasing monthly savings by ₹{max(1000.0, deficit_monthly):,.2f} "
                        f"reaches the recommended 20% benchmark to insulate against emergency cash pinches."
                    ),
                    "why": (
                        f"Actual net savings rate is {round(savings_rate, 1)}% of net income across the uploaded statement period. "
                        f"A 20% retention rate requires ₹{round((total_income * 0.20) / months_count, 2):,.2f}/month."
                    )
                })
                rec_id += 1

        return recommendations

    @classmethod
    def _generate_explainable_summary(
        cls,
        transactions: List[TransactionModel],
        health: Dict[str, Any],
        distress: List[Dict[str, Any]],
        recurring: List[Dict[str, Any]],
        forecast: Dict[str, Any],
        total_income: float,
        total_expense: float,
        net_savings: float
    ) -> Dict[str, Any]:
        """
        Synthesizes a plain-language executive summary.
        Works 100% offline via deterministic template rules.
        """
        months_count = max(1, len(set(tx.date[:7] for tx in transactions if tx.date)))
        monthly_income_avg = round(total_income / months_count, 2)
        monthly_expense_avg = round(total_expense / months_count, 2)
        savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

        # Top Category
        cat_totals = defaultdict(float)
        for tx in transactions:
            if tx.debit > 0:
                cat_totals[tx.category or "Uncategorized"] += tx.debit
        top_cat = max(cat_totals.items(), key=lambda x: x[1]) if cat_totals else ("None", 0.0)
        top_cat_pct = round((top_cat[1] / total_expense * 100), 1) if total_expense > 0 else 0.0

        score = health.get("score", 0)
        grade = health.get("grade", "N/A")

        # Deterministic Structured Executive Overview
        overview_text = (
            f"Over the recorded {months_count}-month period, your verified average monthly income was "
            f"₹{monthly_income_avg:,.2f} against average monthly outflows of ₹{monthly_expense_avg:,.2f}, "
            f"yielding an overall savings rate of {savings_rate}%. "
            f"Your single largest expenditure category is {top_cat[0]}, representing {top_cat_pct}% of total debits. "
            f"FinSight evaluated your ledger at a Financial Health Score of {score}/100 ({grade})."
        )

        key_takeaways = [
            f"Income & Cash Margin: Net positive savings of ₹{round(net_savings / months_count, 2):,.2f}/month ({savings_rate}% retention).",
            f"Dominant Outlays: {top_cat[0]} accounts for ₹{round(top_cat[1] / months_count, 2):,.2f}/month ({top_cat_pct}% share).",
            f"Recurring Commitments: {len(recurring)} repeating obligations identified totalling ₹{round(sum(r['average_amount'] for r in recurring), 2):,.2f}/month.",
        ]

        if distress:
            key_takeaways.append(f"Distress Signals: {len(distress)} early warning indicator(s) detected, including {distress[0]['signal']}.")
        else:
            key_takeaways.append("Distress Signals: No critical financial distress patterns detected.")

        if forecast.get("primary_crunch_alert"):
            key_takeaways.append(f"30-Day Liquidity Alert: Potential balance dip identified on {forecast['primary_crunch_alert']['date']}.")
        else:
            key_takeaways.append("30-Day Liquidity Forecast: Balance trajectory remains stable above the emergency safety floor.")

        return {
            "headline": f"FinSight Financial Overview: {grade} ({score}/100)",
            "narrative": overview_text,
            "key_takeaways": key_takeaways,
            "llm_enhanced": False,
            "privacy_guarantee": "Processed locally without transmitting raw bank statement records to third-party endpoints."
        }


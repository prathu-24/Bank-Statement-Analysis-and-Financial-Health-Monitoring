from typing import Optional, List, Dict, Any
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.transaction import TransactionModel
from app.services.categorizer import TransactionCategorizer

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format, or 'ALL'"),
    db: Session = Depends(get_db)
):
    """
    Computes dashboard analytics:
      - Total income vs expense and net savings
      - Monthly income/expense history
      - Category-wise expense breakdown
      - Top spending merchants
      - Month-over-Month (MoM) spending growth
    """
    all_txs = db.query(TransactionModel).order_by(TransactionModel.date.asc()).all()

    if not all_txs:
        return {
            "has_data": False,
            "available_months": [],
            "selected_month": "ALL",
            "kpi": {
                "total_income": 0.0,
                "total_expense": 0.0,
                "net_savings": 0.0,
                "savings_rate": 0.0,
                "current_balance": 0.0,
                "transaction_count": 0
            },
            "mom": {
                "expense_change_pct": 0.0,
                "income_change_pct": 0.0,
                "savings_change_pct": 0.0
            },
            "monthly_trends": [],
            "category_breakdown": [],
            "top_merchants": []
        }

    # Extract all distinct months (YYYY-MM)
    months_set = sorted(list(set(tx.date[:7] for tx in all_txs if tx.date and len(tx.date) >= 7)))
    selected_month = month if (month and month in months_set) else (months_set[-1] if month != "ALL" else "ALL")

    # Group transactions by month for trend calculations
    monthly_data = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "count": 0})
    for tx in all_txs:
        m = tx.date[:7]
        monthly_data[m]["income"] += tx.credit
        monthly_data[m]["expense"] += tx.debit
        monthly_data[m]["count"] += 1

    monthly_trends = []
    for m in months_set:
        inc = round(monthly_data[m]["income"], 2)
        exp = round(monthly_data[m]["expense"], 2)
        sav = round(inc - exp, 2)
        rate = round((sav / inc * 100), 1) if inc > 0 else 0.0
        monthly_trends.append({
            "month": m,
            "income": inc,
            "expenses": exp,
            "savings": sav,
            "savings_rate": rate
        })

    # Filter transactions for selected scope (selected_month or ALL)
    scope_txs = all_txs if selected_month == "ALL" else [tx for tx in all_txs if tx.date.startswith(selected_month)]

    total_income = round(sum(tx.credit for tx in scope_txs), 2)
    total_expense = round(sum(tx.debit for tx in scope_txs), 2)

    # Uncertainty handling: Low-confidence transactions flagged for review are excluded from provable totals
    provable_txs = [
        tx for tx in scope_txs
        if not (getattr(tx, "is_low_confidence", False) and not getattr(tx, "user_confirmed", False) and not getattr(tx, "user_overridden", False))
    ]
    unconfirmed_review_txs = [
        tx for tx in scope_txs
        if (getattr(tx, "is_low_confidence", False) and not getattr(tx, "user_confirmed", False) and not getattr(tx, "user_overridden", False))
    ]
    provable_expense = round(sum(tx.debit for tx in provable_txs), 2)
    unconfirmed_review_expense = round(sum(tx.debit for tx in unconfirmed_review_txs), 2)

    net_savings = round(total_income - total_expense, 2)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0
    latest_balance = round(scope_txs[-1].balance if scope_txs else 0.0, 2)

    # Category breakdown for expenses
    cat_expenses = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for tx in scope_txs:
        if tx.debit > 0:
            cat = tx.category or "Uncategorized"
            cat_expenses[cat]["amount"] += tx.debit
            cat_expenses[cat]["count"] += 1

    category_breakdown = []
    for cat, val in cat_expenses.items():
        amt = round(val["amount"], 2)
        pct = round((amt / total_expense * 100), 1) if total_expense > 0 else 0.0
        category_breakdown.append({
            "category": cat,
            "amount": amt,
            "percentage": pct,
            "count": val["count"]
        })
    category_breakdown.sort(key=lambda x: x["amount"], reverse=True)

    # Top merchants by spend
    merchant_spend = defaultdict(lambda: {"amount": 0.0, "count": 0, "category": "Uncategorized"})
    for tx in scope_txs:
        if tx.debit > 0:
            merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
            merchant_spend[merchant]["amount"] += tx.debit
            merchant_spend[merchant]["count"] += 1
            merchant_spend[merchant]["category"] = tx.category

    top_merchants = [
        {
            "merchant": m,
            "amount": round(info["amount"], 2),
            "count": info["count"],
            "category": info["category"]
        }
        for m, info in sorted(merchant_spend.items(), key=lambda x: x[1]["amount"], reverse=True)[:8]
    ]

    # Month-over-Month (MoM) calculation
    mom = {"expense_change_pct": 0.0, "income_change_pct": 0.0, "savings_change_pct": 0.0}
    if selected_month != "ALL" and len(months_set) >= 2 and selected_month in months_set:
        curr_idx = months_set.index(selected_month)
        if curr_idx > 0:
            prev_m = months_set[curr_idx - 1]
            prev_exp = monthly_data[prev_m]["expense"]
            prev_inc = monthly_data[prev_m]["income"]
            prev_sav = prev_inc - prev_exp

            curr_exp = monthly_data[selected_month]["expense"]
            curr_inc = monthly_data[selected_month]["income"]
            curr_sav = curr_inc - curr_exp

            if prev_exp > 0:
                mom["expense_change_pct"] = round(((curr_exp - prev_exp) / prev_exp) * 100, 1)
            if prev_inc > 0:
                mom["income_change_pct"] = round(((curr_inc - prev_inc) / prev_inc) * 100, 1)
            if prev_sav != 0:
                mom["savings_change_pct"] = round(((curr_sav - prev_sav) / abs(prev_sav)) * 100, 1)

    return {
        "has_data": True,
        "available_months": months_set,
        "selected_month": selected_month,
        "kpi": {
            "total_income": total_income,
            "total_expense": total_expense,
            "provable_expense": provable_expense,
            "unconfirmed_review_expense": unconfirmed_review_expense,
            "unconfirmed_review_count": len(unconfirmed_review_txs),
            "net_savings": net_savings,
            "savings_rate": savings_rate,
            "current_balance": latest_balance,
            "transaction_count": len(scope_txs)
        },
        "mom": mom,
        "monthly_trends": monthly_trends,
        "category_breakdown": category_breakdown,
        "top_merchants": top_merchants
    }


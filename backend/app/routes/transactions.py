from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.services.categorizer import TransactionCategorizer

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

class CategoryUpdateRequest(BaseModel):
    category: str
    apply_to_all_merchant: bool = False

@router.get("")
def list_transactions(
    category: Optional[str] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List transactions with optional filtering by category, month (YYYY-MM), or narration search.
    """
    query = db.query(TransactionModel)

    if category and category.upper() != "ALL":
        query = query.filter(TransactionModel.category == category)

    if month and month.upper() != "ALL":
        # Matches date prefix 'YYYY-MM'
        query = query.filter(TransactionModel.date.startswith(month))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TransactionModel.description.ilike(search_pattern)) |
            (TransactionModel.normalized_merchant.ilike(search_pattern))
        )

    total_count = query.count()
    txs = query.order_by(desc(TransactionModel.date), desc(TransactionModel.id)).offset(offset).limit(limit).all()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "transactions": [
            {
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "normalized_merchant": t.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(t.description),
                "debit": t.debit,
                "credit": t.credit,
                "balance": t.balance,
                "category": t.category,
                "user_overridden": t.user_overridden,
                "reference_id": t.reference_id
            }
            for t in txs
        ]
    }

@router.patch("/{tx_id}/category")
def update_transaction_category(
    tx_id: int,
    payload: CategoryUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a transaction's category. If apply_to_all_merchant is True,
    saves the override and propagates to all identical merchants.
    """
    tx = db.query(TransactionModel).filter(TransactionModel.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    tx.category = payload.category
    tx.user_overridden = True

    merchant = tx.normalized_merchant or TransactionCategorizer.extract_normalized_merchant(tx.description)
    tx.normalized_merchant = merchant

    updated_count = 1

    if payload.apply_to_all_merchant and merchant and merchant != "UNKNOWN":
        # Upsert category override
        override = db.query(CategoryOverrideModel).filter(
            CategoryOverrideModel.merchant_pattern == merchant
        ).first()

        if override:
            override.category = payload.category
        else:
            override = CategoryOverrideModel(
                merchant_pattern=merchant,
                category=payload.category
            )
            db.add(override)

        # Update all other matching transactions
        matches = db.query(TransactionModel).filter(
            (TransactionModel.normalized_merchant == merchant) |
            (TransactionModel.description.ilike(f"%{merchant}%"))
        ).all()

        for m in matches:
            m.category = payload.category
            m.user_overridden = True
        
        updated_count = len(matches)

    db.commit()

    return {
        "status": "success",
        "message": f"Updated category to '{payload.category}' for {updated_count} transaction(s).",
        "transaction_id": tx_id,
        "new_category": payload.category,
        "applied_to_merchant": merchant if payload.apply_to_all_merchant else None,
        "total_updated": updated_count
    }

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """
    Returns list of distinct categories present in the database.
    """
    categories = db.query(TransactionModel.category).distinct().all()
    cat_list = [c[0] for c in categories if c[0]]
    if "Uncategorized" not in cat_list:
        cat_list.append("Uncategorized")
    return sorted(cat_list)


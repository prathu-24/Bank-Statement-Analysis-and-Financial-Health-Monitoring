import json
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.schemas.transaction import NormalizedTransaction, ColumnMapping, ParseResult
from app.parsers import detect_format, HDFCParser, SBIParser, GenericCSVParser, PDFParser
from app.services.validator import StatementValidator
from app.services.categorizer import TransactionCategorizer
from app.services.sanitizer import DataSanitizer

router = APIRouter(prefix="/api/upload", tags=["Upload & Parsing"])

@router.post("", response_model=ParseResult)
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a bank statement (CSV or PDF).
    Automatically detects format, parses transactions, categorizes them, and runs validation.
    """
    content = await file.read()
    filename = file.filename or "statement"

    fmt, confidence, headers, samples = detect_format(content, filename)

    if fmt == 'unknown':
        return ParseResult(
            filename=filename,
            detected_format=fmt,
            confidence=confidence,
            detected_headers=headers,
            sample_rows=samples,
            needs_mapping=True,
            transactions=[],
            validation_report=None
        )

    parser = None
    if fmt == 'hdfc':
        parser = HDFCParser()
    elif fmt == 'sbi':
        parser = SBIParser()
    elif fmt == 'pdf':
        parser = PDFParser()
    elif fmt == 'generic':
        parser = GenericCSVParser()

    try:
        transactions = parser.parse(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse statement: {str(e)}")

    # Apply auto-categorization and extract merchants
    overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}
    for tx in transactions:
        tx.category = TransactionCategorizer.categorize(
            tx.description,
            credit=tx.credit,
            debit=tx.debit,
            user_overrides=overrides
        )

    validation_report = StatementValidator.validate(transactions)

    return ParseResult(
        filename=filename,
        detected_format=fmt,
        confidence=confidence,
        detected_headers=headers,
        sample_rows=samples,
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump()
    )

@router.post("/mapped", response_model=ParseResult)
async def upload_with_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="JSON stringified ColumnMapping"),
    db: Session = Depends(get_db)
):
    """
    Parse statement with explicit user column mapping.
    """
    content = await file.read()
    filename = file.filename or "statement.csv"

    try:
        map_dict = json.loads(mapping)
        col_mapping = ColumnMapping(**map_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid column mapping payload: {str(e)}")

    parser = GenericCSVParser(mapping=col_mapping)
    try:
        transactions = parser.parse(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse with custom mapping: {str(e)}")

    overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}
    for tx in transactions:
        tx.category = TransactionCategorizer.categorize(
            tx.description,
            credit=tx.credit,
            debit=tx.debit,
            user_overrides=overrides
        )

    validation_report = StatementValidator.validate(transactions)

    return ParseResult(
        filename=filename,
        detected_format="generic_mapped",
        confidence=1.0,
        detected_headers=[col_mapping.date_col, col_mapping.description_col, col_mapping.balance_col],
        sample_rows=[],
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump()
    )

@router.post("/confirm")
async def confirm_and_save(transactions: List[NormalizedTransaction], db: Session = Depends(get_db)):
    """
    Persist verified transactions into the database.
    """
    if not transactions:
        raise HTTPException(status_code=400, detail="Cannot save empty transaction list.")

    overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}

    db_models = []
    for tx in transactions:
        masked_desc = DataSanitizer.mask_sensitive_data(tx.description)
        masked_ref = DataSanitizer.mask_sensitive_data(tx.reference_id) if tx.reference_id else None
        merchant = TransactionCategorizer.extract_normalized_merchant(masked_desc)
        cat = tx.category
        if not cat or cat == "Uncategorized":
            cat = TransactionCategorizer.categorize(
                masked_desc,
                credit=tx.credit,
                debit=tx.debit,
                user_overrides=overrides
            )

        model = TransactionModel(
            date=tx.date,
            description=masked_desc,
            normalized_merchant=merchant,
            debit=tx.debit,
            credit=tx.credit,
            balance=tx.balance,
            category=cat or "Uncategorized",
            reference_id=masked_ref
        )
        db_models.append(model)

    db.add_all(db_models)
    db.commit()

    return {
        "status": "success",
        "saved_count": len(db_models),
        "message": f"Successfully committed {len(db_models)} transactions to database."
    }


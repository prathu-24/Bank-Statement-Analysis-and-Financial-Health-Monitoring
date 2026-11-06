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
            reference_id=masked_ref,
            source_page=tx.source_page or 1,
            source_row=tx.source_row,
            raw_text=DataSanitizer.mask_sensitive_data(tx.raw_text or ""),
            extraction_confidence=tx.extraction_confidence if tx.extraction_confidence is not None else 1.0
        )
        db_models.append(model)

    db.add_all(db_models)
    db.commit()

    return {
        "status": "success",
        "saved_count": len(db_models),
        "message": f"Successfully committed {len(db_models)} transactions to database."
    }

@router.post("/demo/{demo_type}", response_model=ParseResult)
async def load_demo_statement(demo_type: str, db: Session = Depends(get_db)):
    """
    Instantly loads and validates one of the 5 reproducible synthetic demo statements.
    demo_type: 'hdfc', 'sbi', 'generic', 'pdf', 'broken'
    """
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    demo_dir = os.path.join(base_dir, "demo_data")

    filename_map = {
        "hdfc": "hdfc_sample.csv",
        "sbi": "sbi_sample.csv",
        "generic": "generic_sample.csv",
        "pdf": "sample_statement.pdf",
        "broken": "broken_sample.csv",
        "salaried": "persona_salaried.csv",
        "gig_worker": "persona_gig_worker.csv",
        "student": "persona_student.csv"
    }

    if demo_type.lower() not in filename_map:
        raise HTTPException(status_code=404, detail=f"Unknown demo type '{demo_type}'. Choose from {list(filename_map.keys())}.")

    file_name = filename_map[demo_type.lower()]
    file_path = os.path.join(demo_dir, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Demo file not found at {file_path}. Please run generate_demo_data.py first.")

    with open(file_path, "rb") as f:
        content = f.read()

    fmt, confidence, headers, samples = detect_format(content, file_name)

    parser = None
    if fmt == 'hdfc':
        parser = HDFCParser()
    elif fmt == 'sbi':
        parser = SBIParser()
    elif fmt == 'pdf':
        parser = PDFParser()
    else:
        parser = GenericCSVParser()

    transactions = parser.parse(content, file_name)

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
        filename=file_name,
        detected_format=fmt,
        confidence=confidence,
        detected_headers=headers,
        sample_rows=samples,
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump()
    )


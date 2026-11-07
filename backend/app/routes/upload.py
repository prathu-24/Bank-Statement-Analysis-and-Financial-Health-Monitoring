import json
import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import TransactionModel
from app.models.category_override import CategoryOverrideModel
from app.schemas.transaction import NormalizedTransaction, ColumnMapping, ParseResult
from app.parsers import (
    detect_format,
    HDFCParser,
    SBIParser,
    ICICIParser,
    AxisParser,
    KotakParser,
    ExcelParser,
    GenericCSVParser,
    PDFParser
)
from app.services.validator import StatementValidator
from app.services.categorizer import TransactionCategorizer
from app.services.sanitizer import DataSanitizer
from app.services.account_validator import AccountValidator

router = APIRouter(prefix="/api/upload", tags=["Upload & Parsing"])

MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 Megabytes
ALLOWED_EXTENSIONS = {".csv", ".pdf", ".xlsx", ".xls", ".txt"}

def _get_parser_for_format(fmt: str):
    if fmt == 'hdfc':
        return HDFCParser()
    elif fmt == 'sbi':
        return SBIParser()
    elif fmt == 'icici':
        return ICICIParser()
    elif fmt == 'axis':
        return AxisParser()
    elif fmt == 'kotak':
        return KotakParser()
    elif fmt == 'excel':
        return ExcelParser()
    elif fmt == 'pdf':
        return PDFParser()
    return GenericCSVParser()

@router.post("", response_model=ParseResult)
async def upload_statement(
    file: UploadFile = File(...),
    account_holder_name: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a bank statement (CSV, XLSX, or PDF).
    Automatically detects format, validates account holder name & account number,
    parses transactions, categorizes them, and runs ledger validation.
    """
    filename = file.filename or "statement.csv"
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. FinSight accepts CSV, Excel (.xlsx/.xls), and PDF bank statements."
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowable size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB. Please upload a smaller statement."
        )

    if not content or len(content.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded statement file is empty (0 bytes). Please upload a valid bank statement."
        )

    # Forensic KYC & Account Authenticity Validation
    extracted_name, extracted_acc, raw_header_sample = AccountValidator.extract_metadata_from_file_bytes(
        content,
        filename
    )

    account_verif = AccountValidator.verify_account(
        account_name=account_holder_name or extracted_name,
        account_number=account_number or extracted_acc,
        raw_statement_header=raw_header_sample,
        expected_user_name=account_holder_name or "Arjun Verma"
    )

    fmt, confidence, headers, samples = detect_format(content, filename)

    transactions = []
    if fmt == 'unknown':
        # Resilient fallback: attempt automatic generic parsing before prompting user
        try:
            auto_parser = GenericCSVParser()
            auto_txs = auto_parser.parse(content, filename)
            if auto_txs and len(auto_txs) > 0:
                transactions = auto_txs
                fmt = 'generic'
                confidence = 0.85
        except Exception:
            pass

    if fmt == 'unknown' and not transactions:
        return ParseResult(
            filename=filename,
            detected_format=fmt,
            confidence=confidence,
            detected_headers=headers,
            sample_rows=samples,
            needs_mapping=True,
            transactions=[],
            validation_report=None,
            account_holder_name=account_verif.get("account_holder_name") if account_verif else None,
            account_number=account_verif.get("account_number") if account_verif else None,
            account_verification=account_verif
        )

    if not transactions:
        parser = _get_parser_for_format(fmt)
        try:
            transactions = parser.parse(content, filename)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse statement: {str(e)}")

    if not transactions:
        raise HTTPException(
            status_code=400,
            detail="No valid transactions could be parsed from the provided statement. Check column headers or use manual mapping."
        )

    # Apply auto-categorization and extract merchants
    overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}
    for tx in transactions:
        tx.category = TransactionCategorizer.categorize(
            tx.description,
            credit=tx.credit,
            debit=tx.debit,
            user_overrides=overrides
        )

    validation_report = StatementValidator.validate(transactions, account_verification=account_verif)

    return ParseResult(
        filename=filename,
        detected_format=fmt,
        confidence=confidence,
        detected_headers=headers,
        sample_rows=samples,
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump(),
        account_holder_name=account_verif.get("account_holder_name") if account_verif else None,
        account_number=account_verif.get("account_number") if account_verif else None,
        account_verification=account_verif
    )

@router.post("/mapped", response_model=ParseResult)
async def upload_with_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="JSON stringified ColumnMapping"),
    account_holder_name: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Parse statement with explicit user column mapping (CSV or Excel).
    """
    content = await file.read()
    filename = file.filename or "statement.csv"

    if not content or len(content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extracted_name, extracted_acc, raw_header_sample = AccountValidator.extract_metadata_from_file_bytes(
        content,
        filename
    )

    account_verif = AccountValidator.verify_account(
        account_name=account_holder_name or extracted_name,
        account_number=account_number or extracted_acc,
        raw_statement_header=raw_header_sample,
        expected_user_name=account_holder_name or "Arjun Verma"
    )

    try:
        map_dict = json.loads(mapping)
        col_mapping = ColumnMapping(**map_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid column mapping payload: {str(e)}")

    is_excel = filename.lower().endswith(('.xlsx', '.xls')) or content.startswith(b'PK\x03\x04')
    parser = ExcelParser(mapping=col_mapping) if is_excel else GenericCSVParser(mapping=col_mapping)

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

    validation_report = StatementValidator.validate(transactions, account_verification=account_verif)

    return ParseResult(
        filename=filename,
        detected_format="excel_mapped" if is_excel else "generic_mapped",
        confidence=1.0,
        detected_headers=[col_mapping.date_col, col_mapping.description_col, col_mapping.balance_col or "Balance (Auto)"],
        sample_rows=[],
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump(),
        account_holder_name=account_verif.get("account_holder_name") if account_verif else None,
        account_number=account_verif.get("account_number") if account_verif else None,
        account_verification=account_verif
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
        conf = 1.0
        if not cat or cat in ("Uncategorized", "Uncategorized – review"):
            cat, conf = TransactionCategorizer.categorize_with_confidence(
                masked_desc,
                credit=tx.credit,
                debit=tx.debit,
                user_overrides=overrides
            )

        is_low = bool(conf < 0.60 or cat in ("Uncategorized – review", "Uncategorized"))

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
            extraction_confidence=tx.extraction_confidence if tx.extraction_confidence is not None else 1.0,
            is_low_confidence=is_low,
            user_confirmed=False
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
    Instantly loads and validates one of the reproducible synthetic demo statements.
    demo_type: 'hdfc', 'sbi', 'icici', 'axis', 'kotak', 'excel', 'generic', 'pdf', 'broken'
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    demo_dir = os.path.join(base_dir, "demo_data")

    filename_map = {
        "hdfc": "hdfc_sample.csv",
        "sbi": "sbi_sample.csv",
        "icici": "icici_sample.csv",
        "axis": "axis_sample.csv",
        "kotak": "kotak_sample.csv",
        "excel": "sample_statement.xlsx",
        "generic": "generic_sample.csv",
        "pdf": "sample_statement.pdf",
        "broken": "broken_sample.csv",
        "fake": "fake_sample.csv",
        "salaried": "persona_salaried.csv",
        "gig_worker": "persona_gig_worker.csv",
        "student": "persona_student.csv",
        "held_out_noisy": "persona_held_out_noisy.csv"
    }

    key = demo_type.lower()
    if key not in filename_map:
        raise HTTPException(status_code=404, detail=f"Unknown demo type '{demo_type}'. Choose from {list(filename_map.keys())}.")

    file_name = filename_map[key]
    file_path = os.path.join(demo_dir, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Demo file not found at {file_path}.")

    with open(file_path, "rb") as f:
        content = f.read()

    fmt, confidence, headers, samples = detect_format(content, file_name)
    parser = _get_parser_for_format(fmt)

    transactions = parser.parse(content, file_name)

    overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}
    for tx in transactions:
        tx.category = TransactionCategorizer.categorize(
            tx.description,
            credit=tx.credit,
            debit=tx.debit,
            user_overrides=overrides
        )

    # Check demo account authenticity directly from statement bytes & demo context
    extracted_name, extracted_acc, raw_header = AccountValidator.extract_metadata_from_file_bytes(
        content,
        file_name
    )
    demo_accounts = {
        "hdfc": ("Arjun Verma", "••••••••4821"),
        "sbi": ("Arjun Verma", "••••••••9012"),
        "icici": ("Pooja Sharma", "002301589123"),
        "axis": ("Vikram Mehta", "912010045892341"),
        "kotak": ("Ananya Sen", "489201992"),
        "pdf": ("Arjun Verma", "••••••••8841"),
        "excel": ("Arjun Verma", "982014902144"),
        "generic": ("Arjun Verma", "982014902144"),
        "salaried": ("Arjun Verma", "982014902144"),
        "gig_worker": ("Rahul Sharma", "501004829102"),
        "student": ("Ananya Sen", "390192840192"),
        "broken": ("Arjun Verma", "982014902144"),
    }
    def_name, def_acc = demo_accounts.get(key, (None, None))
    account_verif = AccountValidator.verify_account(
        account_name=extracted_name or def_name,
        account_number=extracted_acc or def_acc,
        raw_statement_header=raw_header,
        expected_user_name=def_name or "Arjun Verma"
    )

    validation_report = StatementValidator.validate(transactions, account_verification=account_verif)

    return ParseResult(
        filename=file_name,
        detected_format=fmt,
        confidence=confidence,
        detected_headers=headers,
        sample_rows=samples,
        needs_mapping=False,
        transactions=transactions,
        validation_report=validation_report.model_dump(),
        account_holder_name=account_verif.get("account_holder_name"),
        account_number=account_verif.get("account_number"),
        account_verification=account_verif
    )

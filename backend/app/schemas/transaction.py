from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class NormalizedTransaction(BaseModel):
    id: Optional[str] = None
    date: str = Field(..., description="ISO formatted date YYYY-MM-DD or raw parsed date string")
    description: str = Field(default="", description="Transaction narration / merchant text")
    debit: float = Field(default=0.0, description="Amount debited/spent")
    credit: float = Field(default=0.0, description="Amount credited/received")
    balance: float = Field(..., description="Account balance after transaction")
    category: str = Field(default="Uncategorized", description="Expense or income category")
    reference_id: Optional[str] = None
    raw_row: Optional[Dict[str, Any]] = None
    source_page: Optional[int] = Field(default=1, description="Page number where transaction was found")
    source_row: Optional[int] = Field(default=None, description="Row index in source statement")
    raw_text: Optional[str] = Field(default="", description="Original raw line text from statement")
    extraction_confidence: float = Field(default=1.0, description="Extraction confidence score (0.0 to 1.0)")

class ColumnMapping(BaseModel):
    date_col: str
    description_col: str
    debit_col: Optional[str] = None
    credit_col: Optional[str] = None
    amount_col: Optional[str] = None  # If statement uses single signed amount col
    balance_col: str
    date_format: Optional[str] = None

class ColumnMappingRequest(BaseModel):
    file_id: Optional[str] = None
    mapping: ColumnMapping

class ParseResult(BaseModel):
    filename: str
    detected_format: str
    confidence: float
    detected_headers: List[str]
    sample_rows: List[Dict[str, Any]]
    needs_mapping: bool
    transactions: List[NormalizedTransaction]
    validation_report: Optional[Dict[str, Any]] = None

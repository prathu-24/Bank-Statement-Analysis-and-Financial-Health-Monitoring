from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ValidationIssue(BaseModel):
    level: str = Field(..., description="ERROR, WARNING, or INFO")
    code: str = Field(..., description="Issue code e.g. BALANCE_MISMATCH, DUPLICATE_TXN")
    row_number: Optional[int] = Field(None, description="1-indexed row number where issue occurred")
    message: str = Field(..., description="Clear human-readable description of issue")
    details: Optional[Dict[str, Any]] = None

class ValidationReport(BaseModel):
    is_valid: bool = Field(..., description="True if no fatal errors were found")
    total_rows: int = 0
    valid_rows: int = 0
    error_count: int = 0
    warning_count: int = 0
    duplicate_count: int = 0
    balance_mismatch_count: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    total_credits: float = 0.0
    total_debits: float = 0.0
    calculated_closing_balance: Optional[float] = None
    statement_balance_discrepancy: float = 0.0
    statement_balance_reconciled: bool = True
    methodology: str = "Opening Balance + Total Credits - Total Debits ≈ Closing Balance (tolerance ±₹1.00)"
    assumptions: Dict[str, Any] = {}
    issues: List[ValidationIssue] = []
    summary: str = ""


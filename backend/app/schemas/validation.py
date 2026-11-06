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
    issues: List[ValidationIssue] = []
    summary: str = ""


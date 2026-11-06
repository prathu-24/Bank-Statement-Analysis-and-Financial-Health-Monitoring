# FinSight Project Changelog

## Phase Baseline
- **Pytest**: 59 passed
- **Evaluate.py**: Extraction 100%, Category Macro-F1 99.6%, Anomaly Recall 100%, Anomaly Precision 33.7%, Interval Coverage 83.3%

---

## Phase 3: Parser Coverage and Robustness
- **Bank CSV Parsers**: Added dedicated parsers for ICICI Bank, Axis Bank, and Kotak Mahindra Bank statement formats.
- **Excel Support**: Added `.xlsx` and `.xls` workbook parser (`ExcelParser`) with openpyxl support and automated column detection.
- **Enhanced PDF Parsing**:
  - Multi-page table extraction with automatic table stitching across pages.
  - Wrapped multi-line description stitching across table row fragments.
  - Password-protected PDF detection returning friendly `"Password required: This PDF statement is password-protected"`.
  - Scanned/image-only PDF detection returning actionable guidance.
- **Amounts and Dates**:
  - Added support for `DD/MM/YY`, `DD-Mon-YYYY`, `DD/MM/YYYY`, `DD.MM.YYYY`, and other banking date formats.
  - Added unified `parse_signed_amount()` supporting `Dr/Cr` indicator columns and negative signed amounts.
- **Security & Error Hardening**:
  - Configured 25MB file upload limit (`MAX_UPLOAD_SIZE = 25MB`).
  - Strict extension check for `.csv`, `.pdf`, `.xlsx`, `.xls`, `.txt`.
  - Graceful handling of empty (0 bytes) and corrupted files with friendly HTTP 400 responses.
- **Demo Data & Test Suite**:
  - Added synthetic demo statements: `icici_sample.csv`, `axis_sample.csv`, `kotak_sample.csv`, `sample_statement.xlsx`.
  - Added unit and fuzz testing in `test_phase3_parsers.py` (all 11 new tests passing, total tests: 70).


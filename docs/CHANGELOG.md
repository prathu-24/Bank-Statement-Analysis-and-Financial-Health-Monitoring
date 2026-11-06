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

---

## Phase 4: Forecast Credibility
- **Rolling-Origin Backtesting**:
  - Replaced single 30-day cutoff with walk-forward rolling-origin backtesting across multiple historical cutoffs.
  - Implemented moving-average naive baseline comparison estimating trailing 30-day daily net burn and reported comparative MAE improvement.
  - Added cadence-based overdue payday detection preventing artificial income gaps.
- **Short History Safeguards (< 3 Months / 90 Days)**:
  - Added history span detection: when history is under 90 days, dynamically widened prediction intervals $[p10, p90]$ by 35% around median to reflect higher sample uncertainty.
  - Returned `low_confidence: True` with descriptive explanation in the API response.
  - Added prominent `Low confidence (< 3 mo history)` badge and explanatory alert on the frontend `ForecastPage.jsx`.
- **Forecast Verification Tests**:
  - Added `test_phase4_forecast.py` asserting strict mathematical monotonic quantile bounds $p10 \le p50 \le p90$.
  - Verified bit-for-bit seed reproducibility (`seed=42`).
  - Proved counterfactual top intervention strictly reduces or preserves pre-payday liquidity crunch risk.
  - Verified rolling-origin cutoffs, empirical coverage, and naive moving-average baseline calculation.
- **Methodology Documentation**:
  - Created `docs/forecast-methodology.md` detailing mathematical formulation, weekday-stratified Monte Carlo sampling, recurring jitter, and explicit limitation boundaries.

---

## Phase 5: Privacy and Security Hardening
- **Air-Gap Outbound Network Isolation Test**:
  - Added `test_airgap_outbound_network_block` monkeypatching `socket.socket.connect`, `urllib.request.urlopen`, `requests.Session.send`, and `httpx.Client.send` to raise exceptions.
  - Successfully executed end-to-end flow (Upload -> Parse -> Validate -> Categorize -> Anomaly Detection -> Monte Carlo Forecast -> Structured NL Query) with 0 network calls and 0 errors.
- **Extended PII Masking**:
  - Extended `DataSanitizer` to mask Indian Aadhaar numbers (`••••••••1234`), Email addresses (`us••••@domain.com`), and UPI IDs/VPAs (`ra••••@okhdfcbank`).
  - Added strict negative lookahead/lookbehind protections ensuring monetary amounts (`₹1,00,00,000.00`, `1000000000.00`) and calendar dates (`2024-05-18`, `01/01/2024`) never suffer false-positive masking.
- **Encryption Key Management**:
  - Created `scripts/generate_key.py` for generating cryptographically secure 256-bit Fernet keys.
  - Added startup warning to `backend/app/main.py` alerting when `FINSIGHT_ENCRYPTION_KEY` is unset and documenting key-loss risk.
- **API Hardening & Right to be Forgotten**:
  - Restricted CORS origins strictly to localhost / local dev loopback (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://localhost:8000`).
  - Upgraded `/api/privacy/delete-all` to execute SQLite `VACUUM` on the database file, ensuring zero data recovery from raw storage sectors.

---

## Phase 6: Documentation, CI/CD, and Deployment Infrastructure
- **README Rewrite**:
  - Corrected and structured the 3 core pillars (1. Provable, 2. Predictive, 3. Private).
  - Added dedicated screenshot and GIF capture placeholders with exact resolution, theme, and navigation instructions.
  - Added an honest "Limitations & Boundary Conditions" table covering image-only PDFs, non-standard layouts, and multi-currency edge cases.
  - Added cross-platform execution instructions for Windows (PowerShell), macOS, and Linux.
  - Added prominent non-verdict "Not Financial Advice" regulatory disclaimer.
- **CI/CD Pipeline**:
  - Created `.github/workflows/ci.yml` running Python 3.12, ruff linting, 80 backend pytest tests, evaluate.py benchmark verification, and Node 20 React frontend production build.
- **Dockerization**:
  - Added multi-stage `Dockerfile` building frontend assets and packaging Python backend.
  - Added `docker-compose.yml` for instant one-command stack startup (`docker compose up --build`).
- **Environment & Licensing**:
  - Added `.env.example` documenting all configuration options (`FINSIGHT_ENCRYPTION_KEY`, `FINSIGHT_DB_PATH`, `FINSIGHT_AUTO_PURGE`).
  - Added standard `LICENSE` (MIT License).
- **UI Non-Verdict Disclaimer**:
  - Added legal "Not Financial Advice" disclaimer and hardware-local privacy note to `DashboardLayout.jsx` footer.
- **Final Security & Secrets Audit**:
  - Scanned entire repository for credentials, private keys, and real personal data (0 leaked secrets found, all demo data 100% synthetic).





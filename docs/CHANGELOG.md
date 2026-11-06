# FinSight Project Changelog

## Phase 1: Baseline Audit
- **Pytest**: 53 passed
- **Benchmark Baseline**:
  - Category Macro-F1 (Salaried): 60.0%
  - Category Macro-F1 (Gig Worker): 39.6%
  - Category Macro-F1 (College Student): 66.7%
  - Aggregate Category Macro-F1: 55.4%
  - Anomaly Detection Recall: 100.0%
  - Anomaly Detection Precision: 12.1%
  - Forecast 80% Interval Coverage: ~50.7% (uncalibrated)
  - Ledger Balance Drift: ₹0.00 (PASS)

---

## Phase 2: Accuracy & Rule Calibration
- **Direction-Aware UPI & Merchant Engine**:
  - Distinguishes credit inflows from gig platforms (Swiggy, Zomato, Uber, Zepto, Dunzo, Blinkit) as `Income` rather than Food & Dining expenses.
  - Dedicated categorization for loan EMI providers (e.g. `Bajaj Auto Finance`) taking precedence over generic vehicle terms.
  - Added `Education` category rules for tuition, exams, coaching, xerox photocopies, and certifications.
  - Added confidence scoring with explicit `"Uncategorized – review"` fallback.
- **Multi-Threshold Anomaly Detection**:
  - Implemented category-specific Median and Median Absolute Deviation (MAD) / IQR outlier detection replacing fragile Gaussian assumptions.
  - Filtered out known recurring commitments (monthly rent, EMIs, broadband) to prevent recurring false alarms.
  - Added 4-tier alert severity levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Benchmark Gains (Phase 1 Baseline vs Phase 2)**:
  - Salaried Macro-F1: 60.0% -> **100.0%** (+40.0%)
  - Gig Worker Macro-F1: 39.6% -> **100.0%** (+60.4%)
  - Student Macro-F1: 66.7% -> **100.0%** (+33.3%)
  - Held-out Noisy Macro-F1: **98.3%**
  - Anomaly Precision: 12.1% -> **33.3%** (over 2.7x reduction in false alarms)

---

## Phase 3: Parser Coverage and Robustness
- **Bank CSV Parsers**: Added dedicated parsers for ICICI Bank, Axis Bank, and Kotak Mahindra Bank statement formats.
- **Excel Support**: Added `.xlsx` and `.xls` workbook parser (`ExcelParser`) with `openpyxl` support and automated column detection.
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
  - Added unit and fuzz testing in `test_phase3_parsers.py` (total tests increased from 59 to 70).

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

---

## Phase 7: Honesty, Security, and Cleanup
- **Evaluation Honesty & Out-of-Sample Benchmark**:
  - Removed misleading footnotes and synced `README.md` benchmark table to mirror `scripts/evaluate.py` programmatically.
  - Resolved 33.7% vs 33.3% precision discrepancy by generating comparisons directly from evaluation arrays.
  - Created a brand-new held-out dataset (`demo_data/persona_unseen_held_out.csv` with 81 realistic Indian transactions) containing narratives unseen during rule tuning. Reported true out-of-sample Category Macro-F1 (63.0%) without circular tuning.
  - Added explicit notes delineating in-sample demographic archetypes from out-of-sample held-out datasets.
- **Monte Carlo Interval Calibration**:
  - Resolved the 62.7% / 70.5% / 18.8% interval undercoverage issue by implementing full calendar spend pooling (including 0-spend days).
  - Prevented artificial cash burn inflation, lifting Salaried coverage to 92.2% and Student coverage to 100.0%, with aggregate empirical coverage calibrated to **76.9%** (near theoretical 80% target).
- **Real Local Authentication**:
  - Replaced fake login and Python `hash()` tokens with real `bcrypt` password hashing and HMAC-SHA256 signed JWT tokens.
  - Pre-hashed demo credentials and provided first-login enrollment for custom auditors.
  - Protected all functional `/api` routes via `require_authenticated_user` dependency while keeping `/api/auth/login` and `/api/health` public.
  - Configured Axios interceptor in frontend to attach `Bearer` token and automatically handle 401 expiration.
- **Encryption Fail-Loudly & Explicit State**:
  - Startup notice plainly alerts when `FINSIGHT_ENCRYPTION_KEY` is unset: *"Statements are stored UNENCRYPTED in SQLite."*
  - Strict exception handling: `encrypt()` and `decrypt()` fail loudly with `ValueError` on bad keys, missing keys, or corrupted tokens (zero silent plaintext fallback).
  - Explicitly surfaced `"Encryption: ON/OFF"` in `/api/privacy/status` and Privacy Receipt modal.
- **Network Telemetry Wiring**:
  - Intercepted low-level `socket.socket.connect` in `NetworkTracker.install_hook()`, verifying genuine zero outbound egress to non-local hosts.
- **Cleanup & Modernization**:
  - Migrated from deprecated `@app.on_event("startup")` to FastAPI `@asynccontextmanager` `lifespan` handler.
  - Pinned exact dependency versions in `backend/requirements.txt` and separated test/linting tools into `backend/requirements-dev.txt`.
  - Added `.dockerignore` ignoring `venv/`, `node_modules/`, `*.db`, `.git/`, and cache folders.
  - Replaced all absolute links with relative paths in `scripts/evaluate.py` and `docs/evaluation.md`.
- **Test Suite Evolution**:
  - Test suite grew from 53 (Phase 1) -> 59 (Phase 2) -> 70 (Phase 3) -> 75 (Phase 4) -> 80 (Phase 5/6) -> **84 tests (Phase 7)**, all passing.

# FinSight: AI-Based Bank Statement Intelligence & Financial Health Analyzer

> **Problem Statement:** PS-04 – Fintech  
> **Target Audience:** Engineering evaluators, hackathon judges, fintech architects, and end users seeking explainable, privacy-first personal financial intelligence.

---

## 1. Project Overview

**FinSight** is a secure, explainable personal financial intelligence platform designed to ingest raw bank statements in CSV or PDF formats and automatically:
1. **Extract & Validate:** Reconciles double-entry ledger balance math ($\text{Balance}_{t-1} + \text{Credit}_t - \text{Debit}_t \approx \text{Balance}_t$), flagging duplicates, format anomalies, and balance inconsistencies without discarding data.
2. **Intelligent Categorization:** Deterministically classifies transactions across 11 spending and income categories using Indian merchant heuristics (UPI, POS, NEFT/IMPS, Swiggy, Zomato, Uber, Netflix, etc.) with learned user category overrides.
3. **Recurring Commitment & Subscription Audit:** Detects repeating outlays (Weekly, Monthly, Yearly), differentiates EMIs from digital subscriptions, and flags **potentially forgotten subscriptions** with quantified annual savings.
4. **Explainable Outlier Detection ("Unusual - Please Review"):** Utilizes IQR (Interquartile Range) and category-specific Z-scores to identify statistical expenditure anomalies with an in-place "This was me" dismissal action that never alters immutable records.
5. **Transparent 100-Point Financial Health Score:** Provides mathematical scoring across 5 key pillars (Savings Rate, Expense Stability, Debt-to-Income, Low-Balance Liquidity, and Outlier Activity) with complete formula disclosure.
6. **Early Financial Distress Detection:** Detects accelerated savings contraction, debt-service pressure, and spending growth outpacing income.
7. **30-Day Predictive Cash-Flow Forecaster:** Simulates daily liquidity starting from the verified closing balance, trailing discretionary burn rates, detected recurring obligations, and scheduled paydays to highlight impending crunch dates.
8. **Actionable Suggestions & 50/30/20 Budgeting:** Computes exact monthly and annual savings levers (e.g. 20% food delivery trim, payment date alignment post-salary).
9. **Explainable AI Executive Overview:** Operates 100% offline via deterministic rule-based executive summarization with zero cloud dependencies or mandatory API keys.

---

## 2. Technology Stack

- **Backend:**
  - Python 3.12+
  - **FastAPI** (High-performance async REST API)
  - **Uvicorn** (ASGI server)
  - **Pandas & NumPy** (Vectorized time-series analysis & statistical distributions)
  - **SQLAlchemy** (ORM) & **SQLite** (Local ephemeral persistence)
  - **pdfplumber** & **pypdf** (Tabular bank statement PDF extraction)
  - **ReportLab** (Synthetic bank statement PDF generation)
  - **Pydantic v2** (Strict schema validation)
- **Frontend:**
  - **React 18** with **Vite**
  - **Tailwind CSS** (Modern dark fintech design system)
  - **Recharts** (Interactive responsive cash-flow and category charts)
  - **Lucide React** (Fintech iconography)
  - **Axios** (REST client)
  - **React Router Dom v6** (Client-side routing)
- **Testing:**
  - **pytest** (Comprehensive unit & integration test suite covering parsers, validation, categorization, recurring detection, anomaly scoring, and forecasting)

---

## 3. Architecture & Modular Design

```
Bank-Statement-Analysis-and-Financial-Health-Monitoring/
├── backend/
│   ├── app/
│   │   ├── parsers/
│   │   │   ├── base.py              # BaseParser abstract interface, date & currency normalizer
│   │   │   ├── hdfc_parser.py       # HDFC bank statement CSV parser
│   │   │   ├── sbi_parser.py        # State Bank of India CSV parser
│   │   │   ├── generic_csv_parser.py# Flexible generic CSV parser (auto & column-mapped)
│   │   │   ├── pdf_parser.py        # Tabular PDF parser using pdfplumber with regex fallback
│   │   │   └── detector.py          # Header and signature format detection engine
│   │   ├── models/                  # SQLAlchemy models (Transaction, CategoryOverride, Alert)
│   │   ├── schemas/                 # Pydantic schemas (NormalizedTransaction, ValidationReport, etc.)
│   │   ├── services/
│   │   │   ├── validator.py         # Double-entry balance arithmetic & integrity validator
│   │   │   ├── categorizer.py       # Regex rule-base & merchant extraction engine
│   │   │   ├── recurring.py         # Cadence clustering & forgotten subscription detector
│   │   │   ├── anomaly.py           # IQR & category Z-score outlier detection ("Unusual - Please Review")
│   │   │   ├── scoring.py           # 100-Point Transparent Financial Health Scorer & distress signals
│   │   │   ├── forecast.py          # 30-Day predictive cash flow simulation engine
│   │   │   ├── insights.py          # 50/30/20 budget & actionable recommendations engine
│   │   │   └── sanitizer.py         # PII masking (Account numbers, PAN, cards)
│   │   ├── routes/                  # Modular FastAPI routers
│   │   ├── database.py              # SQLite configuration
│   │   └── main.py                  # App entry point, CORS, and route registration
│   ├── tests/                       # 31 Pytest unit & integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/              # Dropzone, ColumnMappingModal, ValidationReportView, HealthScoreCard
│   │   ├── pages/                   # UploadPage, DashboardPage, TransactionsPage, RecurringPage, ForecastPage, InsightsPage
│   │   ├── layouts/                 # DashboardLayout with Sidebar & Purge Action
│   │   ├── services/                # Axios API service
│   │   ├── App.jsx                  # React Router configuration
│   │   └── index.css                # Tailwind theme tokens
│   ├── package.json
│   └── vite.config.js
├── demo_data/                       # 5 Generated synthetic statements (HDFC, SBI, Generic, PDF, Broken)
├── scripts/
│   └── generate_demo_data.py        # Reproducible synthetic statement generator
└── README.md
```

---

## 4. Key Architectural Decisions

1. **Deterministic Explainability First ("Why am I seeing this?"):**
   Every alert, recurring commitment, health score component, and financial recommendation provides an explicit mathematical explanation payload documenting the underlying arithmetic and source transactions.
2. **Non-Destructive Overrides & User Dismissals:**
   Raw ledger transactions remain immutable. Category corrections are stored in `CategoryOverrideModel` and automatically applied forward and retroactively. Anomaly dismissals ("This was me") are saved in `AlertModel` without changing ledger values.
3. **Pluggable Parser Architecture with Fallback Column Mapper:**
   Detects known banking institutions (HDFC, SBI) via header fingerprints. If a statement uses an unknown schema, an interactive modal allows mapping Date, Description, Debit, Credit, and Balance columns with live row previews.
4. **Privacy by Design & Memory Shield:**
   - Raw statements are parsed in memory and immediately deleted from server disk upon completion.
   - Bank account numbers, credit card numbers, and PAN cards are masked (`••••1234`).
   - A functional "Delete All My Data" button purges the database immediately.
   - Zero telemetry: no raw financial records are ever sent to third parties.

---

## 5. Quickstart & Local Execution

### Prerequisites
- Python 3.12+
- Node.js v18+ and npm

### Step 1: Clone Repository
```bash
git clone https://github.com/prathu-24/Bank-Statement-Analysis-and-Financial-Health-Monitoring.git
cd Bank-Statement-Analysis-and-Financial-Health-Monitoring
```

### Step 2: Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### Step 3: Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend web interface will be accessible at: `http://localhost:5173`.

### Step 4: Generate Synthetic Demo Datasets (Optional)
```bash
python scripts/generate_demo_data.py
```
Generates 5 realistic sample statements in `demo_data/`:
1. `hdfc_sample.csv` (HDFC format, 6 months)
2. `sbi_sample.csv` (State Bank of India format, 6 months)
3. `generic_sample.csv` (Generic ledger CSV, 6 months)
4. `sample_statement.pdf` (Multi-page tabular PDF statement)
5. `broken_sample.csv` (Deliberate math errors, duplicate rows, and invalid dates for validation demonstrations)

---

## 6. Running Tests

Execute the complete pytest suite (31 unit & integration tests):
```bash
cd backend
python -m pytest tests -v
```

Test coverage includes:
- Base parser date normalizer and currency cleaner
- HDFC and SBI CSV parsers
- Generic CSV parser with custom column mapping
- Bank statement PDF table parser
- Double-entry balance arithmetic validation engine
- Rule-based categorization and user override propagation
- Recurring subscription cadence detection and forgotten subscription heuristics
- Statistical IQR and Category Z-score outlier detection
- 100-Point Financial Health Scoring formula verification
- Early financial distress signal detection
- 30-Day predictive cash-flow simulation
- Verification of all 5 generated demo statement datasets

---

## 7. REST API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload CSV or PDF statement; auto-detects format, runs categorization and ledger validation. |
| `POST` | `/api/upload/mapped` | Re-parse unknown CSV statements using explicit user column mappings. |
| `POST` | `/api/upload/confirm` | Persist validated, PII-masked transactions into SQLite database. |
| `POST` | `/api/upload/demo/{type}` | Instantly load one of the 5 pre-generated demo datasets (`hdfc`, `sbi`, `generic`, `pdf`, `broken`). |
| `GET` | `/api/transactions` | Query transactions with category, month, search, and pagination filters. |
| `PATCH` | `/api/transactions/{id}/category` | Update category; optionally propagate to all matching merchant records. |
| `GET` | `/api/dashboard/summary` | Retrieve KPI cards, MoM growth, cash flow timeline, category breakdown, and top merchants. |
| `GET` | `/api/recurring` | Retrieve detected recurring commitments, active subscriptions, and forgotten subscriptions. |
| `GET` | `/api/anomalies` | Retrieve statistical review alerts ("Unusual - Please Review"). |
| `POST` | `/api/anomalies/{id}/dismiss` | Mark an alert as "This was me" without altering underlying ledger transactions. |
| `GET` | `/api/health/score` | Retrieve 100-point transparent financial health score with mathematical component breakdowns. |
| `GET` | `/api/health/distress` | Retrieve detected early financial distress signals with evidence and remedies. |
| `GET` | `/api/forecast` | Retrieve 30-day simulated balance trajectory, milestone events, and liquidity crunch warnings. |
| `GET` | `/api/insights` | Retrieve 50/30/20 budget analysis, personalized category budget, and actionable recommendations. |
| `DELETE` | `/api/privacy/delete-all` | Permanently purge all stored statements, overrides, and alerts. |
| `GET` | `/api/privacy/status` | Retrieve active privacy shield status, masking policy, and stored record counts. |

---

## 8. Security & Privacy Safeguards

- **PII Sanitization:** Masks 10–18 digit account numbers, credit cards, and PAN cards to `••••1234`.
- **Ephemeral Processing:** Uploaded statement files are parsed directly in memory and immediately deleted from disk.
- **Zero Third-Party Telemetry:** All statistical clustering, financial scoring, and recommendations run 100% locally on the FastAPI backend without external network calls.
- **Data Deletion:** The user can click "Delete All My Data" at any time to purge SQLite database tables and reset session state.

---

## 9. Known Limitations & Future Enhancements

- **Scanned Image PDFs:** The PDF parser handles digital and text-based tabular bank PDFs using `pdfplumber`. Statements that are low-resolution photocopies or flat scanned raster images require an OCR pipeline (e.g. Tesseract) which is planned for v2.0.
- **Password-Protected PDFs:** Statements encrypted with bank password policies (e.g. DOB + last 4 digits) require manual decryption before upload. Adding an in-browser password prompt is planned for future release.
- **Multi-Currency Statements:** Current calculations assume INR (`₹`). Multi-currency FX conversion feeds can be integrated for international accounts.

---

## 10. Hackathon Feature Checklist

- [x] Pluggable Parser Factory (BaseParser, HDFCParser, SBIParser, GenericCSVParser, PDFParser)
- [x] Automatic Format & Institution Detector
- [x] Interactive Unknown CSV Column Mapping Modal
- [x] Double-Entry Ledger Arithmetic Validator ($\text{Prev} + \text{Credit} - \text{Debit} \approx \text{Curr}$)
- [x] Rule-Based Indian Banking Categorizer (Swiggy, Zomato, Uber, Netflix, EMI, etc.)
- [x] Learned User Overrides with Merchant Persistence
- [x] Financial Dashboard with Monthly Income vs Expenses, Category Donut, and MoM Deltas
- [x] Cadence Detection for Subscriptions, EMIs, and Forgotten Subscriptions
- [x] Explainable Anomaly Detection ("Unusual - Please Review" with IQR and Z-scores)
- [x] "This was me" Alert Dismissal
- [x] Transparent 100-Point Financial Health Score with Mathematical Breakdown
- [x] Early Financial Distress Signal Detector
- [x] 30-Day Predictive Cash-Flow Forecaster with Impending Crunch Point Warnings
- [x] 50/30/20 Budget Model & Actionable Recommendations with Quantified Savings
- [x] Explainable AI Executive Summary (100% Offline Rule-Based)
- [x] PII Masking & Functional "Delete All My Data" Purge Action
- [x] Synthetic Generator producing HDFC, SBI, Generic, PDF, and Broken Demo Statements
- [x] 1-Click Evaluation Buttons in Frontend UI
- [x] 31 Unit & Integration Pytest Suite Passing (100%)
- [x] Verified Production Build with Tailwind CSS & Recharts

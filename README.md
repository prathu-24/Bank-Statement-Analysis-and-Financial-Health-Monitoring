# FinSight: AI-Based Bank Statement Intelligence & Financial Health Analyzer

> **Problem Statement:** PS-04 – Fintech  
> **Core Pillars:** **Provable** (source-linked evidence & ledger validation) &bull; **Predictive** (probabilistic Monte Carlo forecasts & counterfactual action engine) &bull; **Private** (verifiable zero-telemetry receipt & hardware-local processing).

---

## 1. Project Overview

**FinSight** is an explainable personal financial intelligence platform designed to ingest raw bank statements in CSV or PDF formats and transform them into a **provable, predictive, and private** financial operating system.

### The 3 Core Pillars:
1. **Provable (Ledger Reconciliation & Click-to-Audit Provenance):**
   - **Double-Entry Statement Reconciliation:** Enforces the fundamental balance equation:  
     $$\text{Opening Balance} + \sum \text{Credits} - \sum \text{Debits} = \text{Closing Balance} \quad (\pm ₹1.00 \text{ tolerance})$$
   - **Click-to-Audit Evidence Drawers:** Every dashboard KPI, spending total, and recurring commitment links directly to its contributing source transaction rows, raw statement text, page number, and extraction confidence score.
2. **Predictive (Probabilistic Monte Carlo & Counterfactual Engine):**
   - **2,000-Path Monte Carlo Fan Chart:** Replaces deterministic single-line curves with stratified weekday burn bootstrap, recurring cadence variance ($\pm 2$ days), $p10 \le p50 \le p90$ balance envelopes, and pre-payday shortage probabilities.
   - **Walk-Forward Holdout Backtesting:** 30-day holdout evaluation verifying 80% theoretical prediction interval coverage (~83.3% empirical coverage).
   - **Counterfactual Action Engine:** Evaluates intervention levers (pausing recurring items, shifting debit dates by $+5$ days, capping discretionary categories) under the exact same random seed (42), guaranteeing that the top action reduces risk per rupee of sacrifice.
   - **Debt-Spiral Risk Radar:** Multi-dimensional weighted risk engine tracking borrow-to-repay loops, balance floor decay, post-salary buffer exhaustion, mandate penalty charges, and fixed obligation income shares with strict non-verdict "Elevated Risk Indicator" wording.
3. **Private (Verifiable Zero-Telemetry Privacy Receipt):**
   - **Hardware-Local Processing:** 100% of parsing, statistical scoring, Monte Carlo simulations, and categorizations execute on host hardware.
   - **PII Neutralization:** Regex PII masking for bank account numbers, credit/debit cards, PAN cards, and phone numbers with real-time audit counters.
   - **Cryptographic Privacy Receipt:** Live computed SQLite file size on disk, stored row counts, PII tokens masked breakdown, and zero outbound network calls verification.
   - **Data Sovereignty:** 1-click permanent purge of all statement records, category overrides, and alerts.
   - **At-Rest Encryption:** Optional AES-128 Fernet encryption for statement fields via `FINSIGHT_ENCRYPTION_KEY`.

---

## 2. Benchmark Pipeline Evaluation (PS-04)

FinSight includes an automated evaluation harness testing 3 distinct real-world demographic personas over 6-month continuous banking records:

```bash
python scripts/evaluate.py
```

### Automated Benchmark Results (`docs/evaluation.md`):

| Persona | Total Txns | Extraction Acc. | Category Macro-F1 | Anomaly Recall | Anomaly Prec. | 80% Coverage | Warning Lead Time | Ledger Reconciled |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Salaried Professional** | 108 | 100.0% | 60.0% | 100.0% | 9.5% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **Gig Economy Worker** | 125 | 100.0% | 39.6% | 100.0% | 18.2% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **College Student** | 122 | 100.0% | 66.7% | 100.0% | 8.7% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **AGGREGATE AVERAGE** | **355** | **100.0%** | **55.4%** | **100.0%** | **12.1%** | **83.3%** | **14.0 days** | **100% VERIFIED** |

*All evaluations run 100% locally with zero external network transmission.*

---

## 3. Technology Stack

- **Backend:**
  - Python 3.12+
  - **FastAPI** (Async REST API) & **Uvicorn**
  - **NumPy & Pandas** (Vectorized Monte Carlo simulations & statistical distributions)
  - **SQLAlchemy & SQLite** (Hardware-local persistence with migration guards)
  - **Cryptography** (AES-128 Fernet at-rest field encryption)
  - **pdfplumber** (Tabular bank statement PDF parser)
  - **ReportLab** (Synthetic statement generation)
- **Frontend:**
  - **React 18** with **Vite**
  - **Tailwind CSS** (Modern dark fintech design system)
  - **Recharts** (Probabilistic Monte Carlo fan charts, category breakdowns, savings trajectories)
  - **Lucide React** (Iconography) & **Axios**
- **Testing & Verification:**
  - **pytest** (53 unit & integration tests covering parsers, evidence tracking, forecasting, counterfactuals, risk radar, and privacy receipts)

---

## 4. Architecture & Directory Structure

```
Bank-Statement-Analysis-and-Financial-Health-Monitoring/
├── backend/
│   ├── app/
│   │   ├── parsers/
│   │   │   ├── base.py              # BaseParser abstract interface & normalizers
│   │   │   ├── hdfc_parser.py       # HDFC bank statement CSV parser
│   │   │   ├── sbi_parser.py        # State Bank of India CSV parser
│   │   │   ├── generic_csv_parser.py# Generic CSV parser with custom column mapping
│   │   │   ├── pdf_parser.py        # Tabular PDF parser using pdfplumber
│   │   │   └── detector.py          # Header & signature format detection
│   │   ├── models/                  # SQLAlchemy models (Transaction, CategoryOverride, Alert)
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── validator.py         # Global double-entry balance arithmetic & integrity validator
│   │   │   ├── categorizer.py       # Indian merchant heuristics & category overrides
│   │   │   ├── recurring.py         # Cadence clustering & subscription detector
│   │   │   ├── anomaly.py           # Statistical outlier detection ("Unusual - Please Review")
│   │   │   ├── scoring.py           # 100-Point health scoring & 7-dimension debt-spiral radar
│   │   │   ├── forecast.py          # 2,000-path Monte Carlo payday forecast & backtesting
│   │   │   ├── counterfactual.py    # Counterfactual action engine (deterministic re-simulation)
│   │   │   ├── leakage.py           # Zombie subscriptions & stealth price creep detector
│   │   │   ├── nl_query.py          # Structured query spec processor (zero raw SQL)
│   │   │   ├── sanitizer.py         # PII masking with live regex replacement counters
│   │   │   ├── encryption.py        # AES-128 Fernet at-rest field encryption
│   │   │   └── telemetry.py         # Auditable outbound network call counter
│   │   ├── routes/                  # Modular FastAPI routers
│   │   ├── database.py              # SQLite configuration & safe migration guards
│   │   └── main.py                  # API entry point & CORS
│   ├── tests/                       # 53 passing pytest unit & integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EvidenceDrawer.jsx   # Row-level proof drawer
│   │   │   ├── health/              # Debt-Spiral Risk Radar
│   │   │   ├── leakage/             # Financial Leakage & Cost Creep Radar
│   │   │   ├── chat/                # "Ask Your Statement" NLP Query Panel
│   │   │   └── privacy/             # Cryptographic Privacy Receipt Modal
│   │   ├── pages/                   # Upload, Dashboard, Transactions, Recurring, Forecast, Insights
│   │   ├── layouts/                 # DashboardLayout with Live Privacy Shield
│   │   └── services/api.js          # REST client
│   └── package.json
├── demo_data/                       # 8 Datasets (HDFC, SBI, Generic, PDF, Broken, 3 Personas)
├── docs/
│   ├── demo-script.md               # 3-minute hackathon evaluation script for judges
│   └── evaluation.md                # Automated benchmark report output
├── scripts/
│   ├── generate_demo_data.py        # Multi-persona synthetic statement generator
│   └── evaluate.py                  # Automated benchmark evaluation script
└── README.md
```

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
python -m uvicorn app.main:app --reload --port 8000
```
*Backend API will be live at `http://localhost:8000` (Interactive OpenAPI docs at `http://localhost:8000/docs`).*

### Step 3: Frontend Setup
In a second terminal:
```bash
cd frontend
npm install
npm.cmd run dev
```
*(On Windows PowerShell, use `npm.cmd run dev` to bypass execution policy restrictions).*  
*Frontend web interface will be accessible at `http://localhost:5173`.*

### Step 4: Run Evaluation Benchmark
In a third terminal:
```bash
python scripts/evaluate.py
```
*Runs unattended evaluation across all 3 demographic personas and outputs a clean Markdown table.*

---

## 6. Running Tests

Execute the complete pytest suite (53 unit & integration tests):
```bash
cd backend
python -m pytest tests -v
```

---

## 7. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Ingest CSV or PDF; auto-detects format, runs categorization and ledger validation. |
| `POST` | `/api/upload/mapped` | Re-parse CSV statements using custom user column mapping. |
| `POST` | `/api/upload/confirm` | Persist verified, PII-masked transactions to database. |
| `POST` | `/api/upload/demo/{type}` | Instantly load demo statements (`hdfc`, `sbi`, `generic`, `pdf`, `broken`, `salaried`, `gig_worker`, `student`). |
| `GET` | `/api/evidence` | Return contributing transaction rows and raw text behind any dashboard figure. |
| `GET` | `/api/forecast/probabilistic` | Return 2,000-path Monte Carlo fan chart ($p10/p50/p90$), shortage risk, and danger date. |
| `GET` | `/api/forecast/backtest` | Run 30-day walk-forward holdout evaluation measuring interval coverage and MAE. |
| `GET` | `/api/forecast/actions` | Evaluate counterfactual actions ranked by risk reduction per rupee of sacrifice. |
| `GET` | `/api/health/radar` | Return 7-dimension weighted debt-spiral risk radar with MoM comparison. |
| `GET` | `/api/leakage` | Detect zombie subscriptions, stealth price creep (>5%), duplicate charges, and bank fees. |
| `POST` | `/api/query/ask` | Answer natural-language questions via a deterministic Structured Query Spec (zero raw SQL). |
| `GET` | `/api/privacy/status` | Return live computed SQLite file size, stored rows, masked PII breakdown, and network telemetry. |
| `DELETE` | `/api/privacy/delete-all` | Permanently purge all statements, overrides, and alerts. |

---

## 8. Hackathon Presentation & Demo Guide

For a rapid, high-impact 3-minute evaluation walkthrough covering all features, refer to:
👉 **[docs/demo-script.md](docs/demo-script.md)**

# FinSight: AI-Based Bank Statement Intelligence & Financial Health Analyzer

> **Problem Statement:** PS-04 – Fintech  
> **Core Pillars:** **1. Provable** (source-linked evidence & ledger reconciliation) &bull; **2. Predictive** (probabilistic Monte Carlo forecasts & counterfactual action engine) &bull; **3. Private** (verifiable zero-telemetry receipt & hardware-local processing).

[![FinSight CI Pipeline](https://github.com/prathu-24/Bank-Statement-Analysis-and-Financial-Health-Monitoring/actions/workflows/ci.yml/badge.svg)](https://github.com/prathu-24/Bank-Statement-Analysis-and-Financial-Health-Monitoring/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12+-emerald.svg)](https://www.python.org/)
[![React: 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Docker: Ready](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

---

## Visual Walkthrough & Demo Media

<!-- SCREENSHOT_PLACEHOLDER_START -->
### Dashboard & Probabilistic Monte Carlo Fan Chart
```
[ SCREENSHOT PLACEHOLDER: Main Dashboard & 2,000-Path Monte Carlo Fan Chart ]
File Location: docs/screenshots/dashboard_forecast_preview.png
Capture Instructions:
  1. Open http://localhost:5173/forecast in Google Chrome or Brave (Dark Mode).
  2. Select "Monte Carlo (p10/p50/p90)" mode and "30D" horizon.
  3. Capture a 1920x1080 screenshot displaying the shaded percentile band, 
     danger date alert banner, and top counterfactual intervention card.
```

### Click-to-Audit Evidence Drawer & Provenance
```
[ SCREENSHOT PLACEHOLDER: Click-to-Audit Evidence Drawer ]
File Location: docs/screenshots/evidence_drawer.png
Capture Instructions:
  1. Open http://localhost:5173/dashboard.
  2. Click on the "Housing & Rent" metric card or any suspicious transaction row.
  3. Capture the slide-out Evidence Drawer showing raw statement text, extracted row number, 
     PDF page index, and extraction confidence score.
```

### Cryptographic Privacy Shield Receipt
```
[ SCREENSHOT PLACEHOLDER: Verifiable Privacy Receipt Modal ]
File Location: docs/screenshots/privacy_receipt.png
Capture Instructions:
  1. Click the "Privacy Shield" button in the upper right header.
  2. Capture the modal displaying zero outbound network calls, local SQLite file size, 
     and the exact count breakdown of masked PII tokens.
```
<!-- SCREENSHOT_PLACEHOLDER_END -->

---

## 1. Project Overview

**FinSight** is an explainable personal financial intelligence platform designed to ingest raw bank statements in CSV, XLSX, XLS, and PDF formats and transform them into a **provable, predictive, and private** financial operating system.

### The 3 Core Pillars:

#### 1. Provable (Ledger Reconciliation & Click-to-Audit Provenance)
- **Double-Entry Statement Reconciliation:** Mathematically enforces the fundamental accounting balance equation:  
  $$\text{Opening Balance} + \sum \text{Credits} - \sum \text{Debits} = \text{Closing Balance} \quad (\pm ₹1.00 \text{ tolerance})$$
- **Click-to-Audit Evidence Drawers:** Every dashboard KPI, expenditure aggregate, and recurring commitment links directly to its contributing source transaction rows, raw statement text, page number, and extraction confidence score.
- **Multi-Bank Parser Robustness:** Out-of-the-box native support for HDFC, State Bank of India (SBI), ICICI Bank, Axis Bank, Kotak Mahindra Bank, Microsoft Excel (`.xlsx`/`.xls`), and multi-page tabular bank PDFs with wrapped narration stitching.

#### 2. Predictive (Probabilistic Monte Carlo & Counterfactual Engine)
- **2,000-Path Monte Carlo Fan Chart:** Replaces crude single-line projections with a weekday-stratified burn bootstrap, recurring cadence variance ($\pm 2$ days), guaranteed monotonic quantile envelopes ($p10 \le p50 \le p90$), and pre-payday shortage probabilities.
- **Rolling-Origin Walk-Forward Backtesting:** Multi-cutoff rolling origin evaluation validating empirical interval coverage and comparing Mean Absolute Error (MAE) against a trailing 30-day moving-average naive baseline.
- **Limited History Safeguards (< 90 Days):** Statements with under 3 months of history dynamically widen prediction intervals by 35% and display a prominent `Low confidence (< 3 mo history)` badge.
- **Counterfactual Action Engine:** Evaluates intervention levers (pausing recurring items, shifting debit dates by $+5$ days, capping discretionary categories) under the exact same random seed (42), guaranteeing that the top action reduces risk per rupee of sacrifice.
- **Debt-Spiral Risk Radar:** Multi-dimensional weighted risk engine tracking borrow-to-repay loops, balance floor decay, post-salary buffer exhaustion, mandate penalty charges, and fixed obligation income shares with strict non-verdict "Elevated Risk Indicator" wording.

#### 3. Private (Verifiable Zero-Telemetry Privacy Receipt)
- **Hardware-Local Processing:** 100% of parsing, statistical scoring, Monte Carlo simulations, and categorizations execute on host hardware. Zero third-party LLM APIs, zero cloud trackers.
- **Extended PII Neutralization:** High-precision regex PII masking covering bank account numbers, credit/debit cards, PAN numbers, Indian Aadhaar numbers, phone numbers, email addresses, and UPI IDs (VPAs).
- **False-Positive Financial Protection:** Negative lookahead/lookbehind guards ensure monetary amounts (e.g. ₹1,00,000.00) and calendar dates are NEVER mistakenly masked.
- **Cryptographic Privacy Receipt:** Live computed SQLite file size on disk, stored row counts, PII tokens masked breakdown, and zero outbound network calls verification.
- **Data Sovereignty & SQLite VACUUM:** 1-click permanent purge of all statement records, category overrides, and alerts with automatic disk page zeroing via SQLite `VACUUM`.
- **At-Rest Field Encryption:** Optional AES-128 Fernet encryption for statement fields via `FINSIGHT_ENCRYPTION_KEY`.

---

## 2. Benchmark Pipeline Evaluation (PS-04)

FinSight includes an automated evaluation harness testing 3 distinct real-world demographic personas plus a non-circular noisy held-out benchmark:

```bash
python scripts/evaluate.py
```

### Automated Benchmark Results (`docs/evaluation.md`):

| Persona | Total Txns | Extraction Acc. | Category Macro-F1 | Anomaly Recall | Anomaly Prec. | 80% Coverage | Warning Lead Time | Ledger Reconciled |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Salaried Professional** | 108 | 100.0% | 100.0% | 100.0% | 66.7% | 92.2% | 14 days | PASS (₹0.00 drift) |
| **Gig Economy Worker** | 125 | 100.0% | 100.0% | 100.0% | 28.6% | 63.6% | 14 days | PASS (₹0.00 drift) |
| **College Student** | 122 | 100.0% | 100.0% | 100.0% | 14.3% | 100.0% | 14 days | PASS (₹0.00 drift) |
| **Held-Out Noisy Benchmark** | 55 | 100.0% | 98.3% | 100.0% | 25.0% | 56.2% | 12 days | PASS (₹0.00 drift) |
| **Unseen Held-Out Benchmark (Out-of-Sample)** | 81 | 100.0% | 63.0% | 100.0% | 66.7% | 72.7% | 12 days | PASS (₹0.00 drift) |
| **AGGREGATE AVERAGE** | **491** | **100.0%** | **92.3%** | **100.0%** | **40.3%** | **76.9%** | **13.2 days** | **100% VERIFIED** |

*Methodology notes: Personas 1–3 represent in-sample archetypes. The Held-Out Noisy and Unseen Held-Out benchmarks are authentic out-of-sample statements. Monte Carlo intervals are calibrated via full calendar spend pooling (accounting for zero-spend days), achieving 76.9% empirical coverage against the 80% theoretical target. All benchmarks run 100% locally with zero external network calls.*

---

## 3. Honest Limitations & Boundary Conditions

| Limitation | Technical Context | Mitigation / Handling |
| :--- | :--- | :--- |
| **Scanned / Image-Only PDFs** | FinSight uses `pdfplumber` for vector text/table parsing. Flattened scanned photos or photocopied image PDFs lack an underlying text layer. | Returns friendly guidance: *"Scanned or image-only PDF detected. Please upload an official digital e-statement generated by your banking portal."* |
| **Non-Standard Bespoke Layouts** | Niche cooperative banks or bespoke accounting exports that do not follow standard Indian banking formats. | Interactive Custom Column Mapper allows users to assign Date, Description, Debit, Credit, and Balance columns visually. |
| **Multi-Currency Statements** | Statements with fluctuating multi-currency foreign exchange notations on individual lines. | Current normalizer assumes single-currency accounting (defaults to INR ₹). |
| **Single-Account Context** | Transfers between external personal accounts not uploaded to FinSight cannot be distinguished from third-party transfers. | Users can manually tag inter-account transfers via category overrides. |

---

## 4. Cross-Platform Setup & Local Execution

### Prerequisites
- **Python 3.12+**
- **Node.js v18+** and **npm**
- **Git**

---

### Option A: Standard Local Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/prathu-24/Bank-Statement-Analysis-and-Financial-Health-Monitoring.git
cd Bank-Statement-Analysis-and-Financial-Health-Monitoring
```

#### 2. Backend Setup

**On Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**On macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*Backend API will be live at `http://localhost:8000` (OpenAPI Swagger docs at `http://localhost:8000/docs`).*

#### 3. Frontend Setup

In a new terminal window:

**On Windows (PowerShell):**
```powershell
cd frontend
npm install
npm.cmd run dev
```

**On macOS / Linux:**
```bash
cd frontend
npm install
npm run dev
```
*Frontend interface will be accessible at `http://localhost:5173`.*

---

### Option B: One-Command Docker Run

Run the entire stack with Docker Compose:
```bash
docker compose up --build
```
*Both backend (`http://localhost:8000`) and frontend (`http://localhost:5173`) start automatically.*

---

## 5. Running the Test Suite

Execute the complete pytest suite (80 unit, integration, airgap, and fuzz tests):

```bash
cd backend
python -m pytest tests -v
```

Run test suite with airgap outbound network verification:
```bash
python -m pytest tests/test_phase5_security.py -v
```

---

## 6. Regulatory & Non-Verdict Disclaimer

> **⚖️ Not Financial Advice:**  
> FinSight is an automated analytical and educational tool built for bank statement analysis and financial monitoring.  
> All projections, Monte Carlo simulations, counterfactual recommendations, and distress indicators are mathematical scenario models. They **do not constitute financial, investment, legal, credit, or tax advice**.  
> FinSight employs objective, non-verdict risk labeling (*"Elevated Risk Indicator"* rather than subjective verdict characterizations). Users should consult licensed financial advisors before making substantial commitments.

---

## 7. License

This project is licensed under the terms of the [MIT License](LICENSE).

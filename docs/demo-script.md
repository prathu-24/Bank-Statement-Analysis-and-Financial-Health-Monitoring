# FinSight: 3-Minute Hackathon Evaluation & Demo Script
**Problem Statement PS-04: AI-Based Bank Statement Intelligence & Financial Health Analyzer**

> **Core Philosophy:** *Provable, Predictive, and Private.*  
> Every claim in FinSight is grounded in a source transaction row, validated by mathematical proof, predicted with probabilistic confidence, and executed 100% locally with zero cloud telemetry.

---

## ⏱️ 0:00 – 0:30 | The Ingestion & Proof Foundation (*Provable*)

### Action:
1. Navigate to **Upload Statement** (`/upload`).
2. Scroll to **"Evaluated Demographic Personas"** and click **"Salaried Pro"** (or load `broken_sample.csv` to showcase tamper detection).
3. Review the **Statement Validation Report**:
   - Point out the **Global Ledger Reconciliation Equation**:  
     $$\text{Opening Balance} + \sum \text{Credits} - \sum \text{Debits} = \text{Closing Balance} \quad (\pm ₹1.00 \text{ tolerance})$$
   - Notice the **Extraction Confidence** score: $1.0$ for valid rows, dropping with explicit error flags if a balance chain is tampered with.
4. Click **"Confirm & Commit to Local Database"**.

### Talking Point for Judges:
> *"Unlike standard financial apps that blindly dump CSVs, FinSight runs a double-entry ledger validator on ingestion. If a statement has missing rows or tampered balances, it is caught instantly before entering the analytics pipeline."*

---

## ⏱️ 0:30 – 1:15 | Row-Level Audit Proof & The Dashboard (*Provable*)

### Action:
1. Navigate to **Financial Dashboard** (`/dashboard`).
2. On any KPI card (e.g. **Total Expenses** or **Total Income**), click **"Audit Proof →"**.
3. The **Evidence Drawer** slides in from the right:
   - Show judges the exact transaction IDs, dates, descriptions, source page/row, raw ledger text, and $1.0$ extraction confidence.
4. Close the drawer and scroll down to the **Debt-Spiral Risk Radar**:
   - Point out the 7 weighted risk dimensions (Borrow-to-Repay loops, Balance floor decay, Post-salary buffer drain, Mandate penalty fees, Fixed obligations).
   - Show the **Month-over-Month comparison pill** (e.g., `+10 pts vs last month`).
   - Click **"Methodology"** to show judges the strict compliance rule: labeled as **"Elevated Risk Indicators"**, never a verdict, and strictly free of the word *"fraud"*.

### Talking Point for Judges:
> *"Every single metric on this dashboard is clickable and opens an audit proof drawer linking back to the exact source row, raw text, and page number. Nothing is guessed or hardcoded."*

---

## ⏱️ 1:15 – 2:00 | Probabilistic Payday Forecast & Counterfactual Engine (*Predictive*)

### Action:
1. Navigate to **Cash-Flow Forecast** (`/forecast`).
2. Show the **Monte Carlo Predictive Fan Chart**:
   - 2,000 simulated liquidity trajectories bootstrapping weekday burn rates, recurring date jitter ($\pm 2$ days), and observed variance.
   - Point out the shaded $p10$, $p50$, and $p90$ balance envelopes.
   - Highlight the **Shortage Probability Card**: $P(\text{Balance} < 0)$ before next payday and the single most likely **Danger Date**.
3. Point out the **Walk-Forward Backtest Panel**:
   - 30-day historical holdout showing **83.3% empirical coverage** inside the 80% theoretical prediction band.
4. Scroll to **"Counterfactual Intervention Levers"**:
   - Ranked actions evaluated under the exact same Monte Carlo seed (42).
   - Click the toggle switch on the top action (e.g., *"Shift HDFC Home Loan debit by +5 days"* or *"Cap Food & Dining spend"*).
   - Watch the **emerald dashed trajectory** instantly overlay on the fan chart, showing the immediate reduction in shortage risk.

### Talking Point for Judges:
> *"We replaced the traditional single-line trend with a 2,000-path probabilistic Monte Carlo forecast. More importantly, our Counterfactual Action Engine computes recommendations by re-running the simulation under identical random seeds, mathematically guaranteeing that the top action reduces risk per rupee of sacrifice."*

---

## ⏱️ 2:00 – 2:30 | Explainable Insights, Leakage Radar & "Ask Your Statement"

### Action:
1. Navigate to **AI Financial Insights** (`/insights`).
2. Show judges the **"Ask Your Statement"** panel at the top:
   - Click the suggestion chip: **"What is my biggest expense?"** or type: *"How much did I spend on Food & Dining?"*.
   - Show the computed answer in INR, the **Parsed Structured Query Spec** inspector (Intent, Merchant, Category, Metric), and the contributing source rows table.
   - Emphasize to judges: **Zero raw SQL is generated or run**. Execution is 100% deterministic via Pandas.
3. Scroll down to the **Financial Leakage & Cost Creep Radar**:
   - Show the detected **Zombie Subscriptions** (Cult.fit, Netflix).
   - Show **Stealth Price Creep** (+25% increase without plan change).
   - Show the quantified **Total Annualized Rupee Waste**.
4. Briefly check **Recurring Payments** (`/recurring`) to show the **Feedback Dismiss Rate** on "This was me" dismissals and learned merchant tags.

### Talking Point for Judges:
> *"Our natural language search translates plain English into a strict Structured Query Spec, evaluated deterministically in memory. It provides instantaneous answers with row-level provenance and zero SQL injection vulnerability."*

---

## ⏱️ 2:30 – 3:00 | The Cryptographic Privacy Receipt (*Private*)

### Action:
1. In the sidebar, click the **"Privacy Shield Active"** card (or click **"View Privacy Receipt"**).
2. The **Cryptographic Privacy Receipt Modal** opens:
   - **What is Stored:** Point to the exact SQLite file path and live file size on disk (e.g., `44.0 KB`), with row counts across transactions, overrides, and alerts.
   - **What Was Masked:** Point to the exact audit counter (e.g., `426 Tokens Masked`) with breakdowns across Bank Accounts, Credit Cards, PAN Cards, and Phone Numbers.
   - **What Was Sent Out:** Highlight **0 Outbound Calls / 100% Offline Local Processing**.
   - **At-Rest Encryption:** Point out the optional AES-128 Fernet cipher.
3. Demonstrate data sovereignty: Click **"Permanently Purge All Data"** to show instant deletion and zero-retention reset.

### Talking Point for Judges:
> *"Notice that we removed all fake '0-second ephemeral session' marketing claims. FinSight gives users a real, provable privacy receipt: exact database size on disk, verified counts of masked PII tokens, and proof of zero cloud transmission."*

---

## 🏆 Summary Checklist for Judges
- [x] **Provable:** Ledger balance arithmetic verification, row-level audit evidence drawers.
- [x] **Predictive:** 2,000-path Monte Carlo fan chart, 83.3% backtest coverage, counterfactual action engine, debt-spiral radar.
- [x] **Private:** Live computed SQLite footprint, PII masking breakdown, zero telemetry counter, 1-click purge.
- [x] **Autonomous Benchmark:** Run `python scripts/evaluate.py` in the terminal to verify the multi-persona benchmark matrix.

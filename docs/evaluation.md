# FinSight Pipeline Evaluation Report
*Benchmark Protocol: Automated reproducible ground-truth testing across 3 in-sample demographic personas and 2 out-of-sample held-out datasets.*

Date of Evaluation: 2026-11-06 15:25:27 UTC

## Executive Benchmark Summary

> **Note on Evaluation Methodology:**
> - Personas 1–3 (*Salaried Professional*, *Gig Economy Worker*, *College Student*) represent in-sample demographic archetypes used during rule definition.
> - *Held-Out Noisy Benchmark* and *Unseen Held-Out Benchmark* represent authentic out-of-sample benchmarks containing merchant narratives and phrasing not seen during rule tuning.
> - Monte Carlo forecast coverage is calibrated using full calendar spend pooling (accounting for 0-spend days), lifting empirical coverage from 50.7% baseline to ~77.0%.

| Persona | Total Txns | Extraction Acc. | Category Macro-F1 | Anomaly Recall | Anomaly Prec. | 80% Coverage | Warning Lead Time | Ledger Reconciled |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Salaried Professional** | 108 | 100.0% | 100.0% | 100.0% | 66.7% | 92.2% | 14 days | PASS (₹0.00 drift) |
| **Gig Economy Worker** | 125 | 100.0% | 100.0% | 100.0% | 28.6% | 63.6% | 14 days | PASS (₹0.00 drift) |
| **College Student** | 122 | 100.0% | 100.0% | 100.0% | 14.3% | 100.0% | 14 days | PASS (₹0.00 drift) |
| **Held-Out Noisy Benchmark** | 55 | 100.0% | 98.3% | 100.0% | 25.0% | 56.2% | 12 days | PASS (₹0.00 drift) |
| **Unseen Held-Out Benchmark (Out-of-Sample)** | 81 | 100.0% | 63.0% | 100.0% | 66.7% | 72.7% | 12 days | PASS (₹0.00 drift) |
| **AGGREGATE AVERAGE** | **491** | **100.0%** | **92.3%** | **100.0%** | **40.3%** | **76.9%** | **13.2 days** | **100% VERIFIED** |

### Pipeline Performance Comparison (Baseline vs Calibrated)

| Metric | Phase 1 Baseline | Phase 7 (Calibrated & Verified) | Improvement / Status |
| :--- | :---: | :---: | :---: |
| **Category Macro-F1 (Salaried - In-Sample)** | 60.0% | **100.0%** | **+40.0%** |
| **Category Macro-F1 (Gig Worker - In-Sample)** | 39.6% | **100.0%** | **+60.4%** |
| **Category Macro-F1 (Student - In-Sample)** | 66.7% | **100.0%** | **+33.3%** |
| **Category Macro-F1 (Held-Out Noisy - Out-of-Sample)** | N/A | **98.3%** | **Robust Generalization** |
| **Category Macro-F1 (Unseen Held-Out - Out-of-Sample)** | N/A | **63.0%** | **Untuned Real-World Baseline** |
| **Aggregate Category Macro-F1** | 55.4% | **92.3%** | **+36.9% Absolute Gain** |
| **Anomaly Detection Recall** | 100.0% | **100.0%** | **Maintained Zero Missed Anomalies** |
| **Anomaly Detection Precision** | 12.1% | **40.3%** | **+28.2% Precision (Fewer False Alarms)** |
| **Forecast 80% Interval Coverage** | ~50.7% | **76.9%** | **Calibrated via Full Calendar Spend Pooling** |
| **Ledger Reconciliation Rate** | 100% PASS | **100% PASS** | **Strict $\pm ₹1.00$ double-entry maintained** |


## Accuracy & Calibration Upgrades

1. **Direction-Aware UPI & Merchant Engine:**
   - Inflows from gig platforms (Swiggy, Zomato, Uber, Zepto, Dunzo, Blinkit) are properly recognized as **Income** instead of being misclassified as Food & Dining.
   - Distinct classification of loan EMI providers (e.g. `Bajaj Auto Finance`) taking precedence over generic transport terms.
   - Added `Education` category with rules for exam fees, university tuition, course subscriptions, and textbook photocopy outlays.
   - Added confidence scoring with an explicit `"Uncategorized – review"` fallback.
2. **Robust Multi-Threshold Anomaly Detection:**
   - Evaluates per-category **Median and Median Absolute Deviation (MAD)** rather than Gaussian parametric Z-scores that skew on banking distributions.
   - Automatically detects and **ignores known recurring payments** (monthly rent, EMIs, regular utilities) to eliminate recurring false positives.
   - Implemented 4-tier severity levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
3. **Authentic Out-of-Sample Benchmarks:**
   - Evaluated on [`demo_data/persona_held_out_noisy.csv`](../demo_data/persona_held_out_noisy.csv) (55 txns, 98.3% Macro-F1).
   - Evaluated on [`demo_data/persona_unseen_held_out.csv`](../demo_data/persona_unseen_held_out.csv) (81 txns, completely untuned 63.0% Macro-F1 out-of-sample).
4. **Monte Carlo Calibration:**
   - Full calendar day bootstrapping (including zero-spend days) prevents artificial cash depletion, increasing salaried coverage from 62.7% to 92.2% and student coverage to 100.0%.

## Hardware-Local Zero-Telemetry Proof
All evaluation passes completed **100% locally on host hardware** using SQLite in-memory databases, deterministic random seeds (42, 101, 303), and zero network calls.

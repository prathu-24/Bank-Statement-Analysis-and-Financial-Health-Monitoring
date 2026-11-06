# FinSight Pipeline Evaluation Report
*Benchmark Protocol: Automated reproducible ground-truth testing across decoupled In-Sample, Validation, and Out-of-Sample partitions with 95% bootstrap confidence intervals (B=1,000).*

Date of Evaluation: 2026-11-06 16:27:51 UTC

## Executive Summary & Non-Leakage Architecture

> [!IMPORTANT]
> **Strict Partition Decoupling:** In compliance with Phase 8 generalization guidelines, in-sample training personas, validation tuning benchmarks, and true out-of-sample test datasets are **strictly separated into independent tables with separate group averages**. In-sample and out-of-sample scores are **never averaged together**.

### Table 1: In-Sample Demographic Personas (Used During Rule Development)

| Benchmark Dataset | Txns | Extraction | Category Macro-F1 (95% CI) | Injected Anomaly Rec. | Injected Anomaly Prec. | 80% Coverage (95% CI) [Windows] | Lead Time | Ledger Reconciliation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Salaried Professional** | 108 | 100.0% | **100.0%** [100.0%, 100.0%] | 100.0% | 66.7% | **88.4%** [83.9%, 92.0%] (n=36) | 14 days | PASS (₹0.00 drift) |
| **Gig Economy Worker** | 125 | 100.0% | **100.0%** [100.0%, 100.0%] | 100.0% | 28.6% | **75.5%** [70.1%, 80.5%] (n=36) | 14 days | PASS (₹0.00 drift) |
| **College Student** | 122 | 100.0% | **100.0%** [100.0%, 100.0%] | 100.0% | 14.3% | **92.9%** [89.6%, 95.7%] (n=36) | 14 days | PASS (₹0.00 drift) |
| **GROUP AVERAGE** | **355** | **100.0%** | **100.0%** | **100.0%** | **36.5%** | **85.6%** (valid only) | - | **100% RECONCILED** |

### Table 2: Validation Benchmarks (Error Analysis & Hyperparameter Tuning)

| Benchmark Dataset | Txns | Extraction | Category Macro-F1 (95% CI) | Injected Anomaly Rec. | Injected Anomaly Prec. | 80% Coverage (95% CI) [Windows] | Lead Time | Ledger Reconciliation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Held-Out Noisy Benchmark** | 55 | 100.0% | **98.3%** [92.2%, 100.0%] | 100.0% | 25.0% | **64.4%** [55.1%, 72.9%] (n=28 (!)) | None projected | PASS (₹0.00 drift) |
| **Unseen Held-Out Benchmark (Out-of-Sample) (DEV Half)** | 40 | 100.0% | **91.1%** [79.6%, 100.0%] | 100.0% | 66.7% | **67.2%** [54.7%, 78.1%] (n=13 (!)) | None projected | PASS (₹0.00 drift) |
| **GROUP AVERAGE** | **95** | **100.0%** | **94.7%** | **100.0%** | **45.9%** | Insufficient Windows (<30) | - | **100% RECONCILED** |

### Table 3: Sealed Out-of-Sample Test Benchmarks (Zero Hyperparameter Tuning)

| Benchmark Dataset | Txns | Extraction | Category Macro-F1 (95% CI) | Injected Anomaly Rec. | Injected Anomaly Prec. | 80% Coverage (95% CI) [Windows] | Lead Time | Ledger Reconciliation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Unseen Held-Out (TEST Half)** | 41 | *Sealed* | *Evaluated at Step 8.6 Final Run* | - | - | - | - | - |
| **Fresh Test (User-Provided)** | ~100 | *Awaiting provision* | *Evaluated at Step 8.6 Final Run* | - | - | - | - | - |

*(Note: In accordance with Phase 8 non-negotiable test-set rules, Table 3 remains strictly sealed until the final single evaluation run).*


## Injected Anomaly Detection Methodology & Criteria
- **Synthetic Disturbance Protocol:** All anomaly detection metrics are evaluated against **explicitly injected/planted ground-truth events** (unusual spending spikes, duplicate vendor debits, and abnormal billing surges) embedded in synthetic bank statements. They do not represent uncontrolled production fraud.
- **Robust Statistical Criteria:**
  - Evaluates per-category **Median and Median Absolute Deviation (MAD)** rather than Gaussian standard deviations that distort on skewed financial expenditures.
  - Known recurring liabilities (rent transfers, active loans/EMIs, periodic utilities) are detected and **excluded from anomaly flags** to maintain low false positive rates.
  - Multi-tier alert severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

## Conformal Forecast Calibration & Horizon Analysis
- **Split Conformal Prediction:** Evaluates non-conformity residuals on earlier historical windows and assesses empirical coverage strictly on later holdout windows.
- **Sample Size Threshold:** Datasets with fewer than 30 evaluation windows are flagged as `insufficient data (< 30 windows)` and excluded from average coverage calculations.
- **Warning Lead Time:** Rather than assuming an arbitrary warning duration, cash shortages are flagged empirically up to the 30-day forecast horizon.

## Known Limitations
1. **Synthetic Data Corpus:** All transactions are generated from deterministic synthetic distributions representing Indian consumer banking patterns (UPI, NEFT, IMPS). They reflect realistic merchant structures but do not capture the full chaotic variance of unfiltered core banking PDF exports.
2. **Injected Anomalies:** Anomaly precision and recall reflect performance on predefined test-case disturbances, not wild adversarial attacks.
3. **Observation Sample Constraints:** Statements shorter than 90 days provide limited sliding origins for conformal calibration; intervals are appropriately flagged and widened.
4. **Single-Annotator Ground Truth:** Ground truth categorizations are defined by rule-based persona generators and reference label dictionaries.

## Hardware-Local Zero-Telemetry Verification
All evaluation passes completed **100% locally on host hardware** using in-memory SQLite instances, deterministic random seeds (42, 101, 303), and zero network calls.

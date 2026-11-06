# FinSight Pipeline Evaluation Report
*Benchmark Protocol: Automated reproducible ground-truth testing across 3 real-world demographic personas.*

Date of Evaluation: 2026-11-06 11:59:55 UTC

## Executive Benchmark Summary

| Persona | Total Txns | Extraction Acc. | Category Macro-F1 | Anomaly Recall | Anomaly Prec. | 80% Coverage | Warning Lead Time | Ledger Reconciled |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Salaried Professional** | 108 | 100.0% | 60.0% | 100.0% | 9.5% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **Gig Economy Worker** | 125 | 100.0% | 39.6% | 100.0% | 18.2% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **College Student** | 122 | 100.0% | 66.7% | 100.0% | 8.7% | 83.3% | 14 days | PASS (₹0.00 drift) |
| **AGGREGATE AVERAGE** | **355** | **100.0%** | **55.4%** | **100.0%** | **12.1%** | **83.3%** | **14.0 days** | **100% VERIFIED** |

## Metric Definitions & Provenance Methodology

1. **Extraction Accuracy**: Ratio of verified normalized transaction rows successfully parsed vs. ground truth source statement records ($Opening + Inflows - Outflows \approx Closing$).
2. **Categorization Macro-F1**: Unweighted average F1-score across all 12 standard financial categories, testing merchant classification accuracy against true labels without class frequency bias.
3. **Anomaly Recall on Planted Events**: Ability to detect deliberate planted anomalies (duplicate charges, spending spikes, unusual outlays) without false verifications.
4. **80% Forecast Interval Coverage**: Percentage of actual daily balances residing within the Monte Carlo $p10-p90$ fan chart band over a 30-day walk-forward holdout. Target is $\ge 75\%$.
5. **Warning Lead Time**: Predictive runway (in days) between early crunch warning and the actual minimum cash trough.

## Hardware-Local Zero-Telemetry Proof
All evaluation passes completed **100% locally on host hardware** using SQLite in-memory databases, deterministic random seeds (42, 101, 303), and zero network calls.

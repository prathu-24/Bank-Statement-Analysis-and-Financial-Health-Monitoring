# FinSight Generalization Error Analysis (DEV Half)
*Protocol: Evaluated strictly on the first 50% temporal split (2024-01-01 to 2024-03-28, 40 transactions) of `demo_data/persona_unseen_held_out.csv`.*
*No code modifications were made prior to recording this baseline.*

---

## 1. Executive Summary

| Dataset Partition | Rows | Correct | Misclassified | Rule Accuracy |
| :--- | :---: | :---: | :---: | :---: |
| **DEV Half (Jan 1 – Mar 28, 2024)** | 40 | 27 | 13 | **67.5%** |
| **TEST Half (Mar 30 – Jun 30, 2024)** | 41 | *Sealed* | *Sealed* | *Sealed until Step 6* |

---

## 2. Top Misclassified Descriptions on DEV Half

| # | Date | Raw Statement Description | True Category | Predicted Category | Primary Failure Mode |
| :-: | :---: | :--- | :---: | :---: | :--- |
| 1 | 2024-01-02 | `UPI/THEOBROMA BANDRA/PASTRY ORDER` | Food & Dining | Transfers | UPI prefix caught by transfer rule; missing bakery merchant token |
| 2 | 2024-01-11 | `UPI/HALDIRAMS NAGPUR/DINNER` | Food & Dining | Transfers | UPI prefix default fallback before merchant match |
| 3 | 2024-01-13 | `NATURES BASKET KORAMANGALA/ORGANIC GROCERY` | Groceries | Shopping | "Basket" or generic store token routed to broad retail shopping |
| 4 | 2024-01-18 | `FASTAG RECHARGE IHMCL HIGHWAY` | Transport | Utilities & Bills | Keyword "recharge" captured by prepaid bill/utility rule |
| 5 | 2024-01-20 | `MAX HEALTHCARE SAKET/OPD CONSULTATION` | Healthcare | Uncategorized | "OPD" / "Consultation" absent from clinical keyword dictionaries |
| 6 | 2024-02-10 | `LE MARCHE GOURMET STORE/GROCERIES` | Groceries | Uncategorized | Gourmet brand name unseen; "Groceries" token missed by regex |
| 7 | 2024-02-14 | `NIC NATURAL ICE CREAM JUHU` | Food & Dining | Uncategorized | Regional dessert brand unseen in dictionary |
| 8 | 2024-02-20 | `RED_BUS INTERCITY VOLVO TICKET` | Transport | Uncategorized | Underscored delimiter `RED_BUS` and "Volvo" not covered in transport rules |
| 9 | 2024-02-27 | `OXFORD BOOK STORE KOLKATA/BOOKS` | Education | Uncategorized | "Book store" absent from academic education dictionary |
| 10 | 2024-03-02 | `UPI/THEOBROMA BANDRA/PASTRY ORDER` | Food & Dining | Transfers | Repeated UPI prefix default fallback |
| 11 | 2024-03-12 | `NATURES BASKET KORAMANGALA/ORGANIC GROCERY` | Groceries | Shopping | Generic retail shopping classification override |
| 12 | 2024-03-21 | `HAMLEYS TOYS STORE PHOENIX` | Shopping | Uncategorized | Toy brand store unrecognized |
| 13 | 2024-03-28 | `BRITISH COUNCIL LIBRARY ANNUAL PASS` | Education | Uncategorized | "Library annual pass" unindexed under educational rules |

---

## 3. Confusion Matrix (True Rows vs Predicted Columns)

```
True \ Pred             Education  Food & Di  Groceries  Healthcar  Housing &     Income   Shopping  Subscript  Transfers  Transport  Uncategor  Utilities
----------------------------------------------------------------------------------------------------------------------------------------------------------
Education                       1          0          0          0          0          0          0          0          0          0          2          0
Food & Dining                   0          3          0          0          0          0          0          0          3          0          1          0
Groceries                       0          0          0          0          0          0          2          0          0          0          1          0
Healthcare                      0          0          0          2          0          0          0          0          0          0          1          0
Housing & Rent                  0          0          0          0          3          0          0          0          0          0          0          0
Income                          0          0          0          0          0          3          0          0          0          0          0          0
Shopping                        0          0          0          0          0          0          3          0          0          0          1          0
Subscriptions                   0          0          0          0          0          0          0          3          0          0          0          0
Transfers                       0          0          0          0          0          0          0          0          0          0          0          0
Transport                       0          0          0          0          0          0          0          0          0          3          1          1
Uncategorized                   0          0          0          0          0          0          0          0          0          0          0          0
Utilities & Bills               0          0          0          0          0          0          0          0          0          0          0          6
```

---

## 4. Primary Failure Patterns

1. **Unseen Merchant / Brand Long-Tail (53.8% of errors - 7/13)**:
   - High-end grocery stores (`Le Marche`), regional sweet shops (`Haldirams`), niche dessert chains (`Theobroma`, `NIC Natural`), hospital OPD clinics (`Max Healthcare`), bookshops (`Oxford Book Store`), toy shops (`Hamleys`), and cultural institutions (`British Council Library`).
   - Pure regex keyword matching is inherently fragile against the combinatorial explosion of merchant branding across India.

2. **UPI Transfer False Positive Fallback (23.1% of errors - 3/13)**:
   - When merchant regex fails on a `UPI/...` narrative, the regex engine assigns `Transfers` as a catch-all rather than examining surrounding sub-tokens like `DINNER` or `PASTRY ORDER`.

3. **Keyword Overlap / Semantic Conflation (23.1% of errors - 3/13)**:
   - "FASTAG RECHARGE" matched `Utilities & Bills` because of the generic keyword "recharge".
   - "ORGANIC GROCERY" matched general `Shopping` rather than `Groceries`.

---

## 5. Architectural Solution for Phase 8.2

To resolve these failure modes without brittle hard-coded rule hacking:
- Maintain high-precision **Deterministic Rules First**.
- Implement an **Offline Char n-gram TF-IDF + Logistic Regression Classifier** as a fallback:
  - Sub-word character n-grams (e.g. `n_gram_range=(2, 5)`) naturally capture word fragments like `pastry`, `dinner`, `gourmet`, `fastag`, `bus`, `ticket`, `book`, `library`, `consultation`.
  - Trained on a strictly disjoint synthetic training corpus (disjoint from all `demo_data` files).
  - Fires **only** when rule confidence is low or returns `"Uncategorized – review"`.

# FinSight Cash-Flow Forecasting & Monte Carlo Simulation Methodology

## 1. Overview
FinSight provides a dual cash-flow forecasting engine:
1. **Deterministic Baseline Projection**: Linear daily cash burn aggregating verified closing balances, detected recurring obligations, and scheduled paydays.
2. **Probabilistic Monte Carlo Engine (2,000 paths)**: Empirical bootstrap simulation modeling liquidity trajectories under uncertainty, yielding calibrated confidence intervals ($p_{10}, p_{50}, p_{90}$) and pre-payday shortage probabilities.
3. **Rolling-Origin Walk-Forward Backtesting**: Empirical evaluation across multiple historical origins validating interval coverage against actual balances and benchmarking against a moving-average naive baseline.

---

## 2. Probabilistic Monte Carlo Formulation

### 2.1 State Vector & Daily Update Equation
Let $B_t^{(i)}$ denote the simulated account balance on day $t \in [1, D]$ for path $i \in [1, N]$ where $N = 2000$.

$$B_t^{(i)} = B_{t-1}^{(i)} + I_t^{(i)} - R_t^{(i)} - D_t^{(i)}$$

Where:
- $B_0^{(i)} = B_{\text{current}}$ (verified reconciled ledger closing balance).
- $I_t^{(i)}$: Stochastic income inflow on day $t$.
- $R_t^{(i)}$: Stochastic scheduled recurring commitments on day $t$.
- $D_t^{(i)}$: Bootstrapped daily discretionary outlays sampled according to weekday.

### 2.2 Weekday-Stratified Discretionary Spend Bootstrap
Discretionary expenditures exhibit strong intra-week seasonality (e.g. higher spending on Fridays and Saturdays in Indian urban contexts). Historical non-recurring debits are grouped into pools:

$$\mathcal{S}_w = \{ d_{\tau} \mid \text{weekday}(\tau) = w \}, \quad w \in \{0, \dots, 6\}$$

On day $t$ with weekday $w(t)$, $D_t^{(i)}$ is drawn with replacement:

$$D_t^{(i)} \sim \text{Uniform}(\mathcal{S}_{w(t)})$$

If $|\mathcal{S}_w| < 3$, the engine falls back to the pooled all-day discretionary distribution.

### 2.3 Recurring Payment Modeling with Date Jitter
Recurring payments (EMIs, SIPs, rent, subscriptions) detected by `RecurringPaymentDetector` are mapped to expected dates with execution jitter:

$$t_{\text{execution}} = t_{\text{nominal}} + \delta, \quad \delta \in \{-2, -1, 0, 1, 2\} \text{ with uniform probability}$$

Amount variance is modeled with normal perturbation clipped to $\pm 15\%$:

$$A_{\text{sim}} \sim \text{Clip}(\mathcal{N}(\mu_A, 0.04 \mu_A), 0.85 \mu_A, 1.15 \mu_A)$$

### 2.4 Recurrence-Based Income & Payday Delay Probability
Income is detected using cadence clustering (credits within 15% amount tolerance occurring at ~30-day intervals). Empirical payday delay probability $p_{\text{delay}}$ is estimated from historical credit timestamps. On expected payday:
- Arrives on nominal date with probability $1 - p_{\text{delay}}$.
- Delayed by 1 to 2 days with probability $p_{\text{delay}}$ (reflecting bank holidays or employer payroll processing batches).

---

## 3. Mathematical Monotonicity: Guaranteed $p_{10} \le p_{50} \le p_{90}$

Daily distribution quantiles are computed across all $N$ simulation paths:

$$q_p(t) = \text{Quantile}_p(\{ B_t^{(i)} \}_{i=1}^N)$$

To eliminate any numerical floating-point anomalies or inversion artifacts, strict monotonic order is enforced:

$$p_{10}(t) \leftarrow \min(p_{10}(t), p_{50}(t))$$
$$p_{90}(t) \leftarrow \max(p_{90}(t), p_{50}(t))$$

By construction:
$$\forall t: \quad p_{10}(t) \le p_{50}(t) \le p_{90}(t)$$

---

## 4. Limited History Guardrails (< 90 Days)

When a bank statement spans fewer than 90 days (< 3 months):
1. **Uncertainty Expansion**: Because small sample sizes fail to observe quarterly or seasonal expenditure variations, prediction intervals $[p_{10}, p_{90}]$ are artificially widened by 35% around the median:
   $$p_{10}^{\text{widened}} = p_{50} - 1.35 \times (p_{50} - p_{10})$$
   $$p_{90}^{\text{widened}} = p_{50} + 1.35 \times (p_{90} - p_{50})$$
2. **`low_confidence` Flag**: The API returns `"low_confidence": true` alongside an explanation string.
3. **UI Warning Badge**: The Forecast dashboard renders an amber `Low confidence (< 3 mo history)` badge to alert the user.

---

## 5. Rolling-Origin Walk-Forward Backtesting

### 5.1 Multi-Origin Methodology
Rather than relying on a single arbitrary 30-day holdout, FinSight implements rolling-origin evaluation (expanding window) across multiple historical cutoff dates:

$$\mathcal{C} = \{ C_1, C_2, C_3 \}$$

For each cutoff $C_k$:
- **Training Set**: All transactions on or before $C_k$.
- **Evaluation Window**: $[C_k + 1, C_k + H]$ where $H$ is the forecast horizon.
- **Monte Carlo Forecast**: Runs using training history only.

### 5.2 Metrics Evaluated
1. **Empirical Interval Coverage (Target: 80%)**:
   $$\text{Coverage} = \frac{1}{|\mathcal{T}|} \sum_{t \in \mathcal{T}} \mathbf{1}_{\{ p_{10}(t) \le B_t^{\text{actual}} \le p_{90}(t) \}}$$
2. **Mean Absolute Error (MAE)**:
   $$\text{MAE}_{\text{model}} = \frac{1}{|\mathcal{T}|} \sum_{t \in \mathcal{T}} |B_t^{\text{actual}} - p_{50}(t)|$$
3. **Naive Moving-Average Baseline**:
   A benchmark model that extrapolates the 30-day trailing net daily burn from the balance at $C_k$:
   $$\hat{B}_{\text{naive}}(t) = B_{C_k} + (t - C_k) \cdot \Delta_{\text{net}}$$
   $$\text{MAE}_{\text{naive}} = \frac{1}{|\mathcal{T}|} \sum_{t \in \mathcal{T}} |B_t^{\text{actual}} - \hat{B}_{\text{naive}}(t)|$$
4. **Relative Improvement**:
   $$\text{Improvement} = \frac{\text{MAE}_{\text{naive}} - \text{MAE}_{\text{model}}}{\text{MAE}_{\text{naive}}} \times 100\%$$

---

## 6. Assumptions and Limitations

| Assumption | Description | Failure Mode / Boundary Condition |
| :--- | :--- | :--- |
| **Ergodicity** | Past spending patterns reflect future behavior over the next 30 days. | Major life events, medical emergencies, sudden employment changes break this assumption. |
| **Recurring Cadence** | Fixed expenses recur with a predictable periodicity ($\pm 2$ days). | Discretionary lump-sum payments or irregular quarterly insurance premiums may not be captured. |
| **Single Account Context** | Predictions assume transactions occur primarily from the uploaded account. | Out-of-band transfers between personal accounts can artificially distort discretionary burn. |
| **No Credit Card Integration** | Only bank statement debit/credit flows are visible. | If a user shifts spending from debit cards to external credit cards, bank burn appears artificially low until payment date. |

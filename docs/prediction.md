# Predictive Inference & Historical Analogue Methodology

## 1. Historical Analogue Engine

The historical analogue module scans accumulated historical observations for each equity to identify past trading days with matching technical, volume, and volatility characteristics.

### Matching Criteria
An observation on historical date $T_{hist}$ is considered an analogue to the current market state $T_{curr}$ if:

$$|\text{RSI}_{14}(T_{hist}) - \text{RSI}_{14}(T_{curr})| \le 7.0$$
$$|\text{Volatility}_{20d}(T_{hist}) - \text{Volatility}_{20d}(T_{curr})| \le 0.08$$
$$|\text{RelVolume}(T_{hist}) - \text{RelVolume}(T_{curr})| \le 0.5$$

If fewer than 3 historical matches are found, criteria windows automatically expand to capture empirical setup distributions.

### Empirical Forward Return Statistics
For all identified analogue instances, forward price returns are calculated across five prediction horizons ($h \in \{1, 3, 5, 10, 20\}$):

$$\text{Forward Return}_h = \frac{P_{T_{hist}+h} - P_{T_{hist}}}{P_{T_{hist}}}$$

The engine records:
- **Observation Count ($N$)**
- **Mean & Median Forward Return (%)**
- **Win Probability** ($P(\text{Return}_h > 0)$)
- **Loss Probability** ($P(\text{Return}_h < 0)$)
- **Maximum Gain & Maximum Drawdown observed**
- **Forward Volatility (Standard Deviation)**

---

## 2. Machine Learning Predictive Engine & Anti-Lookahead Safeguards

### Anti-Lookahead Bias Prevention
When building feature matrices for machine learning model training:
1. All feature inputs for row date $T$ (e.g. `rsi_14`, `volatility_20d`, `distance_from_52w_high`, `market_return_1d`) use strictly data available on or before date $T$.
2. Target variables $y_{T, h}$ represent future returns calculated using backward shifts ($T+h$ close prices):

$$y_{T, h} = \begin{cases} 1 & \text{if } P_{T+h} > P_T \\ 0 & \text{otherwise} \end{cases}$$

This ensures that models trained on $y_{T, h}$ never inadvertently access future price information during feature construction.

### Model Evaluation Scheme
- **Walk-Forward Time-Series Split:** Data is partitioned strictly along temporal lines (e.g., 80% initial chronological split for training, subsequent 20% for out-of-sample evaluation). Random shuffling is explicitly prohibited.
- **Base Classifier:** Random Forest Classifiers ($N=50$, max depth=4) trained on walk-forward partitions to generate calibrated directional probabilities $P(\text{Up}_h)$.

### Probability to Directional Bias Mapping
- **Bullish:** $P(\text{Up}) \ge 0.65$
- **Slightly Bullish:** $0.55 \le P(\text{Up}) < 0.65$
- **Neutral:** $0.45 < P(\text{Up}) < 0.55$
- **Slightly Bearish:** $0.35 < P(\text{Up}) \le 0.45$
- **Bearish:** $P(\text{Up}) \le 0.35$

Confidence scores (0–100) scale proportionally with $|P(\text{Up}) - 0.50|$.

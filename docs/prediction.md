# Prediction & Machine Learning Research Methodology

## Historical Analogue Pattern Matching

The historical analogue finder identifies historical setups that closely match a stock's current technical state based on:
1. RSI similarity ($\pm 7.5$ points).
2. Annualized volatility similarity ($\pm 25\%$).
3. Moving average alignment relative to 20, 50, and 200 DMAs.

### Empirical Forward Returns
For each identified historical analogue match $i$, forward price trajectories are evaluated over horizons $h \in \{1, 3, 5, 10, 20\}$ trading days:

$$\text{Return}_{i, h} = \frac{P_{i+h} - P_i}{P_i} \times 100$$

Summary statistics are stored:
- Sample match count $N$
- Average & median forward returns
- Empirical win rate ($\%$ of historical instances with positive returns)
- Loss rate
- Maximum historical gain and loss observed

## Prevention of Look-Ahead Bias

1. **Point-in-Time Feature Construction:** Features at date $T$ strictly use observations $\le T$.
2. **Forward Target Alignment:** Target columns `future_return_1d` through `future_return_20d` are strictly shifted forward relative to date $T$.
3. **Analogue Search Constraint:** Historical matches are searched strictly prior to $T - \max(h)$ bars.

## Baseline Probabilistic Prediction Models

The system evaluates directional signals using:
- **Logistic Regression Classifier**
- **Random Forest Classifier**

### Validation Strategy
Model performance is evaluated using **`TimeSeriesSplit` walk-forward cross-validation** (5 temporal splits) to ensure test samples always follow training samples chronologically. Temporal financial data is **never randomly shuffled**.

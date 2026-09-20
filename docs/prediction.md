# Prediction Methodology & Preventing Look-Ahead Bias

## Historical Analogue Pattern Engine

The analogue matching engine identifies historical situations in a stock's past trading history that closely mirror the current technical state.

### Distance Metric
Euclidean similarity score computed on:
1. RSI 14
2. 20-Day Annualized Volatility
3. Distance (%) from 20-Day Simple Moving Average

For top $N$ matching historical dates $T_{hist}$, the forward return distributions across 1, 3, 5, 10, and 20 trading days are calculated:
- Mean and Median Forward Return
- Win Rate (% positive returns)
- Maximum Observed Gain & Maximum Observed Loss
- Forward Volatility

---

## Machine Learning Signal Layer

Predictive models generate probabilistic directional signals ($P(Up)$) across 1D, 3D, 5D, 10D, and 20D horizons.

### Strict Prevention of Look-Ahead Bias & Temporal Leakage

1. **Point-In-Time Features**: Features for date $T$ strictly use information available up to market close on date $T$.
2. **Forward Target Variables**: Target variables `future_return_Kd` for date $T$ are calculated using close prices from date $T+K$. Target column values for the most recent $K$ dates are marked as `NaN` during inference.
3. **Walk-Forward Time Splits**: Training and testing sets are strictly separated chronologically (e.g. initial 70% historical dates for training, subsequent 30% for out-of-sample evaluation). **Data is never randomly shuffled**.

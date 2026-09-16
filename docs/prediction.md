# Predictive Modeling & Historical Analogue Methodology

## Historical Analogue Pattern Matching

The system identifies historical market setups that closely resemble the stock's current state based on key technical features:
- RSI-14 proximity (within $\pm 7$ points)
- 20-day annualized volatility proximity (within $\pm 5\%$)
- Relative volume level

For each matched historical instance, the system tracks forward price movement over multiple horizons:
- **1 Trading Day (1D)**
- **3 Trading Days (3D)**
- **5 Trading Days (5D)**
- **10 Trading Days (10D)**
- **20 Trading Days (20D)**

### Empirical Probability Metrics Calculated
- **Observations Count**: Number of matching historical setups identified.
- **Mean & Median Forward Returns**: Expected directional return magnitude.
- **Win / Loss Probability**: Percentage of positive vs. negative forward returns.
- **Max Observed Gain / Loss**: Historical empirical boundary extremes.
- **Forward Volatility**: Standard deviation of historical forward returns.

Directional bias labels (Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish) and confidence ratings (0–100) are assigned dynamically based on win probabilities and mean returns.

---

## Prevention of Look-Ahead Bias / Data Leakage

To guarantee that ML datasets are suitable for valid empirical research and training:

1. **Feature Alignment**:
   Features for row $T$ (e.g., `rsi_14`, `sma_20`, `volatility_20d`, `market_return_1d`) strictly utilize market observations available **on or before date $T$**.

2. **Target Alignment**:
   Target columns (e.g., `future_return_1d`, `future_return_5d`) compute forward percentage returns:
   $$\text{future\_return\_5d}(T) = \frac{Close(T + 5) - Close(T)}{Close(T)}$$
   Target columns are computed exclusively as training labels and are never passed as inputs to feature matrices during training or inference.

3. **Validation Strategy**:
   Models are evaluated using **Walk-Forward Time-Series Validation**. Random temporal shuffling (e.g. standard K-Fold CV) is strictly prohibited to prevent data leakage across time.

# Prediction & Pattern Matching Methodology

## Historical Pattern Matching

The `HistoricalAnalogueFinder` searches the accumulated historical database for days where:
- RSI 14 was within ±7.5 points of today's RSI.
- 20-day annualized volatility was within ±25% of today's volatility.
- Price relation to the 20-day SMA matches today's relation (above/below).

### Empirical Forward Returns
For all matching historical days, forward close prices over 1, 3, 5, 10, and 20 trading days are retrieved to calculate:
- Sample size
- Average and median forward return
- Positive and negative return probability
- Max gain and max loss
- Forward return volatility

## Machine Learning & Look-Ahead Prevention

### Strict Feature Alignment
For any trading date $T$:
- Features $X_T$ use only price, volume, and indicator information available on or before date $T$.
- Target variables $Y_T$ (e.g., `future_return_5d`) are constructed by looking forward to $T + 5$, and are kept strictly isolated from feature matrices during prediction time.

### Model Design
- **Algorithms:** Random Forest Classifier & Historical Conditional Probability models.
- **Validation Scheme:** Time-Series Walk-Forward Split (80% historical train, 20% recent test) without shuffling.

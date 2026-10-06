# Analysis Methodology

## Technical Indicator Calculations

- **Simple Moving Average (SMA)**: Unweighted mean of closing prices over lookback period $N$.
- **Exponential Moving Average (EMA)**: Exponentially weighted average with smoothing multiplier $\alpha = \frac{2}{N + 1}$.
- **Relative Index (RSI 14)**: Ratio of average upward price changes to average downward price changes over 14 periods.
- **MACD**: $EMA_{12} - EMA_{26}$, Signal line = $EMA_9(MACD)$, Histogram = $MACD - Signal$.
- **Average True Range (ATR 14)**: 14-period moving average of True Range $TR = \max(H - L, |H - C_{prev}|, |L - C_{prev}|)$.
- **Relative Volume (RVOL)**: Daily Volume divided by 20-day Volume SMA.

## Composite Scoring Engine

Scoring weights:
- Technical Trend: 25%
- Momentum: 20%
- Volume: 15%
- Relative Strength vs NIFTY: 15%
- Volatility: 10%
- Market Regime: 10%
- Fundamentals: 5%

Normalized Score Ranges:
- 80–100: Very Strong
- 65–79: Strong
- 50–64: Neutral
- 35–49: Weak
- 0–34: Very Weak

## Historical Pattern Matching

The `PatternAnalogueFinder` projects current stock features (RSI, distance from SMA 20, relative volume, 5-day returns, volatility) into Euclidean feature space and identifies the top $K$ historical trading days with highest setup similarity. Forward returns over 1, 3, 5, 10, and 20 days are empirically computed across these analogues.

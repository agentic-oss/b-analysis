# Indicator, Scoring & Market Regime Methodology

## 1. Technical Indicators

- **Simple Moving Average (SMA)**: Unweighted average price over window $N$:
  $$\text{SMA}_N = \frac{1}{N} \sum_{i=0}^{N-1} P_{t-i}$$
- **Exponential Moving Average (EMA)**: Exponentially weighted average with multiplier $\alpha = \frac{2}{N+1}$:
  $$\text{EMA}_t = P_t \cdot \alpha + \text{EMA}_{t-1} \cdot (1 - \alpha)$$
- **Relative Strength Index (RSI 14)**:
  $$\text{RS} = \frac{\text{EMA}(\text{Gain}, 14)}{\text{EMA}(\text{Loss}, 14)}, \quad \text{RSI} = 100 - \frac{100}{1 + \text{RS}}$$
- **MACD**: Difference between 12-period EMA and 26-period EMA. Signal line is 9-period EMA of MACD.
- **Average True Range (ATR 14)**: Moving average of True Range $TR = \max(H-L, |H-C_{prev}|, |L-C_{prev}|)$.
- **Annualized Historical Volatility**: Standard deviation of 20-day daily log returns scaled by $\sqrt{252} \times 100$.

## 2. Market Regime Classification

Market regime is calculated using a rule-based composite framework (0-100 points):
- **NIFTY Trend (0-30 pts)**: Price position relative to 20, 50, and 200 DMAs.
- **Bank NIFTY Trend (0-15 pts)**: Financial sector strength.
- **Market Breadth (0-25 pts)**: Percentage of stocks trading above 50 DMA.
- **Advance/Decline Ratio (0-15 pts)**: Ratio of advancing vs declining stocks.
- **Volatility Regime (0-15 pts)**: Low/Normal volatility rewards points, Extreme volatility penalizes.

Regime Labels:
- **80-100**: Strong Bullish
- **60-79**: Bullish
- **40-59**: Neutral
- **20-39**: Bearish
- **0-19**: Strong Bearish

## 3. Composite Stock Scoring System

Composite ratings (0-100) aggregate 8 transparent sub-component scores:
- **Trend Score (20-25%)**: Alignment across SMA 20, 50, 200, and EMA 20.
- **Momentum Score (15-20%)**: RSI location (50-70 ideal), MACD histogram sign, ROC 12.
- **Volume Score (10-15%)**: Relative volume vs 20-day SMA and volume change.
- **Relative Strength Score (15%)**: Excess performance relative to NIFTY.
- **Volatility Score (10%)**: Volatility regime penalty/reward.
- **Market Regime Score (10%)**: Broad market tailwind.
- **Sector Score (5%)**: Sector momentum rank.
- **Fundamental Score (15% if available)**: ROE, Debt/Equity, P/E, revenue growth.

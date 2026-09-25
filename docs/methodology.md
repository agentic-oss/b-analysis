# Methodology & Technical Indicator Formulations

## Technical Indicators

### Trend Indicators
- **Simple Moving Average (SMA):** Unweighted mean of closing prices over $N$ periods ($N \in \{5, 10, 20, 50, 100, 200\}$).
- **Exponential Moving Average (EMA):** Exponentially weighted moving average ($N \in \{9, 20, 50, 200\}$).
- **Golden / Death Cross:** Triggered when SMA 50 crosses above (Golden) or below (Death) SMA 200.

### Momentum Indicators
- **Relative Strength Index (RSI 14):** Wilder's RSI calculated over 14 bars.
- **Stochastic RSI:**
  $$\text{Stoch RSI} = \frac{\text{RSI}_{14} - \min(\text{RSI}_{14})}{\max(\text{RSI}_{14}) - \min(\text{RSI}_{14})} \times 100$$
- **MACD (12, 26, 9):**
  $$\text{MACD Line} = \text{EMA}_{12}(\text{Close}) - \text{EMA}_{26}(\text{Close})$$
  $$\text{Signal Line} = \text{EMA}_9(\text{MACD Line})$$
  $$\text{Histogram} = \text{MACD Line} - \text{Signal Line}$$

### Volatility Indicators
- **Average True Range (ATR 14):** Wilders' 14-period average of True Range ($\max(H-L, |H-C_{prev}|, |L-C_{prev}|)$).
- **Historical Volatility:** Annualized 20-day standard deviation of logarithmic daily returns:
  $$\sigma_{ann} = \text{std}(\ln(C_t / C_{t-1})) \times \sqrt{252} \times 100$$
- **Bollinger Bands (20, 2.0):** Upper and Lower bands set 2 standard deviations away from 20-day SMA.

## Stock Composite Scoring Methodology

The overall score (0–100) is calculated as a weighted average of 8 transparent sub-components:

| Component | Default Weight | Key Rules / Signals |
| --- | --- | --- |
| Technical Trend | 25% | Price vs SMA 20/50/200, Golden Cross, Breakouts |
| Momentum | 20% | RSI (50–70 sweet spot), MACD histogram sign, Stoch RSI |
| Volume | 15% | Relative volume vs 20-day average, volume surge |
| Relative Strength | 15% | 20-day excess return over NIFTY 50 index |
| Volatility | 10% | Volatility regime (Low = 70, High = 30) |
| Market Regime | 10% | Overall market-wide breadth & regime score |
| Fundamentals | 5% | ROE, Debt/Equity, Profit Growth, Net Margins |

Score Tiers:
- **80–100:** Very Strong
- **65–79:** Strong
- **50–64:** Neutral
- **35–49:** Weak
- **0–34:** Very Weak

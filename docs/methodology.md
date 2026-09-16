# Methodology Documentation

## Technical Analysis Methodology

All technical indicator calculations are deterministic, reproducible, and computed on sorted chronological daily price series:

- **Simple Moving Averages (SMA)**: Computed for periods 5, 10, 20, 50, 100, and 200.
  $$SMA_p(t) = \frac{1}{p} \sum_{i=0}^{p-1} Close(t-i)$$
- **Exponential Moving Averages (EMA)**: Computed for periods 9, 20, 50, and 200.
  $$EMA_p(t) = Close(t) \cdot \alpha + EMA_p(t-1) \cdot (1 - \alpha), \quad \alpha = \frac{2}{p + 1}$$
- **Relative Strength Index (RSI-14)**:
  $$RS = \frac{\text{Average Gain over 14 periods}}{\text{Average Loss over 14 periods}}, \quad RSI = 100 - \frac{100}{1 + RS}$$
- **Stochastic RSI (14)**:
  $$StochRSI = \frac{RSI_{14} - \min(RSI_{14}, 14)}{\max(RSI_{14}, 14) - \min(RSI_{14}, 14)}$$
- **MACD (12, 26, 9)**:
  $$MACD = EMA_{12}(Close) - EMA_{26}(Close), \quad Signal = EMA_9(MACD), \quad Hist = MACD - Signal$$
- **Average True Range (ATR-14)**:
  $$TR = \max(High - Low, |High - Close_{t-1}|, |Low - Close_{t-1}|), \quad ATR_{14} = \text{Rolling 14-day mean}(TR)$$
- **Historical Volatility (20d)**: Annualized log return standard deviation.
  $$\sigma_{20d} = \text{StdDev}(\ln(Close_t / Close_{t-1}))_{20d} \times \sqrt{252}$$
- **Bollinger Bands (20, 2)**:
  $$Upper = SMA_{20} + (2 \times \sigma_{20d}), \quad Lower = SMA_{20} - (2 \times \sigma_{20d})$$

---

## Market Regime Classification Framework

Evaluates NIFTY 50 price alignment with moving averages, Bank NIFTY trend, advance/decline ratio, and market breadth (% stocks > 20/50/200 DMA).

| Market Regime | Classification Rule Criteria | Score Base |
|---------------|------------------------------|------------|
| **Strong Bullish** | NIFTY > 20, 50 & 200 DMA + Breadth > 60% above 50 DMA + AD Ratio > 1.2 | 90 / 100 |
| **Bullish** | NIFTY > 50 DMA + Market Breadth > 50% above 50 DMA | 70 / 100 |
| **Neutral** | Mixed DMA positioning or breadth between 40% - 60% | 50 / 100 |
| **Bearish** | NIFTY < 50 DMA or Market Breadth < 40% above 50 DMA | 30 / 100 |
| **Strong Bearish** | NIFTY < 20, 50 & 200 DMA + Breadth < 30% above 50 DMA + AD Ratio < 0.7 | 10 / 100 |

---

## Composite Stock Scoring Methodology

Scores every stock from 0 to 100 based on eight weighted component scores:

1. **Technical Trend Score (25% Weight)**: Evaluates close price above 20, 50, and 200 DMAs.
2. **Momentum Score (20% Weight)**: Combines RSI-14 and 5-day / 20-day returns.
3. **Volume Score (15% Weight)**: Evaluates relative volume vs 20-day SMA volume.
4. **Relative Strength Score (15% Weight)**: Evaluates 5-day return differential against NIFTY 50.
5. **Volatility Score (10% Weight)**: Prefers lower/stable historical volatility.
6. **Market Regime Score (5% Weight)**: Inherits current market regime score.
7. **Sector Score (5% Weight)**: Evaluates sector momentum score.
8. **Fundamental Score (5% Weight)**: Evaluates PE, PB, ROE, Debt/Equity, margins, and growth.

### Composite Score Labels
- **80 – 100**: Very Strong
- **65 – 79**: Strong
- **50 – 64**: Neutral
- **35 – 49**: Weak
- **0 – 34**: Very Weak

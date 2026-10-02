# Analytical Methodology & Technical Indicator Specifications

## Technical Indicator Formulas

1. **Simple Moving Average (SMA)**:
   $$SMA_n = \frac{1}{n} \sum_{i=0}^{n-1} Close_{t-i}$$

2. **Exponential Moving Average (EMA)**:
   $$EMA_t = Close_t \times \alpha + EMA_{t-1} \times (1 - \alpha), \quad \alpha = \frac{2}{N+1}$$

3. **Relative Strength Index (RSI 14)**:
   $$RS = \frac{Average Gain_{14}}{Average Loss_{14}}, \quad RSI = 100 - \frac{100}{1 + RS}$$

4. **MACD**:
   $$MACD = EMA_{12}(Close) - EMA_{26}(Close), \quad Signal = EMA_9(MACD)$$

5. **Historical Volatility (20-Day Annualized)**:
   $$\sigma_{20d} = \text{StdDev}(\ln(Close_t / Close_{t-1})) \times \sqrt{252}$$

---

## Composite Stock Scoring Methodology (0 - 100)

Stock composite scores are calculated transparently using weighted component scores:

| Component | Weight | Key Metrics Evaluated |
| --- | --- | --- |
| **Technical Trend** | 25% | Price relative to 20, 50, 200 DMAs and moving average alignment. |
| **Momentum** | 20% | RSI 14 in optimal range (50-70), MACD histogram sign, ROC 12. |
| **Volume** | 15% | Relative volume spike (> 1.5x) accompanied by positive 1D price return. |
| **Relative Strength** | 15% | Excess daily return over benchmark NIFTY 50 return. |
| **Market Regime** | 10% | Overall market environment classification (Strong Bullish to Strong Bearish). |
| **Sector Score** | 10% | Sector relative strength and sector momentum rank. |
| **Fundamental Score**| 5% | Valuation (PE), profitability (ROE), balance sheet health (Debt/Equity). |

### Score Categories
- **80 – 100**: Very Strong
- **65 – 79**: Strong
- **50 – 64**: Neutral
- **35 – 49**: Weak
- **0 – 34**: Very Weak

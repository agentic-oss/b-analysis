# Methodology Guide: Market Regime & Stock Scoring

## 1. Market Regime Classification Methodology

Market regime classification evaluates overall market health and directional environment using NIFTY moving averages and market breadth indicators across the tracked stock universe.

### Rules Matrix:
1. **Strong Bullish**:
   - NIFTY Close > 50 DMA and 200 DMA
   - NIFTY 20 DMA > 50 DMA
   - Market Breadth (% of stocks above 50 DMA) >= 70%
2. **Bullish**:
   - NIFTY Close > 50 DMA
   - Market Breadth (% of stocks above 50 DMA) >= 50%
3. **Neutral**:
   - Mixed moving average alignment or Breadth between 40% and 50%
4. **Bearish**:
   - NIFTY Close < 50 DMA
   - Market Breadth (% of stocks above 50 DMA) < 40%
5. **Strong Bearish**:
   - NIFTY Close < 50 DMA and 200 DMA
   - NIFTY 20 DMA < 50 DMA
   - Market Breadth (% of stocks above 50 DMA) < 30%

---

## 2. Stock Composite Scoring Methodology

Each stock receives a 0–100 normalized composite score computed from individual transparent sub-scores:

```
Composite Score = Sum(Sub_Score_i * Weight_i)
```

### Sub-Score Component Weights:
- **Technical Trend Score (25%)**: Evaluates close price relative to 20 DMA, 50 DMA, and 200 DMA.
- **Momentum Score (20%)**: Evaluates RSI 14 and MACD histogram momentum.
- **Volume Score (15%)**: Evaluates relative volume (>1.2x) on up days versus down days.
- **Relative Strength Score (15%)**: Evaluates stock 1D return relative to NIFTY 50 1D return.
- **Volatility Score (10%)**: Evaluates 20-day annualized historical volatility regime.
- **Market Regime Score (10%)**: Contribution based on overall market classification.
- **Fundamental Score (5%)**: Evaluates valuation (P/E, P/B), profitability (ROE, Margins), and solvency (Debt/Equity).

### Composite Score Labels:
- **80 – 100**: Very Strong
- **65 – 79**: Strong
- **50 – 64**: Neutral
- **35 – 49**: Weak
- **0 – 34**: Very Weak

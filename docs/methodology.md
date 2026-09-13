# Analytics & Scoring Methodology

## 1. Indicator Calculations
- **Trend:** Simple Moving Averages (5, 10, 20, 50, 100, 200) and Exponential Moving Averages (9, 20, 50, 200).
- **Momentum:** RSI 14 (EMA smoothed), Stochastic RSI 14, MACD (12, 26, 9), Rate of Change 10.
- **Volatility:** Average True Range 14 (incorporating price gaps), 20-day annualized historical volatility, Bollinger Bands (20-period SMA +/- 2.0 std).
- **Volume:** Relative Volume (RVOL = Volume / 20-day Volume SMA), On Balance Volume (OBV), Accumulation/Distribution Line.

## 2. Market Regime Rules
Transparent rule-based environment classification:
- **Strong Bullish:** NIFTY > 20, 50, 200 DMA and Universe Breadth (% > 50 DMA) >= 70%.
- **Bullish:** NIFTY > 50 DMA and Breadth >= 50%.
- **Neutral:** Mixed indicator signals or Breadth between 40% and 50%.
- **Bearish:** NIFTY < 50 DMA and Breadth <= 40%.
- **Strong Bearish:** NIFTY < 20, 50, 200 DMA and Breadth <= 30%.

## 3. Stock Composite Scoring
Scores are calculated on a 0–100 scale using transparent weights:
- **Technical Trend (25%):** Count of price above key moving averages.
- **Momentum (20%):** Weighted combination of RSI, MACD histogram sign, and 10-day ROC.
- **Volume (15%):** Relative volume intensity relative to 20-day baseline.
- **Relative Strength (15%):** Outperformance differential vs NIFTY 50 benchmark.
- **Market Regime (10%):** Regime factor score.
- **Sector Score (10%):** Sector rank and momentum.
- **Fundamental Score (5%):** Optional score based on ROE, P/E ratio, and Debt/Equity.

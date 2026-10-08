# Methodology & Scoring Framework

## 1. Indicator Calculation Methodology
- **SMA/EMA:** Moving averages calculated across [5, 10, 20, 50, 100, 200] and [9, 20, 50, 200].
- **RSI (14):** Relative Strength Index using standard rolling average gain/loss over 14 trading days.
- **MACD:** Fast EMA (12), Slow EMA (26), Signal EMA (9).
- **ATR (14):** Average True Range over 14 days.
- **Bollinger Bands:** SMA(20) +/- 2 StdDev(20).
- **OBV & A/D Line:** On-Balance Volume and Accumulation/Distribution Line.

## 2. Market Regime Classification Rules
Analyzes NIFTY 50 trend, Bank NIFTY trend, % of stocks above 20, 50, 200 DMA, advance/decline ratio, and new highs/lows.
- **Strong Bullish:** Score >= +4
- **Bullish:** Score >= +2
- **Neutral:** -1 <= Score <= +1
- **Bearish:** Score <= -2
- **Strong Bearish:** Score <= -4

## 3. Stock Scoring Methodology (0–100)
Composite score based on:
- Technical Trend (35%)
- Momentum (25%)
- Volume (15%)
- Relative Strength (15%)
- Market & Sector Context (10%)

# Methodology Documentation

## Technical Indicators

1. **Simple Moving Averages (SMA):** 5, 10, 20, 50, 100, and 200 periods.
2. **Exponential Moving Averages (EMA):** 9, 20, 50, and 200 periods.
3. **RSI (14):** Relative Strength Index calculated using standard rolling average of positive/negative close deltas.
4. **Stochastic RSI (14):** Standardized RSI range calculation over 14 periods with 3-period smoothing (%K, %D).
5. **MACD:** 12-day EMA minus 26-day EMA with 9-day signal EMA and histogram.
6. **Average True Range (ATR 14):** Rolling maximum of High-Low, |High - Prev Close|, |Low - Prev Close|.
7. **Bollinger Bands:** 20-day SMA with 2 standard deviation upper/lower bands.

## Market Regime Framework

Rule-based framework combining multiple market signals into a score from -100 to +100:
- **NIFTY vs 200 DMA:** +30 / -30
- **NIFTY vs 50 DMA:** +20 / -20
- **Universe Breadth (>50 DMA %):** >60% (+25), <40% (-25)
- **Advance/Decline Ratio:** >= 1.5 (+15), <= 0.67 (-15)
- **Bank NIFTY Trend:** Bullish (+10), Bearish (-10)

### Categories
- **80 to 100:** Strong Bullish
- **20 to 79:** Bullish
- **-19 to 19:** Neutral
- **-79 to -20:** Bearish
- **-100 to -80:** Strong Bearish

## Stock Composite Scoring (0–100)

Weighted average of individual component scores:
- **Technical Trend:** 25%
- **Momentum:** 25%
- **Volume:** 15%
- **Relative Strength:** 15%
- **Volatility:** 10%
- **Market Regime:** 10%

### Label Mappings
- **80 – 100:** Very Strong
- **65 – 79:** Strong
- **50 – 64:** Neutral
- **35 – 49:** Weak
- **0 – 34:** Very Weak

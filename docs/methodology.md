# Methodology & Scoring Framework

## Technical Indicators
All indicators are calculated deterministically:
- **Moving Averages:** Simple Moving Average (SMA) and Exponential Moving Average (EMA).
- **RSI (14):** Relative Strength Index using 14-period average gain/loss.
- **MACD (12, 26, 9):** Fast EMA (12) minus Slow EMA (26), Signal Line = EMA (9) of MACD.
- **ATR (14):** Average True Range computed over 14 trading days.
- **Volatility (20d):** Annualized standard deviation of daily log returns over rolling 20 days ($ \sigma \times \sqrt{252} $).

## Market Regime Framework
Combines benchmark (NIFTY 50) trend position against moving averages and overall universe market breadth (% stocks above 20/50/200 DMA and Advance/Decline ratio).
Classification rules:
- **Strong Bullish (80–100):** Benchmark in strong uptrend + market breadth > 70%.
- **Bullish (62.5–79.9):** Benchmark > 50DMA & 200DMA + breadth > 50%.
- **Neutral (37.5–62.4):** Mixed moving average alignment / sideways trend.
- **Bearish (20.0–37.4):** Benchmark < 50DMA & 200DMA + breadth < 40%.
- **Strong Bearish (0.0–19.9):** Benchmark in strong downtrend + market breadth < 30%.

## Stock Scoring Framework
Composite score (0–100) constructed from weighted component scores:
- **Technical Trend Score (25%):** Price relative to 20, 50, 200 DMAs and 50/200 cross.
- **Momentum Score (20%):** RSI reading and MACD histogram momentum.
- **Volume Score (15%):** Relative volume vs 20-day average.
- **Relative Strength Score (15%):** 20-day return magnitude vs market.
- **Volatility Score (10%):** Lower volatility rewarded with higher stability score.
- **Market Regime Score (10%):** Overall market macro regime score.
- **Sector Score (5%):** Underlying sector index momentum score.

Score Labels:
- `80 - 100`: Very Strong
- `65 - 79`: Strong
- `50 - 64`: Neutral
- `35 - 49`: Weak
- `0 - 34`: Very Weak

## Historical Analogue Engine
Search engine identifies past historical days for the same stock having similar RSI (+/- 7.5 points) and 50 DMA distance (+/- 5%).
Computes empirical conditional distribution of subsequent forward returns over 1D, 3D, 5D, 10D, and 20D horizons:
- Mean and median forward return.
- Win rate (% positive returns) and loss rate.
- Maximum observed historical gain and drawdown.
- Forward return volatility.

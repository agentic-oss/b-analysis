# Technical Indicators, Scoring & Pattern Methodology

## 1. Technical Indicator Calculations

All indicators are calculated deterministically on standardized historical daily OHLCV data:

- **Moving Averages:** Simple Moving Averages ($SMA_p$) and Exponential Moving Averages ($EMA_p$).
- **Relative Strength Index ($RSI_{14}$):** Calculated using 14-day average gain / average loss.
- **Stochastic RSI:** Normalized $RSI_{14}$ relative to its 14-day high-low range.
- **MACD:** Line = $EMA_{12} - EMA_{26}$, Signal = $EMA_9(MACD)$, Histogram = $MACD - Signal$.
- **Average True Range ($ATR_{14}$):** 14-day rolling mean of $True Range = \max(H-L, |H-C_{prev}|, |L-C_{prev}|)$.
- **Historical Volatility ($Vol_{20d}$):** 20-day annualized standard deviation of daily log returns ($std(r_{1d}) \times \sqrt{252}$).
- **Bollinger Bands:** $SMA_{20} \pm (2 \times \sigma_{20})$.
- **On Balance Volume (OBV) & Accumulation/Distribution:** Cumulative volume flows based on close price direction and close-location value.

## 2. Composite Stock Scoring System (0-100)

Stock scores are computed via transparent weighted aggregation:

$$Score = \sum_{k} w_k \times Score_k$$

Where weights $w_k$ are assigned as:

- **Technical Trend Score ($25\%$):** Alignment of close vs SMA 20, 50, 200.
- **Momentum Score ($20\%$):** RSI level and MACD histogram sign.
- **Volume Score ($15\%$):** Relative volume vs 20-day volume SMA.
- **Relative Strength Score ($15\%$):** 20-day return relative to market benchmark.
- **Volatility Score ($10\%$):** Normalization of 20-day volatility.
- **Market Regime Score ($5\%$):** Global market regime alignment.
- **Sector Rank Score ($5\%$):** Relative momentum rank of stock sector.
- **Fundamental Score ($5\%$):** Normalized P/E, Margins, Growth, and Debt/Equity.

### Score Categorization Labels
- **80–100:** Very Strong
- **65–79:** Strong
- **50–64:** Neutral
- **35–49:** Weak
- **0–34:** Very Weak

## 3. Historical Pattern Analogue Methodology

For each stock at target date $T$, historical trading days $t < T - 20$ are scanned for matching technical configurations:
- $|RSI_t - RSI_T| \le 7.5$
- $|Vol_t - Vol_T| \le 0.10$
- Same SMA 20 price position (above or below)

For all matched historical dates, forward return distributions are evaluated across $h \in \{1, 3, 5, 10, 20\}$ trading days:
- **Mean & Median Forward Returns**
- **Positive & Negative Return Probabilities**
- **Maximum Observed Gain & Loss**
- **Forward Return Volatility**

Probabilities are converted into directional signal labels (**Bullish**, **Slightly Bullish**, **Neutral**, **Slightly Bearish**, **Bearish**) accompanied by explicit confidence metrics ($0-100$).

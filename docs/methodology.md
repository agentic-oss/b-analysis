# Methodology Documentation

## Analytical Methodology

The Daily Indian Stock Market Analysis Pipeline utilizes deterministic quantitative methods, empirical historical pattern matching, transparent component scoring, and machine-learning feature engineering.

---

## 1. Technical Indicators & Event Detection

### Indicator Mathematical Definitions
* **Simple Moving Average (SMA)**: Average close price over window $N$.
* **Exponential Moving Average (EMA)**: Weighted moving average giving greater weight to recent prices.
* **Relative Strength Index (RSI 14)**:
  $$RSI = 100 - \left( \frac{100}{1 + RS} \right)$$
  where $RS = \frac{\text{Average Gain}}{\text{Average Loss}}$ over 14 periods.
* **MACD (12, 26, 9)**: Difference between 12-period EMA and 26-period EMA. Signal line is 9-period EMA of MACD.
* **Average True Range (ATR 14)**:
  $$TR = \max(H - L, |H - C_{prev}|, |L - C_{prev}|)$$
  ATR is 14-period rolling mean of TR.
* **20-Day Annualized Historical Volatility**: Standard deviation of daily log returns multiplied by $\sqrt{252}$.

---

## 2. Transparent Stock Scoring Methodology

Each stock receives a 0–100 score computed as a weighted linear combination:

$$\text{Composite Score} = \sum_{k} w_k \cdot S_k$$

Where:
* **Technical Trend Score ($S_{trend}, w=25\%$)**: Evaluates close relative to SMA 20, 50, 200 and moving average alignments.
* **Momentum Score ($S_{mom}, w=20\%$)**: RSI range (50-70 optimal), positive MACD histogram, and positive 1-day return.
* **Volume Score ($S_{vol}, w=15\%$)**: Relative volume vs 20-day volume average ($>2.0\text{x}$ adds $+30$ points).
* **Relative Strength Score ($S_{rs}, w=15\%$)**: 1-week and 1-month return vs NIFTY 50 benchmark.
* **Volatility Score ($S_{vola}, w=10\%$)**: Evaluates rolling volatility regime ($10\% - 30\%$ annualized is optimal).
* **Market Regime Score ($S_{regime}, w=10\%$)**: Incorporates broad market trend and market breadth.
* **Fundamental Score ($S_{fund}, w=5\%$)**: Evaluates P/E, ROE, and earnings growth.

---

## 3. Historical Analogue Pattern Matching

To build empirical forward return distributions without subjective speculation:
1. For stock at date $T$, current features vector $V_T = [\text{RSI}_{14}, \text{Volatility}_{20d}, \text{DistSMA}_{20}]$ is extracted.
2. Historical rows $\{t \le T - 20\}$ are searched for candidate matches satisfying:
   $$|\text{RSI}_t - \text{RSI}_T| \le 7.5$$
   $$|\text{Volatility}_t - \text{Volatility}_T| \le 0.10$$
3. Top $K$ closest historical instances are selected via normalized Euclidean distance.
4. Forward returns over horizons $H \in \{1d, 3d, 5d, 10d, 20d\}$ are calculated across the matched analogues:
   $$\text{Forward Return}_{t, H} = \frac{\text{Close}_{t+H} - \text{Close}_t}{\text{Close}_t}$$
5. Empirical summary statistics (average, median, positive probability, min/max gain) are stored.

# Scoring & Historical Pattern Matching Methodology

## Composite Stock Scoring Methodology

The 0–100 score is calculated as a weighted average of transparent sub-scores:

* **Technical Trend Score (25%):** Alignment of close price with 20, 50, and 200 SMAs.
* **Momentum Score (20%):** RSI position (optimal 50–70), MACD histogram sign, and 10-day Rate of Change.
* **Volume Score (15%):** Relative volume spikes associated with positive daily returns.
* **Relative Strength Score (15%):** Proximity to 52-week high and low levels.
* **Volatility Score (10%):** Normalized based on volatility regime (Normal vs High/Low).
* **Market Regime Score (5%):** Macro market health contribution from benchmark analysis.
* **Sector Score (5%):** Relative momentum score of the stock's sector.
* **Fundamental Score (5%):** Fundamental evaluation based on PE, ROE, Debt/Equity, and growth.

## Historical Pattern Analogue Matching

Rather than relying on black-box predictions, the engine uses **empirical historical matching**:
1. It scans historical price records for similar technical conditions (RSI ±5, relative volume ±30%, MA distance ±3%).
2. For matching historical dates, it tracks forward returns over 1D, 3D, 5D, 10D, and 20D horizons.
3. It derives win rates (positive return probability), average returns, and maximum observed gain/loss.

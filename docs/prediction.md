# Prediction & Historical Analogue Methodology

## 1. Historical Pattern Matching
The analogue engine searches historical stock data for similar technical states:
- **Criteria:** RSI within +/- 7.5, Relative Volume (RVOL) within +/- 0.5, and 20 DMA price distance within +/- 3%.
- **Forward Horizon Distributions:** Calculates empirical forward returns over 1D, 3D, 5D, 10D, and 20D trading days.
- **Metrics Tracked:** Observation count, mean return, median return, positive return probability (win rate), negative return probability, max gain, max loss, and forward volatility.

## 2. Probabilistic Signals & Directional Bias
- Directional signals (Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish) combine composite stock scores with empirical analogue win rates.
- Confidence scores range from 0 to 100%.

## 3. Look-Ahead Bias & Data Leakage Prevention
- Features for date `T` are generated strictly using price, volume, and indicator data available on or before date `T`.
- Future returns are shifted backwards (`shift(-k)`) and marked explicitly as target labels.
- Walk-forward temporal splits (`RandomForestClassifier`) evaluate baseline predictive model performance without temporal shuffling.

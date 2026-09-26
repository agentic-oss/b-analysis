# Probabilistic Signals & Machine Learning Feature Engineering

## 1. Historical Pattern Search (Analogues)

For every stock, the system searches historical price history for setup analogues matching current technical conditions:
- **RSI 14**: $\pm 7$ points
- **Volatility 20D**: $\pm 10\%$
- **Trend Alignment**: Price position relative to 20-day SMA.

For all matching historical instances, empirical forward returns are evaluated across horizons $H \in \{1, 3, 5, 10, 20\}$ trading days. The system records:
- Sample size count
- Mean and median forward returns
- Positive win rate probability ($\%$)
- Maximum observed gain and loss ($\%$)
- Forward standard deviation volatility ($\%$)

## 2. Preventing Look-Ahead Bias

To ensure machine learning models trained on this historical dataset do not suffer from data leakage:
- **Point-in-Time Features**: All indicators and market features for row $t$ are derived **strictly from observations available on or before day $t$**.
- **Separate Forward Targets**: Target columns (`future_return_1d`, `future_return_5d`, etc.) look forward from day $t$ and are populated only for training labels.
- **Walk-Forward Validation**: Time-series cross-validation uses expanding windows ($t_{1} \dots t_{train}$) to predict $t_{train+1} \dots t_{train+k}$. **Random temporal shuffling is strictly prohibited.**

## 3. Directional Forecast Labels

Forward-looking signals output:
- **Horizons**: 1D, 3D, 5D, 10D, 20D
- **Labels**: Bullish ($\ge 65\%$), Slightly Bullish ($\ge 55\%$), Neutral ($45\%-55\%$), Slightly Bearish ($\le 45\%$), Bearish ($\le 35\%$).
- **Confidence Score (0-100)**: Magnitude deviation from $50\%$ probability baseline.

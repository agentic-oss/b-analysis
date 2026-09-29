# Predictive Machine Learning Framework & Research Layer

## Prevented Look-Ahead Bias

To ensure financial dataset integrity and prevent data leakage:
1. **Feature Vector ($X_t$)**: Standardized using price and volume observations up to and including time $T$.
2. **Forward Targets ($Y_{t+H}$)**: Explicitly computed using prices strictly from $T+1$ to $T+H$.
3. **Chronological Splitting**: Model training uses chronological temporal train/test splits (e.g. 80% past observations for training, 20% future observations for testing). **Random shuffling is strictly prohibited**.

---

## Baseline ML Models

1. **Random Forest Classifier**:
   - Depth-bounded trees ($max\_depth=4$, $n\_estimators=50$) to prevent overfitting on noisy daily financial data.
   - Evaluated on directional accuracy ($\%$ correct directional forecast over $H$-day horizons).

2. **Metrics Tracked**:
   - Accuracy
   - Precision
   - Recall
   - F1-Score
   - Directional Accuracy ($\%$)

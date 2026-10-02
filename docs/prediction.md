# Prediction Methodology & Historical Pattern Analogue Engine

## Empirical Probability vs. Deterministic Forecasting

Financial markets exhibit high noise and non-stationarity. Attempting to output exact price targets or guaranteed predictions leads to severe overfitting and false confidence.

Instead, this system uses an **Empirical Historical Analogue Framework**:

1. **Pattern Matching**: For stock observation at date $T$, the system searches historical periods for that stock where:
   - RSI 14 was within $\pm 10$ points of current RSI.
   - Distance from 20 DMA was within $\pm 5\%$ of current distance.
   - Annualized 20-day volatility was within $\pm 10\%$ of current volatility.

2. **Forward Distribution Statistics**: For matched historical analogue dates $T_{hist}$, the pipeline tracks subsequent realized returns over 1, 3, 5, 10, and 20 trading days ($T_{hist} + H$).
   - Calculates average return, median return, positive return probability ($\mathbb{P}(R > 0)$), maximum historical gain, and maximum drawdown.

3. **Inference & Directional Bias**: Directional labels (*Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish*) and confidence scores (0-100) are assigned based on empirical historical probability and expected return.

## Machine Learning Baseline Models

To benchmark predictive power:
- **Models**: Logistic Regression, Random Forest Classifier.
- **Validation Scheme**: **Time-Series Walk-Forward Split** (Never randomly shuffle temporal financial data).
- **Leakage Prevention**: Features on date $T$ use strictly observations available up to date $T$. Targets ($T+1 \dots T+N$) are evaluated strictly out-of-sample.

# Feature Engineering & Machine Learning Methodology

## Look-Ahead Bias Prevention

To ensure ML models trained on this dataset remain valid:
1. All technical indicators for date $T$ strictly use price observations $t \le T$.
2. Forward return targets ($T+1, T+3, T+5, T+10, T+20$) are stored as separate target columns and strictly isolated during model inputs.
3. Train/test splitting uses strict walk-forward temporal order without random shuffling.

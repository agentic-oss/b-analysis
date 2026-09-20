# Methodology & Scoring Framework

## Market Regime Classification

The market regime is classified deterministically using a transparent rule-based evaluation framework:

1. **Strong Bullish**: NIFTY > 20 DMA & NIFTY > 50 DMA, >70% of tracked stocks above 20 DMA, Advance/Decline ratio >= 1.5.
2. **Bullish**: NIFTY > 50 DMA, >50% of tracked stocks above 20 DMA, Advance/Decline ratio >= 1.0.
3. **Neutral**: Mixed moving average alignments or 40–60% of stocks above 20 DMA.
4. **Bearish**: NIFTY < 50 DMA, <50% of tracked stocks above 20 DMA.
5. **Strong Bearish**: NIFTY < 20 DMA & NIFTY < 50 DMA, <30% of tracked stocks above 20 DMA, Advance/Decline ratio <= 0.6.

---

## Transparent Stock Composite Rating (0–100)

The composite stock rating is a weighted combination of individual sub-scores:

| Component | Weight | Key Metrics Evaluated |
|---|---|---|
| **Technical Trend** | 25% | Price relative to 20, 50, 200 SMA; SMA alignment |
| **Momentum** | 20% | RSI 14, Stoch RSI, MACD Histogram, 52-week High distance |
| **Volume** | 15% | Relative Volume vs 20-day Volume SMA |
| **Relative Strength** | 15% | Outperformance vs benchmark daily return |
| **Volatility** | 10% | 20-day annualized volatility regime |
| **Market Regime** | 10% | Current overall market regime score |
| **Sector Performance**| 5% | Sector momentum score |

### Rating Labels
- **80 – 100**: Very Strong
- **65 – 79**: Strong
- **50 – 64**: Neutral
- **35 – 49**: Weak
- **0 – 34**: Very Weak

# Analysis Methodology & Composite Scoring

## Composite Scoring Methodology

The stock composite score is a transparent weighted average ranging from 0 to 100:

$$ \text{Composite Score} = \sum_{w_i \cdot \text{SubScore}_i} $$

### Component Weights (`config/config.json`)
- **Technical Trend Score**: 25% (Moving average alignments: 20 DMA > 50 DMA > 200 DMA)
- **Momentum Score**: 20% (RSI 14 optimal ranges + MACD Histogram positivity)
- **Volume Score**: 15% (Relative Volume > 1.5x on positive return days)
- **Relative Strength Score**: 15% (Excess daily return over NIFTY 50 index return)
- **Volatility Score**: 10% (Normalized volatility regime analysis)
- **Sector Score**: 10% (Rank of stock's sector in sector momentum table)
- **Fundamental Score**: 5% (Valuation, ROE, net margins, and debt-to-equity ratios)

### 5-Tier Classification Labels
- **80 – 100**: Very Strong
- **65 – 79**: Strong
- **50 – 64**: Neutral
- **35 – 49**: Weak
- **0 – 34**: Very Weak

## Historical Pattern Analogue Matching

Matches past observations in a stock's historical timeline that possessed similar RSI values (within ±5 points) and SMA 20 distances (within ±3%). For each match group, forward price movement is evaluated across 1d, 3d, 5d, 10d, and 20d horizons to compute empirical win probabilities and return distribution metrics.

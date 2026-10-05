# Data Schema Documentation

## Directory Hierarchy

- `data/raw/YYYY/MM/YYYY-MM-DD/`: Ingested raw price files for stocks and indices.
- `data/processed/prices/`: Accumulated historical stock OHLCV datasets.
- `data/processed/indices/`: Accumulated historical index OHLCV datasets.
- `data/features/daily/YYYY-MM-DD.parquet`: Engineered ML feature matrices.
- `data/quality/YYYY-MM-DD.json`: Data quality report.
- `data/analysis/daily/YYYY-MM-DD.json`: Machine-readable daily analysis output.
- `reports/daily/YYYY-MM-DD.md`: Human-readable daily report.

## Daily Analysis Output Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Bullish",
    "score": 45,
    "confidence": 75,
    "nifty_trend": "Above 200 DMA",
    "nifty_volatility_annualized": 14.5,
    "bank_nifty_trend": "Bullish",
    "breadth": {
      "total_tracked": 14,
      "advances": 10,
      "declines": 4,
      "advance_decline_ratio": 2.5,
      "pct_above_20_dma": 71.4,
      "pct_above_50_dma": 64.3,
      "pct_above_200_dma": 85.7,
      "new_highs_20d": 3,
      "new_lows_20d": 0
    }
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "NIFTY IT",
      "daily_return_pct": 1.25,
      "weekly_return_pct": 2.4,
      "relative_strength_1d": 0.85,
      "momentum_score": 18.5
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "market_regime": "Bullish",
      "score": {
        "composite_score": 78.5,
        "label": "Strong",
        "components": {
          "technical_trend": 85.0,
          "momentum": 80.0,
          "volume": 60.0,
          "relative_strength": 75.0,
          "volatility": 70.0,
          "market_regime": 72.5,
          "fundamental": 50.0
        }
      },
      "signals": ["20-Day High Breakout"],
      "forward_probabilities": {
        "bias_1d": "Slightly Bullish",
        "bias_5d": "Bullish",
        "confidence": 72.0
      }
    }
  ]
}
```

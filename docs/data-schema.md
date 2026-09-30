# Data Schema Documentation

## Data Directory Structure

```
data/
├── raw/
│   └── YYYY/MM/YYYY-MM-DD/
│       ├── raw_prices.parquet
│       └── raw_prices.csv
├── processed/
│   └── prices/
│       ├── historical.parquet
│       └── historical.csv
├── features/
│   └── daily/
│       └── YYYY-MM-DD.parquet
├── quality/
│   └── YYYY-MM-DD.json
├── analysis/
│   └── daily/
│       └── YYYY-MM-DD.json
└── reports/
    └── daily/
        └── YYYY-MM-DD.md
```

---

## Daily Machine-Readable Analysis Output Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Bullish",
    "regime_score": 75.0,
    "nifty_close": 22450.50,
    "nifty_return_1d": 0.0085,
    "nifty_volatility_20d": 0.1250,
    "bank_nifty_close": 48200.10,
    "market_breadth": {
      "total_tracked": 16,
      "advances": 11,
      "declines": 5,
      "advance_decline_ratio": 2.2,
      "pct_above_20dma": 75.0,
      "pct_above_50dma": 81.25,
      "pct_above_200dma": 87.5,
      "new_52w_highs": 3,
      "new_52w_lows": 0
    },
    "rules_description": "Regime based on NIFTY moving averages alignment (50%) and market breadth (% stocks > 50DMA, advance/decline ratio) (50%)."
  },
  "sectors": [
    {
      "sector": "Information Technology",
      "close": 38500.0,
      "daily_return": 0.012,
      "weekly_return": 0.025,
      "monthly_return": 0.045,
      "relative_strength_vs_nifty": 0.0035,
      "rsi_14": 62.5,
      "volatility": 0.14,
      "relative_volume": 1.25,
      "momentum_score": 78.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "sector": "Energy",
      "close": 1285.50,
      "daily_return": 0.011,
      "rsi_14": 58.4,
      "composite_score": 76.5,
      "rating": "Strong",
      "score_components": {
        "technical_trend": 80.0,
        "momentum": 75.0,
        "volume": 65.0,
        "relative_strength": 70.0,
        "volatility": 75.0,
        "market_regime": 75.0,
        "fundamental": 70.0
      },
      "technical_events": [
        "20-Day High Breakout"
      ],
      "support_levels": [1240.0, 1260.0],
      "resistance_levels": [1300.0, 1320.0],
      "fundamentals": {
        "available": true,
        "valuation_assessment": "Fair",
        "profitability_assessment": "High Profitability",
        "solvency_assessment": "Low Debt",
        "metrics": {
          "market_cap": 1800000000000,
          "pe_ratio": 24.5,
          "roe": 0.16
        }
      },
      "historical_analogues": {
        "num_matches": 24,
        "horizons": {
          "1d": {
            "avg_return": 0.0042,
            "median_return": 0.0035,
            "positive_prob": 0.625,
            "negative_prob": 0.375,
            "max_gain": 0.028,
            "max_loss": -0.018,
            "volatility": 0.009
          }
        }
      },
      "forward_probabilities": {
        "signals": {
          "1d": {
            "directional_bias": "Slightly Bullish",
            "confidence": 68.5,
            "blended_positive_probability": 0.6025
          }
        }
      }
    }
  ]
}
```

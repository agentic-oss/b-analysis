# Data Schema Documentation

## Storage Directory Layout

```
data/
├── raw/
│   └── YYYY/
│       └── MM/
│           └── YYYY-MM-DD/
│               ├── {clean_ticker}.parquet
│               └── {clean_ticker}.csv
├── processed/
│   └── prices/
│       ├── dataset.parquet
│       └── dataset.csv
├── features/
│   └── daily/
├── quality/
│   └── YYYY-MM-DD.json
├── analysis/
│   └── daily/
│       └── YYYY-MM-DD.json
└── reports/
    └── YYYY-MM-DD.md
```

## Raw Price Record Schema

| Field | Type | Description |
|-------|------|-------------|
| `date` | String (YYYY-MM-DD) | Trading date |
| `open` | Float64 | Opening price |
| `high` | Float64 | Session high price |
| `low` | Float64 | Session low price |
| `close` | Float64 | Closing price |
| `adj_close` | Float64 | Adjusted closing price |
| `volume` | Int64 / Float64 | Trading volume |
| `ticker` | String | Yahoo Finance symbol (e.g. `RELIANCE.NS`) |
| `provider` | String | Data provider identifier |
| `ingestion_timestamp` | String (ISO 8601) | Timestamp when record was saved |

## Data Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "2026-03-01",
  "records_processed": 500,
  "records_valid": 498,
  "tickers_checked": 15,
  "warnings": [
    "[RELIANCE.NS] Zero volume recorded in 1 trading sessions"
  ],
  "errors": []
}
```

## Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "2026-03-01",
  "pipeline_timestamp": "2026-03-01T18:00:00.000000",
  "data_quality": {
    "records_processed": 500,
    "records_valid": 498,
    "warnings": [],
    "errors": []
  },
  "market": {
    "regime": "Bullish",
    "nifty_close": 22000.0,
    "nifty_trend": "Uptrend",
    "nifty_volatility_annualized": 14.5,
    "breadth_pct_above_20dma": 70.0,
    "breadth_pct_above_50dma": 65.0,
    "breadth_pct_above_200dma": 80.0,
    "advance_decline_ratio": 1.5,
    "advances": 9,
    "declines": 6,
    "new_highs_20d": 3,
    "new_lows_20d": 0,
    "total_stocks_analyzed": 15
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "IT",
      "daily_return": 1.25,
      "weekly_return": 3.10,
      "monthly_return": 5.40,
      "relative_strength_vs_nifty": 2.10,
      "volatility_annualized": 16.2,
      "momentum_score": 78.5
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "ticker": "RELIANCE.NS",
      "exchange": "NSE",
      "sector": "Energy",
      "score": {
        "composite_score": 82.5,
        "label": "Very Strong",
        "components": {
          "technical_trend_score": 85.0,
          "momentum_score": 80.0,
          "volume_score": 75.0,
          "relative_strength_score": 88.0,
          "volatility_score": 80.0,
          "market_regime_score": 75.0,
          "sector_score": 78.0,
          "fundamental_score": 74.0
        }
      },
      "technical_events": {
        "golden_cross": false,
        "death_cross": false,
        "breakout_20d": true,
        "breakdown_20d": false,
        "unusual_volume": false,
        "support_level": 2400.0,
        "resistance_level": 2650.0,
        "trend_state": "Uptrend"
      },
      "fundamental_analysis": {
        "fundamental_score": 74.0,
        "valuation_status": "Fairly Valued",
        "profitability_status": "High Profitability",
        "growth_status": "Moderate Growth",
        "has_data": true
      },
      "historical_analogues": {
        "num_analogues": 18,
        "horizons": {
          "5d": {
            "sample_size": 18,
            "avg_forward_return_pct": 1.85,
            "median_forward_return_pct": 1.50,
            "positive_return_probability": 72.22,
            "negative_return_probability": 27.78,
            "max_observed_gain_pct": 6.40,
            "max_observed_loss_pct": -3.10,
            "forward_volatility_pct": 2.10
          }
        }
      },
      "signals": {
        "5d": {
          "horizon": "5d",
          "directional_bias": "Bullish",
          "confidence": 76.5,
          "empirical_positive_probability": 72.22,
          "expected_average_return_pct": 1.85,
          "inference_type": "Probabilistic Historical Analogue + Technical Scoring"
        }
      }
    }
  ]
}
```

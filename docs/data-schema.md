# Data Schema Documentation

## Storage Directory Organization

Data outputs are structured across `data/` and `reports/`:

```
data/
├── raw/                      # Raw daily downloads partitioned by date
│   └── YYYY/
│       └── MM/
│           └── YYYY-MM-DD/
│               ├── RELIANCE_NS.parquet
│               └── RELIANCE_NS.csv
├── processed/                # Cumulative historical datasets
│   ├── prices/               # Stock OHLCV + technical indicators (Parquet/CSV)
│   └── indices/              # Index historical data (Parquet/CSV)
├── features/                 # Machine learning feature datasets
│   └── YYYY-MM-DD.parquet
├── analysis/                 # Machine-readable daily analysis
│   └── daily/
│       └── YYYY-MM-DD.json
├── quality/                  # Data quality reports
│   └── YYYY-MM-DD.json
reports/
└── daily/                    # Human-readable daily Markdown reports
    └── YYYY-MM-DD.md
```

---

## Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "nifty_trend": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "nifty_close": 23217.6,
    "nifty_sma_20": 23873.48,
    "nifty_sma_50": 24103.56,
    "nifty_sma_200": 24521.63,
    "bank_nifty_trend": "Bullish | Bearish",
    "market_breadth": {
      "total_tracked": 12,
      "advance_decline_ratio": 1.5,
      "pct_above_20dma": 65.0,
      "pct_above_50dma": 58.3,
      "pct_above_200dma": 75.0,
      "new_20d_highs": 3,
      "new_20d_lows": 0
    },
    "regime": "Strong Bearish",
    "regime_score": 10.0,
    "classification_rules": []
  },
  "sectors": [
    {
      "sector": "Information Technology",
      "daily_return": -1.58,
      "weekly_return": -2.66,
      "monthly_return": -3.73,
      "rs_vs_nifty_1d": -2.01,
      "rs_vs_nifty_5d": -0.9,
      "volatility": 23.7,
      "rsi_14": 38.37,
      "momentum_score": 45.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE.NS",
      "raw_symbol": "RELIANCE",
      "sector": "Energy",
      "close": 1240.0,
      "return_1d_pct": 0.38,
      "relative_volume": 0.97,
      "composite_score": 46.57,
      "score_label": "Weak",
      "score_components": {
        "technical_trend": 50.0,
        "momentum": 31.65,
        "volume": 50.0,
        "relative_strength": 46.79,
        "volatility": 74.76,
        "market_regime": 10.0,
        "sector": 50.0,
        "fundamental": 55.0
      },
      "technical_signals": {
        "golden_cross": false,
        "death_cross": false,
        "breakout_20d": false,
        "breakdown_20d": false
      },
      "breakout_20d": false,
      "breakdown_20d": false,
      "directional_bias": {
        "1d": "Slightly Bullish",
        "3d": "Slightly Bearish",
        "5d": "Bearish",
        "10d": "Bearish",
        "20d": "Slightly Bullish"
      },
      "historical_analogues": {
        "matches_found": 14,
        "forward_probabilities": {
          "1d": {
            "observations": 14,
            "mean_return": -0.19,
            "median_return": 0.14,
            "win_probability": 57.1,
            "loss_probability": 42.9,
            "max_gain": 2.36,
            "max_loss": -2.65,
            "forward_volatility": 1.43
          }
        },
        "directional_bias": {},
        "confidence": 42.0,
        "disclaimer": "..."
      },
      "fundamentals": {
        "symbol": "RELIANCE.NS",
        "source": "yfinance",
        "timestamp": "2026-09-16T16:06:32.076707",
        "available": true,
        "pe_ratio": 22.45,
        "pb_ratio": 1.85,
        "eps": 55.22,
        "debt_to_equity": 36.65
      }
    }
  ],
  "data_quality": {
    "date": "YYYY-MM-DD",
    "symbols_processed": 22,
    "records_processed": 7997,
    "records_valid": 7997,
    "warnings_count": 8,
    "errors_count": 0,
    "warnings": [],
    "errors": []
  },
  "ml_research_baseline": {
    "model_type": "RandomForestClassifier Baseline",
    "validation_method": "Walk-Forward Time-Series Split",
    "samples_evaluated": 5891,
    "accuracy": 0.5186,
    "precision": 0.5188,
    "recall": 0.2329,
    "f1_score": 0.3214,
    "limitations": "..."
  }
}
```

---

## Data Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "symbols_processed": 22,
  "records_processed": 7997,
  "records_valid": 7997,
  "warnings_count": 8,
  "errors_count": 0,
  "warnings": [
    {
      "symbol": "HDFCBANK.NS",
      "message": "Anomalous volume spike (>10x median) on dates: ['2024-11-25']"
    }
  ],
  "errors": []
}
```

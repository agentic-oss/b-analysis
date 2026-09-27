# Data Schema Specifications

## 1. Quality Report Schema (`data/quality/YYYY-MM-DD.json`)
```json
{
  "date": "YYYY-MM-DD",
  "timestamp": "ISO-8601 UTC",
  "records_processed": 50,
  "records_valid": 50,
  "warnings_count": 0,
  "errors_count": 0,
  "warnings": [],
  "errors": []
}
```

## 2. Daily Analysis Schema (`data/analysis/daily/YYYY-MM-DD.json`)
```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "score": 82.5,
    "confidence": 85.0,
    "nifty_trend": "Uptrend",
    "breadth_above_20dma_pct": 75.0,
    "breadth_above_50dma_pct": 68.0,
    "breadth_above_200dma_pct": 60.0,
    "advance_decline_ratio": 1.8,
    "rules_applied": []
  },
  "sectors": [
    {
      "sector": "NIFTY IT",
      "daily_return_pct": 1.25,
      "weekly_return_pct": 2.40,
      "monthly_return_pct": 5.10,
      "relative_strength_vs_nifty": 0.85,
      "momentum_score": 78.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "sector": "Energy",
      "price_close": 1250.0,
      "daily_return_pct": 0.5,
      "technical_score": 78.5,
      "score_label": "Strong",
      "score_components": {
        "technical_trend": 100,
        "momentum": 75,
        "volume": 80,
        "relative_strength": 70,
        "volatility": 80,
        "market_regime": 80,
        "sector": 75
      },
      "fundamental_score": 70.0,
      "market_regime": "Bullish",
      "historical_analogues": {
        "sample_size": 45,
        "match_conditions": "RSI ~ 55, Dist 50DMA ~ 2.1%",
        "horizons": {
          "1d": { "count": 45, "mean_return_pct": 0.35, "win_rate_pct": 62.0 }
        }
      },
      "predictive_signals": {
        "model_type": "random_forest",
        "accuracy": 0.58,
        "directional_bias": "Bullish",
        "confidence_score": 24.0
      }
    }
  ],
  "technical_events": [],
  "quality": {}
}
```

## 3. Daily Feature Dataset (`data/features/daily/YYYY-MM-DD.parquet`)
Columns include:
- `ticker`, `Date`, `Open`, `High`, `Low`, `Close`, `Volume`
- `return_1d`, `return_5d`, `return_20d`
- `sma_5`, `sma_10`, `sma_20`, `sma_50`, `sma_100`, `sma_200`
- `ema_9`, `ema_20`, `ema_50`, `ema_200`
- `rsi_14`, `stoch_rsi`, `macd`, `macd_signal`, `macd_histogram`
- `atr_14`, `volatility_20d`, `bollinger_upper`, `bollinger_lower`, `bollinger_bandwidth`
- `relative_volume`, `obv`, `dist_sma_50_pct`, `dist_52w_high_pct`, `dist_52w_low_pct`
- Target columns: `future_return_1d`, `future_return_3d`, `future_return_5d`, `future_return_10d`, `future_return_20d`

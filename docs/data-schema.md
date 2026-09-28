# Data Schema Reference

## 1. Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "2026-03-27",
  "market": {
    "market_regime": "Bullish",
    "nifty_close": 22500.0,
    "nifty_trend": "Uptrend",
    "banknifty_trend": "Uptrend",
    "nifty_volatility_20d": 0.14,
    "breadth": {
      "total_tracked": 25,
      "pct_above_20dma": 75.0,
      "pct_above_50dma": 68.0,
      "pct_above_200dma": 80.0,
      "advance_decline_ratio": 2.1,
      "advances": 17,
      "declines": 8,
      "new_highs_20d": 3,
      "new_lows_20d": 0
    },
    "rules_applied": "Rule-based classification string..."
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "NIFTY IT",
      "daily_return": 1.5,
      "weekly_return": 3.2,
      "monthly_return": 5.1,
      "relative_strength_vs_nifty": 0.8,
      "volatility": 0.18,
      "relative_volume": 1.2,
      "rsi_14": 62.5,
      "momentum_score": 78.5
    }
  ],
  "stocks": [
    {
      "symbol": "TCS",
      "sector": "Information Technology",
      "close": 3850.0,
      "technical_score": 82.0,
      "label": "Very Strong",
      "components": {
        "technical_trend": 100.0,
        "momentum": 75.0,
        "volume": 75.0,
        "relative_strength": 80.0,
        "volatility": 80.0,
        "market_regime": 75.0,
        "fundamental": 75.0
      },
      "fundamental_score": 75.0,
      "fundamental_metrics": {
        "pe_ratio": 28.5,
        "pb_ratio": 12.0,
        "roe": 0.45,
        "profit_margins": 0.22,
        "revenue_growth": 0.12,
        "debt_to_equity": 10.0
      },
      "signals": ["20-Day High Breakout"],
      "support_levels": [3800.0, 3750.0],
      "resistance_levels": [3900.0, 3950.0],
      "historical_analogues": {
        "historical_matches_count": 12,
        "horizons": {
          "1d": {
            "observations": 12,
            "mean_forward_return": 0.45,
            "win_probability": 66.7,
            "loss_probability": 33.3
          }
        }
      },
      "forward_signals": {
        "1d": {
          "directional_bias": "Bullish",
          "confidence": 72.0,
          "probability_up": 0.61,
          "model_used": "RandomForest (Walk-Forward Split)"
        }
      }
    }
  ],
  "quality": {
    "records_processed": 25,
    "records_valid": 25,
    "warnings": [],
    "errors": []
  }
}
```

## 2. Data Quality Audit Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "2026-03-27",
  "records_processed": 25,
  "records_valid": 25,
  "warnings": [],
  "errors": []
}
```

## 3. Machine Learning Feature Dataset Schema (`data/features/daily/YYYY-MM-DD.parquet`)

| Column Name | Type | Description |
|---|---|---|
| `date` | String | Trading date (YYYY-MM-DD) |
| `symbol` | String | Equities ticker symbol |
| `price_open` | Float64 | Opening price |
| `price_high` | Float64 | High price |
| `price_low` | Float64 | Low price |
| `price_close` | Float64 | Closing price |
| `volume` | Int64 | Trading volume |
| `return_1d` | Float64 | 1-day price return |
| `return_5d` | Float64 | 5-day price return |
| `return_20d` | Float64 | 20-day price return |
| `rsi_14` | Float64 | 14-period RSI |
| `stoch_rsi` | Float64 | 14-period Stochastic RSI |
| `macd` | Float64 | MACD line value |
| `macd_signal` | Float64 | MACD signal line |
| `atr_14` | Float64 | 14-period Average True Range |
| `volatility_20d` | Float64 | 20-day annualized historical volatility |
| `sma_20` | Float64 | 20-day Simple Moving Average |
| `sma_50` | Float64 | 50-day Simple Moving Average |
| `sma_200` | Float64 | 200-day Simple Moving Average |
| `ema_20` | Float64 | 20-day Exponential Moving Average |
| `relative_volume` | Float64 | Volume / 20-day Volume SMA |
| `distance_from_52w_high` | Float64 | (Close - 52w High) / 52w High |
| `distance_from_52w_low` | Float64 | (Close - 52w Low) / 52w Low |
| `market_return_1d` | Float64 | 1-day NIFTY benchmark return |
| `market_volatility` | Float64 | NIFTY benchmark 20-day volatility |
| `sector_return_1d` | Float64 | Sector index 1-day return |
| `target_future_return_1d` | Float64 | **Target:** Forward 1-day return ($t+1$) |
| `target_direction_1d` | Int64 | **Target:** Forward 1-day direction (1 if return > 0 else 0) |

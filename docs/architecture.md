# System Architecture

## Overview

The Daily Indian Stock Market Data & Deep Analysis Pipeline is designed as a modular, decoupled data and analytics engine.

```
+-------------------------------------------------------------------+
|                        Daily Pipeline                             |
+-------------------------------------------------------------------+
                                  |
    +-----------------------------+-----------------------------+
    |                             |                             |
    v                             v                             v
[Ingestion]                 [Validation]                 [Storage]
(YFinanceProvider)         (DataValidator)             (DataStorage)
    |                             |                             |
    +-----------------------------+-----------------------------+
                                  |
                                  v
              +---------------------------------------+
              |           Analytics Engine            |
              |  - TechnicalIndicators                |
              |  - MarketRegimeDetector               |
              |  - SectorAnalyzer                     |
              |  - FundamentalAnalyzer                |
              |  - StockScorer                        |
              |  - HistoricalAnalogueFinder           |
              |  - FeatureEngineer                    |
              |  - ProbabilisticPredictor             |
              +---------------------------------------+
                                  |
                                  v
                      +-----------------------+
                      |   Reporting Engine    |
                      |  - JSON Export        |
                      |  - Markdown Report    |
                      +-----------------------+
```

## Module Responsibilities

1. **`src/ingestion`**: Abstraction for data provider APIs (`MarketDataProvider`), implemented via `YFinanceProvider` with retries, exponential backoff, and rate-limit handling.
2. **`src/validation`**: Validates OHLC relationships, positive prices, missing rows, extreme volume spikes, and exports data quality reports (`data/quality/YYYY-MM-DD.json`).
3. **`src/storage`**: Manages persistence across Parquet (for efficient time-series queries), CSV (for easy inspection), and JSON.
4. **`src/indicators`**: Deterministic technical indicator calculations (SMA, EMA, RSI, Stoch RSI, MACD, ATR, Bollinger Bands, OBV, A/D).
5. **`src/market`**: Calculates market breadth and classifies market regime (Strong Bullish to Strong Bearish).
6. **`src/sectors`**: Measures sector returns, relative strength vs NIFTY 50, and rankings.
7. **`src/fundamentals`**: Collects key valuation and financial ratios with timestamp metadata.
8. **`src/scoring`**: Componentized, transparent composite scoring engine (0-100).
9. **`src/patterns`**: Historical analogue pattern search evaluating forward empirical return distributions.
10. **`src/features`**: Point-in-time ML feature store ensuring zero look-ahead bias.
11. **`src/modeling`**: Baseline ML modeling with TimeSeriesSplit validation.
12. **`src/backtesting`**: Event/vector backtester incorporating transaction costs and slippage.
13. **`src/reporting`**: Generates daily Markdown research reports and structured JSON exports.
14. **`src/pipeline`**: Main orchestrator binding ingestion, analysis, storage, and reporting into a single daily workflow.

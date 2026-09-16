# Architecture Documentation

## System Overview

The Daily Indian Stock Market Data & Deep Analysis Pipeline is an automated market analytics and historical research engine. The system is designed to execute every trading day, fetch OHLCV and index data for Indian equities (NSE & BSE), validate quality, compute technical indicators, analyze fundamentals and market regimes, evaluate sector rankings, generate composite stock scores, identify historical analogue setups, engineer leakage-free ML features, run walk-forward baseline model evaluations, run strategy backtests, and publish daily Markdown reports and JSON datasets.

---

## High-Level Data Flow

```
[ Market Data Provider (yfinance) ]
               │
               ▼
   [ Data Validation Layer ]
               │
               ├──────────────────────────┐
               ▼                          ▼
   [ Data Storage (Parquet/CSV/JSON) ]   [ Quality Reports ]
               │
               ▼
   [ Technical Indicators & Fundamental Analyzer ]
               │
               ├──────────────────────────┬──────────────────────────┐
               ▼                          ▼                          ▼
   [ Market Regime Engine ]      [ Sector Ranking Engine ]    [ Stock Scorer (0-100) ]
               │                          │                          │
               └──────────────────────────┴──────────────────────────┘
                                          │
                                          ▼
                         [ Historical Analogue Pattern Engine ]
                                          │
                                          ▼
                         [ Feature Engineering (Leakage-Free) ]
                                          │
                                          ├──────────────────────────┐
                                          ▼                          ▼
                         [ Walk-Forward ML Baseline ]    [ Backtesting Framework ]
                                          │                          │
                                          └──────────────────────────┘
                                          │
                                          ▼
                         [ Daily Markdown & JSON Reporting ]
                                          │
                                          ▼
                         [ Automated Git Integration & Actions ]
```

---

## Component Breakdown

### 1. Ingestion Layer (`src/ingestion/`)
- Abstract base class `MarketDataProvider` defines standardized interface (`get_historical_prices`, `get_latest_prices`, `get_volume_data`, `get_corporate_actions`, `get_index_data`).
- `YFinanceProvider` implements retries with exponential backoff, rate limit handling, logging, error capture, and metadata tagging (`symbol`, `provider`, `ingested_at`).

### 2. Validation Layer (`src/validation/`)
- `DataValidator` checks OHLC price relationships ($High \ge Low$, $High \ge Open/Close$, $Low \le Open/Close$), flags duplicate dates, zero/negative prices, volume spikes (>10x 20-day median), price return jumps (>30%), and tracks missing trading days using a configurable market holiday calendar.
- Writes detailed quality reports to `data/quality/YYYY-MM-DD.json`.

### 3. Storage Architecture (`src/storage/`)
- `HistoricalStorage` partitions raw historical data (`data/raw/YYYY/MM/YYYY-MM-DD/`) and updates cumulative historical datasets (`data/processed/prices/`, `data/processed/indices/`).
- Uses an append/update deduplication strategy on `(Date, symbol)` key pairs to prevent duplicate entries while preserving historical observations.

### 4. Technical Analysis & Indicators (`src/indicators/`)
- `TechnicalIndicators` computes deterministic indicators: SMAs (5, 10, 20, 50, 100, 200), EMAs (9, 20, 50, 200), RSI-14, Stochastic RSI, MACD (12,26,9), ATR-14, Annualized Volatility (20d), Bollinger Bands, OBV, Accumulation/Distribution, VWAP, support/resistance levels, golden/death crosses, and 20-day breakouts/breakdowns.

### 5. Fundamental Analysis (`src/fundamentals/`)
- `FundamentalAnalyzer` fetches fundamental metrics (PE, PB, EPS, ROE, Debt/Equity, margins, growth, holdings) and computes a transparent 0-100 fundamental score. Missing data is handled gracefully with neutral defaults and source timestamps.

### 6. Market Regime Analysis (`src/market/`)
- `MarketRegimeAnalyzer` evaluates market health using NIFTY 50 DMA relationships (20, 50, 200 DMA), Bank NIFTY trend, advance/decline ratio, % of universe above 20/50/200 DMAs, and new 20-day highs/lows. Classifies environment into:
  - Strong Bullish
  - Bullish
  - Neutral
  - Bearish
  - Strong Bearish

### 7. Sector Analysis (`src/sectors/`)
- `SectorAnalyzer` evaluates tracked sector performance across 1D, 5D, 20D horizons, calculates relative strength against NIFTY 50, calculates composite momentum scores, and generates sector rankings.

### 8. Composite Stock Scoring (`src/scoring/`)
- `StockScorer` combines technical trend (25%), momentum (20%), volume (15%), relative strength (15%), volatility (10%), market regime (5%), sector (5%), and fundamental (5%) components into a transparent score (0-100) with rating labels (Very Strong to Very Weak).

### 9. Historical Analogue Engine (`src/patterns/`)
- `HistoricalAnalogueEngine` searches historical dataset windows matching current RSI and volatility conditions. Computes forward return statistics (mean, median, win probability, max gain/loss, volatility) across 1D, 3D, 5D, 10D, and 20D horizons and assigns empirical directional biases and confidence scores.

### 10. ML Feature Engineering (`src/features/`)
- `FeatureEngineer` compiles leakage-free tabular datasets saved to `data/features/YYYY-MM-DD.parquet`. Features for date $T$ strictly utilize historical data available on or before date $T$. Future return targets (`future_return_1d`, `future_return_5d`, etc.) are computed separately as forward targets for model training.

### 11. Predictive Modeling Research Layer (`src/modeling/`)
- `PredictiveModelManager` performs walk-forward time-series validation (no random temporal shuffling) using baseline machine learning models (Random Forest) and logs evaluation metrics (Accuracy, Precision, Recall, F1 score).

### 12. Backtesting Engine (`src/backtesting/`)
- `BacktestingEngine` simulates strategy trades based on stock scores, incorporating transaction fees (0.1%), slippage (0.05%), position sizing assumptions, holding periods, cumulative returns, max drawdowns, and Sharpe ratios.

### 13. Daily Reporting & Orchestration (`src/reporting/` & `src/pipeline/`)
- `ReportGenerator` constructs daily Markdown reports (`reports/daily/YYYY-MM-DD.md`) and structured JSON outputs (`data/analysis/daily/YYYY-MM-DD.json`).
- `DailyPipelineRunner` coordinates execution end-to-end, logging duration and metrics.
- `git_commit.py` manages automated Git staging and commits.

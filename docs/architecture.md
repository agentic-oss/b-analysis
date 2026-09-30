# Architecture Documentation

## Overview

The Daily Indian Stock Market Analysis Pipeline is designed as a modular, decoupled data processing and quantitative analytics platform. The codebase follows strict separation of concerns, ensuring that ingestion, validation, technical analysis, feature engineering, machine learning modeling, and reporting can be independently extended or replaced.

---

## Component Architecture

### 1. Ingestion Layer (`src/ingestion/`)
- Abstract base class `MarketDataProvider` defines standardized interface for market data retrieval.
- Concrete implementation `YFinanceProvider` handles rate limits, automatic retry logic with exponential backoff, and standardized output column schemas.

### 2. Validation Layer (`src/validation/`)
- `DataValidator` checks incoming OHLC data against logical constraints (e.g. High >= Low, Close > 0).
- Identifies missing trading days, duplicate records, volume spikes, and unexplained price gaps.
- Produces daily structured quality reports (`data/quality/YYYY-MM-DD.json`). Raw data is preserved without silent mutation.

### 3. Storage Layer (`src/storage/`)
- `StorageManager` coordinates persistence across `data/raw/`, `data/processed/`, `data/features/`, `data/analysis/`, `data/predictions/`, and `reports/`.
- Uses Parquet format for optimized historical data storage and CSV/JSON for human-readable outputs.

### 4. Technical Indicators & Patterns (`src/indicators/`, `src/patterns/`)
- `TechnicalIndicators` computes deterministic moving averages (SMA 5, 10, 20, 50, 100, 200; EMA 9, 20, 50, 200), momentum (RSI 14, Stochastic RSI, MACD, ROC), volatility (ATR 14, 20-day annualized volatility, Bollinger Bands), and volume indicators (OBV, A/D, Relative Volume).
- `PatternEngine` identifies crossovers (Golden/Death Cross), 20-day breakouts/breakdowns, volume spikes, and support/resistance levels.
- `AnalogueFinder` locates historical market setups with matching RSI, volatility, and MA distances to build forward empirical return distributions over 1D, 3D, 5D, 10D, and 20D horizons.

### 5. Market Regime & Sector Analysis (`src/market/`, `src/sectors/`)
- `MarketRegimeAnalyzer` assesses index trends and market breadth (% stocks above 20/50/200 DMA, advance/decline ratio, new 52-week highs/lows) to classify market regime (Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish).
- `SectorAnalyzer` ranks tracked sector indices by multi-period returns, relative strength vs NIFTY 50, and momentum scores.

### 6. Scoring & Fundamentals (`src/scoring/`, `src/fundamentals/`)
- `StockScorer` computes transparent 0–100 composite stock ratings from weighted component scores.
- `FundamentalAnalyzer` enriches stocks with optional fundamental metrics (P/E, P/B, ROE, Debt/Equity, Growth).

### 7. Feature Engineering, ML & Backtesting (`src/features/`, `src/modeling/`, `src/backtesting/`)
- `FeatureEngine` builds clean tabular feature datasets for date $T$ strictly using information available up to date $T$.
- `PredictionEngine` evaluates baseline predictive models using walk-forward time-series validation and produces probabilistic directional signals.
- `Backtester` simulates trading performance accounting for transaction costs and slippage.

### 8. Reporting & Orchestration (`src/reporting/`, `src/pipeline/`)
- `ReportGenerator` produces daily Markdown reports (`reports/daily/YYYY-MM-DD.md`) and stable JSON outputs (`data/analysis/daily/YYYY-MM-DD.json`).
- `run_pipeline` orchestrates daily workflow execution.

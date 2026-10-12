# System Architecture & Design

## Overview
The pipeline follows a clean, modular architecture designed for high maintainability, reproducibility, and extensibility.

## Core Modules

1. **Ingestion Layer (`src/ingestion/`)**:
   - `MarketDataProvider`: Abstract base class specifying standard methods.
   - `YFinanceProvider`: Concrete implementation utilizing `yfinance` with retries, exponential backoff, and rate-limit safety.

2. **Validation Module (`src/validation/`)**:
   - `DataValidator`: Checks OHLC consistency, detects zero/negative prices, flag extreme return spikes, volume spikes, and data gaps. Generates data quality JSON logs.

3. **Storage Manager (`src/storage/`)**:
   - `StorageManager`: Manages reading/writing across `data/` subdirectories (`raw`, `processed`, `features`, `analysis`, `predictions`, `quality`) and `reports/`. Supports Parquet, CSV, and JSON formats with deduplication.

4. **Technical Indicators (`src/indicators/`)**:
   - `TechnicalIndicators`: Deterministically calculates SMAs, EMAs, RSI, Stochastic RSI, MACD, ATR, Volatility, Bollinger Bands, OBV, Accumulation/Distribution, and 52W distances.

5. **Market Regime & Sector Analysis (`src/market/`, `src/sectors/`)**:
   - `MarketRegimeAnalyzer`: Computes NIFTY trends, market breadth (% above 50 DMA), advance/decline ratio, and classifies regime (Strong Bullish to Strong Bearish).
   - `SectorAnalyzer`: Ranks sector performance across daily, weekly, and monthly horizons.

6. **Fundamental Analysis & Composite Scoring (`src/fundamentals/`, `src/scoring/`)**:
   - `FundamentalAnalyzer`: Evaluates valuation, profitability, growth, and leverage metrics.
   - `CompositeScorer`: Computes transparent 0-100 composite score with 5-tier classification labels (Very Strong to Very Weak).

7. **Pattern Analogues & Machine Learning Features (`src/patterns/`, `src/features/`)**:
   - `PatternAnalogueEngine`: Identifies matching historical setups and computes forward conditional return statistics.
   - `FeatureEngineer`: Builds point-in-time feature matrices with anti-leakage target variables (`future_return_1d` to `20d`).

8. **Modeling, Backtesting & Reporting (`src/modeling/`, `src/backtesting/`, `src/reporting/`)**:
   - `MLPredictionModel`: Train baseline ML models on chronological time-series splits.
   - `Backtester`: Simulates strategy performance with slippage and transaction costs.
   - `ReportGenerator`: Generates Markdown daily reports and JSON analysis files.

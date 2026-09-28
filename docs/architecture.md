# System Architecture Documentation

## Overview

The Indian Stock Market Data & Deep Analysis Pipeline is designed as a modular, decoupled daily ETL and analytical machine learning engine. It ingests price and fundamental data for tracked Indian equities and indices, validates data quality, builds partitioned historical datasets, computes technical and market regime features, matches historical analogues, trains walk-forward predictive baseline models, and outputs human- and machine-readable daily research reports.

```
[ Data Ingestion ] ---> [ Data Validation ] ---> [ Storage Engine ]
                                                         |
                                                         v
[ Report Generation ] <--- [ Scoring & Prediction ] <--- [ Indicators & Features ]
(Markdown / JSON)         (Analogue & RF Models)         (Technical / Regime / Sector)
```

## Module Responsibilities

1. **`src/ingestion/provider.py` (`MarketDataProvider` / `YFinanceProvider`)**
   - Fetches historical daily OHLCV prices, volume, corporate actions, and fundamental financial metrics.
   - Handles rate limits, retries with exponential backoff, and missing symbol fallbacks.

2. **`src/validation/validator.py` (`DataValidator`)**
   - Audits incoming market data for date sanity, logical OHLC relationships ($Low \le Open, Close \le High$), price positivity, zero volume, and price/volume spikes.
   - Outputs daily data quality reports to `data/quality/YYYY-MM-DD.json`.

3. **`src/storage/store.py` (`StorageEngine`)**
   - Manages raw CSV/Parquet files (`data/raw/YYYY/MM/YYYY-MM-DD/`) and accumulated processed time-series (`data/processed/prices/`).
   - Ensures idempotent append/update operations to prevent duplicate records.

4. **`src/indicators/technical.py` (`TechnicalAnalysisEngine`)**
   - Computes deterministic technical indicators: SMAs (5, 10, 20, 50, 100, 200), EMAs (9, 20, 50, 200), RSI (14), Stochastic RSI, MACD, ATR, Historical Volatility, Bollinger Bands, OBV, A/D Line, and price structure metrics.
   - Identifies pattern signals: Golden/Death Crosses, 20-day High/Low Breakouts, Bollinger Band breakouts, unusual volume.

5. **`src/market/regime.py` (`MarketRegimeAnalyzer`) & `src/sectors/sector_analysis.py` (`SectorAnalyzer`)**
   - Classifies market environment into *Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish* using NIFTY 50 trend alignment and market breadth (% above 20/50/200 DMA, A/D ratio).
   - Ranks NIFTY sector indices by momentum score, relative strength vs NIFTY 50, and relative volume.

6. **`src/fundamentals/fundamental_analysis.py` (`FundamentalAnalyzer`) & `src/scoring/composite_score.py` (`CompositeScorer`)**
   - Evaluates valuation (P/E, P/B), profitability (ROE, margins), solvency (D/E), and growth metrics.
   - Calculates a transparent composite stock score (0–100) with configurable weights across 7 factors.

7. **`src/patterns/historical_analogue.py` (`HistoricalAnalogueEngine`)**
   - Scans historical records for similar technical setups (RSI, volatility, relative volume) and calculates empirical forward return statistics over 1D, 3D, 5D, 10D, and 20D horizons.

8. **`src/features/engineer.py` (`FeatureEngineer`)**
   - Builds reusable ML feature matrices (`data/features/daily/YYYY-MM-DD.parquet`) with target columns ($t + h$) explicitly created without lookahead bias.

9. **`src/modeling/predictions.py` (`PredictionEngine`) & `src/backtesting/engine.py` (`BacktestEngine`)**
   - Implements Random Forest classifiers using walk-forward time-series splitting to estimate directional probabilities (0–100 confidence).
   - Provides backtesting with transaction cost (0.1%) and slippage (0.05%) assumptions.

10. **`src/pipeline/daily_pipeline.py`**
    - Master end-to-end orchestrator supporting `--date YYYY-MM-DD` and `--commit` flags.

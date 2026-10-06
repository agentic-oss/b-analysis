# System Architecture Documentation

## Overview

The Daily Indian Stock Market Analysis Pipeline is designed as a modular, decoupled ETL and research framework.

```
[ Data Ingestion ] ---> [ Data Validation ] ---> [ Storage Manager ]
                                                        |
                                                        v
[ Feature Builder ] <--- [ Scoring & Analogues ] <--- [ Indicators & Regimes ]
         |
         v
[ JSON & Markdown Reports ]
```

## Core Modules

1. **Ingestion (`src/ingestion/`)**:
   - `MarketDataProvider`: Base interface.
   - `YFinanceProvider`: Implements retries, exponential backoff, rate limiting, and exception logging.

2. **Validation (`src/validation/`)**:
   - `DataValidator`: Checks negative prices, impossible OHLC (high < low, high < open, etc.), volume anomalies, and gap jumps.
   - Produces `data/quality/YYYY-MM-DD.json`.

3. **Storage (`src/storage/`)**:
   - `StorageManager`: Handles Parquet and CSV file persistence under `data/raw/`, `data/processed/`, `data/features/`, `data/analysis/`, and `data/quality/`.

4. **Indicators (`src/indicators/`)**:
   - `TechnicalIndicators`: Calculates trend, momentum, volatility, volume, price structures, and breakout signals deterministically.

5. **Market & Sector Analysis (`src/market/`, `src/sectors/`, `src/fundamentals/`)**:
   - `MarketRegimeAnalyzer`: Rule-based regime scoring and market breadth (% stocks above 20/50/200 DMA, A/D ratio).
   - `SectorAnalyzer`: Sector momentum rankings and relative strength vs NIFTY.
   - `FundamentalAnalyzer`: Normalizes company valuation, profitability, and growth metrics.

6. **Scoring, Analogues & Modeling (`src/scoring/`, `src/patterns/`, `src/modeling/`)**:
   - `StockScorer`: Transparent 0–100 composite score.
   - `PatternAnalogueFinder`: Nearest-neighbor historical setup matching for forward return empirical distributions.
   - `ProbabilisticSignalGenerator`: Synthesizes directional bias labels with confidence scores.
   - `BaselineMLModels`: Walk-forward time-series split prediction models.

7. **Pipeline Orchestrator (`src/pipeline/`)**:
   - `DailyPipeline`: Coordinates ingestion, processing, feature creation, and report generation.

# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, long-running Indian stock market data ingestion, validation, deep analytics, and ML-ready feature generation pipeline.

Designed to run every trading day, accumulate high-quality market observations, calculate technical, fundamental, market regime, and sector metrics, identify historical analogues, and generate daily research reports and ML datasets without look-ahead bias.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────┐
                        │        config/stocks.json           │
                        │       config/holidays.json          │
                        └──────────────────┬──────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DAILY MARKET PIPELINE                                  │
│                                (src/pipeline/daily_pipeline.py)                        │
├───────────────────┬──────────────────┬─────────────────┬───────────────────────────────┤
│ 1. Data Ingestion │ 2. Data Quality  │ 3. Deep Analysis│ 4. Outputs & Artifacts        │
│    (yfinance)     │    Validation    │    - Technicals │    - Parquet & CSV Datasets   │
│                   │                  │    - Regime     │    - ML Features Dataset     │
│                   │                  │    - Sectors    │    - JSON Machine Outputs    │
│                   │                  │    - Scoring    │    - Markdown Daily Report   │
│                   │                  │    - Analogues  │    - Git Auto-Commit          │
└───────────────────┴──────────────────┴─────────────────┴───────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
git clone <repository_url>
cd b-analysis
pip install -r requirements.txt # or pip install yfinance pandas numpy scikit-learn pyarrow pytest
```

### Running the Pipeline Locally

To run the pipeline for a specific trading date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10
```

To run with automatic Git commit of generated artifacts:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10 --auto-commit
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/
```

---

## Key Features

1. **Configurable Universe (`config/stocks.json`)**
   - Supports NSE and BSE equities and major indices (NIFTY 50, NIFTY Next 50, Bank, IT, Auto, Pharma, FMCG, Metal, Realty, Energy, Financial Services).

2. **Data Ingestion & Provider Abstraction (`src/ingestion/`)**
   - Decoupled `MarketDataProvider` interface with concrete `YFinanceProvider` featuring rate-limit backoff, timeouts, and retry logic.

3. **Data Quality & Validation (`src/validation/`)**
   - Detects OHLC price anomalies, duplicate dates, missing trading days, zero/negative prices, and unusual volume spikes. Saves quality reports to `data/quality/YYYY-MM-DD.json`.

4. **Storage Architecture (`src/storage/`)**
   - Optimized directory hierarchy using Parquet for fast time-series query performance and CSV/JSON for human inspection. Metadata enriched and deduplicated.

5. **Technical Indicators & Signal Engine (`src/indicators/`)**
   - Calculates SMAs (5, 10, 20, 50, 100, 200), EMAs (9, 20, 50, 200), RSI 14, Stochastic RSI, MACD, ATR, HV, Bollinger Bands, OBV, A/D line, Relative Volume, 52w High/Low distances, golden/death crosses, and 20-day breakouts/breakdowns.

6. **Market Regime & Sector Analysis (`src/market/`, `src/sectors/`)**
   - Evaluates NIFTY/Bank NIFTY trends, market breadth (% stocks above 20/50/200 DMA, A/D ratio, new highs/lows) to classify market regime into: *Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish*.
   - Ranks sector performance, momentum, and relative strength vs NIFTY.

7. **Transparent Stock Scoring (`src/scoring/`, `src/fundamentals/`)**
   - Multi-factor transparent score (0–100) combining trend, momentum, volume, relative strength, regime, sector, and fundamentals.

8. **Historical Pattern Analogue Matching (`src/patterns/`)**
   - Matches current market setups against historical observations and computes empirical forward outcome distributions (1, 3, 5, 10, 20 trading days).

9. **Feature Engineering for Machine Learning (`src/features/`)**
   - Generates ML-ready datasets preventing look-ahead bias and aligning future returns separately.

10. **Machine Learning Baselines & Backtesting (`src/modeling/`, `src/backtesting/`)**
    - Evaluates baseline models (Logistic Regression, Random Forest) using walk-forward time-series splits.
    - Includes a realistic backtester accounting for transaction fees, slippage, and position sizing.

11. **Automated Daily Reporting & GitHub Actions (`.github/workflows/daily-market-analysis.yml`)**
    - Generates human-readable Markdown (`reports/daily/YYYY-MM-DD.md`) and machine-readable JSON (`data/analysis/daily/YYYY-MM-DD.json`).
    - GitHub Actions schedule executes automatically on Indian trading days.

---

## Detailed Documentation

- [Architecture Guide](docs/architecture.md)
- [Data Schema Specifications](docs/data-schema.md)
- [Methodology & Technical Indicators](docs/methodology.md)
- [Prediction & Historical Analogue Framework](docs/prediction.md)
- [Backtesting Framework & Guidelines](docs/backtesting.md)

---

## Financial Safeguards & Disclaimer

This engine produces probabilistic empirical signals and statistical research outputs. **It does not guarantee future price movements or stock performance.** Market predictions should be treated strictly as probabilistic research indicators rather than deterministic forecasts.

# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade daily stock market ingestion, validation, feature engineering, research modeling, and reporting system tailored for Indian equities (NSE & BSE) and major market indices.

---

## Key Features

1. **Configurable Universe**: Fully JSON-configured stock and index tracking (`config/stocks.json`).
2. **Robust Data Ingestion**: Modular `MarketDataProvider` abstraction with `YFinanceProvider` implementing exponential backoff retries and error logging.
3. **Automated Data Validation**: OHLC logical integrity checks, missing data detection, volume anomalies, stock split checks, and daily data quality reports (`data/quality/YYYY-MM-DD.json`).
4. **Historical Dataset Storage**: Partitioned Parquet and CSV/JSON storage (`data/raw/`, `data/processed/`, `data/features/`).
5. **Deterministic Technical Analysis**: Trend (SMA, EMA), Momentum (RSI, Stoch RSI, MACD, ROC), Volatility (ATR, Hist Vol, Bollinger Bands), Volume (Relative Vol, OBV, A/D), and Key Price Events (Golden/Death Cross, Breakouts, Breakdowns).
6. **Market Regime Analysis**: Rule-based classification (Strong Bullish to Strong Bearish) based on NIFTY/BANKNIFTY moving averages and market breadth metrics (% above 20/50/200 DMA, Advance/Decline ratio).
7. **Sector Analysis**: Daily/Weekly/Monthly relative strength vs NIFTY, momentum scoring, rankings, and sector constituent leaders/laggards.
8. **Transparent Stock Scoring**: 0–100 composite stock score combining weighted sub-scores (Technical Trend, Momentum, Volume, Relative Strength, Volatility, Market Regime, Sector, and Fundamentals).
9. **Historical Pattern Analysis (Analogues)**: Empirical setup matching looking back across history to calculate forward return probabilities over 1, 3, 5, 10, and 20 trading days.
10. **ML Feature Engineering**: Strict prevention of look-ahead bias and data leakage for historical observations and forward prediction targets (`future_return_1d`, etc.).
11. **Prediction Research Layer**: Baseline directional prediction model (Random Forest / Logistic Regression) with walk-forward time-series cross-validation.
12. **Backtesting Framework**: Long-only simulation engine incorporating transaction costs, slippage, position sizing, Sharpe ratio, and Max Drawdown calculation.
13. **Dual Output Formats**: Human-readable Markdown summary reports (`reports/daily/YYYY-MM-DD.md`) and machine-readable JSON schemas (`data/analysis/daily/YYYY-MM-DD.json`).
14. **GitHub Actions Automation**: Daily scheduled execution post-market close with automatic git commits and push workflow.

---

## Quick Start & Local Execution

### 1. Requirements & Setup
Python 3.10+ required. Install dependencies:
```bash
pip install yfinance pandas scikit-learn pyarrow pytest
```

### 2. Run Pipeline Locally
Execute daily pipeline for today or a target date:
```bash
# Run for today
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py

# Run for a specific historical date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-03-06
```

### 3. Run Automated Tests
```bash
PYTHONPATH=. pytest tests/
```

---

## Directory Structure

```
├── config/
│   ├── stocks.json        # Configured stock & index universe
│   ├── config.json        # Technical parameters, score weights, lookback settings
│   └── holidays.json      # NSE trading holidays calendar
├── data/
│   ├── raw/               # Raw ingested parquet data partitioned by YYYY/MM/YYYY-MM-DD/
│   ├── processed/         # Normalized historical prices & indices
│   ├── features/          # ML-ready daily feature datasets
│   ├── quality/           # Daily data quality validation reports
│   └── analysis/          # Machine-readable daily JSON outputs
├── reports/
│   └── daily/             # Daily Markdown human-readable summary reports
├── src/
│   ├── ingestion/         # Market data provider abstraction & yfinance provider
│   ├── validation/        # OHLC logic & volume anomaly validator
│   ├── storage/           # Parquet & CSV/JSON storage manager
│   ├── indicators/        # Technical indicators (SMA, EMA, RSI, MACD, ATR, BB)
│   ├── market/            # Market regime & breadth analyzer
│   ├── sectors/           # Sector relative strength, ranking, & leaders/laggards
│   ├── fundamentals/      # Fundamental ratios & health scorer
│   ├── scoring/           # Transparent 0-100 composite stock scorer
│   ├── patterns/          # Historical setup analogue matcher & forward stats
│   ├── features/          # ML feature engineering (leakage-free)
│   ├── modeling/          # Walk-forward prediction baseline models
│   ├── backtesting/       # Trading strategy simulator with transaction costs
│   ├── reporting/         # Report generator for MD & JSON schema
│   └── pipeline/          # End-to-end daily runner script
├── docs/                  # Detailed architecture & methodology documentation
└── tests/                 # Comprehensive Pytest test suite
```

---

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Data Schema Specification](docs/data-schema.md)
- [Scoring & Regime Methodology](docs/methodology.md)
- [Prediction & Research Layer](docs/prediction.md)
- [Backtesting Framework](docs/backtesting.md)

---

## Financial Safeguards & Disclaimer

This system is built solely for quantitative analysis, financial data engineering, and statistical research purposes.
- All forward-looking directional signals and historical probabilities represent empirical statistical estimates, NOT guaranteed forecasts or investment advice.
- Backtested performance metrics reflect hypothetical historical simulations.

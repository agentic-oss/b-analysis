# Indian Stock Market Data & Deep Analysis Pipeline

Production-quality automated quantitative research, historical dataset builder, technical analysis, stock scoring, pattern analogue engine, and feature engineering pipeline for Indian equities (NSE/BSE) and indices.

## System Architecture Overview

```
                          ┌───────────────────────────┐
                          │   config/stocks.json      │
                          │   config/config.json      │
                          │   config/holidays.json    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  src/ingestion/           │
                          │  (YFinanceProvider)       │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  src/validation/          │ ──► data/quality/YYYY-MM-DD.json
                          │  (DataValidator)          │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌─────────────────────────┬─────────────┴─────────────┬──────────────────────────┐
│                         │                           │                          │
▼                         ▼                           ▼                          ▼
src/indicators/           src/market/                 src/sectors/               src/fundamentals/
(TechnicalIndicators)     (MarketRegimeAnalyzer)      (SectorAnalyzer)           (FundamentalAnalyzer)
│                         │                           │                          │
└─────────────────────────┼───────────────────────────┴──────────────────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │  src/scoring/           │
             │  (StockScorer 0-100)    │
             └────────────┬────────────┘
                          │
                          ▼
┌─────────────────────────┴───────────────────────────┬──────────────────────────┐
│                                                     │                          │
▼                                                     ▼                          ▼
src/patterns/                                         src/modeling/              src/features/
(HistoricalPatternEngine)                             (PredictorModule / ML)     (FeatureBuilder)
│                                                     │                          │
└─────────────────────────┬───────────────────────────┴──────────────────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │  src/reporting/         │
             │  (ReportGenerator)      │
             └────────────┬────────────┘
                          │
                          ├───────────────────────────┐
                          ▼                           ▼
            reports/daily/YYYY-MM-DD.md     data/analysis/daily/YYYY-MM-DD.json
```

---

## Features & Capabilities

1. **Multi-Asset Ingestion & Fallbacks**: Ingests NIFTY 50 benchmark, major sector indices (`^NSEBANK`, `^CNXIT`, `^CNXAUTO`, etc.), and equities from NSE/BSE with rate-limiting, retries, and timeout handling.
2. **Data Quality Validation**: Validates OHLC sanity, negative/zero prices, missing trading days, price gaps, volume spikes, and generates daily quality logs in `data/quality/YYYY-MM-DD.json`.
3. **Multi-Tiered Parquet & CSV Storage**: Preserves raw data partitioned by `data/raw/YYYY/MM/YYYY-MM-DD/` and updates cumulative datasets under `data/processed/prices/`.
4. **Deterministic Technical Analysis**: Calculates Trend (SMA/EMA), Momentum (RSI, Stoch RSI, MACD, ROC), Volatility (ATR, Historical Volatility, Bollinger Bands), Volume (OBV, A/D, Relative Volume), Price Structure, and Technical Events (Golden/Death Cross, 20d Breakouts/Breakdowns).
5. **Market Regime Classification**: Classifies environment (`Strong Bullish` to `Strong Bearish`) using benchmark trend, market breadth (% above 20/50/200 DMA), advance/decline ratios, and sector momentum.
6. **Transparent Composite Stock Scoring (0–100)**: Unifies technical trend, momentum, volume, relative strength, volatility, market regime, sector momentum, and fundamentals into a transparent weighted score.
7. **Historical Pattern Analogue Engine**: Finds historical trading setups matching current RSI/volatility/MA configurations and computes empirical forward return distributions (1d, 3d, 5d, 10d, 20d).
8. **Leakage-Free Feature Engineering**: Constructs standardized ML feature matrices (`data/features/daily/`) strictly isolating features at time $T$ from future return targets ($T+1..T+N$).
9. **Daily Markdown & Machine-Readable JSON Reports**: Automatically generates human-readable research reports (`reports/daily/YYYY-MM-DD.md`) and JSON outputs (`data/analysis/daily/YYYY-MM-DD.json`).
10. **Automated CI/CD Workflows**: GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`) runs after Indian market close, executes tests, and auto-commits generated datasets.

---

## Directory Structure

```
├── .github/
│   └── workflows/
│       └── daily-market-analysis.yml
├── config/
│   ├── config.json          # Main pipeline configuration & weights
│   ├── holidays.json        # Indian stock market holiday calendar
│   └── stocks.json          # Configurable stock & index universe
├── data/                    # (Auto-generated datasets & outputs)
│   ├── raw/                 # YYYY/MM/YYYY-MM-DD raw parquet files
│   ├── processed/           # Cumulative historical prices & indices
│   ├── features/            # Daily engineered ML feature matrices
│   ├── analysis/            # Daily machine-readable JSON outputs
│   └── quality/             # Daily data quality diagnostic reports
├── docs/                    # Detailed technical documentation
│   ├── architecture.md
│   ├── backtesting.md
│   ├── data-schema.md
│   ├── methodology.md
│   └── prediction.md
├── reports/
│   └── daily/               # Daily human-readable Markdown research reports
├── scripts/
│   └── auto_commit.sh       # Local & CI git commit automation script
├── src/
│   ├── backtesting/         # Event-driven backtesting engine
│   ├── features/            # ML feature builder (no look-ahead bias)
│   ├── fundamentals/        # Valuation & financial performance analyzer
│   ├── indicators/          # Deterministic technical indicators
│   ├── ingestion/           # Data provider abstraction & YFinance client
│   ├── market/              # Market regime & breadth classification
│   ├── modeling/            # Forward signals & walk-forward ML models
│   ├── patterns/            # Historical analogue pattern matching engine
│   ├── pipeline/            # End-to-end DailyPipeline orchestrator
│   ├── reporting/           # Markdown report & JSON schema generator
│   ├── scoring/             # Transparent composite stock scorer (0-100)
│   ├── sectors/             # Sector relative strength & performance analyzer
│   ├── storage/             # File storage manager (Parquet/CSV/JSON)
│   └── validation/          # Data quality validator
├── tests/                   # Comprehensive pytest test suite
└── README.md
```

---

## Quick Start & Local Execution

### 1. Requirements & Installation

```bash
python3 -m pip install --upgrade pip
pip install pandas numpy yfinance scikit-learn pyarrow pytest requests pyyaml
```

### 2. Running the Daily Pipeline

To execute the pipeline for today's trading date or a specific historical date:

```bash
# Run for current date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py

# Run for a specific historical date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-09-29
```

### 3. Running Automated Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## Methodology & Financial Safeguards

- **Probabilistic Research Focus**: Directional biases and score outputs are empirical quantitative signals, not price guarantees.
- **Strict Look-Ahead Bias Prevention**: Feature matrices at date $T$ never contain or observe data from dates $>T$. Forward return targets are computed strictly separately.
- **Execution Cost Realism**: Strategy backtests account for transaction commissions ($0.1\%$) and execution slippage ($0.05\%$).
- **Dynamic Stock Universe**: The stock universe is configured via `config/stocks.json` and can be expanded without code changes.

For further details, see the documentation under `docs/`.

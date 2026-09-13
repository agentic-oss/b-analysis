# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade daily data ingestion, validation, technical/fundamental scoring, market regime classification, historical analogue matching, and predictive feature engineering engine for Indian equities and sector indices (NSE & BSE).

---

## 🏗 Architecture Overview

The system is structured into modular layers designed to continuously build an un-leaked historical dataset suitable for training future Machine Learning models.

```
src/
├── ingestion/        # MarketDataProvider & YFinanceProvider implementations
├── validation/       # DataValidator for OHLC, bounds, duplicates, gaps & volume spikes
├── storage/          # DataStorage parquet/CSV/JSON snapshot & incremental persistence
├── indicators/       # TechnicalIndicators calculation engine (Trend, Momentum, Volatility, Volume)
├── fundamentals/     # FundamentalsCollector for corporate financial metrics
├── market/           # MarketRegimeDetector for NIFTY/BANK NIFTY & stock universe breadth
├── sectors/          # SectorAnalyzer for sector performance & relative strength vs NIFTY
├── scoring/          # StockScorer transparent composite 0-100 scoring engine
├── patterns/         # HistoricalPatternMatcher empirical analogue probability framework
├── features/         # FeatureBuilder leakage-free ML dataset builder
├── modeling/         # PredictionResearchLayer walk-forward baseline ML validation & directional signals
├── backtesting/      # Backtester framework accounting for slippage & transaction costs
├── reporting/        # DailyReportGenerator human-readable Markdown report generator
├── pipeline/         # daily_pipeline orchestrator entry point
└── utils/            # GitIntegrator & utility modules
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Required packages: `yfinance`, `pandas`, `numpy`, `scikit-learn`, `pyarrow`, `pytest`

### Installation

```bash
pip install yfinance pandas numpy scikit-learn pyarrow pytest
```

---

## ⚙️ Configuration

- `config/stocks.json`: Tracked stock tickers, exchanges, names, and sector indices.
- `config/config.json`: Technical indicator parameters, score weights, rate limits, and backtest parameters.
- `config/holidays.json`: Calendar of declared NSE/BSE trading holidays.

---

## 🏃 Running the Pipeline Locally

Run the complete daily analysis pipeline:

```bash
python -m src.pipeline.daily_pipeline
```

Run for a specific date in dry-run mode (without committing to Git):

```bash
python -m src.pipeline.daily_pipeline --date 2026-01-02 --dry-run
```

---

## 🧪 Testing

Execute automated unit and integration tests:

```bash
python3 -m pytest tests/
```

---

## 📊 Data Outputs & Schema

Every daily execution produces machine-readable and human-readable artifacts:

- **Raw Data Snapshots:** `data/raw/YYYY/MM/YYYY-MM-DD/{TICKER}.csv`
- **Processed Prices:** `data/processed/prices/{TICKER}.parquet` & `.csv`
- **Data Quality Report:** `data/quality/YYYY-MM-DD.json`
- **Machine-Readable Analysis:** `data/analysis/daily/YYYY-MM-DD.json`
- **Feature Matrix:** `data/features/daily/YYYY-MM-DD.parquet` & `.csv`
- **Human-Readable Report:** `reports/daily/YYYY-MM-DD.md`

---

## 🤖 Machine Learning & Research Safeguards

1. **Leakage Prevention Guarantee:** Features calculated on date `T` only use information available on or before date `T`. Target variables (`target_future_return_Kd`) are generated via `shift(-k)` and are excluded from feature vectors.
2. **Temporal Walk-Forward Validation:** Baseline models use strict time-series splits (`RandomForestClassifier`) without temporal shuffling to prevent survivorship or look-ahead bias.
3. **Empirical Probabilities:** Forward directional signals are represented as empirical probability estimates derived from historical analogues rather than deterministic price guarantees.

---

## 📜 Documentation

For detailed methodology, schemas, and architecture documentation, refer to:
- `docs/architecture.md`
- `docs/data-schema.md`
- `docs/methodology.md`
- `docs/prediction.md`
- `docs/backtesting.md`

# Data Schema Specifications

## Data Directories

- `data/processed/prices/<ticker>.parquet`: Processed historical daily OHLCV, moving averages, and metadata (`ticker`, `data_provider`, `ingestion_timestamp`).
- `data/quality/<YYYY-MM-DD>.json`: Data audit with `records_processed`, `records_valid`, `warnings`, and `errors`.
- `data/features/daily/<YYYY-MM-DD>.parquet`: Feature matrix for ML training with `future_return_Nd` targets.
- `data/analysis/daily/<YYYY-MM-DD>.json`: Aggregated analysis containing `market` regime, `sectors` rankings, and `stocks` deep dive.
- `reports/daily/<YYYY-MM-DD>.md`: Human-readable daily summary report.

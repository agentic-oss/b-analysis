import os
import sys
import json
import logging
import argparse
from datetime import datetime
import pandas as pd

from src.ingestion.yfinance_provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.historical_storage import HistoricalStorage
from src.indicators.technical import TechnicalIndicators
from src.fundamentals.fundamental_analyzer import FundamentalAnalyzer
from src.market.market_regime import MarketRegimeAnalyzer
from src.sectors.sector_analyzer import SectorAnalyzer
from src.scoring.stock_scorer import StockScorer
from src.patterns.historical_analogue import HistoricalAnalogueEngine
from src.features.feature_engineer import FeatureEngineer
from src.modeling.predictive_model import PredictiveModelManager
from src.backtesting.backtest_engine import BacktestingEngine
from src.reporting.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DailyPipelineRunner")


class DailyPipelineRunner:
    """
    Main Orchestrator for the Daily Indian Stock Market Data & Analysis Pipeline.
    Runs ingestion -> validation -> storage -> technical/fundamental indicators ->
    market regime -> sector analysis -> composite scoring -> historical analogue matching ->
    leakage-free ML feature generation -> baseline model evaluation -> backtesting -> report generation.
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        with open(os.path.join(config_dir, "stocks.json")) as f:
            self.stocks_config = json.load(f)
        with open(os.path.join(config_dir, "config.json")) as f:
            self.app_config = json.load(f)
        with open(os.path.join(config_dir, "holidays.json")) as f:
            self.holidays_config = json.load(f)

        self.provider = YFinanceProvider()
        self.validator = DataValidator()
        self.storage = HistoricalStorage()
        self.fund_analyzer = FundamentalAnalyzer()
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.scorer = StockScorer()
        self.analogue_engine = HistoricalAnalogueEngine()
        self.feature_engineer = FeatureEngineer()
        self.model_mgr = PredictiveModelManager()
        self.backtester = BacktestingEngine()
        self.reporter = ReportGenerator()

    def run_pipeline(self, target_date: str = None) -> str:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"--- Starting Daily Pipeline Execution for Date: {target_date} ---")

        # 1. Ingestion & Validation for Indices
        index_dfs = {}
        validation_results = {}

        for idx_item in self.stocks_config.get("indices", []):
            if not idx_item.get("enabled", True):
                continue
            sym = idx_item["symbol"]
            logger.info(f"Fetching index data: {sym}")
            raw_df = self.provider.get_index_data(sym)
            if not raw_df.empty:
                val_res = self.validator.validate_ohlcv(raw_df, sym)
                validation_results[sym] = val_res
                ind_df = TechnicalIndicators.calculate_all(raw_df)
                self.storage.update_processed_history(sym, ind_df, category="indices")
                index_dfs[sym] = ind_df

        nifty_df = index_dfs.get("^NSEI", pd.DataFrame())
        bank_nifty_df = index_dfs.get("^NSEBANK", pd.DataFrame())

        # Sector indices map
        sector_dfs = {}
        for idx_item in self.stocks_config.get("indices", []):
            sym = idx_item["symbol"]
            sec_name = idx_item.get("sector")
            if sec_name and sym in index_dfs:
                sector_dfs[sec_name] = index_dfs[sym]

        # 2. Ingestion, Validation, Fundamentals & Technicals for Stock Universe
        stock_dfs = {}
        stock_fundamentals = {}
        stock_analyses = []
        all_features_list = []

        for st_item in self.stocks_config.get("stocks", []):
            if not st_item.get("enabled", True):
                continue
            sym = st_item["symbol"]
            raw_sym = st_item.get("raw_symbol", sym)
            sec = st_item.get("sector", "General")

            logger.info(f"Processing stock: {sym}")
            raw_df = self.provider.get_historical_prices(sym)
            if raw_df.empty:
                logger.warning(f"No price data retrieved for {sym}, skipping.")
                continue

            self.storage.save_raw_daily(target_date, sym, raw_df)
            val_res = self.validator.validate_ohlcv(raw_df, sym, holidays=self.holidays_config.get("holidays", []))
            validation_results[sym] = val_res

            # Calculate Technical Indicators
            tech_df = TechnicalIndicators.calculate_all(raw_df)
            stock_dfs[sym] = tech_df

            # Fundamentals
            funds = self.fund_analyzer.fetch_fundamentals(sym)
            fund_score = self.fund_analyzer.calculate_fundamental_score(funds)
            stock_fundamentals[sym] = funds

            # Feature Engineering for ML
            sec_df = sector_dfs.get(sec, pd.DataFrame())
            feat_df = self.feature_engineer.build_feature_set(tech_df, sym, nifty_df=nifty_df, sector_df=sec_df)
            if not feat_df.empty:
                all_features_list.append(feat_df)

        # Save cumulative features
        if all_features_list:
            combined_features = pd.concat(all_features_list, ignore_index=True)
            feat_path = os.path.join("data", "features", f"{target_date}.parquet")
            os.makedirs(os.path.dirname(feat_path), exist_ok=True)
            combined_features.to_parquet(feat_path, index=False)

        # 3. Market Regime Analysis
        regime_analysis = self.regime_analyzer.analyze_market_regime(nifty_df, bank_nifty_df, stock_dfs)

        # 4. Sector Analysis
        sector_rankings = self.sector_analyzer.analyze_sectors(sector_dfs, nifty_df)
        sector_score_map = {s["sector"]: s["momentum_score"] for s in sector_rankings}

        # 5. Stock Scoring, Historical Analogues & Forward Signals
        for sym, tech_df in stock_dfs.items():
            st_info = next((s for s in self.stocks_config["stocks"] if s["symbol"] == sym), {})
            sec = st_info.get("sector", "General")

            fund_score = self.fund_analyzer.calculate_fundamental_score(stock_fundamentals.get(sym, {}))
            sec_score = sector_score_map.get(sec, 50.0)
            reg_score = regime_analysis.get("regime_score", 50.0)

            score_res = self.scorer.calculate_score(
                tech_df, nifty_df, fundamental_score=fund_score, regime_score=reg_score, sector_score=sec_score
            )

            # Calculate historical scores vectorially for backtesting without look-ahead bias
            tech_df["composite_score"] = self.scorer.calculate_historical_scores(
                tech_df, nifty_df, fundamental_score=fund_score, regime_score=reg_score, sector_score=sec_score
            )
            self.storage.update_processed_history(sym, tech_df, category="prices")

            # Historical Analogue Match & Forward Probabilities
            analogue_res = self.analogue_engine.find_analogues_and_forward_stats(tech_df)

            last_row = tech_df.iloc[-1]
            stock_analyses.append({
                "symbol": sym,
                "raw_symbol": st_info.get("raw_symbol", sym),
                "sector": sec,
                "close": float(last_row["close"]),
                "return_1d_pct": round(float(last_row.get("return_1d", 0.0) or 0.0) * 100, 2),
                "relative_volume": round(float(last_row.get("relative_volume", 1.0) or 1.0), 2),
                "composite_score": score_res["composite_score"],
                "score_label": score_res["label"],
                "score_components": score_res["components"],
                "technical_signals": {
                    "golden_cross": bool(last_row.get("golden_cross", False)),
                    "death_cross": bool(last_row.get("death_cross", False)),
                    "breakout_20d": bool(last_row.get("breakout_20d", False)),
                    "breakdown_20d": bool(last_row.get("breakdown_20d", False)),
                },
                "breakout_20d": bool(last_row.get("breakout_20d", False)),
                "breakdown_20d": bool(last_row.get("breakdown_20d", False)),
                "directional_bias": analogue_res.get("directional_bias", {}),
                "historical_analogues": analogue_res,
                "fundamentals": stock_fundamentals.get(sym, {}),
            })

        # 6. ML Model Training Baseline & Walk-Forward Cross Validation
        if all_features_list:
            ml_metrics = self.model_mgr.train_and_evaluate(combined_features, target_col="future_return_5d")
        else:
            ml_metrics = {"accuracy": 0.0, "f1_score": 0.0, "status": "No feature data"}

        # 7. Backtesting
        backtest_res = self.backtester.run_backtest(stock_dfs, score_threshold=70.0)

        # 8. Generate Data Quality Report
        quality_rep = self.validator.generate_quality_report(target_date, validation_results)
        self.storage.save_quality_report(target_date, quality_rep)

        # 9. Generate Reports & JSON Outputs
        json_output = self.reporter.generate_json_output(
            target_date, regime_analysis, sector_rankings, stock_analyses, quality_rep, ml_metrics
        )
        self.storage.save_daily_analysis_json(target_date, json_output)

        md_output = self.reporter.generate_markdown_report(
            target_date, regime_analysis, sector_rankings, stock_analyses, quality_rep, ml_metrics, backtest_res
        )

        md_path = os.path.join("reports", "daily", f"{target_date}.md")
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, "w") as f:
            f.write(md_output)

        logger.info(f"--- Pipeline completed successfully for {target_date} ---")
        logger.info(f"Markdown report generated: {md_path}")
        return md_path


def main():
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Data & Deep Analysis Pipeline")
    parser.add_argument("--date", type=str, help="Target date YYYY-MM-DD", default=None)
    args = parser.parse_args()

    runner = DailyPipelineRunner()
    runner.run_pipeline(target_date=args.date)


if __name__ == "__main__":
    main()

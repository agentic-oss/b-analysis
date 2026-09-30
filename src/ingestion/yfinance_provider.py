import logging
import time
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf
from src.ingestion.base import MarketDataProvider

logger = logging.getLogger(__name__)

class YFinanceProvider(MarketDataProvider):
    """
    Market data provider implementation using yfinance with retries and rate-limit handling.
    """

    def __init__(self, retry_attempts: int = 3, retry_delay: float = 2.0, timeout: int = 30):
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.timeout = timeout

    def _execute_with_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{self.retry_attempts} failed for {func.__name__}: {e}")
                last_exception = e
                time.sleep(self.retry_delay * attempt)
        logger.error(f"All {self.retry_attempts} attempts failed for {func.__name__}")
        raise last_exception

    def get_historical_prices(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        def _fetch():
            ticker_symbol = symbol if ("." in symbol or symbol.startswith("^")) else f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False, timeout=self.timeout)
            if df.empty:
                logger.warning(f"No historical price data returned for {ticker_symbol}")
                return pd.DataFrame()

            df = df.reset_index()
            # Standardize date column
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

            # Map columns
            col_map = {
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            }
            renamed = {}
            for col in df.columns:
                if col in col_map:
                    renamed[col] = col_map[col]
            df = df.rename(columns=renamed)

            if 'adj_close' not in df.columns and 'close' in df.columns:
                df['adj_close'] = df['close']

            # Calculate estimated VWAP if not provided: (High + Low + Close) / 3
            if 'open' in df.columns and 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
                df['vwap'] = (df['high'] + df['low'] + df['close']) / 3.0
                df['turnover'] = df['vwap'] * df['volume']
            else:
                df['vwap'] = None
                df['turnover'] = None

            df['deliverable_qty'] = None
            df['delivery_pct'] = None
            df['symbol'] = symbol
            df['provider'] = 'yfinance'

            expected_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'turnover', 'deliverable_qty', 'delivery_pct', 'vwap', 'provider']
            available_cols = [c for c in expected_cols if c in df.columns]
            return df[available_cols]

        return self._execute_with_retry(_fetch)

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for sym in symbols:
            try:
                df = self.get_historical_prices(sym, start_date=(pd.Timestamp.now() - pd.Timedelta(days=7)).strftime('%Y-%m-%d'))
                if not df.empty:
                    latest = df.iloc[-1].to_dict()
                    results[sym] = latest
            except Exception as e:
                logger.error(f"Failed to fetch latest price for {sym}: {e}")
        return results

    def get_volume_data(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        if df.empty:
            return pd.DataFrame()
        return df[['symbol', 'date', 'volume', 'turnover', 'deliverable_qty', 'delivery_pct']]

    def get_corporate_actions(self, symbol: str) -> Dict[str, pd.DataFrame]:
        def _fetch():
            ticker_symbol = symbol if ("." in symbol or symbol.startswith("^")) else f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            actions = ticker.actions
            dividends = ticker.dividends
            splits = ticker.splits

            div_df = pd.DataFrame()
            if dividends is not None and not dividends.empty:
                div_df = dividends.reset_index()
                div_df.columns = ['date', 'dividend']
                div_df['date'] = pd.to_datetime(div_df['date']).dt.strftime('%Y-%m-%d')

            split_df = pd.DataFrame()
            if splits is not None and not splits.empty:
                split_df = splits.reset_index()
                split_df.columns = ['date', 'split_ratio']
                split_df['date'] = pd.to_datetime(split_df['date']).dt.strftime('%Y-%m-%d')

            return {
                'dividends': div_df,
                'splits': split_df
            }

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to fetch corporate actions for {symbol}: {e}")
            return {'dividends': pd.DataFrame(), 'splits': pd.DataFrame()}

    def get_index_data(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        return self.get_historical_prices(symbol, start_date, end_date)

    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        def _fetch():
            ticker_symbol = symbol if ("." in symbol or symbol.startswith("^")) else f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info or {}

            return {
                'symbol': symbol,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'eps': info.get('trailingEps'),
                'roe': info.get('returnOnEquity'),
                'roce': info.get('returnOnAssets'),
                'debt_to_equity': info.get('debtToEquity'),
                'revenue_growth': info.get('revenueGrowth'),
                'profit_growth': info.get('earningsGrowth'),
                'ebitda_margins': info.get('ebitdaMargins'),
                'net_margins': info.get('profitMargins'),
                'dividend_yield': info.get('dividendYield'),
                'free_cash_flow': info.get('freeCashflow'),
                'promoter_holding': info.get('heldPercentInsiders'),
                'institutional_ownership': info.get('heldPercentInstitutions'),
                'provider': 'yfinance',
                'timestamp': pd.Timestamp.now().isoformat()
            }

        try:
            return self._execute_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to fetch fundamental data for {symbol}: {e}")
            return {
                'symbol': symbol,
                'provider': 'yfinance',
                'timestamp': pd.Timestamp.now().isoformat(),
                'error': str(e)
            }

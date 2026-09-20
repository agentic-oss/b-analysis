"""Technical Indicators Engine for Stock and Index OHLCV data."""

import numpy as np
import pandas as pd
from typing import Dict, Any

class TechnicalIndicators:
    """Deterministic and reproducible calculation of technical indicators and price structure."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculates trend, momentum, volatility, volume indicators, and price structure features on a DataFrame sorted by date.

        Input df must contain: ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        if df.empty or len(df) < 5:
            return df

        res = df.copy()
        close = res['close']
        high = res['high']
        low = res['low']
        volume = res['volume']

        # 1. Trend Indicators (SMA & EMA)
        for period in [5, 10, 20, 50, 100, 200]:
            res[f'sma_{period}'] = close.rolling(window=period, min_periods=1).mean()

        for period in [9, 20, 50, 200]:
            res[f'ema_{period}'] = close.ewm(span=period, adjust=False).mean()

        # 2. Momentum Indicators
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        res['rsi_14'] = 100 - (100 / (1 + rs))
        res['rsi_14'] = res['rsi_14'].fillna(50)

        # Stochastic RSI
        rsi = res['rsi_14']
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        rsi_diff = rsi_max - rsi_min
        res['stoch_rsi'] = np.where(rsi_diff == 0, 50.0, ((rsi - rsi_min) / rsi_diff) * 100.0)

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        res['macd'] = ema_12 - ema_26
        res['macd_signal'] = res['macd'].ewm(span=9, adjust=False).mean()
        res['macd_hist'] = res['macd'] - res['macd_signal']

        # ROC & Momentum
        res['roc_10'] = close.pct_change(periods=10) * 100
        res['momentum_10'] = close.diff(periods=10)

        # 3. Volatility Indicators
        # ATR 14
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res['atr_14'] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        daily_log_returns = np.log(close / close.shift(1))
        res['volatility_20d'] = daily_log_returns.rolling(window=20, min_periods=2).std() * np.sqrt(252)
        res['volatility_20d'] = res['volatility_20d'].fillna(0)

        # Bollinger Bands (20, 2)
        sma_20 = res['sma_20']
        std_20 = close.rolling(window=20, min_periods=1).std()
        res['bb_upper'] = sma_20 + (std_20 * 2)
        res['bb_lower'] = sma_20 - (std_20 * 2)
        res['bb_width'] = np.where(sma_20 == 0, 0, (res['bb_upper'] - res['bb_lower']) / sma_20)

        # Volatility Regime
        hist_vol_med = res['volatility_20d'].rolling(window=200, min_periods=20).median()
        res['volatility_regime'] = np.where(res['volatility_20d'] > hist_vol_med * 1.25, 'High',
                                  np.where(res['volatility_20d'] < hist_vol_med * 0.75, 'Low', 'Normal'))

        # 4. Volume Indicators
        res['volume_sma_20'] = volume.rolling(window=20, min_periods=1).mean()
        res['relative_volume'] = np.where(res['volume_sma_20'] == 0, 1.0, volume / res['volume_sma_20'])
        res['volume_change'] = volume.pct_change() * 100

        # On Balance Volume (OBV)
        obv_direction = np.sign(close.diff()).fillna(0)
        res['obv'] = (obv_direction * volume).cumsum()

        # Accumulation / Distribution (A/D)
        mf_multiplier = np.where((high - low) == 0, 0, ((close - low) - (high - close)) / (high - low))
        res['ad_line'] = (mf_multiplier * volume).cumsum()

        # 5. Price Structure & Distances
        res['daily_return'] = close.pct_change()
        res['gap_pct'] = np.where(prev_close == 0, 0, ((res['open'] - prev_close) / prev_close) * 100)
        res['intraday_range_pct'] = np.where(res['low'] == 0, 0, ((res['high'] - res['low']) / res['low']) * 100)

        # Moving Average Distances
        res['dist_sma_20_pct'] = np.where(res['sma_20'] == 0, 0, ((close - res['sma_20']) / res['sma_20']) * 100)
        res['dist_sma_50_pct'] = np.where(res['sma_50'] == 0, 0, ((close - res['sma_50']) / res['sma_50']) * 100)
        res['dist_sma_200_pct'] = np.where(res['sma_200'] == 0, 0, ((close - res['sma_200']) / res['sma_200']) * 100)

        # 52-week High / Low Distances
        high_52w = high.rolling(window=252, min_periods=1).max()
        low_52w = low.rolling(window=252, min_periods=1).min()
        res['dist_52w_high_pct'] = np.where(high_52w == 0, 0, ((close - high_52w) / high_52w) * 100)
        res['dist_52w_low_pct'] = np.where(low_52w == 0, 0, ((close - low_52w) / low_52w) * 100)

        # 6. Technical Signals & Events
        res['golden_cross'] = (res['sma_50'] > res['sma_200']) & (res['sma_50'].shift(1) <= res['sma_200'].shift(1))
        res['death_cross'] = (res['sma_50'] < res['sma_200']) & (res['sma_50'].shift(1) >= res['sma_200'].shift(1))

        # Breakouts & Breakdowns (20-day High / Low)
        high_20d = high.shift(1).rolling(window=20, min_periods=1).max()
        low_20d = low.shift(1).rolling(window=20, min_periods=1).min()
        res['breakout_20d'] = close > high_20d
        res['breakdown_20d'] = close < low_20d

        # Support & Resistance (Pivot Points: 20-day High/Low/Close avg)
        res['pivot_support'] = low.rolling(window=20, min_periods=1).min()
        res['pivot_resistance'] = high.rolling(window=20, min_periods=1).max()

        return res

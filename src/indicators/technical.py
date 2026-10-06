import numpy as np
import pandas as pd
from typing import Dict, Any, List


class TechnicalIndicators:
    """Calculates technical indicators and identifies technical signals for stock price series."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators on a historical price DataFrame.
        Expected columns in df: 'date', 'open', 'high', 'low', 'close', 'volume'
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy().sort_values('date').reset_index(drop=True)

        # 1. Trend - Simple Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{p}'] = df['close'].rolling(window=p, min_periods=1).mean()

        # Trend - Exponential Moving Averages
        for p in [9, 20, 50, 200]:
            df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()

        # 2. Momentum - RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        df['rsi_14'] = df['rsi_14'].fillna(50)

        # Stochastic RSI
        rsi = df['rsi_14']
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        rsi_denom = (rsi_max - rsi_min).replace(0, np.nan)
        df['stoch_rsi'] = ((rsi - rsi_min) / rsi_denom).fillna(0.5)

        # MACD (12, 26, 9)
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Rate of Change (ROC 10) & Momentum (10)
        df['roc_10'] = df['close'].pct_change(periods=10) * 100
        df['momentum_10'] = df['close'] - df['close'].shift(10)

        # 3. Volatility - Average True Range (ATR 14)
        prev_close = df['close'].shift(1)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - prev_close).abs()
        tr3 = (df['low'] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        daily_ret = df['close'].pct_change()
        df['daily_return'] = daily_ret
        df['volatility_20d'] = daily_ret.rolling(window=20, min_periods=5).std() * np.sqrt(252)

        # Bollinger Bands (20-day, 2 std)
        sma_20 = df['sma_20']
        std_20 = df['close'].rolling(window=20, min_periods=1).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / sma_20).fillna(0)

        # Volatility Regime
        vol_pct = df['volatility_20d'].rank(pct=True)
        df['volatility_regime'] = np.where(vol_pct >= 0.75, 'High', np.where(vol_pct <= 0.25, 'Low', 'Normal'))

        # 4. Volume Indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['relative_volume'] = (df['volume'] / df['volume_sma_20'].replace(0, np.nan)).fillna(1.0)
        df['volume_change'] = df['volume'].pct_change()

        # On-Balance Volume (OBV)
        obv_direction = np.where(df['close'] > prev_close, 1, np.where(df['close'] < prev_close, -1, 0))
        df['obv'] = (df['volume'] * obv_direction).cumsum()

        # Accumulation / Distribution Line (A/D)
        clv_denom = (df['high'] - df['low']).replace(0, np.nan)
        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / clv_denom
        df['ad_line'] = (clv.fillna(0) * df['volume']).cumsum()

        # 5. Price Structure & Distances
        df['gap_pct'] = ((df['open'] - prev_close) / prev_close).fillna(0)
        df['intraday_range_pct'] = ((df['high'] - df['low']) / df['low'].replace(0, np.nan)).fillna(0)

        df['dist_sma_20'] = (df['close'] - df['sma_20']) / df['sma_20']
        df['dist_sma_50'] = (df['close'] - df['sma_50']) / df['sma_50']
        df['dist_sma_200'] = (df['close'] - df['sma_200']) / df['sma_200']

        # 52-week High / Low (approx 252 trading days)
        rolling_52w_high = df['high'].rolling(window=252, min_periods=1).max()
        rolling_52w_low = df['low'].rolling(window=252, min_periods=1).min()
        df['dist_52w_high'] = (df['close'] - rolling_52w_high) / rolling_52w_high
        df['dist_52w_low'] = (df['close'] - rolling_52w_low) / rolling_52w_low

        return df

    @staticmethod
    def identify_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Identifies key technical events for the latest bar in the DataFrame.
        """
        if df.empty or len(df) < 2:
            return {
                "events": [],
                "support_level": None,
                "resistance_level": None,
                "unusual_volume": False
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        events = []

        # 1. Moving Average Crosses
        if prev['sma_50'] <= prev['sma_200'] and latest['sma_50'] > latest['sma_200']:
            events.append("Golden Cross")
        elif prev['sma_50'] >= prev['sma_200'] and latest['sma_50'] < latest['sma_200']:
            events.append("Death Cross")

        # 2. Breakouts / Breakdowns (20-day high/low)
        high_20d = df['high'].iloc[:-1].tail(20).max() if len(df) > 20 else df['high'].max()
        low_20d = df['low'].iloc[:-1].tail(20).min() if len(df) > 20 else df['low'].min()

        if latest['close'] > high_20d and latest['relative_volume'] > 1.2:
            events.append("Bullish Breakout (20-day high)")
        elif latest['close'] < low_20d and latest['relative_volume'] > 1.2:
            events.append("Bearish Breakdown (20-day low)")

        # 3. Unusual Volume
        unusual_volume = latest['relative_volume'] >= 2.0
        if unusual_volume:
            events.append("Unusual Volume Spike")

        # 4. Momentum Divergence (simple check: price making new 10d high but RSI lower than 10d max RSI)
        if len(df) >= 10:
            price_10d_high = df['close'].tail(10).max()
            rsi_10d_high = df['rsi_14'].tail(10).max()
            if latest['close'] == price_10d_high and latest['rsi_14'] < rsi_10d_high:
                events.append("Bearish Momentum Divergence")

        # Support / Resistance levels (using 20-day min/max and SMA 50)
        support = float(min(df['low'].tail(20).min(), latest['sma_50']))
        resistance = float(max(df['high'].tail(20).max(), latest['sma_50']))

        return {
            "events": events,
            "support_level": support,
            "resistance_level": resistance,
            "unusual_volume": bool(unusual_volume)
        }

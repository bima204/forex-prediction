"""
Market Regime Detector Module.
Identifies market states: Trending (Bullish/Bearish), Ranging/Sideways, Volatility levels, and Trading Sessions.
"""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


class MarketRegimeDetector:
    """
    Analyzes price data to classify market regime, trend direction/strength, volatility state,
    and market trading sessions (London, New York, Asia, Rollover).
    """

    def __init__(self, adx_threshold: float = 25.0, ema_fast: int = 20, ema_mid: int = 50, ema_slow: int = 200):
        self.adx_threshold = adx_threshold
        self.ema_fast = ema_fast
        self.ema_mid = ema_mid
        self.ema_slow = ema_slow

    def compute_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends market regime features to the OHLCV DataFrame.
        """
        data = df.copy()

        # 1. EMAs for Trend Classification
        data[f"ema_{self.ema_fast}"] = data["close"].ewm(span=self.ema_fast, adjust=False).mean()
        data[f"ema_{self.ema_mid}"] = data["close"].ewm(span=self.ema_mid, adjust=False).mean()
        data[f"ema_{self.ema_slow}"] = data["close"].ewm(span=self.ema_slow, adjust=False).mean()

        # EMA Slopes (Normalized by ATR or percentage)
        data["ema_fast_slope"] = (data[f"ema_{self.ema_fast}"] - data[f"ema_{self.ema_fast}"].shift(3)) / data[f"ema_{self.ema_fast}"].shift(3) * 100
        data["ema_mid_slope"] = (data[f"ema_{self.ema_mid}"] - data[f"ema_{self.ema_mid}"].shift(5)) / data[f"ema_{self.ema_mid}"].shift(5) * 100

        # 2. Average True Range (ATR) & Volatility
        high_low = data["high"] - data["low"]
        high_close = (data["high"] - data["close"].shift()).abs()
        low_close = (data["low"] - data["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data["atr_14"] = tr.rolling(window=14).mean()

        # Rolling ATR percentile for volatility regime
        atr_median = data["atr_14"].rolling(window=100, min_periods=20).median()
        atr_std = data["atr_14"].rolling(window=100, min_periods=20).std()
        data["volatility_zscore"] = (data["atr_14"] - atr_median) / (atr_std + 1e-8)

        # 3. Directional Movement (ADX Calculation)
        up_move = data["high"] - data["high"].shift(1)
        down_move = data["low"].shift(1) - data["low"]

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr_smooth = tr.rolling(14).sum()
        plus_di = 100 * (pd.Series(plus_dm, index=data.index).rolling(14).sum() / (tr_smooth + 1e-8))
        minus_di = 100 * (pd.Series(minus_dm, index=data.index).rolling(14).sum() / (tr_smooth + 1e-8))
        dx = 100 * ((plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-8))
        data["adx_14"] = dx.rolling(14).mean()
        data["plus_di"] = plus_di
        data["minus_di"] = minus_di

        # 4. Bollinger Bands Width (Bandwidth = (Upper - Lower) / Middle)
        bb_mid = data["close"].rolling(20).mean()
        bb_std = data["close"].rolling(20).std()
        data["bb_bandwidth"] = (4 * bb_std) / (bb_mid + 1e-8)

        # 5. Market Session Classification (UTC Hours)
        hours = data.index.hour
        data["is_asia"] = ((hours >= 0) & (hours < 9)).astype(int)
        data["is_london"] = ((hours >= 7) & (hours < 16)).astype(int)
        data["is_new_york"] = ((hours >= 12) & (hours < 21)).astype(int)
        data["is_overlap"] = ((hours >= 12) & (hours < 16)).astype(int)
        # Rollover hour (high spread risk usually 21:00-23:00 UTC)
        data["is_rollover"] = ((hours >= 21) & (hours < 23)).astype(int)
        data["is_tradeable_session"] = (data["is_rollover"] == 0).astype(int)

        # 6. Trend State Classification
        # 1: Bullish Trend, -1: Bearish Trend, 0: Sideways / Range
        is_bullish = (
            (data["close"] > data[f"ema_{self.ema_fast}"])
            & (data[f"ema_{self.ema_fast}"] > data[f"ema_{self.ema_mid}"])
            & (data["adx_14"] >= self.adx_threshold)
            & (data["plus_di"] > data["minus_di"])
        )
        is_bearish = (
            (data["close"] < data[f"ema_{self.ema_fast}"])
            & (data[f"ema_{self.ema_fast}"] < data[f"ema_{self.ema_mid}"])
            & (data["adx_14"] >= self.adx_threshold)
            & (data["minus_di"] > data["plus_di"])
        )

        data["regime_trend"] = 0
        data.loc[is_bullish, "regime_trend"] = 1
        data.loc[is_bearish, "regime_trend"] = -1

        # Volatility Classification: 0: Low, 1: Normal, 2: High
        data["regime_volatility"] = 1
        data.loc[data["volatility_zscore"] < -0.8, "regime_volatility"] = 0
        data.loc[data["volatility_zscore"] > 1.2, "regime_volatility"] = 2

        return data

    def get_current_regime_summary(self, df_with_regime: pd.DataFrame) -> Dict[str, Any]:
        """
        Returns a concise dictionary describing the most recent market regime.
        """
        latest = df_with_regime.iloc[-1]
        trend_code = int(latest.get("regime_trend", 0))
        vol_code = int(latest.get("regime_volatility", 1))

        trend_labels = {1: "BULLISH_TREND", -1: "BEARISH_TREND", 0: "SIDEWAYS_RANGING"}
        vol_labels = {0: "LOW_VOLATILITY", 1: "NORMAL_VOLATILITY", 2: "HIGH_VOLATILITY"}

        # Session name
        if latest.get("is_overlap", 0) == 1:
            session_str = "LONDON_NY_OVERLAP (High Liquidity)"
        elif latest.get("is_london", 0) == 1:
            session_str = "LONDON"
        elif latest.get("is_new_york", 0) == 1:
            session_str = "NEW_YORK"
        elif latest.get("is_asia", 0) == 1:
            session_str = "ASIA"
        elif latest.get("is_rollover", 0) == 1:
            session_str = "ROLLOVER (Spread Warning)"
        else:
            session_str = "OFF_HOURS"

        return {
            "trend_state": trend_labels.get(trend_code, "UNKNOWN"),
            "trend_code": trend_code,
            "adx_strength": float(latest.get("adx_14", 0.0)),
            "is_trending": float(latest.get("adx_14", 0.0)) >= self.adx_threshold,
            "volatility_state": vol_labels.get(vol_code, "NORMAL"),
            "volatility_zscore": float(latest.get("volatility_zscore", 0.0)),
            "atr_14": float(latest.get("atr_14", 0.0)),
            "session": session_str,
            "is_tradeable_session": bool(latest.get("is_tradeable_session", 1)),
        }

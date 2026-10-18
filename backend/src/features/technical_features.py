"""
Technical Indicators & Price Action Feature Generator.
Computes Momentum, Oscillators, Smart Money Price Action (FVG, Swing Pivots, Candlestick anatomy).
"""
import numpy as np
import pandas as pd


class TechnicalFeatureExtractor:
    """
    Computes a comprehensive set of predictive technical and price-action features.
    """

    def __init__(self, rsi_period: int = 14, pivot_window: int = 10):
        self.rsi_period = rsi_period
        self.pivot_window = pivot_window

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators and appends them to the DataFrame.
        """
        data = df.copy()
        eps = 1e-8

        # --- 1. Momentum & Oscillators ---
        # RSI
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + eps)
        data["rsi_14"] = 100 - (100 / (1 + rs))
        data["rsi_oversold"] = (data["rsi_14"] < 30).astype(int)
        data["rsi_overbought"] = (data["rsi_14"] > 70).astype(int)

        # Stochastic Oscillator (%K, %D)
        lowest_low = data["low"].rolling(14).min()
        highest_high = data["high"].rolling(14).max()
        data["stoch_k"] = 100 * ((data["close"] - lowest_low) / (highest_high - lowest_low + eps))
        data["stoch_d"] = data["stoch_k"].rolling(3).mean()

        # MACD (12, 26, 9)
        ema12 = data["close"].ewm(span=12, adjust=False).mean()
        ema26 = data["close"].ewm(span=26, adjust=False).mean()
        data["macd_line"] = ema12 - ema26
        data["macd_signal"] = data["macd_line"].ewm(span=9, adjust=False).mean()
        data["macd_hist"] = data["macd_line"] - data["macd_signal"]
        data["macd_bull_cross"] = ((data["macd_line"] > data["macd_signal"]) & (data["macd_line"].shift(1) <= data["macd_signal"].shift(1))).astype(int)
        data["macd_bear_cross"] = ((data["macd_line"] < data["macd_signal"]) & (data["macd_line"].shift(1) >= data["macd_signal"].shift(1))).astype(int)

        # --- 2. Candlestick Anatomy & Price Action ---
        candle_range = data["high"] - data["low"] + eps
        candle_body = (data["close"] - data["open"]).abs()
        upper_wick = data["high"] - data[["open", "close"]].max(axis=1)
        lower_wick = data[["open", "close"]].min(axis=1) - data["low"]

        data["candle_body_ratio"] = candle_body / candle_range
        data["candle_upper_wick_ratio"] = upper_wick / candle_range
        data["candle_lower_wick_ratio"] = lower_wick / candle_range
        data["candle_direction"] = np.where(data["close"] >= data["open"], 1, -1)

        # Pinbar / Hammer detection
        data["is_bullish_pinbar"] = ((data["candle_lower_wick_ratio"] >= 0.6) & (data["candle_body_ratio"] <= 0.3)).astype(int)
        data["is_bearish_pinbar"] = ((data["candle_upper_wick_ratio"] >= 0.6) & (data["candle_body_ratio"] <= 0.3)).astype(int)

        # --- 3. Smart Money Concepts: Fair Value Gap (FVG / Imbalance) ---
        # Bullish FVG: Low of candle 3 is higher than High of candle 1
        bullish_fvg = (data["low"] > data["high"].shift(2)).astype(int)
        # Bearish FVG: High of candle 3 is lower than Low of candle 1
        bearish_fvg = (data["high"] < data["low"].shift(2)).astype(int)
        data["is_bullish_fvg"] = bullish_fvg
        data["is_bearish_fvg"] = bearish_fvg

        # --- 4. Dynamic Swing Pivots & S/R Distance ---
        w = self.pivot_window
        rolling_max = data["high"].rolling(window=w * 2 + 1, center=True).max()
        rolling_min = data["low"].rolling(window=w * 2 + 1, center=True).min()
        
        # Forward-fill confirmed pivots to avoid lookahead bias during actual inference
        data["swing_high"] = data["high"].where(data["high"] == rolling_max).ffill()
        data["swing_low"] = data["low"].where(data["low"] == rolling_min).ffill()

        # ATR-normalized distances to key S/R
        atr = data["high"].combine(data["close"].shift(), max) - data["low"].combine(data["close"].shift(), min)
        atr_14 = atr.rolling(14).mean() + eps
        data["dist_to_swing_high"] = (data["swing_high"] - data["close"]) / atr_14
        data["dist_to_swing_low"] = (data["close"] - data["swing_low"]) / atr_14

        # --- 5. Return & Statistical Features ---
        data["log_return_1"] = np.log(data["close"] / data["close"].shift(1))
        data["log_return_5"] = np.log(data["close"] / data["close"].shift(5))
        data["realized_vol_20"] = data["log_return_1"].rolling(20).std()

        # Volume ratio
        if "volume" in data.columns and (data["volume"] > 0).any():
            vol_mean = data["volume"].rolling(20).mean() + eps
            data["volume_ratio"] = data["volume"] / vol_mean
        else:
            data["volume_ratio"] = 1.0

        return data

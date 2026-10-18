"""
Triple Barrier Labeling Generator (Marcos Lopez de Prado Method).
Generates realistic trading labels based on Take Profit (TP), Stop Loss (SL), and Vertical (Time) Barriers.
"""
from typing import Tuple
import numpy as np
import pandas as pd


class TripleBarrierLabeler:
    """
    Labels historical bars based on whether price hits Take Profit or Stop Loss first within a maximum time horizon.
    """

    def __init__(
        self,
        atr_multiplier_tp: float = 2.0,
        atr_multiplier_sl: float = 1.0,
        max_holding_bars: int = 24,
    ):
        self.tp_mult = atr_multiplier_tp
        self.sl_mult = atr_multiplier_sl
        self.max_bars = max_holding_bars

    def apply_triple_barrier(self, df: pd.DataFrame, pip_value: float = 0.0001) -> pd.DataFrame:
        """
        Calculates labels for both BUY and SELL opportunities.
        
        Labels generated:
        - `target_buy`: 1 if BUY hits TP before SL, 0 otherwise
        - `target_sell`: 1 if SELL hits TP before SL, 0 otherwise
        - `target_signal`: 
            1  -> BUY Opportunity
           -1  -> SELL Opportunity
            0  -> NEUTRAL / Timeout
        - `return_pips`: Pips realized during the trade
        """
        data = df.copy()
        n = len(data)

        # Estimate ATR for dynamic volatility-adjusted barriers if not present
        if "atr_14" not in data.columns:
            high_low = data["high"] - data["low"]
            high_close = (data["high"] - data["close"].shift()).abs()
            low_close = (data["low"] - data["close"].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().bfill()
        else:
            atr = data["atr_14"].bfill()

        target_buy = np.zeros(n, dtype=int)
        target_sell = np.zeros(n, dtype=int)
        target_signal = np.zeros(n, dtype=int)
        realized_pips = np.zeros(n, dtype=float)

        close_vals = data["close"].values
        high_vals = data["high"].values
        low_vals = data["low"].values
        atr_vals = atr.values

        for i in range(n - self.max_bars):
            entry_price = close_vals[i]
            current_atr = atr_vals[i]
            tp_dist = current_atr * self.tp_mult
            sl_dist = current_atr * self.sl_mult

            # Buy Barriers
            buy_tp = entry_price + tp_dist
            buy_sl = entry_price - sl_dist

            # Sell Barriers
            sell_tp = entry_price - tp_dist
            sell_sl = entry_price + sl_dist

            # Scan future bars
            horizon_end = min(i + self.max_bars + 1, n)
            future_highs = high_vals[i + 1: horizon_end]
            future_lows = low_vals[i + 1: horizon_end]

            buy_hit_tp_idx = -1
            buy_hit_sl_idx = -1
            sell_hit_tp_idx = -1
            sell_hit_sl_idx = -1

            for step, (h, l) in enumerate(zip(future_highs, future_lows)):
                # Buy check
                if buy_hit_tp_idx == -1 and h >= buy_tp:
                    buy_hit_tp_idx = step
                if buy_hit_sl_idx == -1 and l <= buy_sl:
                    buy_hit_sl_idx = step

                # Sell check
                if sell_hit_tp_idx == -1 and l <= sell_tp:
                    sell_hit_tp_idx = step
                if sell_hit_sl_idx == -1 and h >= sell_sl:
                    sell_hit_sl_idx = step

            # Evaluate BUY Outcome
            if buy_hit_tp_idx != -1 and (buy_hit_sl_idx == -1 or buy_hit_tp_idx < buy_hit_sl_idx):
                target_buy[i] = 1

            # Evaluate SELL Outcome
            if sell_hit_tp_idx != -1 and (sell_hit_sl_idx == -1 or sell_hit_tp_idx < sell_hit_sl_idx):
                target_sell[i] = 1

            # Determine dominant signal
            if target_buy[i] == 1 and target_sell[i] == 0:
                target_signal[i] = 1
                realized_pips[i] = tp_dist / pip_value
            elif target_sell[i] == 1 and target_buy[i] == 0:
                target_signal[i] = -1
                realized_pips[i] = tp_dist / pip_value
            else:
                target_signal[i] = 0
                # If hit SL first
                if buy_hit_sl_idx != -1 and sell_hit_sl_idx == -1:
                    realized_pips[i] = -sl_dist / pip_value
                elif sell_hit_sl_idx != -1 and buy_hit_sl_idx == -1:
                    realized_pips[i] = -sl_dist / pip_value
                else:
                    realized_pips[i] = 0.0

        data["target_buy"] = target_buy
        data["target_sell"] = target_sell
        data["target_signal"] = target_signal
        data["realized_pips"] = realized_pips

        return data

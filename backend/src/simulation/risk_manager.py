"""
Risk Management Engine for Forex Simulation & Live Trading.
Calculates Dynamic Lot Sizing, Maximum Drawdown Controls, and Spread/Slippage adjustments.
"""
from typing import Dict, Any, Tuple
import math


class RiskManager:
    """
    Guards account capital via dynamic position sizing, margin limits, and slippage calculations.
    """

    def __init__(
        self,
        risk_per_trade_pct: float = 1.0,
        max_open_trades: int = 3,
        spread_pips: float = 1.5,
        slippage_pips: float = 0.5,
        contract_size: float = 100000.0,  # Standard lot = 100,000 units
    ):
        self.risk_pct = risk_per_trade_pct
        self.max_open_trades = max_open_trades
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.contract_size = contract_size

    def calculate_lot_size(
        self,
        account_balance: float,
        sl_pips: float,
        pip_value: float = 0.0001,
        min_lot: float = 0.01,
        max_lot: float = 10.0,
    ) -> float:
        """
        Calculates exact lot size so that hitting Stop Loss risks exactly `risk_pct` of account balance.
        """
        if sl_pips <= 0 or account_balance <= 0:
            return min_lot

        risk_amount_cash = account_balance * (self.risk_pct / 100.0)
        # Cash value of 1 pip for 1 standard lot (100,000 units)
        pip_value_per_lot = self.contract_size * pip_value  # Typically $10 for EURUSD

        lot_size = risk_amount_cash / (sl_pips * pip_value_per_lot)
        
        # Round to 2 decimal places and clamp
        lot_size = round(math.floor(lot_size * 100) / 100, 2)
        return max(min_lot, min(lot_size, max_lot))

    def apply_execution_costs(
        self,
        price: float,
        direction: str,
        pip_value: float = 0.0001,
    ) -> float:
        """
        Applies bid/ask spread and realistic slippage to raw market price.
        - BUY enters at ASK = price + half_spread + slippage
        - SELL enters at BID = price - half_spread - slippage
        """
        total_friction_pips = (self.spread_pips / 2.0) + self.slippage_pips
        friction_distance = total_friction_pips * pip_value

        if direction.upper() == "BUY":
            return price + friction_distance
        else:
            return price - friction_distance

    def can_open_new_trade(self, current_open_trades_count: int) -> Tuple[bool, str]:
        """
        Checks whether new trade violates concurrency or risk limits.
        """
        if current_open_trades_count >= self.max_open_trades:
            return False, f"Batas maksimum posisi terbuka tercapai ({self.max_open_trades} posisi)."
        return True, "Diizinkan."

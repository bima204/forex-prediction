"""
Position and Order Execution Model for Simulation & Paper Trading.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TradePosition:
    """
    Represents an open or closed trade position.
    """
    ticket_id: int
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    lot_size: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    
    # State tracking
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: str = "OPEN"  # 'OPEN', 'CLOSED_TP', 'CLOSED_SL', 'CLOSED_TRAILING'
    pnl_cash: float = 0.0
    pnl_pips: float = 0.0
    is_breakeven_activated: bool = False

    def update_trailing_stop(self, current_price: float, pip_value: float = 0.0001, trail_step_pips: float = 15.0):
        """
        Adjusts Stop Loss to lock in profits as trade advances favorably.
        """
        if self.status != "OPEN":
            return

        trail_step_dist = trail_step_pips * pip_value

        if self.direction == "BUY":
            profit_dist = current_price - self.entry_price
            # Breakeven trigger: when profit exceeds 1x initial risk or 1.5x trail step
            if profit_dist >= trail_step_dist and not self.is_breakeven_activated:
                self.stop_loss = self.entry_price + (2.0 * pip_value)  # Entry + 2 pips buffer
                self.is_breakeven_activated = True
            
            # Trailing stop update
            if self.is_breakeven_activated and (current_price - trail_step_dist) > self.stop_loss:
                self.stop_loss = current_price - trail_step_dist

        elif self.direction == "SELL":
            profit_dist = self.entry_price - current_price
            # Breakeven trigger
            if profit_dist >= trail_step_dist and not self.is_breakeven_activated:
                self.stop_loss = self.entry_price - (2.0 * pip_value)
                self.is_breakeven_activated = True

            # Trailing stop update
            if self.is_breakeven_activated and (current_price + trail_step_dist) < self.stop_loss:
                self.stop_loss = current_price + trail_step_dist

    def close(self, price: float, time: datetime, reason: str, pip_value: float = 0.0001, contract_size: float = 100000.0):
        """
        Closes position and calculates net profit in cash and pips.
        """
        self.exit_price = price
        self.exit_time = time
        self.status = reason

        if self.direction == "BUY":
            self.pnl_pips = (self.exit_price - self.entry_price) / pip_value
            self.pnl_cash = (self.exit_price - self.entry_price) * contract_size * self.lot_size
        else:
            self.pnl_pips = (self.entry_price - self.exit_price) / pip_value
            self.pnl_cash = (self.entry_price - self.exit_price) * contract_size * self.lot_size

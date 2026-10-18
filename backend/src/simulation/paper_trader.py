"""
Paper Trading Engine for Real-Time Forward Testing without Real Capital Risk.
Persists simulated portfolio state to local storage.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json

from config.settings import DATA_DIR, DEFAULT_PAIRS
from .position import TradePosition
from .risk_manager import RiskManager


class PaperTrader:
    """
    Autonomous paper trading manager that tracks simulated portfolio and trades.
    """

    def __init__(self, state_file: Optional[Path] = None, initial_balance: float = 10000.0):
        self.state_file = state_file or (DATA_DIR / "paper_account.json")
        self.initial_balance = initial_balance
        self.risk_manager = RiskManager()
        self.load_state()

    def load_state(self):
        """
        Loads state from disk or initializes defaults.
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.balance = data.get("balance", self.initial_balance)
                    self.open_positions = data.get("open_positions", [])
                    self.closed_positions = data.get("closed_positions", [])
                    self.ticket_counter = data.get("ticket_counter", 1)
                    return
            except Exception as e:
                print(f"[PaperTrader] Error loading state: {e}. Reinitializing...")

        self.balance = self.initial_balance
        self.open_positions = []
        self.closed_positions = []
        self.ticket_counter = 1
        self.save_state()

    def save_state(self):
        """
        Persists account state to disk.
        """
        data = {
            "balance": round(self.balance, 2),
            "ticket_counter": self.ticket_counter,
            "open_positions": self.open_positions,
            "closed_positions": self.closed_positions[-200:],  # keep last 200 closed
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def process_candle(
        self,
        symbol: str,
        candle: Dict[str, float],
        signal: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Processes new candle: checks SL/TP on open positions and enters new trade if signal is active.
        """
        pair_info = DEFAULT_PAIRS.get(symbol.upper(), {})
        pip_value = pair_info.get("pip_value", 0.0001)

        cur_close = candle["close"]
        cur_high = candle["high"]
        cur_low = candle["low"]
        cur_time = candle.get("time", datetime.now().isoformat())

        # 1. Update Open Positions
        surviving = []
        closed_this_tick = []

        for p in self.open_positions:
            closed = False
            direction = p["direction"]
            sl = p["stop_loss"]
            tp = p["take_profit"]
            entry = p["entry_price"]
            lot = p["lot_size"]

            if direction == "BUY":
                if cur_low <= sl:
                    pnl_pips = (sl - entry) / pip_value
                    pnl_cash = (sl - entry) * 100000.0 * lot
                    p["status"] = "CLOSED_SL"
                    p["exit_price"] = sl
                    p["pnl_cash"] = round(pnl_cash, 2)
                    p["pnl_pips"] = round(pnl_pips, 1)
                    self.balance += pnl_cash
                    self.closed_positions.append(p)
                    closed_this_tick.append(p)
                    closed = True
                elif cur_high >= tp:
                    pnl_pips = (tp - entry) / pip_value
                    pnl_cash = (tp - entry) * 100000.0 * lot
                    p["status"] = "CLOSED_TP"
                    p["exit_price"] = tp
                    p["pnl_cash"] = round(pnl_cash, 2)
                    p["pnl_pips"] = round(pnl_pips, 1)
                    self.balance += pnl_cash
                    self.closed_positions.append(p)
                    closed_this_tick.append(p)
                    closed = True
            elif direction == "SELL":
                if cur_high >= sl:
                    pnl_pips = (entry - sl) / pip_value
                    pnl_cash = (entry - sl) * 100000.0 * lot
                    p["status"] = "CLOSED_SL"
                    p["exit_price"] = sl
                    p["pnl_cash"] = round(pnl_cash, 2)
                    p["pnl_pips"] = round(pnl_pips, 1)
                    self.balance += pnl_cash
                    self.closed_positions.append(p)
                    closed_this_tick.append(p)
                    closed = True
                elif cur_low <= tp:
                    pnl_pips = (entry - tp) / pip_value
                    pnl_cash = (entry - tp) * 100000.0 * lot
                    p["status"] = "CLOSED_TP"
                    p["exit_price"] = tp
                    p["pnl_cash"] = round(pnl_cash, 2)
                    p["pnl_pips"] = round(pnl_pips, 1)
                    self.balance += pnl_cash
                    self.closed_positions.append(p)
                    closed_this_tick.append(p)
                    closed = True

            if not closed:
                surviving.append(p)

        self.open_positions = surviving

        # 2. Open New Position if Signal Provided
        new_trade_opened = None
        if signal and signal.get("action") in ["BUY", "SELL"]:
            can_open, _ = self.risk_manager.can_open_new_trade(len(self.open_positions))
            if can_open:
                action = signal["action"]
                sl = float(signal["stop_loss"])
                tp = float(signal["take_profit"])
                sl_pips = abs(cur_close - sl) / pip_value

                lot_size = self.risk_manager.calculate_lot_size(self.balance, sl_pips=sl_pips, pip_value=pip_value)
                exec_price = self.risk_manager.apply_execution_costs(cur_close, action, pip_value=pip_value)

                new_trade_opened = {
                    "ticket_id": self.ticket_counter,
                    "symbol": symbol,
                    "direction": action,
                    "lot_size": lot_size,
                    "entry_price": exec_price,
                    "entry_time": cur_time,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "status": "OPEN",
                }
                self.open_positions.append(new_trade_opened)
                self.ticket_counter += 1

        self.save_state()

        return {
            "balance": round(self.balance, 2),
            "open_count": len(self.open_positions),
            "new_trade": new_trade_opened,
            "closed_trades": closed_this_tick,
        }

    def open_order(
        self,
        pair: str,
        order_type: str,
        entry_price: float,
        lots: float = 0.1,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: str = "Manual Entry"
    ) -> Dict[str, Any]:
        """Manually open a paper trading position."""
        pair_info = DEFAULT_PAIRS.get(pair.upper(), {})
        pip_value = pair_info.get("pip_value", 0.0001)

        # Default SL / TP if not provided
        if stop_loss is None:
            stop_loss = entry_price - (pip_value * 30) if order_type == "BUY" else entry_price + (pip_value * 30)
        if take_profit is None:
            take_profit = entry_price + (pip_value * 60) if order_type == "BUY" else entry_price - (pip_value * 60)

        trade = {
            "ticket_id": self.ticket_counter,
            "symbol": pair.upper(),
            "direction": order_type.upper(),
            "lot_size": round(lots, 2),
            "entry_price": round(entry_price, 5),
            "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(take_profit, 5),
            "strategy": strategy,
            "status": "OPEN",
        }
        self.open_positions.append(trade)
        self.ticket_counter += 1
        self.save_state()
        return trade

    def close_order(self, ticket_id: int, exit_price: float, reason: str = "Manual Close") -> Optional[Dict[str, Any]]:
        """Close an open trade by ticket_id."""
        target_trade = None
        surviving = []
        for p in self.open_positions:
            if p.get("ticket_id") == ticket_id:
                target_trade = p
            else:
                surviving.append(p)

        if not target_trade:
            return None

        pair_info = DEFAULT_PAIRS.get(target_trade["symbol"], {})
        pip_value = pair_info.get("pip_value", 0.0001)
        direction = target_trade["direction"]
        entry = target_trade["entry_price"]
        lot = target_trade["lot_size"]

        if direction == "BUY":
            pnl_pips = (exit_price - entry) / pip_value
            pnl_cash = (exit_price - entry) * 100000.0 * lot
        else:
            pnl_pips = (entry - exit_price) / pip_value
            pnl_cash = (entry - exit_price) * 100000.0 * lot

        target_trade["status"] = f"CLOSED ({reason})"
        target_trade["exit_price"] = round(exit_price, 5)
        target_trade["exit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_trade["pnl_cash"] = round(pnl_cash, 2)
        target_trade["pnl_pips"] = round(pnl_pips, 1)

        self.balance += pnl_cash
        self.open_positions = surviving
        self.closed_positions.append(target_trade)
        self.save_state()
        return target_trade

    def reset_account(self, balance: float = 10000.0):
        """
        Resets simulated account to initial state.
        """
        self.balance = balance
        self.open_positions = []
        self.closed_positions = []
        self.ticket_counter = 1
        self.save_state()


"""
Signal Stability and Active Signal Lock-In Manager.
Prevents signal flickering upon refresh, tracks active trade duration,
and maintains signal validity until Take Profit, Stop Loss, or Expiry is reached.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json

from config.settings import DATA_DIR, DEFAULT_PAIRS

TRADING_STYLES: Dict[str, Dict[str, Any]] = {
    "scalping": {
        "name": "⚡ Scalping (Cepat / Kilat)",
        "default_tf": "5m",
        "holding_time_str": "15 - 45 Menit",
        "validity_bars": 6,
        "validity_minutes": 45,
        "tp_mult": 1.5,
        "sl_mult": 1.0,
        "confidence_threshold": 0.53,
    },
    "daytrading": {
        "name": "☀️ Day Trading (Harian)",
        "default_tf": "1h",
        "holding_time_str": "2 - 8 Jam",
        "validity_bars": 8,
        "validity_minutes": 480,
        "tp_mult": 2.0,
        "sl_mult": 1.0,
        "confidence_threshold": 0.55,
    },
    "swing": {
        "name": "🌊 Swing Trading (Santai / Multi-Hari)",
        "default_tf": "4h",
        "holding_time_str": "1 - 5 Hari",
        "validity_bars": 18,
        "validity_minutes": 4320,
        "tp_mult": 2.5,
        "sl_mult": 1.2,
        "confidence_threshold": 0.58,
    },
}


class SignalLockManager:
    """
    Manages active trading signals so users don't experience signal flickering on refresh.
    Locks in BUY/SELL signals until price hits TP/SL or validity duration elapses.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (DATA_DIR / "active_signals.json")
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self.active_signals = json.load(f)
                    return
            except Exception:
                pass
        self.active_signals = {}

    def _save(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.active_signals, f, indent=2)
        except Exception as e:
            print(f"[SignalLockManager] Error saving signals: {e}")

    def get_or_update_signal(
        self,
        symbol: str,
        style_key: str,
        new_signal: Dict[str, Any],
        current_price: float,
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves existing locked signal if still valid and unclosed, or registers a new confirmed signal.
        """
        now = current_time or datetime.now()
        signal_key = f"{symbol.upper()}_{style_key.lower()}"
        style_config = TRADING_STYLES.get(style_key, TRADING_STYLES["daytrading"])
        pip_val = DEFAULT_PAIRS.get(symbol.upper(), {}).get("pip_value", 0.0001)

        existing = self.active_signals.get(signal_key)

        # 1. Check existing active signal
        if existing and existing.get("action") in ["BUY", "SELL"]:
            entry_time = datetime.fromisoformat(existing["created_at"])
            expiry_time = entry_time + timedelta(minutes=style_config["validity_minutes"])
            action = existing["action"]
            tp = existing["take_profit"]
            sl = existing["stop_loss"]

            # Check if hit TP
            hit_tp = (action == "BUY" and current_price >= tp) or (action == "SELL" and current_price <= tp)
            # Check if hit SL
            hit_sl = (action == "BUY" and current_price <= sl) or (action == "SELL" and current_price >= sl)
            # Check if expired
            is_expired = now > expiry_time

            if hit_tp:
                existing["status"] = "CLOSED_HIT_TP"
                existing["message"] = f"Target Take Profit tercapai pada {tp:.5f}!"
                self._save()
                return self._format_signal_output(existing, current_price, pip_val, style_config)

            elif hit_sl:
                existing["status"] = "CLOSED_HIT_SL"
                existing["message"] = f"Stop Loss tersentuh pada {sl:.5f} (proteksi risiko aktif)."
                self._save()
                return self._format_signal_output(existing, current_price, pip_val, style_config)

            elif not is_expired:
                # Signal is STILL VALID and LOCKED IN!
                existing["status"] = "ACTIVE_LOCKED"
                time_left_min = max(0, int((expiry_time - now).total_seconds() / 60))
                existing["time_remaining"] = f"{time_left_min} menit tersisa"
                return self._format_signal_output(existing, current_price, pip_val, style_config)

        # 2. No active locked signal, or previous signal is closed/expired:
        # Check if new_signal generates a new BUY or SELL
        if new_signal.get("action") in ["BUY", "SELL"]:
            locked_entry = {
                "symbol": symbol,
                "style": style_key,
                "action": new_signal["action"],
                "confidence": new_signal["confidence"],
                "entry_price": current_price,
                "take_profit": new_signal["take_profit"],
                "stop_loss": new_signal["stop_loss"],
                "tp_pips": new_signal["tp_pips"],
                "sl_pips": new_signal["sl_pips"],
                "risk_reward": new_signal["risk_reward"],
                "reason": new_signal["reason"],
                "p_buy": new_signal.get("p_buy", 0.0),
                "p_sell": new_signal.get("p_sell", 0.0),
                "created_at": now.isoformat(),
                "status": "ACTIVE_LOCKED",
                "time_remaining": f"{style_config['validity_minutes']} menit tersisa",
            }
            self.active_signals[signal_key] = locked_entry
            self._save()
            return self._format_signal_output(locked_entry, current_price, pip_val, style_config)

        # 3. Otherwise, state is clean HOLD
        hold_output = dict(new_signal)
        hold_output["status"] = "WAITING_SETUP"
        hold_output["time_remaining"] = style_config["holding_time_str"]
        return hold_output

    def _format_signal_output(
        self,
        signal_data: Dict[str, Any],
        current_price: float,
        pip_val: float,
        style_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        out = dict(signal_data)
        action = out.get("action", "HOLD")
        entry = out.get("entry_price", current_price)

        if action == "BUY":
            floating_pips = (current_price - entry) / pip_val
        elif action == "SELL":
            floating_pips = (entry - current_price) / pip_val
        else:
            floating_pips = 0.0

        out["floating_pips"] = round(floating_pips, 1)
        out["holding_advice"] = style_config["holding_time_str"]
        return out

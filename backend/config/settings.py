"""
Configuration module for Forex Machine Learning Trading System.
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = BASE_DIR / "saved_models"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# List of popular Forex and Metal Pairs
DEFAULT_PAIRS: Dict[str, Dict[str, str]] = {
    "EURUSD": {"yfinance": "EURUSD=X", "name": "Euro / US Dollar", "pip_decimal": 4, "pip_value": 0.0001},
    "GBPUSD": {"yfinance": "GBPUSD=X", "name": "British Pound / US Dollar", "pip_decimal": 4, "pip_value": 0.0001},
    "USDJPY": {"yfinance": "USDJPY=X", "name": "US Dollar / Japanese Yen", "pip_decimal": 2, "pip_value": 0.01},
    "AUDUSD": {"yfinance": "AUDUSD=X", "name": "Australian Dollar / US Dollar", "pip_decimal": 4, "pip_value": 0.0001},
    "USDCAD": {"yfinance": "CAD=X", "name": "US Dollar / Canadian Dollar", "pip_decimal": 4, "pip_value": 0.0001},
    "USDCHF": {"yfinance": "CHF=X", "name": "US Dollar / Swiss Franc", "pip_decimal": 4, "pip_value": 0.0001},
    "NZDUSD": {"yfinance": "NZDUSD=X", "name": "New Zealand Dollar / US Dollar", "pip_decimal": 4, "pip_value": 0.0001},
    "XAUUSD": {"yfinance": "GC=F", "name": "Gold / US Dollar", "pip_decimal": 2, "pip_value": 0.10},
    "BTCUSD": {"yfinance": "BTC-USD", "name": "Bitcoin / US Dollar", "pip_decimal": 2, "pip_value": 1.0},
}

SUPPORTED_TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]

@dataclass
class RiskSettings:
    risk_per_trade_pct: float = 1.0  # 1% per trade
    max_open_trades: int = 3
    default_stop_loss_pips: float = 20.0
    default_take_profit_pips: float = 40.0
    min_risk_reward_ratio: float = 1.5
    slippage_pips: float = 0.5
    spread_pips: float = 1.5

@dataclass
class SystemConfig:
    data_source: str = "yfinance"  # 'yfinance' or 'mt5'
    default_pair: str = "EURUSD"
    default_timeframe: str = "1h"
    cache_expiry_hours: int = 1
    risk: RiskSettings = field(default_factory=RiskSettings)

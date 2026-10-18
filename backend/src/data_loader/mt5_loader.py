"""
MetaTrader 5 DataLoader for Real-Time & Historical Forex Data.
"""
from typing import Optional
from datetime import datetime
import pandas as pd
from .base_loader import BaseDataLoader

# Optional import of MetaTrader5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class MT5DataLoader(BaseDataLoader):
    """
    DataLoader using the official MetaTrader 5 Python API.
    """

    TIMEFRAME_MAP = {}
    if MT5_AVAILABLE:
        TIMEFRAME_MAP = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
        }

    def __init__(self):
        self.initialized = False

    def initialize(self, login: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None) -> bool:
        """
        Initialize connection to MetaTrader 5 terminal.
        """
        if not MT5_AVAILABLE:
            print("[MT5DataLoader] MetaTrader5 package is not installed. To use MT5, run: pip install MetaTrader5")
            return False

        if login and password and server:
            self.initialized = mt5.initialize(login=login, password=password, server=server)
        else:
            self.initialized = mt5.initialize()

        if not self.initialized:
            print(f"[MT5DataLoader] Failed to connect to MetaTrader 5 terminal. Error: {mt5.last_error()}")
        return self.initialized

    def fetch_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: Optional[str] = "1y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        count: int = 5000,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candles from MetaTrader 5 terminal.
        """
        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 python package is not installed.")

        if not self.initialized and not self.initialize():
            raise RuntimeError("Could not connect to active MetaTrader 5 terminal.")

        tf = self.TIMEFRAME_MAP.get(timeframe.lower(), mt5.TIMEFRAME_H1)

        # Check symbol availability
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            # Try appending suffix or common broker variants
            for variant in [symbol, symbol + ".m", symbol + ".raw", symbol + "pro"]:
                if mt5.symbol_info(variant) is not None:
                    symbol = variant
                    break

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            raise ValueError(f"Failed to fetch rates for {symbol} from MT5. Error: {mt5.last_error()}")

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)

        return self.standardize_df(df)

    def shutdown(self):
        if MT5_AVAILABLE and self.initialized:
            mt5.shutdown()
            self.initialized = False

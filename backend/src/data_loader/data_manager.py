"""
Unified Data Manager with multi-source fallback, local caching, and integrity validation.
"""
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from config.settings import CACHE_DIR, DEFAULT_PAIRS
from .base_loader import BaseDataLoader
from .yfinance_loader import YFinanceDataLoader
from .mt5_loader import MT5DataLoader, MT5_AVAILABLE


class DataManager:
    """
    Central data manager that coordinates fetching, local caching, and multi-timeframe resolution.
    """

    def __init__(self, primary_source: str = "yfinance", cache_dir: Optional[Path] = None):
        self.primary_source = primary_source.lower()
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.yf_loader = YFinanceDataLoader()
        self.mt5_loader = MT5DataLoader() if MT5_AVAILABLE else None

    def _get_cache_filepath(self, symbol: str, timeframe: str) -> Path:
        clean_symbol = symbol.upper().replace("/", "").replace("=", "_").replace("-", "_")
        return self.cache_dir / f"{clean_symbol}_{timeframe}.parquet"

    def _is_cache_valid(self, cache_file: Path, max_age_hours: float = 1.0) -> bool:
        if not cache_file.exists():
            return False
        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - file_mtime < timedelta(hours=max_age_hours)

    def get_data(self, *args, **kwargs) -> pd.DataFrame:
        """Alias for get_ohlcv for backward and external compatibility."""
        return self.get_ohlcv(*args, **kwargs)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_refresh: bool = False,
        max_cache_age_hours: float = 1.0,
    ) -> pd.DataFrame:
        """
        Retrieves clean OHLCV data. Checks cache first, otherwise fetches from data provider and caches it.
        """
        symbol = symbol.upper().strip()
        timeframe = timeframe.lower().strip()
        cache_path = self._get_cache_filepath(symbol, timeframe)

        # 1. Check local cache
        if not force_refresh and self._is_cache_valid(cache_path, max_age_hours=max_cache_age_hours):
            try:
                df = pd.read_parquet(cache_path)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"[DataManager] Warning reading cache {cache_path}: {e}. Refetching...")

        # 2. Fetch fresh data
        df = None
        # Try primary source
        if self.primary_source == "mt5" and self.mt5_loader is not None:
            try:
                df = self.mt5_loader.fetch_data(symbol, timeframe=timeframe, period=period, start_date=start_date, end_date=end_date)
            except Exception as e:
                print(f"[DataManager] MT5 fetch failed: {e}. Falling back to Yahoo Finance...")

        if df is None or df.empty:
            df = self.yf_loader.fetch_data(symbol, timeframe=timeframe, period=period, start_date=start_date, end_date=end_date)

        # 3. Save to local cache
        if df is not None and not df.empty:
            try:
                df.to_parquet(cache_path, engine="pyarrow")
            except Exception as e:
                # Fallback to CSV if parquet fails
                csv_path = cache_path.with_suffix(".csv")
                df.to_csv(csv_path)

        return df

    def get_realtime_quote(self, symbol: str) -> Optional[float]:
        """
        Fast fetch of the latest real-time market price via fast_info.
        """
        try:
            ticker_sym = self.yf_loader._resolve_symbol(symbol)
            import yfinance as yf
            t = yf.Ticker(ticker_sym)
            price = t.fast_info.get("lastPrice", None)
            if price is not None and not pd.isna(price):
                return float(price)
        except Exception:
            pass
        return None

    def get_live_ohlcv(
        self,
        symbol: str,
        timeframe: str = "5m",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Fetches OHLCV data with adaptive cache age for live trading.
        For intraday timeframes (1m, 5m, 15m), cache expires in 20 seconds.
        Dynamically updates the last candle with live market tick.
        """
        # Set max cache age short for intraday
        if timeframe.lower() in ["1m", "5m"]:
            cache_age = 0.005  # ~18 seconds
        elif timeframe.lower() in ["15m", "30m"]:
            cache_age = 0.02   # ~1.2 minutes
        else:
            cache_age = 0.08   # ~5 minutes

        df = self.get_ohlcv(symbol, timeframe=timeframe, force_refresh=force_refresh, max_cache_age_hours=cache_age)

        # Update last candle with live tick if available
        live_price = self.get_realtime_quote(symbol)
        if live_price is not None and not df.empty:
            last_idx = df.index[-1]
            df.loc[last_idx, "close"] = live_price
            if live_price > df.loc[last_idx, "high"]:
                df.loc[last_idx, "high"] = live_price
            if live_price < df.loc[last_idx, "low"]:
                df.loc[last_idx, "low"] = live_price

        return df

    def get_market_summary(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Computes snapshot statistics for the selected market.
        """
        if df.empty:
            return {"symbol": symbol, "status": "No data"}

        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        change = latest["close"] - previous["close"]
        change_pct = (change / previous["close"]) * 100 if previous["close"] != 0 else 0.0

        pair_info = DEFAULT_PAIRS.get(symbol.upper(), {})
        pip_value = pair_info.get("pip_value", 0.0001)

        high_24h = df["high"].tail(24).max()
        low_24h = df["low"].tail(24).min()

        return {
            "symbol": symbol,
            "name": pair_info.get("name", symbol),
            "bars_count": len(df),
            "start_time": str(df.index[0]),
            "last_time": str(df.index[-1]),
            "current_close": float(latest["close"]),
            "current_open": float(latest["open"]),
            "current_high": float(latest["high"]),
            "current_low": float(latest["low"]),
            "change": float(change),
            "change_pct": float(change_pct),
            "range_24h_pips": float((high_24h - low_24h) / pip_value) if pip_value else 0.0,
            "latest_volume": float(latest["volume"]),
        }

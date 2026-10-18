"""
Yahoo Finance DataLoader for Forex and CFD Market Data.
"""
from typing import Optional
import yfinance as yf
import pandas as pd
from .base_loader import BaseDataLoader
from config.settings import DEFAULT_PAIRS


class YFinanceDataLoader(BaseDataLoader):
    """
    Data loader utilizing yfinance for online forex and commodity market feeds.
    """

    TIMEFRAME_MAPPING = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "1d": "1d",
        "1wk": "1wk",
    }

    def _resolve_symbol(self, pair: str) -> str:
        """
        Maps standard pair (e.g., EURUSD) to Yahoo Finance ticker.
        """
        pair_clean = pair.upper().replace("/", "").replace("-", "")
        if pair_clean in DEFAULT_PAIRS:
            return DEFAULT_PAIRS[pair_clean]["yfinance"]
        
        # Fallback heuristic
        if len(pair_clean) == 6:
            return f"{pair_clean}=X"
        return pair_clean

    def fetch_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: Optional[str] = "1y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Yahoo Finance.
        Supports automatic 4h generation by resampling 1h data.
        """
        ticker_symbol = self._resolve_symbol(symbol)
        
        # Handle 4h timeframe (yfinance doesn't provide 4h natively, so fetch 1h and resample)
        needs_4h_resample = False
        fetch_interval = timeframe
        if timeframe.lower() == "4h":
            needs_4h_resample = True
            fetch_interval = "1h"

        interval = self.TIMEFRAME_MAPPING.get(fetch_interval, "1h")

        # Set default period safely based on interval limits of yfinance
        if period is None and start_date is None:
            if interval in ["1m", "5m", "15m", "30m"]:
                period = "60d"  # yfinance intraday limit
            elif interval == "1h":
                period = "730d"  # 2 years
            else:
                period = "5y"

        ticker = yf.Ticker(ticker_symbol)

        if start_date:
            df = ticker.history(interval=interval, start=start_date, end=end_date, auto_adjust=False)
        else:
            df = ticker.history(interval=interval, period=period, auto_adjust=False)

        if df.empty:
            # Try alternate fallback symbol if applicable
            if ticker_symbol == "GC=F":
                alt_ticker = yf.Ticker("XAUUSD=X")
                df = alt_ticker.history(interval=interval, period=period, auto_adjust=False)

        if df.empty:
            raise ValueError(
                f"No data returned from Yahoo Finance for symbol '{symbol}' "
                f"(ticker: '{ticker_symbol}') with interval '{interval}'."
            )

        standardized_df = self.standardize_df(df)

        # Resample to 4h if requested
        if needs_4h_resample:
            standardized_df = self._resample_to_4h(standardized_df)

        return standardized_df

    def _resample_to_4h(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample 1h OHLCV DataFrame into 4h OHLCV.
        """
        resampled = df.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        return resampled

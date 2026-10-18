"""
Base DataLoader Interface for Forex Market Data.
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseDataLoader(ABC):
    """
    Abstract base class for fetching forex and financial market data.
    Ensures standard output DataFrame structure:
    - Index: pd.DatetimeIndex
    - Columns: ['open', 'high', 'low', 'close', 'volume']
    """

    @abstractmethod
    def fetch_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        period: Optional[str] = "1y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for given symbol and timeframe.
        """
        pass

    def standardize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame column names to lowercase and validate required OHLCV columns.
        """
        if df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # Normalize column names
        df.columns = [str(c).lower().strip() for c in df.columns]

        # Handle MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower().strip() for col in df.columns]

        # Check required columns
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col} in fetched data.")

        if "volume" not in df.columns:
            df["volume"] = 0.0

        # Select only standard columns
        df = df[["open", "high", "low", "close", "volume"]].copy()

        # Ensure index is datetime and sorted
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Remove timezone info for uniform cross-compatibility
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df.sort_index(inplace=True)
        # Drop duplicates by index
        df = df[~df.index.duplicated(keep="last")]

        # Forward fill and backward fill any occasional missing ticks
        df.ffill(inplace=True)
        df.bfill(inplace=True)

        return df

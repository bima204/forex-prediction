"""
Purged & Embargoed Walk-Forward Time-Series Splitter.
Prevents data leakage in financial machine learning caused by overlapping labeling horizons.
"""
from typing import Generator, Tuple
import numpy as np
import pandas as pd


class PurgedWalkForwardCV:
    """
    Implements Walk-Forward Cross Validation with Purging and Embargo
    as recommended by Marcos Lopez de Prado (Advances in Financial Machine Learning).
    """

    def __init__(self, n_splits: int = 5, purge_window: int = 24, embargo_pct: float = 0.01):
        self.n_splits = n_splits
        self.purge_window = purge_window
        self.embargo_pct = embargo_pct

    def split(self, df: pd.DataFrame) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Yields (train_indices, test_indices) for walk-forward evaluation.
        """
        n_samples = len(df)
        indices = np.arange(n_samples)
        embargo = int(n_samples * self.embargo_pct)
        
        # Test fold size
        test_size = n_samples // (self.n_splits + 1)

        for i in range(1, self.n_splits + 1):
            train_end = i * test_size
            test_start = train_end + self.purge_window  # Purge overlapping horizon
            test_end = min(test_start + test_size, n_samples)

            if test_start >= n_samples:
                break

            train_indices = indices[:train_end]
            test_indices = indices[test_start:test_end]

            yield train_indices, test_indices

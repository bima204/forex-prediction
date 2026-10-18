"""
Validation test for Phase 1: Data Ingestion & Market Selector.
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.data_loader.data_manager import DataManager
from src.market_selector import MarketSelector
from config.settings import DEFAULT_PAIRS, CACHE_DIR


def test_data_pipeline():
    print("=== Testing Phase 1: Data Loader & Market Pipeline ===")
    dm = DataManager()
    
    # Test 1: Fetch EURUSD 1h
    test_pair = "EURUSD"
    print(f"\n1. Fetching data for {test_pair} (1h)...")
    df = dm.get_ohlcv(test_pair, timeframe="1h")
    assert not df.empty, "DataFrame should not be empty!"
    assert all(c in df.columns for c in ["open", "high", "low", "close", "volume"]), "All OHLCV columns must be present"
    print(f"   [PASS] Successfully loaded {len(df)} candles for {test_pair}.")
    print(f"   Sample close: {df['close'].iloc[-1]:.5f}, Date range: {df.index[0]} to {df.index[-1]}")

    # Test 2: Check caching
    cache_file = dm._get_cache_filepath(test_pair, "1h")
    assert cache_file.exists(), f"Cache file {cache_file} should exist!"
    print(f"   [PASS] Local cache verified at: {cache_file.name} ({cache_file.stat().st_size / 1024:.1f} KB)")

    # Test 3: Market Summary
    summary = dm.get_market_summary(df, test_pair)
    assert summary["bars_count"] == len(df)
    print(f"   [PASS] Market summary calculated: Current Close = {summary['current_close']}, 24h Range = {summary['range_24h_pips']:.1f} pips")

    # Test 4: Market Selector Catalog
    selector = MarketSelector(dm)
    markets = selector.list_available_markets()
    assert len(markets) >= len(DEFAULT_PAIRS)
    print(f"   [PASS] Market catalog verified with {len(markets)} configured pairs.")

    # Test 5: Fetch Gold (XAUUSD)
    print("\n2. Fetching Metal Pair (XAUUSD)...")
    df_gold = dm.get_ohlcv("XAUUSD", timeframe="1h")
    assert not df_gold.empty, "Gold data should not be empty"
    print(f"   [PASS] Successfully loaded {len(df_gold)} candles for Gold (XAUUSD). Latest price: {df_gold['close'].iloc[-1]:.2f}")

    print("\n[SUCCESS] ALL PHASE 1 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_data_pipeline()

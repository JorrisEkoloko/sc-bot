"""
Tests for HistoricalPriceRetriever

Run with: pytest tests/test_historical_price_retriever.py -v
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pricing import HistoricalPriceRetriever, HistoricalPriceData, OHLCCandle


@pytest.fixture
async def retriever():
    """Create retriever instance."""
    retriever = HistoricalPriceRetriever(
        cache_dir="data/cache/test"
    )
    yield retriever
    await retriever.close()


@pytest.mark.asyncio
async def test_fetch_price_at_timestamp_btc(retriever):
    """Test fetching historical BTC price at specific timestamp."""
    # Fetch BTC price from Nov 10, 2023
    timestamp = datetime(2023, 11, 10)
    price = await retriever.fetch_price_at_timestamp('BTC', timestamp)
    
    assert price is not None
    assert price > 0
    assert price > 30000  # BTC was above $30k in Nov 2023
    assert price < 50000  # BTC was below $50k in Nov 2023
    print(f"✓ BTC price on {timestamp}: ${price:,.2f}")


@pytest.mark.asyncio
async def test_fetch_price_at_timestamp_eth(retriever):
    """Test fetching historical ETH price at specific timestamp."""
    # Fetch ETH price from Nov 10, 2023
    timestamp = datetime(2023, 11, 10)
    price = await retriever.fetch_price_at_timestamp('ETH', timestamp)
    
    assert price is not None
    assert price > 0
    assert price > 1500  # ETH was above $1500 in Nov 2023
    assert price < 3000  # ETH was below $3000 in Nov 2023
    print(f"✓ ETH price on {timestamp}: ${price:,.2f}")


@pytest.mark.asyncio
async def test_fetch_price_invalid_symbol(retriever):
    """Test fetching price for invalid/obscure symbol."""
    timestamp = datetime(2023, 11, 10)
    price = await retriever.fetch_price_at_timestamp('INVALIDTOKEN123', timestamp)
    
    # Should return None for invalid tokens
    assert price is None or price == 0
    print(f"✓ Invalid token correctly returned None/0")


@pytest.mark.asyncio
async def test_fetch_ohlc_window_btc(retriever):
    """Test fetching OHLC window for BTC."""
    start_timestamp = datetime(2023, 11, 1)
    data = await retriever.fetch_ohlc_window('BTC', start_timestamp, window_days=30)
    
    assert data is not None
    assert data.symbol == 'BTC'
    assert data.price_at_timestamp > 0
    assert data.ath_in_window > 0
    assert data.ath_in_window >= data.price_at_timestamp  # ATH should be >= entry
    assert len(data.candles) > 0
    assert data.source in ['cryptocompare', 'twelvedata']
    
    print(f"✓ BTC OHLC window:")
    print(f"  Entry: ${data.price_at_timestamp:,.2f}")
    print(f"  ATH: ${data.ath_in_window:,.2f}")
    print(f"  Days to ATH: {data.days_to_ath:.1f}")
    print(f"  Candles: {len(data.candles)}")
    print(f"  Source: {data.source}")


@pytest.mark.asyncio
async def test_caching(retriever):
    """Test that caching works correctly."""
    start_timestamp = datetime(2023, 11, 1)
    
    # First fetch - should not be cached
    data1 = await retriever.fetch_ohlc_window('BTC', start_timestamp, window_days=30)
    assert data1 is not None
    assert not data1.cached
    
    # Second fetch - should be cached
    data2 = await retriever.fetch_ohlc_window('BTC', start_timestamp, window_days=30)
    assert data2 is not None
    assert data2.cached
    
    # Data should be identical
    assert data1.price_at_timestamp == data2.price_at_timestamp
    assert data1.ath_in_window == data2.ath_in_window
    
    print(f"✓ Caching works correctly")


def test_smart_checkpoints_2_days():
    """Test smart checkpoint calculation for 2-day-old message."""
    retriever = HistoricalPriceRetriever()
    
    message_date = datetime.now() - timedelta(days=2)
    checkpoints = retriever.calculate_smart_checkpoints(message_date)
    
    # Should have 1h, 4h, 24h (3 checkpoints)
    checkpoint_names = [name for name, _ in checkpoints]
    assert '1h' in checkpoint_names
    assert '4h' in checkpoint_names
    assert '24h' in checkpoint_names
    assert '3d' not in checkpoint_names  # Not reached yet
    assert '7d' not in checkpoint_names
    assert '30d' not in checkpoint_names
    
    print(f"✓ 2-day-old message: {len(checkpoints)} checkpoints reached")


def test_smart_checkpoints_10_days():
    """Test smart checkpoint calculation for 10-day-old message."""
    retriever = HistoricalPriceRetriever()
    
    message_date = datetime.now() - timedelta(days=10)
    checkpoints = retriever.calculate_smart_checkpoints(message_date)
    
    # Should have 1h, 4h, 24h, 3d, 7d (5 checkpoints)
    checkpoint_names = [name for name, _ in checkpoints]
    assert '1h' in checkpoint_names
    assert '4h' in checkpoint_names
    assert '24h' in checkpoint_names
    assert '3d' in checkpoint_names
    assert '7d' in checkpoint_names
    assert '30d' not in checkpoint_names  # Not reached yet
    
    print(f"✓ 10-day-old message: {len(checkpoints)} checkpoints reached")


def test_smart_checkpoints_35_days():
    """Test smart checkpoint calculation for 35-day-old message."""
    retriever = HistoricalPriceRetriever()
    
    message_date = datetime.now() - timedelta(days=35)
    checkpoints = retriever.calculate_smart_checkpoints(message_date)
    
    # Should have all 6 checkpoints
    checkpoint_names = [name for name, _ in checkpoints]
    assert len(checkpoints) == 6
    assert '1h' in checkpoint_names
    assert '4h' in checkpoint_names
    assert '24h' in checkpoint_names
    assert '3d' in checkpoint_names
    assert '7d' in checkpoint_names
    assert '30d' in checkpoint_names
    
    print(f"✓ 35-day-old message: {len(checkpoints)} checkpoints reached (all)")


@pytest.mark.asyncio
async def test_batch_prices_at_timestamp(retriever):
    """Test batch fetching prices at timestamp."""
    symbols = ['BTC', 'ETH', 'SOL']
    timestamp = datetime(2023, 11, 10)
    
    results = await retriever.fetch_batch_prices_at_timestamp(symbols, timestamp, max_concurrent=3)
    
    assert len(results) == 3
    assert results['BTC'] is not None
    assert results['BTC'] > 0
    assert results['ETH'] is not None
    assert results['ETH'] > 0
    
    print(f"✓ Batch prices at {timestamp}:")
    for symbol, price in results.items():
        if price:
            print(f"  {symbol}: ${price:,.2f}")


@pytest.mark.asyncio
async def test_batch_ohlc(retriever):
    """Test batch fetching OHLC windows."""
    symbols = ['BTC', 'ETH']
    start_timestamp = datetime(2023, 11, 1)
    
    results = await retriever.fetch_batch_ohlc(symbols, start_timestamp, window_days=30, max_concurrent=2)
    
    assert len(results) == 2
    assert results['BTC'] is not None
    assert results['ETH'] is not None
    
    print(f"✓ Batch OHLC windows:")
    for symbol, data in results.items():
        if data:
            print(f"  {symbol}: Entry ${data.price_at_timestamp:,.2f}, ATH ${data.ath_in_window:,.2f}")


@pytest.mark.asyncio
async def test_roi_calculation():
    """Test ROI calculation from historical data."""
    retriever = HistoricalPriceRetriever()
    
    # Fetch BTC data
    start_timestamp = datetime(2023, 11, 1)
    data = await retriever.fetch_ohlc_window('BTC', start_timestamp, window_days=30)
    
    if data:
        # Calculate ROI
        roi_multiplier = data.ath_in_window / data.price_at_timestamp
        roi_percentage = (roi_multiplier - 1) * 100
        
        assert roi_multiplier >= 1.0  # ATH should be >= entry
        
        print(f"✓ ROI Calculation:")
        print(f"  Entry: ${data.price_at_timestamp:,.2f}")
        print(f"  ATH: ${data.ath_in_window:,.2f}")
        print(f"  ROI: {roi_multiplier:.3f}x ({roi_percentage:.1f}%)")
        print(f"  Days to ATH: {data.days_to_ath:.1f}")
        
        # Classify outcome
        if roi_multiplier >= 2.0:
            outcome = "WINNER"
        elif roi_multiplier < 1.0:
            outcome = "LOSER"
        else:
            outcome = "BREAK_EVEN"
        
        print(f"  Outcome: {outcome}")
    
    await retriever.close()


if __name__ == '__main__':
    # Run tests manually
    print("Running HistoricalPriceRetriever tests...\n")
    
    async def run_tests():
        retriever = HistoricalPriceRetriever(cache_dir="data/cache/test")
        
        try:
            print("1. Testing BTC price at timestamp...")
            await test_fetch_price_at_timestamp_btc(retriever)
            
            print("\n2. Testing ETH price at timestamp...")
            await test_fetch_price_at_timestamp_eth(retriever)
            
            print("\n3. Testing invalid symbol...")
            await test_fetch_price_invalid_symbol(retriever)
            
            print("\n4. Testing OHLC window...")
            await test_fetch_ohlc_window_btc(retriever)
            
            print("\n5. Testing caching...")
            await test_caching(retriever)
            
            print("\n6. Testing smart checkpoints (2 days)...")
            test_smart_checkpoints_2_days()
            
            print("\n7. Testing smart checkpoints (10 days)...")
            test_smart_checkpoints_10_days()
            
            print("\n8. Testing smart checkpoints (35 days)...")
            test_smart_checkpoints_35_days()
            
            print("\n9. Testing batch prices...")
            await test_batch_prices_at_timestamp(retriever)
            
            print("\n10. Testing batch OHLC...")
            await test_batch_ohlc(retriever)
            
            print("\n11. Testing ROI calculation...")
            await test_roi_calculation()
            
            print("\n✅ All tests passed!")
            
        finally:
            await retriever.close()
    
    asyncio.run(run_tests())

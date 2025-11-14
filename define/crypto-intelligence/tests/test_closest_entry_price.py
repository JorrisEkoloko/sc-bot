"""
Test script for closest entry price and forward OHLC implementation.

Run with: python -m pytest tests/test_closest_entry_price.py -v
"""
import asyncio
import os
from datetime import datetime, timedelta
from services.pricing.historical_price_retriever import HistoricalPriceRetriever


async def test_closest_entry_price():
    """Test fetching closest entry price with fallback."""
    print("\n=== Testing Closest Entry Price ===\n")
    
    # Initialize retriever
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY', '')
    )
    
    try:
        # Test with a known historical date (30 days ago)
        test_date = datetime.now() - timedelta(days=30)
        
        print(f"Test date: {test_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Fetching closest BTC price...\n")
        
        # Fetch closest entry price
        price, source = await retriever.fetch_closest_entry_price('BTC', test_date)
        
        if price:
            print(f"✓ SUCCESS!")
            print(f"  Price: ${price:,.2f}")
            print(f"  Source: {source}")
        else:
            print(f"✗ FAILED: No price found")
            
    finally:
        await retriever.close()


async def test_forward_ohlc_with_ath():
    """Test fetching forward OHLC and calculating ATH."""
    print("\n=== Testing Forward OHLC with ATH ===\n")
    
    # Initialize retriever
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY', '')
    )
    
    try:
        # Test with a date 60 days ago (so we have 30 days of forward data)
        test_date = datetime.now() - timedelta(days=60)
        
        print(f"Entry date: {test_date.strftime('%Y-%m-%d')}")
        print(f"Fetching 30 days of forward OHLC for BTC...\n")
        
        # Fetch forward OHLC
        result = await retriever.fetch_forward_ohlc_with_ath('BTC', test_date, window_days=30)
        
        if result:
            print(f"✓ SUCCESS!")
            print(f"  Entry price: ${result['entry_price']:,.2f}")
            print(f"  ATH price: ${result['ath_price']:,.2f}")
            print(f"  ATH multiplier: {result['ath_price'] / result['entry_price']:.3f}x")
            print(f"  Days to ATH: {result['days_to_ath']:.1f}")
            print(f"  Candles: {len(result['candles'])}")
            print(f"  Data completeness: {result['data_completeness']*100:.1f}%")
            print(f"  Source: {result['source']}")
        else:
            print(f"✗ FAILED: No OHLC data found")
            
    finally:
        await retriever.close()


async def test_checkpoint_rois():
    """Test calculating checkpoint ROIs from OHLC."""
    print("\n=== Testing Checkpoint ROIs from OHLC ===\n")
    
    # Initialize retriever
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY', '')
    )
    
    try:
        # Test with a date 60 days ago
        test_date = datetime.now() - timedelta(days=60)
        
        print(f"Entry date: {test_date.strftime('%Y-%m-%d')}")
        print(f"Fetching OHLC and calculating checkpoint ROIs...\n")
        
        # Get OHLC data
        result = await retriever.fetch_forward_ohlc_with_ath('BTC', test_date, window_days=30)
        
        if not result:
            print(f"✗ FAILED: No OHLC data found")
            return
        
        # Define checkpoints
        checkpoints = [
            ('1h', timedelta(hours=1)),
            ('4h', timedelta(hours=4)),
            ('24h', timedelta(days=1)),
            ('3d', timedelta(days=3)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30))
        ]
        
        # Calculate checkpoint ROIs
        checkpoint_rois = await retriever.calculate_checkpoint_rois_from_ohlc(
            entry_price=result['entry_price'],
            entry_timestamp=test_date,
            checkpoints=checkpoints,
            candles=result['candles']
        )
        
        if checkpoint_rois:
            print(f"✓ SUCCESS!")
            print(f"  Entry price: ${result['entry_price']:,.2f}\n")
            print(f"  Checkpoint ROIs:")
            for checkpoint_name, roi in checkpoint_rois.items():
                price = roi * result['entry_price']
                gain = (roi - 1) * 100
                print(f"    {checkpoint_name:>4}: ${price:>10,.2f} ({roi:.3f}x, {gain:+6.1f}%)")
        else:
            print(f"✗ FAILED: No checkpoint ROIs calculated")
            
    finally:
        await retriever.close()


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Testing Historical Price Retriever Implementation")
    print("="*60)
    
    await test_closest_entry_price()
    await test_forward_ohlc_with_ath()
    await test_checkpoint_rois()
    
    print("\n" + "="*60)
    print("All tests complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    asyncio.run(main())

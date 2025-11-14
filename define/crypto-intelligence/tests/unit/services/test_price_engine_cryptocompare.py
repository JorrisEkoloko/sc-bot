"""Test CryptoCompare integration in PriceEngine."""
import asyncio
from datetime import datetime
from config.price_config import PriceConfig
from services.pricing.price_engine import PriceEngine

async def test_price_engine_cryptocompare():
    """Test CryptoCompare methods in PriceEngine."""
    print("="*60)
    print("Testing CryptoCompare Integration in PriceEngine")
    print("="*60)
    
    # Initialize price engine
    config = PriceConfig()
    price_engine = PriceEngine(config)
    
    try:
        # Test 1: Get historical OHLC
        print("\n📈 Test 1: Get Historical OHLC (BTC, 7 days)")
        print("-" * 60)
        ohlc_data = await price_engine.get_historical_ohlc('BTC', days=7)
        if ohlc_data:
            print(f"✅ Retrieved {len(ohlc_data)} daily candles")
            print("\nLast 3 days:")
            for candle in ohlc_data[-3:]:
                date = datetime.fromtimestamp(candle['time']).strftime('%Y-%m-%d')
                print(f"   {date}: Open=${candle['open']:,.2f}, High=${candle['high']:,.2f}, "
                      f"Low=${candle['low']:,.2f}, Close=${candle['close']:,.2f}")
        else:
            print("❌ Failed to get OHLC data")
        
        # Test 2: Get price at timestamp
        print("\n📅 Test 2: Get Price at Timestamp (BTC on Jan 1, 2021)")
        print("-" * 60)
        timestamp = int(datetime(2021, 1, 1).timestamp())
        price = await price_engine.get_price_at_timestamp('BTC', timestamp)
        if price:
            print(f"✅ BTC Price on Jan 1, 2021: ${price:,.2f}")
        else:
            print("❌ Failed to get historical price")
        
        # Test 3: Get historical OHLC for ETH
        print("\n💎 Test 3: Get Historical OHLC (ETH, 5 days)")
        print("-" * 60)
        eth_ohlc = await price_engine.get_historical_ohlc('ETH', days=5)
        if eth_ohlc:
            print(f"✅ Retrieved {len(eth_ohlc)} daily candles for ETH")
            # Find ATH in the data
            ath_price = max(candle['high'] for candle in eth_ohlc)
            ath_candle = next(c for c in eth_ohlc if c['high'] == ath_price)
            ath_date = datetime.fromtimestamp(ath_candle['time']).strftime('%Y-%m-%d')
            print(f"   ATH in last 5 days: ${ath_price:,.2f} on {ath_date}")
        else:
            print("❌ Failed to get ETH OHLC data")
        
        # Test 4: Get price at recent timestamp
        print("\n⏰ Test 4: Get Price at Recent Timestamp (SOL, 7 days ago)")
        print("-" * 60)
        seven_days_ago = int((datetime.now().timestamp() - 7*24*60*60))
        sol_price = await price_engine.get_price_at_timestamp('SOL', seven_days_ago)
        if sol_price:
            print(f"✅ SOL Price 7 days ago: ${sol_price:,.2f}")
        else:
            print("❌ Failed to get SOL historical price")
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    finally:
        # Clean up
        await price_engine.close()
        print("\n✅ Price engine closed")

if __name__ == "__main__":
    asyncio.run(test_price_engine_cryptocompare())

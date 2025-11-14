"""Test script for CryptoCompare API client."""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from repositories.api_clients.cryptocompare_client import CryptoCompareClient

# Load environment variables
load_dotenv()

async def test_cryptocompare():
    """Test CryptoCompare API endpoints."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    
    if not api_key:
        print("❌ CRYPTOCOMPARE_API_KEY not found in .env")
        return
    
    print(f"✅ API Key loaded: {api_key[:20]}...")
    print("\n" + "="*60)
    
    async with CryptoCompareClient(api_key) as client:
        # Test 1: Current Price
        print("\n📊 Test 1: Get Current Price (BTC)")
        print("-" * 60)
        price_data = await client.get_price('BTC', 'USD')
        if price_data:
            print(f"✅ BTC Price: ${price_data.price_usd:,.2f}")
            print(f"   Source: {price_data.source}")
        else:
            print("❌ Failed to get current price")
        
        # Test 2: Historical Price at Timestamp
        print("\n📅 Test 2: Get Historical Price (BTC on Jan 1, 2021)")
        print("-" * 60)
        timestamp = int(datetime(2021, 1, 1).timestamp())
        historical_price = await client.get_price_at_timestamp('BTC', timestamp)
        if historical_price:
            print(f"✅ BTC Price on Jan 1, 2021: ${historical_price:,.2f}")
        else:
            print("❌ Failed to get historical price")
        
        # Test 3: Daily OHLC (last 7 days)
        print("\n📈 Test 3: Get Daily OHLC (BTC, last 7 days)")
        print("-" * 60)
        ohlc_data = await client.get_daily_ohlc('BTC', limit=7)
        if ohlc_data:
            print(f"✅ Retrieved {len(ohlc_data)} daily candles")
            print("\nLast 3 days:")
            for candle in ohlc_data[-3:]:
                date = datetime.fromtimestamp(candle['time']).strftime('%Y-%m-%d')
                print(f"   {date}: Open=${candle['open']:,.2f}, High=${candle['high']:,.2f}, "
                      f"Low=${candle['low']:,.2f}, Close=${candle['close']:,.2f}")
        else:
            print("❌ Failed to get OHLC data")
        
        # Test 4: Hourly OHLC (last 6 hours)
        print("\n⏰ Test 4: Get Hourly OHLC (BTC, last 6 hours)")
        print("-" * 60)
        hourly_data = await client.get_hourly_ohlc('BTC', limit=6)
        if hourly_data:
            print(f"✅ Retrieved {len(hourly_data)} hourly candles")
            print("\nLast 3 hours:")
            for candle in hourly_data[-3:]:
                time = datetime.fromtimestamp(candle['time']).strftime('%Y-%m-%d %H:%M')
                print(f"   {time}: Open=${candle['open']:,.2f}, Close=${candle['close']:,.2f}")
        else:
            print("❌ Failed to get hourly OHLC data")
        
        # Test 5: Historical Range (Jan 1-7, 2021)
        print("\n📆 Test 5: Get Historical Range (BTC, Jan 1-7, 2021)")
        print("-" * 60)
        start = int(datetime(2021, 1, 1).timestamp())
        end = int(datetime(2021, 1, 7).timestamp())
        range_data = await client.get_historical_ohlc_range('BTC', start, end)
        if range_data:
            print(f"✅ Retrieved {len(range_data)} candles for date range")
            for candle in range_data:
                date = datetime.fromtimestamp(candle['time']).strftime('%Y-%m-%d')
                print(f"   {date}: ${candle['close']:,.2f}")
        else:
            print("❌ Failed to get range data")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_cryptocompare())

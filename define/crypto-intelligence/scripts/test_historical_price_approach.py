"""
Test script to validate 24-hour lookback + forward OHLC approach.

Tests:
1. Entry price with 24h lookback (CryptoCompare)
2. ATH from 30-day forward OHLC (CoinGecko)
3. Complete ROI calculation

Run: python scripts/test_historical_price_approach.py
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
import os


async def test_cryptocompare_24h_lookback(symbol: str, message_date: datetime):
    """Test Phase 1: Entry price with 24h lookback."""
    print(f"\n{'='*80}")
    print(f"PHASE 1: Entry Price (24h lookback)")
    print(f"{'='*80}")
    print(f"Symbol: {symbol}")
    print(f"Message Date: {message_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
    base_url = "https://min-api.cryptocompare.com/data/pricehistorical"
    
    # Define search times (24h lookback)
    search_times = [
        (message_date, "Exact time"),
        (message_date.replace(hour=12, minute=0, second=0), "Same day noon"),
        (message_date.replace(hour=0, minute=0, second=0), "Same day midnight"),
        (message_date - timedelta(hours=12), "12 hours before"),
        (message_date - timedelta(hours=24), "24 hours before"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for search_time, description in search_times:
            unix_ts = int(search_time.timestamp())
            url = f"{base_url}?fsym={symbol}&tsyms=USD&ts={unix_ts}"
            if api_key:
                url += f"&api_key={api_key}"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('Response') == 'Error':
                            print(f"❌ {description}: {data.get('Message')}")
                        elif symbol in data and 'USD' in data[symbol]:
                            price = data[symbol]['USD']
                            if price and price > 0:
                                hours_diff = (message_date - search_time).total_seconds() / 3600
                                print(f"✅ {description}: ${price:,.2f} ({hours_diff:.1f}h before message)")
                                return price, search_time
                            else:
                                print(f"❌ {description}: No price data")
                        else:
                            print(f"❌ {description}: No data in response")
                    else:
                        print(f"❌ {description}: HTTP {response.status}")
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
    
    print(f"\n⚠️  No entry price found within 24 hours")
    return None, None


async def test_cryptocompare_forward_ohlc(symbol: str, entry_date: datetime, entry_price: float):
    """Test Phase 2: ATH from 30-day forward OHLC using CryptoCompare."""
    print(f"\n{'='*80}")
    print(f"PHASE 2: ATH from Forward OHLC (30 days) - CryptoCompare")
    print(f"{'='*80}")
    print(f"Symbol: {symbol}")
    print(f"Entry Date: {entry_date.strftime('%Y-%m-%d')}")
    print(f"Entry Price: ${entry_price:,.2f}")
    print()
    
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
    
    # Calculate end date (30 days after entry)
    end_date = entry_date + timedelta(days=30)
    end_ts = int(end_date.timestamp())
    
    # CryptoCompare histoday endpoint
    url = f"https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        'fsym': symbol,
        'tsym': 'USD',
        'limit': 30,  # 30 days
        'toTs': end_ts  # End at entry_date + 30 days
    }
    if api_key:
        params['api_key'] = api_key
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('Response') == 'Error':
                        print(f"❌ CryptoCompare error: {data.get('Message')}")
                        return None
                    
                    if 'Data' in data and 'Data' in data['Data']:
                        candles = data['Data']['Data']
                        print(f"✅ Fetched {len(candles)} daily candles")
                        
                        # Find ATH in the candles
                        ath_candle = max(candles, key=lambda c: c['high'])
                        ath_price = ath_candle['high']
                        ath_timestamp = datetime.fromtimestamp(ath_candle['time'])
                        
                        # Calculate metrics
                        days_to_ath = (ath_timestamp - entry_date).days
                        roi_multiplier = ath_price / entry_price
                        roi_percentage = (roi_multiplier - 1) * 100
                        
                        print(f"\n📊 Results:")
                        print(f"   ATH Price: ${ath_price:,.2f}")
                        print(f"   ATH Date: {ath_timestamp.strftime('%Y-%m-%d')}")
                        print(f"   Days to ATH: {days_to_ath}")
                        print(f"   ROI: {roi_multiplier:.3f}x ({roi_percentage:+.1f}%)")
                        
                        # Determine outcome
                        if roi_multiplier >= 2.0:
                            outcome = "🎉 WINNER (≥2.0x)"
                        elif roi_multiplier < 1.0:
                            outcome = "📉 LOSER (<1.0x)"
                        else:
                            outcome = "➡️  BREAK_EVEN (1.0-2.0x)"
                        
                        print(f"   Outcome: {outcome}")
                        
                        # Show some checkpoints
                        print(f"\n📈 Sample Checkpoints (first 5 days):")
                        for i, candle in enumerate(candles[:5]):
                            date = datetime.fromtimestamp(candle['time'])
                            days = (date - entry_date).days
                            roi = candle['high'] / entry_price
                            print(f"   Day {days}: ${candle['high']:,.2f} ({roi:.3f}x)")
                        
                        return {
                            'ath_price': ath_price,
                            'ath_date': ath_timestamp,
                            'days_to_ath': days_to_ath,
                            'roi_multiplier': roi_multiplier,
                            'candles': candles
                        }
                    else:
                        print(f"❌ No candle data in response")
                else:
                    print(f"❌ HTTP {response.status}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None


async def test_complete_flow(symbol: str, message_date: datetime):
    """Test complete flow: Entry + ATH + ROI."""
    print(f"\n{'#'*80}")
    print(f"# TESTING: {symbol} from {message_date.strftime('%Y-%m-%d')}")
    print(f"{'#'*80}")
    
    # Phase 1: Get entry price
    entry_price, entry_timestamp = await test_cryptocompare_24h_lookback(symbol, message_date)
    
    if not entry_price:
        print(f"\n❌ FAILED: Could not find entry price")
        return
    
    # Phase 2: Get ATH from forward OHLC
    ath_data = await test_cryptocompare_forward_ohlc(symbol, entry_timestamp, entry_price)
    
    if not ath_data:
        print(f"\n❌ FAILED: Could not fetch forward OHLC data")
        return
    
    # Summary
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE HISTORICAL ROI CALCULATION")
    print(f"{'='*80}")
    print(f"Entry: ${entry_price:,.2f} on {entry_timestamp.strftime('%Y-%m-%d')}")
    print(f"ATH: ${ath_data['ath_price']:,.2f} on {ath_data['ath_date'].strftime('%Y-%m-%d')}")
    print(f"ROI: {ath_data['roi_multiplier']:.3f}x ({(ath_data['roi_multiplier']-1)*100:+.1f}%)")
    print(f"Days to ATH: {ath_data['days_to_ath']}")
    print(f"{'='*80}")


async def main():
    """Run tests."""
    print("\n" + "="*80)
    print("HISTORICAL PRICE APPROACH VALIDATION")
    print("="*80)
    print("\nTesting 24-hour lookback + 30-day forward OHLC approach")
    print("This validates the strategy before full implementation")
    print()
    
    # Test cases: Major tokens from 2023
    test_cases = [
        ('ETH', datetime(2023, 7, 18, 21, 59, 14)),  # WETH example from logs
        ('BTC', datetime(2023, 11, 16, 23, 37, 31)),  # OPTIMUS example from logs
        ('SOL', datetime(2023, 9, 13, 9, 23, 3)),     # Another example
    ]
    
    for symbol, message_date in test_cases:
        await test_complete_flow(symbol, message_date)
        print("\n" + "-"*80 + "\n")
        await asyncio.sleep(2)  # Rate limiting
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print("\nIf tests passed:")
    print("✅ Entry prices found within 24h lookback")
    print("✅ OHLC data available for 30-day forward window")
    print("✅ Complete ROI calculation possible")
    print("\nReady to implement in HistoricalPriceRetriever!")


if __name__ == '__main__':
    asyncio.run(main())

"""
Test dead tokens with ALL working OHLC APIs.

Tests CryptoCompare, Alpha Vantage, and Twelve Data to see if any
can provide historical price data for dead tokens.
"""
import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()


async def test_token_with_cryptocompare(address, symbol, api_key):
    """Test with CryptoCompare."""
    if not symbol or len(symbol) < 2:
        return None
    
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {'fsym': symbol, 'tsym': 'USD', 'limit': 30, 'api_key': api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('Response') == 'Success':
                        candles = data.get('Data', {}).get('Data', [])
                        if candles and len(candles) > 0:
                            return {'api': 'cryptocompare', 'candles': len(candles), 'data': candles}
    except:
        pass
    return None


async def test_token_with_alphavantage(symbol, api_key):
    """Test with Alpha Vantage."""
    if not symbol or len(symbol) < 2:
        return None
    
    url = "https://www.alphavantage.co/query"
    params = {'function': 'DIGITAL_CURRENCY_DAILY', 'symbol': symbol, 'market': 'USD', 'apikey': api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'Time Series (Digital Currency Daily)' in data:
                        candles = data['Time Series (Digital Currency Daily)']
                        if candles and len(candles) > 0:
                            return {'api': 'alphavantage', 'candles': len(candles), 'data': list(candles.items())[:30]}
    except:
        pass
    return None


async def test_token_with_twelvedata(symbol, api_key):
    """Test with Twelve Data."""
    if not symbol or len(symbol) < 2:
        return None
    
    url = "https://api.twelvedata.com/time_series"
    params = {'symbol': f"{symbol}/USD", 'interval': '1day', 'outputsize': 30, 'apikey': api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'values' in data:
                        candles = data['values']
                        if candles and len(candles) > 0:
                            return {'api': 'twelvedata', 'candles': len(candles), 'data': candles}
    except:
        pass
    return None


async def analyze_dead_token(address, chain, symbol, detected_at, reason):
    """Analyze a single dead token with all APIs."""
    print(f"\n{'='*80}")
    print(f"Token: {address[:20]}...")
    print(f"Symbol: {symbol}")
    print(f"Chain: {chain}")
    print(f"Reason: {reason}")
    print(f"{'='*80}")
    
    # Get API keys
    cc_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    av_key = os.getenv('ALPHAVANTAGE_API_KEY')
    td_key = os.getenv('TWELVEDATA_API_KEY')
    
    result = {
        'address': address,
        'symbol': symbol,
        'chain': chain,
        'reason': reason,
        'ohlc_found': False,
        'source': None,
        'candles': 0
    }
    
    # Try CryptoCompare
    if cc_key and symbol:
        print(f"  Testing CryptoCompare with symbol: {symbol}...")
        data = await test_token_with_cryptocompare(address, symbol, cc_key)
        if data:
            print(f"  ✅ CryptoCompare: Found {data['candles']} candles!")
            result['ohlc_found'] = True
            result['source'] = 'cryptocompare'
            result['candles'] = data['candles']
            return result
        print(f"  ❌ CryptoCompare: No data")
    
    # Try Alpha Vantage
    if av_key and symbol:
        print(f"  Testing Alpha Vantage with symbol: {symbol}...")
        data = await test_token_with_alphavantage(symbol, av_key)
        if data:
            print(f"  ✅ Alpha Vantage: Found {data['candles']} candles!")
            result['ohlc_found'] = True
            result['source'] = 'alphavantage'
            result['candles'] = data['candles']
            return result
        print(f"  ❌ Alpha Vantage: No data")
        await asyncio.sleep(12)  # Rate limit: 5 calls/min
    
    # Try Twelve Data
    if td_key and symbol:
        print(f"  Testing Twelve Data with symbol: {symbol}/USD...")
        data = await test_token_with_twelvedata(symbol, td_key)
        if data:
            print(f"  ✅ Twelve Data: Found {data['candles']} candles!")
            result['ohlc_found'] = True
            result['source'] = 'twelvedata'
            result['candles'] = data['candles']
            return result
        print(f"  ❌ Twelve Data: No data")
    
    print(f"  ❌ No OHLC data found from any API")
    return result


async def main():
    """Main function."""
    print("="*80)
    print("DEAD TOKEN OHLC ANALYSIS - Testing All APIs")
    print("="*80)
    
    # Load dead tokens
    blacklist_path = Path("data/dead_tokens_blacklist.json")
    if not blacklist_path.exists():
        print("❌ No dead tokens blacklist found!")
        return
    
    with open(blacklist_path, 'r') as f:
        dead_tokens = json.load(f)
    
    print(f"\nFound {len(dead_tokens)} dead tokens")
    print(f"Testing with CryptoCompare, Alpha Vantage, and Twelve Data...")
    
    # Get symbols from DexScreener first
    from repositories.api_clients.dexscreener_client import DexScreenerClient
    dex_client = DexScreenerClient()
    
    results = []
    for address, data in list(dead_tokens.items())[:5]:  # Test first 5
        chain = data.get('chain', 'evm')
        reason = data.get('reason', '')
        
        # Try to get symbol
        symbol = None
        try:
            chain_map = {"evm": "ethereum", "solana": "solana"}
            mapped_chain = chain_map.get(chain, "ethereum")
            price_data = await dex_client.get_price(address, mapped_chain)
            if price_data and price_data.symbol:
                symbol = price_data.symbol
        except:
            pass
        
        if not symbol:
            symbol = address[:10]
        
        # Test with all APIs
        result = await analyze_dead_token(address, chain, symbol, data.get('detected_at'), reason)
        results.append(result)
        
        await asyncio.sleep(1)  # Rate limiting
    
    await dex_client.close()
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total = len(results)
    with_data = sum(1 for r in results if r['ohlc_found'])
    no_data = total - with_data
    
    print(f"\nTotal Tested: {total}")
    print(f"With OHLC Data: {with_data} ({with_data/total*100:.1f}%)")
    print(f"No OHLC Data: {no_data} ({no_data/total*100:.1f}%)")
    
    if with_data > 0:
        print(f"\n✅ Tokens with data:")
        for r in results:
            if r['ohlc_found']:
                print(f"   - {r['symbol']}: {r['candles']} candles from {r['source']}")
    
    print(f"\n{'='*80}")


if __name__ == '__main__':
    asyncio.run(main())

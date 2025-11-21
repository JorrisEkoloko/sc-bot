"""
Test all available OHLC APIs to find historical data for tokens.

This script tests multiple free and paid APIs to find which ones
can provide OHLC data for our dead tokens.
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


class OHLCAPITester:
    """Test multiple OHLC APIs."""
    
    def __init__(self):
        self.results = {}
        self.apis_tested = []
        
    async def test_cryptocompare(self, symbol="BTC"):
        """Test CryptoCompare API (FREE - 100K calls/month)."""
        api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        if not api_key:
            return {"status": "no_key", "data": None}
        
        url = f"https://min-api.cryptocompare.com/data/v2/histoday"
        params = {
            'fsym': symbol,
            'tsym': 'USD',
            'limit': 30,
            'api_key': api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('Response') == 'Success':
                            candles = data.get('Data', {}).get('Data', [])
                            return {
                                "status": "success",
                                "candles": len(candles),
                                "sample": candles[:2] if candles else None
                            }
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_coingecko(self, coin_id="bitcoin"):
        """Test CoinGecko API (FREE with key)."""
        api_key = os.getenv('COINGECKO_API_KEY')
        if not api_key:
            return {"status": "no_key", "data": None}
        
        # CoinGecko Pro API
        url = f"https://pro-api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params = {
            'vs_currency': 'usd',
            'days': 30
        }
        headers = {'x-cg-pro-api-key': api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "success",
                            "candles": len(data),
                            "sample": data[:2] if data else None
                        }
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_binance(self, symbol="BTCUSDT"):
        """Test Binance API (FREE, no key needed)."""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': '1d',
            'limit': 30
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "success",
                            "candles": len(data),
                            "sample": data[:2] if data else None
                        }
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_coincap(self, asset_id="bitcoin"):
        """Test CoinCap API (FREE, no key needed)."""
        end = int(datetime.now().timestamp() * 1000)
        start = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        
        url = f"https://api.coincap.io/v2/assets/{asset_id}/history"
        params = {
            'interval': 'd1',
            'start': start,
            'end': end
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candles = data.get('data', [])
                        return {
                            "status": "success",
                            "candles": len(candles),
                            "sample": candles[:2] if candles else None
                        }
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_alphavantage(self, symbol="BTC"):
        """Test Alpha Vantage API (FREE - 25 calls/day)."""
        api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        if not api_key:
            return {"status": "no_key", "data": None}
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': 'USD',
            'apikey': api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'Time Series (Digital Currency Daily)' in data:
                            candles = data['Time Series (Digital Currency Daily)']
                            return {
                                "status": "success",
                                "candles": len(candles),
                                "sample": list(candles.items())[:2] if candles else None
                            }
                        return {"status": "error", "data": data}
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_twelvedata(self, symbol="BTC/USD"):
        """Test Twelve Data API (FREE - 800 calls/day)."""
        api_key = os.getenv('TWELVEDATA_API_KEY')
        if not api_key:
            return {"status": "no_key", "data": None}
        
        url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': symbol,
            'interval': '1day',
            'outputsize': 30,
            'apikey': api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'values' in data:
                            candles = data['values']
                            return {
                                "status": "success",
                                "candles": len(candles),
                                "sample": candles[:2] if candles else None
                            }
                        return {"status": "error", "data": data}
                    return {"status": f"error_{resp.status}", "data": await resp.text()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_all_tests(self):
        """Run all API tests."""
        print("="*80)
        print("TESTING ALL OHLC APIs")
        print("="*80)
        
        # Test CryptoCompare
        print("\n1. Testing CryptoCompare (FREE - 100K calls/month)...")
        result = await self.test_cryptocompare("BTC")
        self.results['cryptocompare'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
            print(f"   Sample: {result['sample']}")
        
        # Test CoinGecko
        print("\n2. Testing CoinGecko Pro (FREE with key)...")
        result = await self.test_coingecko("bitcoin")
        self.results['coingecko'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
            print(f"   Sample: {result['sample']}")
        
        # Test Binance
        print("\n3. Testing Binance (FREE, no key)...")
        result = await self.test_binance("BTCUSDT")
        self.results['binance'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
            print(f"   Sample: {result['sample']}")
        
        # Test CoinCap
        print("\n4. Testing CoinCap (FREE, no key)...")
        result = await self.test_coincap("bitcoin")
        self.results['coincap'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
            print(f"   Sample: {result['sample']}")
        
        # Test Alpha Vantage
        print("\n5. Testing Alpha Vantage (FREE - 25 calls/day)...")
        result = await self.test_alphavantage("BTC")
        self.results['alphavantage'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
        
        # Test Twelve Data
        print("\n6. Testing Twelve Data (FREE - 800 calls/day)...")
        result = await self.test_twelvedata("BTC/USD")
        self.results['twelvedata'] = result
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   ✅ Got {result['candles']} candles")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        working_apis = [name for name, result in self.results.items() if result['status'] == 'success']
        no_key_apis = [name for name, result in self.results.items() if result['status'] == 'no_key']
        failed_apis = [name for name, result in self.results.items() if 'error' in result['status']]
        
        print(f"\n✅ Working APIs ({len(working_apis)}):")
        for api in working_apis:
            print(f"   - {api}: {self.results[api]['candles']} candles")
        
        if no_key_apis:
            print(f"\n⚠️  APIs without keys ({len(no_key_apis)}):")
            for api in no_key_apis:
                print(f"   - {api}")
        
        if failed_apis:
            print(f"\n❌ Failed APIs ({len(failed_apis)}):")
            for api in failed_apis:
                print(f"   - {api}: {self.results[api]['status']}")
        
        print("\n" + "="*80)
        
        return self.results


async def main():
    """Main function."""
    tester = OHLCAPITester()
    results = await tester.run_all_tests()
    
    # Recommendations
    print("\n📊 RECOMMENDATIONS:")
    print("\nBest APIs for OHLC data:")
    print("1. CryptoCompare - 100K calls/month (FREE) ✅ Already using")
    print("2. Binance - Unlimited (FREE, no key)")
    print("3. CoinCap - Unlimited (FREE, no key)")
    print("4. Twelve Data - 800 calls/day (FREE)")
    print("5. Alpha Vantage - 25 calls/day (FREE)")
    print("\n" + "="*80)


if __name__ == '__main__':
    asyncio.run(main())

"""Test which APIs have OHLC data for NKP token."""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent))

from repositories.api_clients.coingecko_client import CoinGeckoClient
from repositories.api_clients.cryptocompare_historical_client import CryptoCompareHistoricalClient
from repositories.api_clients.defillama_historical_client import DefiLlamaHistoricalClient
from utils.logger import setup_logger


async def test_all_apis():
    """Test all APIs for NKP OHLC data."""
    logger = setup_logger('TestNPKOHLC')
    
    # NKP token details
    npk_address = "0x11Fa1193743061591CBe47c9E0765EAeBaa3a046"
    npk_symbol = "NKP"
    chain = "evm"
    
    # Test timestamp (16 days ago)
    test_timestamp = datetime.now(timezone.utc) - timedelta(days=16)
    
    print("\n" + "="*80)
    print("TESTING OHLC DATA AVAILABILITY FOR NKP TOKEN")
    print("="*80)
    print(f"Token: {npk_symbol}")
    print(f"Address: {npk_address}")
    print(f"Chain: {chain}")
    print(f"Test Timestamp: {test_timestamp}")
    print("="*80 + "\n")
    
    # Test 1: CoinGecko
    print("-"*80)
    print("TEST 1: CoinGecko API")
    print("-"*80)
    try:
        coingecko_client = CoinGeckoClient(
            api_key=os.getenv('COINGECKO_API_KEY', ''),
            logger=logger
        )
        
        # Test get_historical_data
        print("[*] Testing get_historical_data()...")
        historical_data = await coingecko_client.get_historical_data(npk_address, chain)
        
        if historical_data:
            print(f"[OK] CoinGecko returned historical data:")
            for key, value in historical_data.items():
                print(f"  - {key}: {value}")
            
            # Check if OHLC data is present
            if 'ohlc' in historical_data:
                print(f"[SUCCESS] CoinGecko HAS OHLC data! ({len(historical_data['ohlc'])} candles)")
            else:
                print("[INFO] CoinGecko has historical data but NO OHLC candles")
        else:
            print("[FAIL] CoinGecko returned no historical data")
        
        await coingecko_client.close()
    except Exception as e:
        print(f"[ERROR] CoinGecko test failed: {e}")
    
    # Test 2: CryptoCompare
    print("\n" + "-"*80)
    print("TEST 2: CryptoCompare API")
    print("-"*80)
    try:
        cryptocompare_client = CryptoCompareHistoricalClient(
            api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
            logger=logger
        )
        
        print(f"[*] Testing get_ohlc_window() for {npk_symbol}...")
        ohlc_data = await cryptocompare_client.get_ohlc_window(
            npk_symbol,
            test_timestamp,
            window_days=7
        )
        
        if ohlc_data and ohlc_data.candles:
            print(f"[SUCCESS] CryptoCompare HAS OHLC data! ({len(ohlc_data.candles)} candles)")
            print(f"  - ATH in window: ${ohlc_data.ath_in_window:.6f}")
            print(f"  - ATH timestamp: {ohlc_data.ath_timestamp}")
        else:
            print("[FAIL] CryptoCompare returned no OHLC data")
        
        await cryptocompare_client.close()
    except Exception as e:
        print(f"[ERROR] CryptoCompare test failed: {e}")
    
    # Test 3: DefiLlama
    print("\n" + "-"*80)
    print("TEST 3: DefiLlama API")
    print("-"*80)
    try:
        defillama_client = DefiLlamaHistoricalClient(logger=logger)
        
        print(f"[*] Testing get_historical_prices() for {npk_address}...")
        prices = await defillama_client.get_historical_prices(
            npk_address,
            chain,
            test_timestamp,
            window_days=7
        )
        
        if prices:
            print(f"[SUCCESS] DefiLlama HAS historical prices! ({len(prices)} data points)")
            # Check if we can construct OHLC from prices
            if len(prices) >= 7:
                print(f"  - Sufficient data to calculate ATH")
                max_price = max(p['price'] for p in prices)
                print(f"  - Max price in window: ${max_price:.6f}")
            else:
                print(f"  - Insufficient data ({len(prices)} < 7 days)")
        else:
            print("[FAIL] DefiLlama returned no historical prices")
        
        await defillama_client.close()
    except Exception as e:
        print(f"[ERROR] DefiLlama test failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("Test which APIs successfully returned OHLC/historical data for NKP")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_apis())

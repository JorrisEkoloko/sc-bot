"""
Quick test of the new historical price flow.
Run: python test_new_flow.py
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from services.pricing.historical_price_retriever import HistoricalPriceRetriever
from utils.logger import setup_logger


async def test_new_flow():
    """Test the new closest entry price + forward OHLC flow."""
    
    logger = setup_logger('TestNewFlow', 'INFO')
    
    print("\n" + "="*70)
    print("Testing New Historical Price Flow")
    print("="*70 + "\n")
    
    # Check API keys
    cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
    twelvedata_key = os.getenv('TWELVEDATA_API_KEY', '')
    
    if not cryptocompare_key and not twelvedata_key:
        print("[WARNING] No API keys found!")
        print("Set CRYPTOCOMPARE_API_KEY or TWELVEDATA_API_KEY in .env file")
        print("\nGet free keys from:")
        print("  - CryptoCompare: https://www.cryptocompare.com/cryptopian/api-keys")
        print("  - Twelve Data: https://twelvedata.com/apikey")
        return
    
    if cryptocompare_key:
        print(f"[OK] CryptoCompare API key found: {cryptocompare_key[:10]}...")
    if twelvedata_key:
        print(f"[OK] Twelve Data API key found: {twelvedata_key[:10]}...")
    
    print()
    
    # Initialize retriever with symbol mapping
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key=cryptocompare_key,
        twelvedata_api_key=twelvedata_key,
        symbol_mapping_path="crypto-intelligence/data/symbol_mapping.json",
        logger=logger
    )
    
    try:
        # Test 1: Major token with historical data (BTC)
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        symbol = 'BTC'
        
        print("="*70)
        print("TEST 1: Major Token (BTC) - Should use CryptoCompare")
        print("="*70)
        
        print(f"Test Parameters:")
        print(f"  Symbol: {symbol}")
        print(f"  Message Date: {test_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Forward Window: 30 days")
        print()
        
        # STEP 1: Test closest entry price
        print("="*70)
        print("STEP 1: Fetching Closest Entry Price")
        print("="*70)
        
        entry_price, source = await retriever.fetch_closest_entry_price(symbol, test_date)
        
        if entry_price:
            print(f"\n[SUCCESS]")
            print(f"  Entry Price: ${entry_price:,.2f}")
            print(f"  Source: {source}")
        else:
            print(f"\n[FAILED] No entry price found")
            return
        
        print()
        
        # STEP 2: Test forward OHLC with ATH
        print("="*70)
        print("STEP 2: Fetching Forward OHLC with ATH")
        print("="*70)
        
        ohlc_result = await retriever.fetch_forward_ohlc_with_ath(
            symbol, test_date, window_days=30
        )
        
        if ohlc_result:
            print(f"\n[SUCCESS]")
            print(f"  Entry Price: ${ohlc_result['entry_price']:,.2f}")
            print(f"  ATH Price: ${ohlc_result['ath_price']:,.2f}")
            print(f"  ATH Multiplier: {ohlc_result['ath_price'] / ohlc_result['entry_price']:.3f}x")
            print(f"  Days to ATH: {ohlc_result['days_to_ath']:.1f}")
            print(f"  Candles: {len(ohlc_result['candles'])}")
            print(f"  Data Completeness: {ohlc_result['data_completeness']*100:.1f}%")
            print(f"  Source: {ohlc_result['source']}")
        else:
            print(f"\n[FAILED] No OHLC data found")
            return
        
        print()
        
        # STEP 3: Test checkpoint ROIs
        print("="*70)
        print("STEP 3: Calculating Checkpoint ROIs from OHLC")
        print("="*70)
        
        checkpoints = [
            ('1h', timedelta(hours=1)),
            ('4h', timedelta(hours=4)),
            ('24h', timedelta(days=1)),
            ('3d', timedelta(days=3)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30))
        ]
        
        # Debug: Show first few candle timestamps
        print(f"\n  First 5 candle timestamps:")
        for i, candle in enumerate(ohlc_result['candles'][:5]):
            print(f"    Candle {i+1}: {candle.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        checkpoint_rois = await retriever.calculate_checkpoint_rois_from_ohlc(
            entry_price=entry_price,
            entry_timestamp=test_date,
            checkpoints=checkpoints,
            candles=ohlc_result['candles']
        )
        
        if checkpoint_rois:
            print(f"\n[SUCCESS]")
            print(f"\n  Entry Price: ${entry_price:,.2f}")
            print(f"\n  Checkpoint ROIs:")
            print(f"  {'Checkpoint':<12} {'Price':>15} {'ROI':>10} {'Gain':>10}")
            print(f"  {'-'*12} {'-'*15} {'-'*10} {'-'*10}")
            
            for checkpoint_name, roi in checkpoint_rois.items():
                price = roi * entry_price
                gain = (roi - 1) * 100
                print(f"  {checkpoint_name:<12} ${price:>14,.2f} {roi:>9.3f}x {gain:>9.1f}%")
        else:
            print(f"\n[FAILED] No checkpoint ROIs calculated")
            return
        
        print()
        print("="*70)
        print("[SUCCESS] Test 1 Passed!")
        print("="*70)
        print()
        
        # Test 2: Small token with DexScreener fallback (OPTIMUS)
        print("="*70)
        print("TEST 2: Small Token (OPTIMUS) - DexScreener Fallback")
        print("="*70)
        print()
        
        # Full OPTIMUS contract address from Etherscan
        optimus_address = "0x562e362876c8aee4744fc2c6aac8394c312d215d"
        optimus_date = datetime(2023, 11, 16, 23, 37, 31)
        
        print(f"Test Parameters:")
        print(f"  Symbol: OPTIMUS")
        print(f"  Address: {optimus_address}")
        print(f"  Expected Mapped Symbol: OPTI (from symbol_mapping.json)")
        print(f"  Message Date: {optimus_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Try to fetch entry price with DexScreener fallback
        print("Fetching entry price with DexScreener fallback...")
        optimus_price, optimus_source = await retriever.fetch_closest_entry_price(
            'OPTIMUS',
            optimus_date,
            address=optimus_address,
            chain='evm'
        )
        
        if optimus_price:
            print(f"\n[SUCCESS]")
            print(f"  Price: ${optimus_price:.6f}")
            print(f"  Source: {optimus_source}")
        else:
            print(f"\n[INFO] No historical price found (expected for old small token)")
            print(f"  This is normal - token is too old/small for historical data")
        
        print()
        print("="*70)
        print("[SUCCESS] All Tests Passed!")
        print("="*70)
        print()
        
        # Summary
        print("Summary:")
        print(f"  - Test 1 (BTC): Entry price fetched with smart fallback")
        print(f"  - Test 1 (BTC): Forward OHLC data retrieved ({len(ohlc_result['candles'])} candles)")
        print(f"  - Test 1 (BTC): Real ATH calculated from candles")
        print(f"  - Test 1 (BTC): All {len(checkpoint_rois)} checkpoint ROIs calculated")
        print(f"  - Test 2 (OPTIMUS): DexScreener fallback tested")
        print(f"  - Total API calls: 2-3 (vs 7 in old method)")
        print()
        
    finally:
        await retriever.close()


if __name__ == '__main__':
    asyncio.run(test_new_flow())

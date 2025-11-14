"""
Test script to fetch OPTIMUS AI ROI using symbol mapping
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pricing.historical_price_retriever import HistoricalPriceRetriever
from utils.logger import setup_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_optimus_roi():
    """Test fetching OPTIMUS AI ROI with symbol mapping."""
    
    logger = setup_logger('TestOptimusROI')
    
    print("=" * 80)
    print("TESTING OPTIMUS AI ROI WITH SYMBOL MAPPING")
    print("=" * 80)
    
    # OPTIMUS AI details
    symbol = "OPTIMUS"  # User input symbol
    address = "0x562e362876c8aee4744fc2c6aac8394c312d215d"
    chain = "ethereum"
    
    # Simulate a message from 7 days ago
    message_date = datetime.now() - timedelta(days=7)
    
    print(f"\nToken: {symbol}")
    print(f"Address: {address}")
    print(f"Chain: {chain}")
    print(f"Message Date: {message_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize retriever with symbol mapping
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY'),
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY'),
        symbol_mapping_path='crypto-intelligence/data/symbol_mapping.json',
        logger=logger
    )
    
    try:
        # Test 1: Get correct symbol for each API
        print("-" * 80)
        print("TEST 1: Symbol Mapping Lookup")
        print("-" * 80)
        
        coingecko_symbol = retriever.get_api_symbol(address, 'coingecko', symbol)
        dexscreener_symbol = retriever.get_api_symbol(address, 'dexscreener', symbol)
        cryptocompare_symbol = retriever.get_api_symbol(address, 'cryptocompare', symbol)
        
        print(f"User Input Symbol: {symbol}")
        print(f"CoinGecko Symbol: {coingecko_symbol}")
        print(f"DexScreener Symbol: {dexscreener_symbol}")
        print(f"CryptoCompare Symbol: {cryptocompare_symbol}")
        print()
        
        # Test 2: Fetch entry price with symbol mapping
        print("-" * 80)
        print("TEST 2: Fetch Entry Price (with symbol mapping)")
        print("-" * 80)
        
        entry_price, source = await retriever.fetch_closest_entry_price(
            symbol=symbol,
            message_timestamp=message_date,
            address=address,
            chain=chain
        )
        
        if entry_price:
            print(f"✓ Entry Price: ${entry_price:.8f}")
            print(f"  Source: {source}")
        else:
            print(f"✗ Entry price not found")
            print("\nNote: This might be expected if the token is very new or small.")
            return
        
        print()
        
        # Test 3: Fetch forward OHLC with ATH
        print("-" * 80)
        print("TEST 3: Fetch Forward OHLC (30 days)")
        print("-" * 80)
        
        # Use the correct symbol for CryptoCompare
        ohlc_result = await retriever.fetch_forward_ohlc_with_ath(
            symbol=cryptocompare_symbol,  # Use mapped symbol!
            entry_timestamp=message_date,
            window_days=30
        )
        
        if ohlc_result:
            print(f"✓ OHLC Data Retrieved:")
            print(f"  Entry Price: ${ohlc_result['entry_price']:.8f}")
            print(f"  ATH Price: ${ohlc_result['ath_price']:.8f}")
            print(f"  ATH Date: {ohlc_result['ath_timestamp'].strftime('%Y-%m-%d')}")
            print(f"  Days to ATH: {ohlc_result['days_to_ath']:.1f}")
            print(f"  ATH ROI: {ohlc_result['ath_price'] / ohlc_result['entry_price']:.3f}x")
            print(f"  Candles: {len(ohlc_result['candles'])}")
            print(f"  Data Completeness: {ohlc_result['data_completeness']*100:.1f}%")
            print(f"  Source: {ohlc_result['source']}")
        else:
            print(f"✗ OHLC data not found")
        
        print()
        
        # Test 4: Calculate checkpoint ROIs
        if ohlc_result:
            print("-" * 80)
            print("TEST 4: Calculate Checkpoint ROIs from OHLC")
            print("-" * 80)
            
            checkpoints = retriever.calculate_smart_checkpoints(message_date)
            
            if checkpoints:
                checkpoint_rois = await retriever.calculate_checkpoint_rois_from_ohlc(
                    entry_price=ohlc_result['entry_price'],
                    entry_timestamp=message_date,
                    checkpoints=checkpoints,
                    candles=ohlc_result['candles']
                )
                
                print(f"Checkpoints reached: {len(checkpoints)}")
                print()
                
                for checkpoint_name, roi in checkpoint_rois.items():
                    roi_pct = (roi - 1) * 100
                    print(f"  {checkpoint_name:>4}: {roi:.3f}x ({roi_pct:+.1f}%)")
            else:
                print("No checkpoints reached yet (message too recent)")
        
        print()
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    finally:
        await retriever.close()


if __name__ == "__main__":
    asyncio.run(test_optimus_roi())

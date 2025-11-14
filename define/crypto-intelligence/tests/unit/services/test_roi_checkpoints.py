"""Test ROI checkpoint data availability with DefiLlama."""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.pricing.historical_price_retriever import HistoricalPriceRetriever
from utils.logger import setup_logger


async def test_roi_checkpoints():
    """Test if we can get prices at all ROI checkpoint thresholds."""
    logger = setup_logger('TestROI')
    
    # Initialize retriever
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key="7154def1a021517ec59cbb67a81f4919033185f742605b372eebcc8714fc5410",
        cache_dir="data/cache",
        symbol_mapping_path="data/symbol_mapping.json",
        logger=logger
    )
    
    print("\n" + "="*80)
    print("Testing ROI Checkpoint Data Availability")
    print("="*80)
    
    # Test token: WAGMIGAMES
    address = "0x3b604747ad1720c01ded0455728b62c0d2f100f0"
    chain = "ethereum"
    
    # Entry point: July 18, 2023, 21:59:14
    entry_time = datetime(2023, 7, 18, 21, 59, 14)
    
    print(f"\n📊 Token: WAGMIGAMES")
    print(f"   Address: {address}")
    print(f"   Entry Time: {entry_time}")
    print(f"   Chain: {chain}")
    
    # Define ROI checkpoints
    checkpoints = {
        "Entry": timedelta(hours=0),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "24h": timedelta(hours=24),
        "3d": timedelta(days=3),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    print("\n" + "-"*80)
    print("Fetching prices at each checkpoint...")
    print("-"*80)
    
    results = {}
    entry_price = None
    
    for checkpoint_name, time_delta in checkpoints.items():
        checkpoint_time = entry_time + time_delta
        
        print(f"\n⏱️  {checkpoint_name} ({checkpoint_time.strftime('%Y-%m-%d %H:%M')})")
        
        # Fetch price using DefiLlama directly
        price = await retriever._fetch_defillama_price_at_timestamp(
            address=address,
            chain=chain,
            timestamp=checkpoint_time
        )
        
        if price and price > 0:
            results[checkpoint_name] = {
                'time': checkpoint_time,
                'price': price,
                'available': True
            }
            
            if checkpoint_name == "Entry":
                entry_price = price
            
            # Calculate ROI if we have entry price
            if entry_price:
                roi_multiplier = price / entry_price
                roi_percentage = (roi_multiplier - 1) * 100
                print(f"   ✅ Price: ${price:.8f}")
                print(f"   📈 ROI: {roi_multiplier:.3f}x ({roi_percentage:+.2f}%)")
            else:
                print(f"   ✅ Price: ${price:.8f}")
        else:
            results[checkpoint_name] = {
                'time': checkpoint_time,
                'price': None,
                'available': False
            }
            print(f"   ❌ No data available")
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    available_count = sum(1 for r in results.values() if r['available'])
    total_count = len(results)
    
    print(f"\n✅ Data Availability: {available_count}/{total_count} checkpoints")
    print(f"   Coverage: {(available_count/total_count)*100:.1f}%")
    
    if entry_price:
        print(f"\n📊 ROI Analysis:")
        print(f"   Entry Price: ${entry_price:.8f}")
        
        # Find ATH
        ath_price = entry_price
        ath_checkpoint = "Entry"
        
        for checkpoint_name, data in results.items():
            if data['available'] and data['price'] > ath_price:
                ath_price = data['price']
                ath_checkpoint = checkpoint_name
        
        ath_multiplier = ath_price / entry_price
        print(f"   ATH: ${ath_price:.8f} at {ath_checkpoint}")
        print(f"   ATH Multiplier: {ath_multiplier:.3f}x ({(ath_multiplier-1)*100:+.2f}%)")
        
        # Check if it's a winner (>2x for micro-cap)
        if ath_multiplier >= 2.0:
            print(f"   🎉 WINNER - Reached 2x threshold!")
        elif ath_multiplier >= 1.5:
            print(f"   📈 GOOD - Reached 1.5x")
        elif ath_multiplier >= 1.0:
            print(f"   ➡️  BREAK EVEN - Slight gain")
        else:
            print(f"   📉 LOSER - Below entry price")
    
    # Test if we can calculate accurate ROI
    print("\n" + "="*80)
    print("ROI Calculation Feasibility")
    print("="*80)
    
    if available_count >= 5:  # Need at least 5 checkpoints
        print("\n✅ YES - We have enough data points to calculate accurate ROI!")
        print("   - Can track price progression over time")
        print("   - Can identify ATH and when it occurred")
        print("   - Can classify outcomes (winner/loser)")
        print("   - Can calculate checkpoint-specific ROIs")
    else:
        print("\n⚠️  LIMITED - Not enough data points for full ROI analysis")
        print(f"   - Only {available_count} checkpoints available")
        print("   - May need to use current price as fallback")
    
    # Cleanup
    await retriever.close()
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_roi_checkpoints())

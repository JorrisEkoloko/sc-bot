"""Test DefiLlama historical price integration."""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.pricing.historical_price_retriever import HistoricalPriceRetriever
from utils.logger import setup_logger


async def test_defillama_historical():
    """Test DefiLlama historical price fetching."""
    logger = setup_logger('TestDefiLlama')
    
    # Initialize retriever
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key="7154def1a021517ec59cbb67a81f4919033185f742605b372eebcc8714fc5410",
        cache_dir="data/cache",
        symbol_mapping_path="data/symbol_mapping.json",
        logger=logger
    )
    
    print("\n" + "="*80)
    print("Testing DefiLlama Historical Price Integration")
    print("="*80)
    
    # Test Case 1: WAGMIGAMES (July 18, 2023)
    print("\n📊 Test 1: WAGMIGAMES Historical Price (July 18, 2023)")
    print("-" * 80)
    wagmi_address = "0x3b604747ad1720c01ded0455728b62c0d2f100f0"
    wagmi_timestamp = datetime(2023, 7, 18, 21, 59, 14)
    
    price, source = await retriever.fetch_closest_entry_price(
        symbol="WAGMIGAMES",
        message_timestamp=wagmi_timestamp,
        address=wagmi_address,
        chain="ethereum"
    )
    
    print(f"✅ Result:")
    print(f"   Price: ${price:.8f}" if price else "   Price: NOT FOUND")
    print(f"   Source: {source}")
    print(f"   Expected: ~$0.000023 from DefiLlama")
    
    if price and price > 0:
        print(f"   ✅ SUCCESS - Got historical price!")
    else:
        print(f"   ❌ FAILED - No price returned")
    
    # Test Case 2: WETH (July 18, 2023) - Should use symbol mapping
    print("\n📊 Test 2: WETH Historical Price (July 18, 2023)")
    print("-" * 80)
    weth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    weth_timestamp = datetime(2023, 7, 18, 21, 59, 14)
    
    price, source = await retriever.fetch_closest_entry_price(
        symbol="WETH",
        message_timestamp=weth_timestamp,
        address=weth_address,
        chain="ethereum"
    )
    
    print(f"✅ Result:")
    print(f"   Price: ${price:.2f}" if price else "   Price: NOT FOUND")
    print(f"   Source: {source}")
    print(f"   Expected: ~$1,900 (ETH price in July 2023)")
    
    if price and price > 1000:
        print(f"   ✅ SUCCESS - WETH mapped to ETH correctly!")
    else:
        print(f"   ⚠️  WARNING - Price seems low or not found")
    
    # Test Case 3: EYE (June 20, 2023) - Should fail (dead token)
    print("\n📊 Test 3: EYE Historical Price (June 20, 2023)")
    print("-" * 80)
    eye_address = "0x5d39957fc88566f14ae7e8ab8971d7c603f0ce5e"
    eye_timestamp = datetime(2023, 6, 20, 17, 49, 13)
    
    price, source = await retriever.fetch_closest_entry_price(
        symbol="EYE",
        message_timestamp=eye_timestamp,
        address=eye_address,
        chain="ethereum"
    )
    
    print(f"✅ Result:")
    print(f"   Price: ${price:.8f}" if price else "   Price: NOT FOUND")
    print(f"   Source: {source}")
    print(f"   Expected: NOT FOUND (dead token)")
    
    if not price or source == "not_found":
        print(f"   ✅ SUCCESS - Correctly identified as unavailable!")
    else:
        print(f"   ⚠️  WARNING - Found price for dead token")
    
    # Test Case 4: Direct DefiLlama method test
    print("\n📊 Test 4: Direct DefiLlama API Call")
    print("-" * 80)
    
    direct_price = await retriever._fetch_defillama_price_at_timestamp(
        address=wagmi_address,
        chain="ethereum",
        timestamp=wagmi_timestamp
    )
    
    print(f"✅ Result:")
    print(f"   Price: ${direct_price:.8f}" if direct_price else "   Price: NOT FOUND")
    print(f"   Expected: ~$0.000023")
    
    if direct_price and direct_price > 0:
        print(f"   ✅ SUCCESS - DefiLlama method working!")
    else:
        print(f"   ❌ FAILED - DefiLlama method not working")
    
    # Cleanup
    await retriever.close()
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_defillama_historical())

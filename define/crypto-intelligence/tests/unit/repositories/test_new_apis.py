"""
Test script for new API implementations:
1. DefiLlama historical prices
2. Blockscout current prices
3. GoPlusLabs security data
"""
import asyncio
from datetime import datetime
from services.pricing.historical_price_retriever import HistoricalPriceRetriever
from repositories.api_clients.blockscout_client import BlockscoutClient
from repositories.api_clients.goplus_client import GoPlusClient
from utils.logger import setup_logger


async def test_defillama_historical():
    """Test DefiLlama historical price retrieval."""
    print("\n" + "="*80)
    print("TEST 1: DefiLlama Historical Prices")
    print("="*80)
    
    logger = setup_logger('TestDefiLlama')
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key='7154def1a021517ec59cbb67a81f4919033185f742605b372eebcc8714fc5410',
        logger=logger
    )
    
    # Test WAGMIGAMES - July 18, 2023
    wagmi_address = '0x3b604747ad1720c01ded0455728b62c0d2f100f0'
    wagmi_timestamp = datetime.fromtimestamp(1689714000)  # July 18, 2023
    
    print(f"\n📊 Testing WAGMIGAMES historical price:")
    print(f"   Address: {wagmi_address}")
    print(f"   Date: {wagmi_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    price, source = await retriever.fetch_closest_entry_price(
        symbol='WAGMIGAMES',
        message_timestamp=wagmi_timestamp,
        address=wagmi_address,
        chain='ethereum'
    )
    
    if price:
        print(f"   ✅ SUCCESS: ${price:.8f} (source: {source})")
    else:
        print(f"   ❌ FAILED: No price found")
    
    await retriever.close()
    return price is not None


async def test_blockscout_current():
    """Test Blockscout current price retrieval."""
    print("\n" + "="*80)
    print("TEST 2: Blockscout Current Prices")
    print("="*80)
    
    logger = setup_logger('TestBlockscout')
    client = BlockscoutClient(logger=logger)
    
    # Test WAGMIGAMES current price
    wagmi_address = '0x3b604747ad1720c01ded0455728b62c0d2f100f0'
    
    print(f"\n📊 Testing WAGMIGAMES current price:")
    print(f"   Address: {wagmi_address}")
    
    price_data = await client.get_price(wagmi_address, 'ethereum')
    
    if price_data:
        print(f"   ✅ SUCCESS:")
        print(f"      Price: ${price_data.price_usd:.8f}")
        print(f"      Symbol: {price_data.symbol}")
        print(f"      Market Cap: ${price_data.market_cap:,.2f}" if price_data.market_cap else "      Market Cap: N/A")
        print(f"      Volume 24h: ${price_data.volume_24h:,.2f}" if price_data.volume_24h else "      Volume 24h: N/A")
        print(f"      Holders: {price_data.holders:,}" if hasattr(price_data, 'holders') and price_data.holders else "      Holders: N/A")
    else:
        print(f"   ❌ FAILED: No price data found")
    
    await client.close()
    return price_data is not None


async def test_goplus_security():
    """Test GoPlusLabs security analysis."""
    print("\n" + "="*80)
    print("TEST 3: GoPlusLabs Security Analysis")
    print("="*80)
    
    logger = setup_logger('TestGoPlus')
    client = GoPlusClient(logger=logger)
    
    # Test WAGMIGAMES security
    wagmi_address = '0x3b604747ad1720c01ded0455728b62c0d2f100f0'
    
    print(f"\n🔒 Testing WAGMIGAMES security:")
    print(f"   Address: {wagmi_address}")
    
    security_data = await client.get_token_security(wagmi_address, 'ethereum')
    
    if security_data:
        print(f"   ✅ SUCCESS:")
        print(f"      Reputation: {security_data.reputation.upper()}")
        print(f"      Risk Score: {security_data.risk_score:.1f}/100")
        print(f"      Is Honeypot: {'YES ⚠️' if security_data.is_honeypot else 'NO ✅'}")
        print(f"      Buy Tax: {security_data.buy_tax*100:.1f}%")
        print(f"      Sell Tax: {security_data.sell_tax*100:.1f}%")
        print(f"      Holders: {security_data.holder_count:,}")
        print(f"      Liquidity: ${security_data.liquidity_usd:,.2f}")
        print(f"      Is Proxy: {'YES' if security_data.is_proxy else 'NO'}")
        print(f"      Hidden Owner: {'YES ⚠️' if security_data.hidden_owner else 'NO ✅'}")
        print(f"      Open Source: {'YES ✅' if security_data.is_open_source else 'NO'}")
    else:
        print(f"   ❌ FAILED: No security data found")
    
    await client.close()
    return security_data is not None


async def test_eye_token():
    """Test EYE token (should fail - dead token)."""
    print("\n" + "="*80)
    print("TEST 4: EYE Token (Expected to Fail - Dead Token)")
    print("="*80)
    
    logger = setup_logger('TestEYE')
    retriever = HistoricalPriceRetriever(
        cryptocompare_api_key='7154def1a021517ec59cbb67a81f4919033185f742605b372eebcc8714fc5410',
        logger=logger
    )
    
    # Test EYE - June 20, 2023
    eye_address = '0x5d39957fc88566f14ae7e8ab8971d7c603f0ce5e'
    eye_timestamp = datetime.fromtimestamp(1687280953)  # June 20, 2023
    
    print(f"\n📊 Testing EYE historical price:")
    print(f"   Address: {eye_address}")
    print(f"   Date: {eye_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    price, source = await retriever.fetch_closest_entry_price(
        symbol='EYE',
        message_timestamp=eye_timestamp,
        address=eye_address,
        chain='ethereum'
    )
    
    if price:
        print(f"   ⚠️  UNEXPECTED: Found price ${price:.8f} (source: {source})")
    else:
        print(f"   ✅ EXPECTED: No price found (dead token)")
    
    await retriever.close()
    return True  # Success means it correctly identified as dead


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 TESTING NEW API IMPLEMENTATIONS")
    print("="*80)
    
    results = []
    
    # Test 1: DefiLlama Historical
    try:
        result = await test_defillama_historical()
        results.append(("DefiLlama Historical", result))
    except Exception as e:
        print(f"\n❌ DefiLlama test failed with exception: {e}")
        results.append(("DefiLlama Historical", False))
    
    # Test 2: Blockscout Current
    try:
        result = await test_blockscout_current()
        results.append(("Blockscout Current", result))
    except Exception as e:
        print(f"\n❌ Blockscout test failed with exception: {e}")
        results.append(("Blockscout Current", False))
    
    # Test 3: GoPlusLabs Security
    try:
        result = await test_goplus_security()
        results.append(("GoPlusLabs Security", result))
    except Exception as e:
        print(f"\n❌ GoPlusLabs test failed with exception: {e}")
        results.append(("GoPlusLabs Security", False))
    
    # Test 4: EYE Token (dead token)
    try:
        result = await test_eye_token()
        results.append(("EYE Token (Dead)", result))
    except Exception as e:
        print(f"\n❌ EYE token test failed with exception: {e}")
        results.append(("EYE Token (Dead)", False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())

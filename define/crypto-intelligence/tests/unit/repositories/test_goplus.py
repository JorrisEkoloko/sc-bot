"""Test GoPlus API integration."""
import asyncio
from repositories.api_clients.goplus_client import GoPlusClient
from utils.logger import setup_logger


async def test_goplus():
    """Test GoPlus client with known token."""
    logger = setup_logger('TestGoPlus')
    
    # Test address: TOR token (Syntor Ai)
    test_address = "0x21e133e07b6cb3ff846b5a32fa9869a1e5040da1"
    
    async with GoPlusClient(logger) as client:
        logger.info(f"Testing GoPlus with address: {test_address}")
        
        # Test 1: Get token metadata
        logger.info("\n=== Test 1: Get Token Metadata ===")
        token_data = await client.get_price(test_address, 'ethereum')
        
        if token_data:
            logger.info(f"✓ Symbol: {token_data.symbol}")
            logger.info(f"✓ Source: {token_data.source}")
            logger.info(f"✓ Price USD: ${token_data.price_usd} (expected 0.0 - GoPlus doesn't provide price)")
        else:
            logger.error("✗ Failed to get token metadata")
        
        # Test 2: Get comprehensive security analysis
        logger.info("\n=== Test 2: Get Security Analysis ===")
        security_info = await client.get_token_security(test_address, 'ethereum')
        
        if security_info:
            logger.info(f"✓ Symbol: {security_info['symbol']}")
            logger.info(f"✓ Name: {security_info['name']}")
            logger.info(f"✓ Holder Count: {security_info['holder_count']}")
            logger.info(f"✓ Is Honeypot: {security_info['is_honeypot']}")
            logger.info(f"✓ Is Open Source: {security_info['is_open_source']}")
            logger.info(f"✓ Buy Tax: {security_info['buy_tax']}")
            logger.info(f"✓ Sell Tax: {security_info['sell_tax']}")
            logger.info(f"✓ Is in DEX: {security_info['is_in_dex']}")
            logger.info(f"✓ Total Supply: {security_info['total_supply']}")
        else:
            logger.error("✗ Failed to get security analysis")
        
        # Test 3: Get DEX info
        logger.info("\n=== Test 3: Get DEX Info ===")
        dex_info = await client.get_dex_info(test_address, 'ethereum')
        
        if dex_info:
            logger.info(f"✓ Found {len(dex_info)} DEX pair(s)")
            for i, dex in enumerate(dex_info, 1):
                logger.info(f"  {i}. {dex.get('name')} ({dex.get('liquidity_type')})")
                logger.info(f"     Liquidity: ${dex.get('liquidity')}")
                logger.info(f"     Pair: {dex.get('pair')}")
        else:
            logger.error("✗ Failed to get DEX info")
        
        # Test 4: Quick honeypot check
        logger.info("\n=== Test 4: Honeypot Check ===")
        is_honeypot = await client.is_honeypot(test_address, 'ethereum')
        
        if is_honeypot is not None:
            if is_honeypot:
                logger.warning("⚠️  Token is flagged as HONEYPOT")
            else:
                logger.info("✓ Token is NOT a honeypot (safe)")
        else:
            logger.error("✗ Failed to check honeypot status")
        
        logger.info("\n=== GoPlus Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_goplus())

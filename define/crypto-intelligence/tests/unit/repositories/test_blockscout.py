"""Test Blockscout API integration."""
import asyncio
from repositories.api_clients.blockscout_client import BlockscoutClient
from utils.logger import setup_logger


async def test_blockscout():
    """Test Blockscout client with known token."""
    logger = setup_logger('TestBlockscout')
    
    # Test address: TOR token (Syntor Ai)
    test_address = "0x21e133e07b6cb3ff846b5a32fa9869a1e5040da1"
    
    async with BlockscoutClient(logger) as client:
        logger.info(f"Testing Blockscout with address: {test_address}")
        
        # Test 1: Get token metadata
        logger.info("\n=== Test 1: Get Token Metadata ===")
        token_data = await client.get_price(test_address, 'ethereum')
        
        if token_data:
            logger.info(f"✓ Symbol: {token_data.symbol}")
            logger.info(f"✓ Source: {token_data.source}")
            logger.info(f"✓ Price USD: ${token_data.price_usd} (expected 0.0 - Blockscout doesn't provide price)")
        else:
            logger.error("✗ Failed to get token metadata")
        
        # Test 2: Get token holders
        logger.info("\n=== Test 2: Get Token Holders ===")
        holders = await client.get_token_holders(test_address, 'ethereum', page=1, offset=5)
        
        if holders:
            logger.info(f"✓ Found {len(holders)} holders")
            for i, holder in enumerate(holders[:3], 1):
                logger.info(f"  {i}. {holder.get('address')}: {holder.get('value')}")
        else:
            logger.error("✗ Failed to get token holders")
        
        # Test 3: Get token supply
        logger.info("\n=== Test 3: Get Token Supply ===")
        supply = await client.get_token_supply(test_address, 'ethereum')
        
        if supply:
            logger.info(f"✓ Total Supply: {supply:,.0f}")
        else:
            logger.error("✗ Failed to get token supply")
        
        logger.info("\n=== Blockscout Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_blockscout())

"""Test price engine with Blockscout enrichment."""
import asyncio
from services.pricing.price_engine import PriceEngine
from config.price_config import PriceConfig
from utils.logger import setup_logger


async def test_price_engine_with_blockscout():
    """Test price engine with Blockscout symbol enrichment."""
    logger = setup_logger('TestPriceEngineBlockscout')
    
    # Initialize price engine
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    config = PriceConfig(
        coingecko_api_key=os.getenv('COINGECKO_API_KEY', ''),
        birdeye_api_key=os.getenv('BIRDEYE_API_KEY', ''),
        moralis_api_key=os.getenv('MORALIS_API_KEY', '')
    )
    engine = PriceEngine(config, logger)
    
    try:
        # Test 1: Token with symbol (should get from primary API)
        logger.info("\n=== Test 1: Token with known symbol ===")
        test_address_1 = "0x21e133e07b6cb3ff846b5a32fa9869a1e5040da1"  # TOR
        
        price_data_1 = await engine.get_price(test_address_1, 'evm')
        
        if price_data_1:
            logger.info(f"✓ Symbol: {price_data_1.symbol}")
            logger.info(f"✓ Price: ${price_data_1.price_usd:.6f}")
            logger.info(f"✓ Source: {price_data_1.source}")
            logger.info(f"✓ Market Cap: ${price_data_1.market_cap:,.0f}" if price_data_1.market_cap else "✓ Market Cap: N/A")
        else:
            logger.error("✗ Failed to get price data")
        
        # Test 2: Simulate missing symbol scenario
        # (In real scenario, this would be a token where primary APIs return null symbol)
        logger.info("\n=== Test 2: Direct Blockscout lookup ===")
        blockscout_client = engine.clients['blockscout']
        blockscout_data = await blockscout_client.get_price(test_address_1, 'ethereum')
        
        if blockscout_data:
            logger.info(f"✓ Blockscout Symbol: {blockscout_data.symbol}")
            logger.info(f"✓ Blockscout Source: {blockscout_data.source}")
        else:
            logger.error("✗ Failed to get Blockscout data")
        
        logger.info("\n=== Price Engine Blockscout Test Complete ===")
        
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_price_engine_with_blockscout())

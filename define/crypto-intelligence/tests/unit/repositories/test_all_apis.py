"""Test all API integrations in the price engine."""
import asyncio
from services.pricing.price_engine import PriceEngine
from config.price_config import PriceConfig
from utils.logger import setup_logger
import os
from dotenv import load_dotenv


async def test_all_apis():
    """Test price engine with all API integrations."""
    logger = setup_logger('TestAllAPIs')
    load_dotenv()
    
    # Initialize price engine
    config = PriceConfig(
        coingecko_api_key=os.getenv('COINGECKO_API_KEY', ''),
        birdeye_api_key=os.getenv('BIRDEYE_API_KEY', ''),
        moralis_api_key=os.getenv('MORALIS_API_KEY', '')
    )
    engine = PriceEngine(config, logger)
    
    try:
        # Test token: TOR (Syntor Ai)
        test_address = "0x21e133e07b6cb3ff846b5a32fa9869a1e5040da1"
        
        logger.info("\n" + "="*60)
        logger.info("Testing Multi-API Symbol Enrichment")
        logger.info("="*60)
        
        # Get price with full enrichment
        price_data = await engine.get_price(test_address, 'evm')
        
        if price_data:
            logger.info("\n✅ FINAL ENRICHED DATA:")
            logger.info(f"  Symbol: {price_data.symbol}")
            logger.info(f"  Price: ${price_data.price_usd:.6f}")
            logger.info(f"  Market Cap: ${price_data.market_cap:,.0f}" if price_data.market_cap else "  Market Cap: N/A")
            logger.info(f"  Volume 24h: ${price_data.volume_24h:,.0f}" if price_data.volume_24h else "  Volume 24h: N/A")
            logger.info(f"  Source: {price_data.source}")
            logger.info(f"  Liquidity: ${price_data.liquidity_usd:,.0f}" if price_data.liquidity_usd else "  Liquidity: N/A")
        else:
            logger.error("✗ Failed to get price data")
        
        # Test individual API clients
        logger.info("\n" + "="*60)
        logger.info("Testing Individual API Clients")
        logger.info("="*60)
        
        # Test Blockscout
        logger.info("\n--- Blockscout ---")
        blockscout_data = await engine.clients['blockscout'].get_price(test_address, 'ethereum')
        if blockscout_data:
            logger.info(f"✓ Symbol: {blockscout_data.symbol}")
        else:
            logger.error("✗ Blockscout failed")
        
        # Test GoPlus
        logger.info("\n--- GoPlus ---")
        goplus_data = await engine.clients['goplus'].get_price(test_address, 'ethereum')
        if goplus_data:
            logger.info(f"✓ Symbol: {goplus_data.symbol}")
        else:
            logger.error("✗ GoPlus failed")
        
        # Test GoPlus security analysis
        logger.info("\n--- GoPlus Security Analysis ---")
        security_info = await engine.clients['goplus'].get_token_security(test_address, 'ethereum')
        if security_info:
            logger.info(f"✓ Holder Count: {security_info['holder_count']}")
            logger.info(f"✓ Is Honeypot: {security_info['is_honeypot']}")
            logger.info(f"✓ Buy Tax: {security_info['buy_tax']}")
            logger.info(f"✓ Sell Tax: {security_info['sell_tax']}")
        else:
            logger.error("✗ GoPlus security analysis failed")
        
        logger.info("\n" + "="*60)
        logger.info("All API Tests Complete")
        logger.info("="*60)
        
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_all_apis())

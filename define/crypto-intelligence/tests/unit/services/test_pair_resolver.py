"""Test LP Pair Resolver."""
import asyncio
from services.message_processing.pair_resolver import PairResolver
from services.message_processing.address_extractor import AddressExtractor
from utils.logger import setup_logger


async def test_pair_resolver():
    """Test pair resolver with known LP pair address."""
    logger = setup_logger('TestPairResolver')
    
    # Known LP pair address for PEAS (from the issue)
    pair_address = "0xae750560b09ad1f5246f3b279b3767afd1d79160"
    expected_token = "0x02f92800F57BCD74066F5709F1Daa1A4302Df875"
    
    logger.info("=== Testing LP Pair Resolver ===\n")
    
    # Test 1: Direct pair resolution
    logger.info("Test 1: Direct Pair Resolution")
    logger.info(f"Pair Address: {pair_address}")
    
    async with PairResolver(logger) as resolver:
        resolution = await resolver.resolve_address(pair_address, 'evm')
        
        if resolution.is_pair:
            logger.info(f"✓ Detected as LP pair")
            logger.info(f"✓ Token Address: {resolution.token_address}")
            logger.info(f"✓ Token Symbol: {resolution.token_symbol}")
            logger.info(f"✓ Pair Type: {resolution.pair_type}")
            
            if resolution.token_address.lower() == expected_token.lower():
                logger.info(f"✓ Correctly resolved to PEAS token!")
            else:
                logger.error(f"✗ Wrong token address!")
        else:
            logger.error(f"✗ Failed to detect as LP pair")
    
    # Test 2: Address extractor with pair resolver
    logger.info("\n\nTest 2: Address Extractor with Pair Resolver")
    
    async with PairResolver(logger) as resolver:
        extractor = AddressExtractor(logger=logger, pair_resolver=resolver)
        
        # Simulate crypto mentions with pair address
        crypto_mentions = ["PEAS", pair_address]
        
        addresses = await extractor.extract_addresses_async(crypto_mentions)
        
        logger.info(f"Found {len(addresses)} addresses")
        for addr in addresses:
            logger.info(f"\nAddress: {addr.address}")
            logger.info(f"  Chain: {addr.chain}")
            logger.info(f"  Valid: {addr.is_valid}")
            logger.info(f"  Is Pair: {addr.is_pair}")
            if addr.is_pair:
                logger.info(f"  Original Pair: {addr.original_address}")
                logger.info(f"  Token Symbol: {addr.ticker}")
                
                if addr.address.lower() == expected_token.lower():
                    logger.info(f"  ✓ Successfully resolved to PEAS token!")
                else:
                    logger.error(f"  ✗ Wrong resolution!")
    
    # Test 3: Regular token address (should not be resolved)
    logger.info("\n\nTest 3: Regular Token Address (should not resolve)")
    regular_token = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # USDT
    
    async with PairResolver(logger) as resolver:
        resolution = await resolver.resolve_address(regular_token, 'evm')
        
        if not resolution.is_pair:
            logger.info(f"✓ Correctly identified as NOT a pair")
        else:
            logger.error(f"✗ Incorrectly identified as pair")
    
    logger.info("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_pair_resolver())

"""Test pair resolver with the 8 failed LP tokens."""
import asyncio
from services.message_processing.pair_resolver import PairResolver


async def test_failed_lp_tokens():
    """Test the 8 LP tokens that failed price fetching."""
    
    resolver = PairResolver()
    
    print("\n" + "="*80)
    print("TESTING FAILED LP TOKENS FROM HISTORICAL SCRAPER")
    print("="*80)
    
    failed_lp_tokens = [
        "0x7626367d028b969a7930c28ee3ae18b20e83ecda",
        "0xdabb0b29fdf826c9ac06b8fcab14435b791bce16",
        "0xe557da50d8be589414beea0d00653e23f40a76c2",
        "0x6fdf03d96c40736f787b6354aed7ca3ae8e3d372",
        "0x74d9360003cb55a01f01110055dc68dbd0282e27",
        "0xC6786e1a929c66F8d015C11053c927C18C9FF4B5",
        "0x7f1205a98f128b7575cd0868d6ce29f47d775dbd",
        "0x74d9360003cb55a01f01110055dc68dbd0282e27"
    ]
    
    resolved_count = 0
    failed_count = 0
    
    for address in failed_lp_tokens:
        print(f"\nChecking: {address}")
        
        resolution = await resolver.resolve_address(address, 'evm')
        
        if resolution.is_pair:
            print(f"  ✓ RESOLVED TO: {resolution.token_address}")
            resolved_count += 1
        else:
            print(f"  ✗ NOT RESOLVED")
            failed_count += 1
    
    await resolver.close()
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {resolved_count} resolved, {failed_count} failed")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_failed_lp_tokens())

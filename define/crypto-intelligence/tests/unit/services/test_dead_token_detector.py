#!/usr/bin/env python3
"""
Test Dead Token Detector

Tests the dead token detection and blacklisting system.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from services.validation.dead_token_detector import DeadTokenDetector
from utils.logger import setup_logger


async def test_dead_token_detector():
    """Test dead token detection."""
    
    print("\n" + "="*80)
    print("DEAD TOKEN DETECTOR TEST")
    print("="*80)
    
    # Get API key
    etherscan_key = os.getenv('ETHERSCAN_API_KEY', '')
    if not etherscan_key:
        print("[ERROR] ETHERSCAN_API_KEY not found in .env")
        return
    
    print(f"[OK] Etherscan API key found: {etherscan_key[:10]}...")
    
    # Initialize detector
    logger = setup_logger('DeadTokenDetector', 'INFO')
    detector = DeadTokenDetector(
        etherscan_api_key=etherscan_key,
        blacklist_path="data/dead_tokens_blacklist.json",
        logger=logger
    )
    
    # Test tokens
    test_tokens = [
        {
            'name': 'Dead LP Token (MSTR/ETH)',
            'address': '0x6d9350d1e65631a9894f9a9dafb17a54349a3b90',
            'chain': 'ethereum',
            'expected_dead': True
        },
        {
            'name': 'USDC (Active Token)',
            'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'chain': 'ethereum',
            'expected_dead': False
        },
        {
            'name': 'WETH (Active Token)',
            'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'chain': 'ethereum',
            'expected_dead': False
        }
    ]
    
    print("\n" + "-"*80)
    print("Testing Token Detection")
    print("-"*80)
    
    for i, token in enumerate(test_tokens, 1):
        print(f"\n[Test {i}] {token['name']}")
        print(f"  Address: {token['address']}")
        print(f"  Chain: {token['chain']}")
        print(f"  Expected: {'DEAD' if token['expected_dead'] else 'ALIVE'}")
        
        # Check token
        stats = await detector.check_and_blacklist_if_dead(
            token['address'],
            token['chain']
        )
        
        print(f"\n  Results:")
        print(f"    Status: {'DEAD' if stats.is_dead else 'ALIVE'}")
        print(f"    Total Supply: {stats.total_supply}")
        print(f"    Reason: {stats.reason}")
        
        # Verify result
        if stats.is_dead == token['expected_dead']:
            print(f"    [OK] Detection correct!")
        else:
            print(f"    [FAILED] Expected {'DEAD' if token['expected_dead'] else 'ALIVE'}, got {'DEAD' if stats.is_dead else 'ALIVE'}")
    
    # Test blacklist check
    print("\n" + "-"*80)
    print("Testing Blacklist Check")
    print("-"*80)
    
    dead_token = test_tokens[0]['address']
    print(f"\nChecking if {dead_token[:10]}... is blacklisted...")
    
    if detector.is_blacklisted(dead_token):
        reason = detector.get_blacklist_reason(dead_token)
        print(f"[OK] Token is blacklisted: {reason}")
    else:
        print(f"[INFO] Token not blacklisted (may not have been detected as dead)")
    
    # Get blacklist stats
    print("\n" + "-"*80)
    print("Blacklist Statistics")
    print("-"*80)
    
    stats = detector.get_blacklist_stats()
    print(f"\nTotal Blacklisted: {stats['total_blacklisted']}")
    print(f"\nBy Chain:")
    for chain, count in stats['by_chain'].items():
        print(f"  {chain}: {count}")
    print(f"\nBy Reason:")
    for reason, count in stats['by_reason'].items():
        print(f"  {reason}: {count}")
    
    # Cleanup
    await detector.close()
    
    print("\n" + "="*80)
    print("[SUCCESS] Dead Token Detector Test Complete!")
    print("="*80)
    print(f"\nBlacklist saved to: data/dead_tokens_blacklist.json")
    print(f"Total blacklisted tokens: {stats['total_blacklisted']}")


if __name__ == '__main__':
    asyncio.run(test_dead_token_detector())

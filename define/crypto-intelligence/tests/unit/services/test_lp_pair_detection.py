"""
Test LP pair detection using Web3 contract calls.

Tests calling token0() and token1() functions to detect Uniswap V2 LP pairs.
"""
import asyncio
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


async def test_lp_pair_detection():
    """Test detecting LP pairs by calling token0() and token1()."""
    
    # Initialize Web3 with public RPC
    # Try multiple public RPCs
    rpcs = [
        'https://eth.llamarpc.com',
        'https://rpc.ankr.com/eth',
        'https://ethereum.publicnode.com'
    ]
    
    w3 = None
    for rpc in rpcs:
        try:
            print(f"Trying RPC: {rpc}")
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                print(f"✓ Connected via {rpc}")
                break
        except Exception as e:
            print(f"✗ Failed: {e}")
            continue
    
    if not w3 or not w3.is_connected():
        print("ERROR: Could not connect to any Ethereum RPC")
        return
    
    print("Connected to Ethereum mainnet")
    print("="*80)
    
    # Test addresses
    test_cases = [
        {
            "address": "0x7626367d028b969a7930c28ee3ae18b20e83ecda",
            "expected": "LP Pair (ETF/ETH)",
            "description": "Failed LP pair from logs"
        },
        {
            "address": "0xdabb0b29fdf826c9ac06b8fcab14435b791bce16",
            "expected": "LP Pair (HOLA/ETH)",
            "description": "Failed LP pair from logs"
        },
        {
            "address": "0xe557da50d8be589414beea0d00653e23f40a76c2",
            "expected": "LP Pair (EYE/ETH)",
            "description": "Failed LP pair from logs"
        },
        {
            "address": "0x562E362876c8Aee4744FC2c6aaC8394C312d215d",
            "expected": "Regular Token (OPTIMUS)",
            "description": "Known regular token"
        },
        {
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "expected": "Regular Token (WETH)",
            "description": "Known regular token"
        }
    ]
    
    # Function signatures
    # token0() = 0x0dfe1681
    # token1() = 0xd21220a7
    token0_sig = "0x0dfe1681"
    token1_sig = "0xd21220a7"
    
    for test in test_cases:
        address = Web3.to_checksum_address(test["address"])
        print(f"\nTest: {test['description']}")
        print(f"Address: {address}")
        print(f"Expected: {test['expected']}")
        
        try:
            # Try calling token0()
            token0_result = w3.eth.call({
                'to': address,
                'data': token0_sig
            })
            
            # Try calling token1()
            token1_result = w3.eth.call({
                'to': address,
                'data': token1_sig
            })
            
            # If both calls succeed and return 32 bytes (address), it's an LP pair
            if len(token0_result) == 32 and len(token1_result) == 32:
                # Extract addresses
                token0_addr = '0x' + token0_result[-20:].hex()
                token1_addr = '0x' + token1_result[-20:].hex()
                
                print(f"✓ IS LP PAIR")
                print(f"  token0: {token0_addr}")
                print(f"  token1: {token1_addr}")
            else:
                print(f"✗ NOT LP PAIR (unexpected return size)")
                
        except Exception as e:
            print(f"✗ NOT LP PAIR (call failed: {str(e)[:50]})")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_lp_pair_detection())

"""Utility script to check if a token would be filtered and why.

Usage:
    python scripts/check_token_filtering.py --symbol ETH --price 3000 --market-cap 400000000000
    python scripts/check_token_filtering.py --symbol SMOON --price 0.00032 --market-cap 316000
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.token_registry import TokenRegistry


def check_token(symbol: str, price: float, market_cap: float, supply: float = None):
    """Check if a token would be filtered."""
    
    print(f"\n{'='*60}")
    print(f"Token Filtering Check: {symbol}")
    print(f"{'='*60}")
    
    # Check if major token
    is_major = TokenRegistry.is_major_token(symbol)
    print(f"\nToken Type: {'MAJOR' if is_major else 'REGULAR'}")
    
    if is_major:
        criteria = TokenRegistry.get_major_token_criteria(symbol)
        print(f"Canonical Name: {criteria['canonical_name']}")
        print(f"\nExpected Criteria:")
        print(f"  Min Price: ${criteria.get('min_price', 0):,.2f}")
        if 'max_price' in criteria:
            print(f"  Max Price: ${criteria['max_price']:,.2f}")
        print(f"  Min Market Cap: ${criteria.get('min_market_cap', 0):,.0f}")
    else:
        print(f"\nMinimum Criteria:")
        print(f"  Min Price: ${TokenRegistry.MIN_PRICE:.8f}")
        print(f"  Min Market Cap: ${TokenRegistry.MIN_MARKET_CAP:,.0f}")
    
    # Show provided values
    print(f"\nProvided Values:")
    print(f"  Price: ${price:,.8f}")
    print(f"  Market Cap: ${market_cap:,.0f}")
    if supply:
        print(f"  Supply: {supply:,.0f}")
    
    # Check if would be filtered
    should_filter, reason = TokenRegistry.should_filter_token(
        symbol, price, market_cap, supply
    )
    
    print(f"\n{'='*60}")
    if should_filter:
        print(f"❌ FILTERED: {reason}")
        print(f"{'='*60}")
        print(f"\nThis token would be FILTERED OUT and NOT processed.")
        return False
    else:
        print(f"✅ PASSED: {reason}")
        print(f"{'='*60}")
        print(f"\nThis token would be PROCESSED.")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Check if a token would be filtered by the token filtering system"
    )
    parser.add_argument("--symbol", required=True, help="Token symbol (e.g., ETH, SMOON)")
    parser.add_argument("--price", type=float, required=True, help="Token price in USD")
    parser.add_argument("--market-cap", type=float, required=True, help="Market cap in USD")
    parser.add_argument("--supply", type=float, help="Token supply (optional)")
    
    args = parser.parse_args()
    
    passed = check_token(args.symbol, args.price, args.market_cap, args.supply)
    
    # Show configuration
    config = TokenRegistry.get_config_info()
    print(f"\nCurrent Configuration:")
    print(f"  Min Market Cap: ${config['min_market_cap']:,}")
    print(f"  Min Price: ${config['min_price']:.8f}")
    print(f"  Major Tokens: {', '.join(config['major_tokens'])}")
    print(f"\nTo adjust these values, edit: config/token_filter_config.py\n")
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

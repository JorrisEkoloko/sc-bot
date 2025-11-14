"""
Test script to analyze symbol mapping and find discrepancies across APIs
"""
import json
from collections import defaultdict

def analyze_symbol_discrepancies():
    """Analyze the symbol mapping to find all discrepancies"""
    
    # Load the mapping
    with open('crypto-intelligence/data/symbol_mapping.json', 'r') as f:
        symbol_map = json.load(f)
    
    print("=" * 80)
    print("SYMBOL MAPPING ANALYSIS")
    print("=" * 80)
    print(f"Total tokens in mapping: {len(symbol_map)}")
    print()
    
    # Track statistics
    stats = {
        'total_tokens': len(symbol_map),
        'tokens_with_multiple_apis': 0,
        'tokens_with_discrepancies': 0,
        'discrepancies_by_type': defaultdict(int)
    }
    
    discrepancies = []
    
    # Analyze each token
    for address, data in symbol_map.items():
        symbols = data.get('symbols', {})
        
        # Skip if only one API has data
        if len(symbols) < 2:
            continue
        
        stats['tokens_with_multiple_apis'] += 1
        
        # Get unique symbols across all APIs
        unique_symbols = set(symbols.values())
        
        # If more than one unique symbol, we have a discrepancy
        if len(unique_symbols) > 1:
            stats['tokens_with_discrepancies'] += 1
            
            # Categorize the type of discrepancy
            apis_involved = list(symbols.keys())
            discrepancy_type = f"{'+'.join(sorted(apis_involved))}"
            stats['discrepancies_by_type'][discrepancy_type] += 1
            
            discrepancies.append({
                'address': address,
                'chain': data.get('chain', 'unknown'),
                'names': data.get('names', []),
                'symbols': symbols,
                'primary_symbol': data.get('primary_symbol', 'N/A')
            })
    
    # Print statistics
    print("STATISTICS")
    print("-" * 80)
    print(f"Tokens with data from multiple APIs: {stats['tokens_with_multiple_apis']}")
    print(f"Tokens with symbol discrepancies: {stats['tokens_with_discrepancies']}")
    print(f"Discrepancy rate: {stats['tokens_with_discrepancies'] / stats['tokens_with_multiple_apis'] * 100:.2f}%")
    print()
    
    print("DISCREPANCIES BY API COMBINATION")
    print("-" * 80)
    for combo, count in sorted(stats['discrepancies_by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"{combo}: {count} tokens")
    print()
    
    # Print detailed discrepancies
    if discrepancies:
        print("=" * 80)
        print(f"DETAILED DISCREPANCIES ({len(discrepancies)} tokens)")
        print("=" * 80)
        
        for i, disc in enumerate(discrepancies, 1):
            print(f"\n{i}. Address: {disc['address']}")
            print(f"   Chain: {disc['chain']}")
            print(f"   Names: {', '.join(disc['names'])}")
            print(f"   Primary Symbol: {disc['primary_symbol']}")
            print(f"   Symbols by API:")
            for api, symbol in sorted(disc['symbols'].items()):
                print(f"     - {api}: {symbol}")
            print("-" * 80)
    else:
        print("No discrepancies found! All symbols match across APIs.")
    
    # Check for case-only differences
    print("\n" + "=" * 80)
    print("CASE-ONLY DIFFERENCES")
    print("=" * 80)
    
    case_differences = []
    for address, data in symbol_map.items():
        symbols = data.get('symbols', {})
        if len(symbols) < 2:
            continue
        
        # Check if symbols are the same when lowercased
        lowercased = set(s.lower() for s in symbols.values())
        if len(lowercased) == 1 and len(set(symbols.values())) > 1:
            case_differences.append({
                'address': address,
                'symbols': symbols,
                'primary': data.get('primary_symbol')
            })
    
    if case_differences:
        print(f"Found {len(case_differences)} tokens with case-only differences:")
        for diff in case_differences[:10]:  # Show first 10
            print(f"\nAddress: {diff['address']}")
            print(f"Primary: {diff['primary']}")
            for api, symbol in diff['symbols'].items():
                print(f"  - {api}: {symbol}")
    else:
        print("No case-only differences found.")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze_symbol_discrepancies()

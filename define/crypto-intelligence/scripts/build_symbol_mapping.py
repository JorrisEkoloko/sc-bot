#!/usr/bin/env python3
"""
Symbol Mapping Builder

This script fetches token data from multiple APIs and builds a comprehensive
symbol mapping file to handle cases where different APIs use different symbols
for the same token (identified by contract address).

Example: OPTIMUS AI
- Contract: 0x562e362876c8aee4744fc2c6aac8394c312d215d
- CoinMarketCap: OPTI
- CryptoCompare: OPTI
- DexScreener: OPTIMUS
- User Input: OPTIMUS

The script will:
1. Fetch token lists from CoinGecko (Ethereum, Solana, Base)
2. Fetch token data from DexScreener for popular tokens
3. Compare symbols across APIs by contract address
4. Build a mapping file: symbol_mapping.json
"""

import json
import requests
from collections import defaultdict
from typing import Dict, List, Set
import time

# API endpoints
COINGECKO_LISTS = {
    "ethereum": "https://tokens.coingecko.com/uniswap/all.json",
    "solana": "https://tokens.coingecko.com/solana/all.json",
    "base": "https://tokens.coingecko.com/base/all.json"
}

DEXSCREENER_SEARCH = "https://api.dexscreener.com/latest/dex/search"

# Popular tokens to check for symbol discrepancies
POPULAR_TOKENS = [
    "WIF", "BONK", "PEPE", "SHIB", "DOGE", "FLOKI", "OPTIMUS",
    "TRUMP", "MAGA", "WOJAK", "BRETT", "ANDY", "MOG", "POPCAT"
]


class SymbolMappingBuilder:
    def __init__(self):
        self.address_to_symbols = defaultdict(lambda: {
            "names": set(),
            "symbols": {},
            "primary_symbol": None,
            "chain": None
        })
        
    def normalize_address(self, address: str, chain: str) -> str:
        """Normalize address to lowercase for comparison"""
        if not address:
            return None
        # Solana addresses are case-sensitive, Ethereum are not
        if chain == "solana":
            return address
        return address.lower()
    
    def fetch_coingecko_tokens(self, chain: str, url: str):
        """Fetch token list from CoinGecko"""
        print(f"Fetching CoinGecko {chain} tokens...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            tokens = data.get("tokens", [])
            print(f"  Found {len(tokens)} tokens")
            
            for token in tokens:
                address = self.normalize_address(token.get("address"), chain)
                if not address:
                    continue
                    
                symbol = token.get("symbol", "").upper()
                name = token.get("name", "")
                
                if address not in self.address_to_symbols:
                    self.address_to_symbols[address]["chain"] = chain
                
                self.address_to_symbols[address]["names"].add(name)
                self.address_to_symbols[address]["symbols"]["coingecko"] = symbol
                
                # Use CoinGecko as primary if not set
                if not self.address_to_symbols[address]["primary_symbol"]:
                    self.address_to_symbols[address]["primary_symbol"] = symbol
                    
        except Exception as e:
            print(f"  Error fetching CoinGecko {chain}: {e}")
    
    def fetch_dexscreener_token(self, search_term: str):
        """Fetch token data from DexScreener"""
        print(f"Searching DexScreener for: {search_term}")
        try:
            response = requests.get(
                f"{DEXSCREENER_SEARCH}?q={search_term}",
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            pairs = data.get("pairs", [])
            print(f"  Found {len(pairs)} pairs")
            
            for pair in pairs[:10]:  # Limit to top 10 results
                base_token = pair.get("baseToken", {})
                address = base_token.get("address")
                chain = pair.get("chainId", "").lower()
                
                if not address:
                    continue
                
                address = self.normalize_address(address, chain)
                symbol = base_token.get("symbol", "").upper()
                name = base_token.get("name", "")
                
                if address not in self.address_to_symbols:
                    self.address_to_symbols[address]["chain"] = chain
                
                self.address_to_symbols[address]["names"].add(name)
                self.address_to_symbols[address]["symbols"]["dexscreener"] = symbol
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  Error searching DexScreener: {e}")
    
    def find_discrepancies(self) -> List[Dict]:
        """Find tokens where symbols differ across APIs"""
        discrepancies = []
        
        for address, data in self.address_to_symbols.items():
            symbols = data["symbols"]
            
            # Check if we have multiple APIs with different symbols
            if len(symbols) > 1:
                unique_symbols = set(symbols.values())
                if len(unique_symbols) > 1:
                    discrepancies.append({
                        "address": address,
                        "chain": data["chain"],
                        "names": list(data["names"]),
                        "symbols": symbols,
                        "primary_symbol": data["primary_symbol"]
                    })
        
        return discrepancies
    
    def build_mapping(self) -> Dict:
        """Build the final symbol mapping structure"""
        mapping = {}
        
        for address, data in self.address_to_symbols.items():
            # Only include tokens with potential discrepancies or multiple API sources
            if len(data["symbols"]) > 0:
                mapping[address] = {
                    "chain": data["chain"],
                    "names": list(data["names"]),
                    "symbols": data["symbols"],
                    "primary_symbol": data["primary_symbol"]
                }
        
        return mapping
    
    def save_mapping(self, filepath: str):
        """Save mapping to JSON file"""
        mapping = self.build_mapping()
        
        with open(filepath, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"\nSaved {len(mapping)} token mappings to {filepath}")
    
    def print_discrepancies(self):
        """Print tokens with symbol discrepancies"""
        discrepancies = self.find_discrepancies()
        
        print(f"\n{'='*80}")
        print(f"Found {len(discrepancies)} tokens with symbol discrepancies")
        print(f"{'='*80}\n")
        
        for item in discrepancies[:20]:  # Show top 20
            print(f"Address: {item['address']}")
            print(f"Chain: {item['chain']}")
            print(f"Names: {', '.join(item['names'])}")
            print(f"Symbols by API:")
            for api, symbol in item['symbols'].items():
                print(f"  - {api}: {symbol}")
            print(f"Primary Symbol: {item['primary_symbol']}")
            print("-" * 80)


def main():
    builder = SymbolMappingBuilder()
    
    # Fetch from CoinGecko token lists
    for chain, url in COINGECKO_LISTS.items():
        builder.fetch_coingecko_tokens(chain, url)
        time.sleep(2)  # Rate limiting
    
    # Fetch popular tokens from DexScreener
    print("\nFetching popular tokens from DexScreener...")
    for token in POPULAR_TOKENS:
        builder.fetch_dexscreener_token(token)
    
    # Print discrepancies
    builder.print_discrepancies()
    
    # Save mapping
    output_file = "crypto-intelligence/data/symbol_mapping.json"
    builder.save_mapping(output_file)
    
    print("\n" + "="*80)
    print("Symbol mapping complete!")
    print("="*80)
    print(f"\nUsage in your code:")
    print(f"1. Load the mapping: symbol_map = json.load(open('{output_file}'))")
    print(f"2. Look up by address: symbol_map[address]['symbols']['dexscreener']")
    print(f"3. Get primary symbol: symbol_map[address]['primary_symbol']")


if __name__ == "__main__":
    main()

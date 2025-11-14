"""
Shared chain mapping utilities for API clients.

Provides consistent chain name mapping across different API providers.
"""
from typing import Dict


# Shared chain mappings for different API providers
CHAIN_MAPPINGS = {
    'defillama': {
        'evm': 'ethereum',
        'ethereum': 'ethereum',
        'eth': 'ethereum',
        'solana': 'solana',
        'sol': 'solana',
        'bsc': 'bsc',
        'bnb': 'bsc',
        'polygon': 'polygon',
        'matic': 'polygon',
        'arbitrum': 'arbitrum',
        'optimism': 'optimism',
        'base': 'base',
        'avalanche': 'avax',
        'avax': 'avax'
    },
    'dexscreener': {
        'evm': 'ethereum',
        'eth': 'ethereum',
        'ethereum': 'ethereum',
        'bnb': 'bsc',
        'bsc': 'bsc',
        'matic': 'polygon',
        'polygon': 'polygon',
        'avax': 'avalanche',
        'avalanche': 'avalanche',
        'ftm': 'fantom',
        'fantom': 'fantom',
        'op': 'optimism',
        'optimism': 'optimism',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'solana': 'solana',
        'sol': 'solana'
    },
    'coinmarketcap': {
        'ethereum': 1,
        'evm': 1,
        'eth': 1,
        'bsc': 56,
        'bnb': 56,
        'polygon': 137,
        'matic': 137,
        'avalanche': 43114,
        'avax': 43114
    }
}


def get_chain_for_api(chain: str, api_name: str) -> str:
    """
    Get the correct chain identifier for a specific API.
    
    Args:
        chain: Generic chain name (e.g., 'ethereum', 'bsc', 'polygon')
        api_name: API provider name ('defillama', 'dexscreener', 'coinmarketcap')
        
    Returns:
        API-specific chain identifier
        
    Example:
        >>> get_chain_for_api('evm', 'defillama')
        'ethereum'
        >>> get_chain_for_api('bnb', 'dexscreener')
        'bsc'
    """
    chain_lower = chain.lower()
    
    if api_name not in CHAIN_MAPPINGS:
        return chain_lower
    
    mapping = CHAIN_MAPPINGS[api_name]
    return mapping.get(chain_lower, chain_lower)


def get_all_chain_aliases(chain: str) -> list:
    """
    Get all known aliases for a chain.
    
    Args:
        chain: Chain name
        
    Returns:
        List of all known aliases for this chain
        
    Example:
        >>> get_all_chain_aliases('ethereum')
        ['ethereum', 'evm', 'eth']
    """
    chain_lower = chain.lower()
    aliases = set([chain_lower])
    
    # Find all keys that map to the same value
    for api_mappings in CHAIN_MAPPINGS.values():
        target_value = api_mappings.get(chain_lower)
        if target_value:
            for key, value in api_mappings.items():
                if value == target_value:
                    aliases.add(key)
    
    return sorted(list(aliases))

"""Token registry for major cryptocurrency symbols.

Provides canonical addresses and filtering criteria for major tokens
to prevent processing scam tokens with similar names.
"""

from typing import Dict, List, Optional

try:
    from config.token_filter_config import (
        MIN_MARKET_CAP as CONFIG_MIN_MARKET_CAP,
        MIN_PRICE as CONFIG_MIN_PRICE,
        MAJOR_TOKEN_THRESHOLDS as CONFIG_MAJOR_THRESHOLDS,
        ALLOW_MISSING_MARKET_CAP as CONFIG_ALLOW_MISSING_MARKET_CAP
    )
except ImportError:
    # Fallback to defaults if config not found
    CONFIG_MIN_MARKET_CAP = 10_000
    CONFIG_MIN_PRICE = 0.000001
    CONFIG_MAJOR_THRESHOLDS = {}
    CONFIG_ALLOW_MISSING_MARKET_CAP = False


class TokenRegistry:
    """Registry of major cryptocurrency tokens with canonical addresses."""
    
    # Major tokens with their canonical addresses across chains
    MAJOR_TOKENS = {
        "ETH": {
            "canonical_name": "Ethereum",
            "addresses": {
                "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "solana": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"   # Wrapped ETH
            },
            "min_price": 1000.0,  # ETH should be > $1000
            "min_market_cap": 100_000_000,  # $100M minimum
            "aliases": ["WETH", "ETHEREUM"]
        },
        "BTC": {
            "canonical_name": "Bitcoin",
            "addresses": {
                "ethereum": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                "solana": "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh"   # Wrapped BTC
            },
            "min_price": 10000.0,  # BTC should be > $10,000
            "min_market_cap": 1_000_000_000,  # $1B minimum
            "aliases": ["WBTC", "BITCOIN"]
        },
        "SOL": {
            "canonical_name": "Solana",
            "addresses": {
                "solana": "So11111111111111111111111111111111111111112",  # Native SOL
                "ethereum": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"   # Wrapped SOL
            },
            "min_price": 10.0,  # SOL should be > $10
            "min_market_cap": 10_000_000_000,  # $10B minimum
            "aliases": ["SOLANA", "WSOL"]
        },
        "USDC": {
            "canonical_name": "USD Coin",
            "addresses": {
                "ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "solana": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
            },
            "min_price": 0.95,  # USDC should be ~$1
            "max_price": 1.05,
            "min_market_cap": 10_000_000_000,  # $10B minimum
            "aliases": ["USD-COIN"]
        },
        "USDT": {
            "canonical_name": "Tether",
            "addresses": {
                "ethereum": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                "solana": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"   # USDT
            },
            "min_price": 0.95,  # USDT should be ~$1
            "max_price": 1.05,
            "min_market_cap": 50_000_000_000,  # $50B minimum
            "aliases": ["TETHER"]
        }
    }
    
    # Minimum filtering criteria for non-major tokens
    # These can be overridden in config/token_filter_config.py
    MIN_MARKET_CAP = CONFIG_MIN_MARKET_CAP  # Default: $10K minimum
    MIN_PRICE = CONFIG_MIN_PRICE  # Default: $0.000001 minimum
    ALLOW_MISSING_MARKET_CAP = CONFIG_ALLOW_MISSING_MARKET_CAP  # Default: False
    
    @classmethod
    def is_major_token(cls, symbol: str) -> bool:
        """
        Check if a symbol represents a major cryptocurrency.
        
        Args:
            symbol: Token symbol to check
            
        Returns:
            bool: True if symbol is a major token
        """
        symbol_upper = symbol.upper()
        
        # Check direct match
        if symbol_upper in cls.MAJOR_TOKENS:
            return True
        
        # Check aliases
        for token_data in cls.MAJOR_TOKENS.values():
            if symbol_upper in [alias.upper() for alias in token_data.get("aliases", [])]:
                return True
        
        return False
    
    @classmethod
    def get_canonical_address(cls, symbol: str, chain: str) -> Optional[str]:
        """
        Get the canonical address for a major token on a specific chain.
        
        Args:
            symbol: Token symbol
            chain: Blockchain name (ethereum, solana, etc.)
            
        Returns:
            str: Canonical address or None if not found
        """
        symbol_upper = symbol.upper()
        
        # Direct match
        if symbol_upper in cls.MAJOR_TOKENS:
            return cls.MAJOR_TOKENS[symbol_upper]["addresses"].get(chain.lower())
        
        # Check aliases
        for token_symbol, token_data in cls.MAJOR_TOKENS.items():
            aliases = [alias.upper() for alias in token_data.get("aliases", [])]
            if symbol_upper in aliases:
                return token_data["addresses"].get(chain.lower())
        
        return None
    
    @classmethod
    def get_major_token_criteria(cls, symbol: str) -> Optional[Dict]:
        """
        Get filtering criteria for a major token.
        
        Args:
            symbol: Token symbol
            
        Returns:
            dict: Filtering criteria or None if not a major token
        """
        symbol_upper = symbol.upper()
        
        # Direct match
        if symbol_upper in cls.MAJOR_TOKENS:
            return cls.MAJOR_TOKENS[symbol_upper]
        
        # Check aliases
        for token_data in cls.MAJOR_TOKENS.values():
            aliases = [alias.upper() for alias in token_data.get("aliases", [])]
            if symbol_upper in aliases:
                return token_data
        
        return None
    
    @classmethod
    def should_filter_token(cls, symbol: str, price: float, market_cap: float, supply: float = None) -> tuple:
        """
        Determine if a token should be filtered out.
        
        Args:
            symbol: Token symbol
            price: Token price in USD
            market_cap: Market capitalization in USD
            supply: Token supply (optional)
            
        Returns:
            tuple: (should_filter, reason)
        """
        symbol_upper = symbol.upper()
        
        # Check if it's a major token with wrong price
        criteria = cls.get_major_token_criteria(symbol)
        if criteria:
            min_price = criteria.get("min_price", 0)
            max_price = criteria.get("max_price", float('inf'))
            min_market_cap = criteria.get("min_market_cap", 0)
            
            if price < min_price:
                return True, f"Price ${price:.6f} too low for {symbol} (expected > ${min_price})"
            
            if price > max_price:
                return True, f"Price ${price:.6f} too high for {symbol} (expected < ${max_price})"
            
            if market_cap < min_market_cap:
                return True, f"Market cap ${market_cap:,.0f} too low for {symbol} (expected > ${min_market_cap:,.0f})"
        
        # General filtering for non-major tokens
        else:
            # Check if market cap is missing/zero
            if market_cap == 0 or market_cap is None:
                if cls.ALLOW_MISSING_MARKET_CAP:
                    # Allow tokens with missing market cap if they have valid price
                    if price >= cls.MIN_PRICE:
                        return False, f"Token passes (missing market cap allowed, price ${price:.8f} valid)"
                    else:
                        return True, f"Price ${price:.8f} below minimum ${cls.MIN_PRICE:.8f}"
                else:
                    return True, f"Market cap data missing or zero"
            
            # Check market cap threshold
            if market_cap < cls.MIN_MARKET_CAP:
                return True, f"Market cap ${market_cap:,.0f} below minimum ${cls.MIN_MARKET_CAP:,.0f}"
            
            # Check price threshold
            if price < cls.MIN_PRICE:
                return True, f"Price ${price:.8f} below minimum ${cls.MIN_PRICE:.8f}"
            
            # Check supply
            if supply is not None and supply == 0:
                return True, "Zero supply - likely dead/scam token"
        
        return False, "Token passes all filters"
    
    @classmethod
    def detect_chain_context(cls, message_text: str) -> Optional[str]:
        """
        Detect which blockchain is being discussed in a message.
        
        Args:
            message_text: Message content
            
        Returns:
            str: Chain name or None if unclear
        """
        message_lower = message_text.lower()
        
        # Explicit chain mentions
        if any(word in message_lower for word in ["ethereum", "eth mainnet", "erc-20", "uniswap"]):
            return "ethereum"
        
        if any(word in message_lower for word in ["solana", "sol", "spl", "raydium", "jupiter"]):
            return "solana"
        
        if any(word in message_lower for word in ["polygon", "matic", "quickswap"]):
            return "polygon"
        
        if any(word in message_lower for word in ["bsc", "binance smart chain", "pancakeswap"]):
            return "bsc"
        
        # Address format detection
        if "0x" in message_text:
            return "ethereum"  # Default for 0x addresses
        
        # Solana address patterns (base58, ~44 chars)
        import re
        solana_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
        if re.search(solana_pattern, message_text):
            return "solana"
        
        return None

    @classmethod
    def get_config_info(cls) -> Dict:
        """
        Get current filtering configuration.
        
        Returns:
            dict: Current configuration values
        """
        return {
            "min_market_cap": cls.MIN_MARKET_CAP,
            "min_price": cls.MIN_PRICE,
            "major_tokens": list(cls.MAJOR_TOKENS.keys()),
            "total_major_tokens": len(cls.MAJOR_TOKENS)
        }

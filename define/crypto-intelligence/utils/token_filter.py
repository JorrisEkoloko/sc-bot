"""Token filtering utilities to prevent processing scam tokens.

Filters out:
- Scam tokens with major token symbols (fake ETH, BTC, etc.)
- Tokens with insufficient market cap
- Tokens with invalid price data
- Dead/abandoned tokens
"""
from typing import List, Optional
from config.token_registry import (
    is_major_token,
    get_canonical_address,
    validate_major_token_price,
    is_market_commentary,
    MIN_MARKET_CAP,
    MIN_PRICE
)


class TokenFilter:
    """Filters tokens to prevent processing scams and false signals."""
    
    def __init__(self, logger=None):
        """
        Initialize token filter.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.stats = {
            'total_checked': 0,
            'major_token_filtered': 0,
            'market_cap_filtered': 0,
            'price_filtered': 0,
            'scam_filtered': 0,
            'passed': 0
        }
    
    def should_process_symbol(self, symbol: str, message_text: str = None) -> bool:
        """
        Check if symbol should be processed based on message context.
        
        Args:
            symbol: Token symbol
            message_text: Optional message text for context
            
        Returns:
            True if symbol should be processed
        """
        # Check if major token mentioned in market commentary
        if is_major_token(symbol) and message_text:
            if is_market_commentary(message_text):
                if self.logger:
                    self.logger.info(
                        f"Skipping {symbol} - appears to be market commentary, not a signal"
                    )
                return False
        
        return True
    
    def filter_address_for_major_token(
        self,
        symbol: str,
        address: str,
        chain: str,
        price: float = None
    ) -> bool:
        """
        Filter address if it's a major token but not the canonical address.
        
        Args:
            symbol: Token symbol
            address: Token address
            chain: Blockchain name
            price: Optional price for validation
            
        Returns:
            True if address should be processed, False if filtered out
        """
        self.stats['total_checked'] += 1
        
        # Check if this is a major token
        if not is_major_token(symbol):
            self.stats['passed'] += 1
            return True  # Not a major token, process normally
        
        # Get canonical address for this chain
        canonical_address = get_canonical_address(symbol, chain)
        
        if not canonical_address:
            # Major token but no canonical address for this chain
            if self.logger:
                self.logger.warning(
                    f"Major token {symbol} has no canonical address for {chain}, filtering out"
                )
            self.stats['major_token_filtered'] += 1
            return False
        
        # Normalize addresses for comparison
        address_normalized = address.lower()
        canonical_normalized = canonical_address.lower()
        
        if address_normalized != canonical_normalized:
            # Not the canonical address - likely a scam
            if self.logger:
                self.logger.warning(
                    f"Filtering fake {symbol} token: {address[:10]}... "
                    f"(canonical: {canonical_address[:10]}...)"
                )
            self.stats['major_token_filtered'] += 1
            return False
        
        # Validate price if provided
        if price is not None:
            if not validate_major_token_price(symbol, price):
                if self.logger:
                    self.logger.warning(
                        f"Filtering {symbol} - price ${price:.6f} outside expected range"
                    )
                self.stats['price_filtered'] += 1
                return False
        
        self.stats['passed'] += 1
        return True
    
    def filter_by_market_data(
        self,
        address: str,
        symbol: str,
        price: float = None,
        market_cap: float = None,
        supply: float = None
    ) -> bool:
        """
        Filter token based on market data quality.
        
        Args:
            address: Token address
            symbol: Token symbol
            price: Token price in USD
            market_cap: Market capitalization
            supply: Token supply
            
        Returns:
            True if token should be processed, False if filtered out
        """
        self.stats['total_checked'] += 1
        
        # Filter 1: Check market cap
        if market_cap is not None and market_cap < MIN_MARKET_CAP:
            if self.logger:
                self.logger.info(
                    f"Filtering {symbol} ({address[:10]}...) - "
                    f"market cap ${market_cap:,.0f} < ${MIN_MARKET_CAP:,.0f}"
                )
            self.stats['market_cap_filtered'] += 1
            return False
        
        # Filter 2: Check price validity
        if price is None or price <= 0:
            if self.logger:
                self.logger.info(
                    f"Filtering {symbol} ({address[:10]}...) - invalid price"
                )
            self.stats['price_filtered'] += 1
            return False
        
        if price < MIN_PRICE:
            if self.logger:
                self.logger.info(
                    f"Filtering {symbol} ({address[:10]}...) - "
                    f"price ${price:.12f} too low (likely dead token)"
                )
            self.stats['price_filtered'] += 1
            return False
        
        # Filter 3: Check for dead tokens (0 supply but has price)
        if supply is not None and supply == 0 and price > 0:
            if self.logger:
                self.logger.warning(
                    f"Filtering {symbol} ({address[:10]}...) - "
                    f"0 supply but has price (suspicious)"
                )
            self.stats['scam_filtered'] += 1
            return False
        
        self.stats['passed'] += 1
        return True
    
    def get_statistics(self) -> dict:
        """
        Get filtering statistics.
        
        Returns:
            Dictionary with filtering stats
        """
        return self.stats.copy()
    
    def log_statistics(self):
        """Log filtering statistics."""
        if self.logger:
            self.logger.info(
                f"Token Filter Stats: "
                f"checked={self.stats['total_checked']}, "
                f"passed={self.stats['passed']}, "
                f"major_token_filtered={self.stats['major_token_filtered']}, "
                f"market_cap_filtered={self.stats['market_cap_filtered']}, "
                f"price_filtered={self.stats['price_filtered']}, "
                f"scam_filtered={self.stats['scam_filtered']}"
            )

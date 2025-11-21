"""Token filtering service to prevent processing scam tokens and false signals.

Filters tokens based on:
1. Major token whitelist (ETH, BTC, etc.)
2. Market cap and price thresholds
3. Supply and trading activity validation
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

from config.token_registry import TokenRegistry
from utils.logger import setup_logger


@dataclass
class TokenCandidate:
    """Represents a token candidate for processing."""
    address: str
    chain: str
    symbol: str
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    supply: Optional[float] = None
    volume_24h: Optional[float] = None
    source: str = "unknown"
    

class TokenFilter:
    """Filters token candidates to prevent processing scams and false signals."""
    
    def __init__(self, logger=None):
        self.logger = logger or setup_logger('TokenFilter')
        self.registry = TokenRegistry()
        self._load_keywords()
    
    def _load_keywords(self):
        """Load filtering keywords from JSON config."""
        try:
            # Get path relative to this file: services/filtering/token_filter.py -> config/filtering_keywords.json
            config_path = Path(__file__).parent.parent.parent / "config" / "filtering_keywords.json"
            with open(config_path, 'r') as f:
                keywords = json.load(f)
                self.result_signal_keywords = keywords.get("result_signal_keywords", [])
                self.trading_signal_keywords = keywords.get("trading_signal_keywords", [])
                self.action_keywords = keywords.get("action_keywords", [])
                self.commentary_keywords = keywords.get("commentary_keywords", [])
                self.logger.debug(f"Loaded {len(self.result_signal_keywords)} result signal keywords, "
                                f"{len(self.trading_signal_keywords)} trading signal keywords, "
                                f"{len(self.action_keywords)} action keywords, "
                                f"{len(self.commentary_keywords)} commentary keywords")
        except Exception as e:
            self.logger.warning(f"Failed to load filtering keywords from JSON: {e}. Using defaults.")
            # Fallback to defaults
            self.result_signal_keywords = ["take-profit target", "tp target", "stop-loss hit", "sl hit"]
            self.trading_signal_keywords = ["entry", "exit", "buy zone", "sell zone"]
            self.action_keywords = ["buy", "sell", "long", "short", "call", "gem", "hold"]
            self.commentary_keywords = ["rally", "bullish", "bearish", "prediction", "analysis"]
    
    def filter_symbol_candidates(self, symbol: str, candidates: List[TokenCandidate], 
                               message_context: str = "") -> List[TokenCandidate]:
        """
        Filter token candidates for a given symbol.
        
        Args:
            symbol: Token symbol being searched
            candidates: List of token candidates found
            message_context: Original message text for context
            
        Returns:
            List of filtered token candidates
        """
        if not candidates:
            return []
        
        self.logger.debug(f"Filtering {len(candidates)} candidates for symbol '{symbol}'")
        
        # Check if this is a major token
        if self.registry.is_major_token(symbol):
            return self._filter_major_token(symbol, candidates, message_context)
        else:
            return self._filter_regular_token(symbol, candidates)
    
    def _filter_major_token(self, symbol: str, candidates: List[TokenCandidate], 
                          message_context: str) -> List[TokenCandidate]:
        """
        Filter candidates for major tokens (ETH, BTC, etc.).
        
        For major tokens, we prefer canonical addresses and filter out obvious scams.
        """
        self.logger.debug(f"Filtering major token '{symbol}' with {len(candidates)} candidates")
        
        # Detect chain context from message
        chain_context = self.registry.detect_chain_context(message_context)
        
        # Get canonical address if chain is clear
        if chain_context:
            canonical_address = self.registry.get_canonical_address(symbol, chain_context)
            if canonical_address:
                # Look for the canonical address in candidates
                for candidate in candidates:
                    if candidate.address.lower() == canonical_address.lower():
                        self.logger.info(f"✅ Using canonical {symbol} address on {chain_context}: {canonical_address[:10]}...")
                        return [candidate]
        
        # If no canonical address found, filter by criteria
        criteria = self.registry.get_major_token_criteria(symbol)
        if not criteria:
            self.logger.warning(f"No criteria found for major token {symbol}")
            return candidates
        
        filtered = []
        for candidate in candidates:
            should_filter, reason = self._should_filter_candidate(candidate, criteria)
            
            if should_filter:
                self.logger.debug(f"❌ Filtered {symbol} candidate {candidate.address[:10]}...: {reason}")
            else:
                self.logger.debug(f"✅ Accepted {symbol} candidate {candidate.address[:10]}...: {reason}")
                filtered.append(candidate)
        
        # For major tokens, limit to 1 result (highest market cap)
        if len(filtered) > 1:
            filtered.sort(key=lambda x: x.market_cap or 0, reverse=True)
            best_candidate = filtered[0]
            self.logger.info(f"✅ Selected best {symbol} candidate: {best_candidate.address[:10]}... (${best_candidate.market_cap:,.0f} market cap)")
            return [best_candidate]
        
        return filtered
    
    def _filter_regular_token(self, symbol: str, candidates: List[TokenCandidate]) -> List[TokenCandidate]:
        """
        Filter candidates for regular (non-major) tokens.
        
        Uses general filtering criteria to remove obvious scams.
        """
        self.logger.debug(f"Filtering regular token '{symbol}' with {len(candidates)} candidates")
        
        filtered = []
        for candidate in candidates:
            should_filter, reason = self._should_filter_candidate(candidate)
            
            if should_filter:
                self.logger.debug(f"❌ Filtered {symbol} candidate {candidate.address[:10]}...: {reason}")
            else:
                self.logger.debug(f"✅ Accepted {symbol} candidate {candidate.address[:10]}...: {reason}")
                filtered.append(candidate)
        
        # Sort by market cap (highest first)
        filtered.sort(key=lambda x: x.market_cap or 0, reverse=True)
        
        # If multiple tokens with same symbol, keep only the best one (highest market cap)
        if len(filtered) > 1:
            best_candidate = filtered[0]
            self.logger.info(
                f"🔍 Multiple {symbol} tokens found - "
                f"Selected best: {best_candidate.address[:10]}... "
                f"(${best_candidate.market_cap:,.0f} market cap) "
                f"on {best_candidate.chain}"
            )
            return [best_candidate]
        
        return filtered
    
    def _should_filter_candidate(self, candidate: TokenCandidate, 
                               major_token_criteria: Dict = None) -> Tuple[bool, str]:
        """
        Determine if a token candidate should be filtered out.
        
        Args:
            candidate: Token candidate to evaluate
            major_token_criteria: Criteria for major tokens (optional)
            
        Returns:
            tuple: (should_filter, reason)
        """
        # Check if we have enough data to evaluate
        if candidate.price_usd is None:
            return True, "No price data available"
        
        # Market cap can be None/0 if ALLOW_MISSING_MARKET_CAP is True
        # Let the registry decide if this is acceptable
        if candidate.market_cap is None:
            candidate.market_cap = 0  # Treat None as 0 for filtering logic
        
        # Use major token criteria if provided
        if major_token_criteria:
            return self.registry.should_filter_token(
                candidate.symbol,
                candidate.price_usd,
                candidate.market_cap,
                candidate.supply
            )
        
        # General filtering for regular tokens
        return self.registry.should_filter_token(
            candidate.symbol,
            candidate.price_usd,
            candidate.market_cap,
            candidate.supply
        )
    
    def is_market_commentary(self, message_text: str, symbols: List[str]) -> bool:
        """
        Detect if a message is market commentary rather than a token call.
        
        Args:
            message_text: Message content
            symbols: Symbols found in message
            
        Returns:
            bool: True if this appears to be market commentary
        """
        message_lower = message_text.lower()
        
        # If it's a result signal (take-profit hit, stop-loss hit), skip it
        # These are just reporting closed trades, not new calls
        is_result_signal = any(keyword in message_lower for keyword in self.result_signal_keywords)
        if is_result_signal:
            self.logger.debug(f"Detected result signal (take-profit/stop-loss hit) - will skip")
            return True  # Treat as commentary to skip processing
        
        # If it's a trading signal (entry/exit), it's NOT commentary
        is_trading_signal = any(keyword in message_lower for keyword in self.trading_signal_keywords)
        if is_trading_signal:
            return False
        
        # Check if message contains commentary keywords
        has_commentary = any(keyword in message_lower for keyword in self.commentary_keywords)
        
        # Check if symbols are major tokens (more likely to be commentary)
        has_major_tokens = any(self.registry.is_major_token(symbol) for symbol in symbols)
        
        # Check if message lacks call-to-action
        has_action = any(keyword in message_lower for keyword in self.action_keywords)
        
        # Check if message has addresses (more likely to be a call)
        has_addresses = "0x" in message_text or any(len(word) > 30 for word in message_text.split())
        
        # Check for price mentions (e.g., "$3,000", "3k", "$100")
        import re
        price_pattern = r'\$[\d,]+\.?\d*[kKmMbB]?|\d+[kKmMbB]\s*(usd|dollars?)'
        has_price_mention = bool(re.search(price_pattern, message_text))
        
        # Decision logic
        if has_commentary and has_major_tokens and not has_action and not has_addresses:
            self.logger.debug(f"Detected market commentary: major tokens + commentary keywords, no action/addresses")
            return True
        
        # Also detect price commentary (e.g., "ETH falls under $3,000")
        if has_price_mention and has_major_tokens and not has_action and not has_addresses:
            self.logger.debug(f"Detected price commentary: major tokens + price mention, no action/addresses")
            return True
        
        return False
    
    def should_skip_processing(self, message_text: str, symbols: List[str]) -> Tuple[bool, str]:
        """
        Determine if message processing should be skipped entirely.
        
        Args:
            message_text: Message content
            symbols: Symbols found in message
            
        Returns:
            tuple: (should_skip, reason)
        """
        # Skip if it's market commentary
        if self.is_market_commentary(message_text, symbols):
            return True, "Market commentary detected - not a token call"
        
        # Skip if only major tokens mentioned without context
        # But ONLY if there are no addresses in the original crypto_mentions
        if symbols and all(self.registry.is_major_token(symbol) for symbol in symbols):
            message_lower = message_text.lower()
            
            # Check for trading signals (take-profit, stop-loss, etc.)
            has_trading_signal = any(keyword in message_lower for keyword in self.trading_signal_keywords)
            if has_trading_signal:
                return False, "Message should be processed"  # Trading signals should be processed
            
            # Check for call-to-action keywords
            has_call_keywords = any(keyword in message_lower for keyword in self.action_keywords)
            
            # Check for addresses
            has_addresses = "0x" in message_text or any(len(word) > 30 for word in message_text.split())
            
            if not has_call_keywords and not has_addresses:
                return True, "Only major tokens mentioned without call context"
        
        return False, "Message should be processed"

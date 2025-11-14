"""
Cryptocurrency mention detector.

Detects ticker symbols, Ethereum addresses, and Solana addresses in message text.
"""

import re
import json
from pathlib import Path
from utils.logger import setup_logger


class CryptoDetector:
    """
    Cryptocurrency mention detector.
    
    Detects:
    - Ticker symbols (loaded from crypto_patterns.json)
    - Ethereum addresses (0x + 40 hex characters)
    - Solana addresses (base58, 32-44 characters)
    - Crypto keywords (loaded from crypto_keywords.json)
    """
    
    def __init__(self):
        """Initialize crypto detector with compiled patterns."""
        self.logger = setup_logger('CryptoDetector')
        
        # Load tickers and keywords from JSON files
        self.tickers = self._load_tickers()
        self.crypto_keywords = self._load_crypto_keywords()
        
        # Ticker pattern: word boundary + ticker + word boundary (case insensitive)
        if self.tickers:
            ticker_pattern = r'\b(' + '|'.join(self.tickers) + r')\b'
            self.ticker_regex = re.compile(ticker_pattern, re.IGNORECASE)
        else:
            self.ticker_regex = None
        
        # Ethereum address: 0x followed by 40 hexadecimal characters
        self.eth_address_regex = re.compile(r'0x[a-fA-F0-9]{40}')
        
        # Solana address: base58 encoded, 32-44 characters (no 0, O, I, l)
        self.sol_address_regex = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
        
        # Crypto keywords pattern (from loaded JSON)
        if self.crypto_keywords:
            # Escape special regex characters and create pattern
            escaped_keywords = [re.escape(kw) for kw in self.crypto_keywords]
            keyword_pattern = r'\b(' + '|'.join(escaped_keywords) + r')\b'
            self.keyword_regex = re.compile(keyword_pattern, re.IGNORECASE)
        else:
            self.keyword_regex = None
        
        ticker_count = len(self.tickers) if self.tickers else 0
        keyword_count = len(self.crypto_keywords) if self.crypto_keywords else 0
        self.logger.info(f"Crypto detector initialized ({ticker_count} tickers, {keyword_count} keywords)")
        
        # Validate that detector has at least some patterns loaded
        if not self.tickers and not self.crypto_keywords:
            self.logger.error("CryptoDetector initialized with no patterns or keywords - detector is non-functional")
    
    def detect_mentions(self, text: str) -> list[str]:
        """
        Detect all crypto mentions in text.
        
        Args:
            text: Message text to analyze
            
        Returns:
            List of unique crypto mentions (tickers and addresses)
        """
        if not text:
            return []
        
        mentions = []
        
        try:
            # Detect ticker symbols
            if self.ticker_regex:
                tickers = self.ticker_regex.findall(text)
                if tickers:
                    # Convert to uppercase and add to mentions
                    mentions.extend([t.upper() for t in tickers])
                    self.logger.debug(f"Tickers detected: {[t.upper() for t in tickers]}")
            
            # Detect Ethereum addresses
            eth_addresses = self.eth_address_regex.findall(text)
            if eth_addresses:
                mentions.extend(eth_addresses)
                self.logger.debug(f"Ethereum addresses detected: {len(eth_addresses)}")
            
            # Detect Solana addresses (filter out false positives)
            sol_addresses = self.sol_address_regex.findall(text)
            if sol_addresses:
                # Filter out common words that match the pattern
                filtered_sol = [addr for addr in sol_addresses if len(addr) >= 32]
                if filtered_sol:
                    mentions.extend(filtered_sol)
                    self.logger.debug(f"Solana addresses detected: {len(filtered_sol)}")
            
            # Remove duplicates while preserving order
            unique_mentions = list(dict.fromkeys(mentions))
            
            if unique_mentions:
                self.logger.info(f"Crypto detection found: {unique_mentions}")
            
            return unique_mentions
            
        except Exception as e:
            self.logger.warning(f"Error detecting crypto mentions: {e}", exc_info=True)
            return []
    
    def _load_tickers(self) -> list[str]:
        """
        Load cryptocurrency tickers from JSON file.
        
        Returns:
            List of ticker symbols
        """
        try:
            patterns_file = Path(__file__).parent.parent / 'config' / 'crypto_patterns.json'
            
            if not patterns_file.exists():
                self.logger.warning(f"Patterns file not found: {patterns_file}")
                return []
            
            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            
            # Get tickers from the patterns file
            tickers_data = patterns_data.get('tickers', {})
            
            # Flatten all ticker categories into single list
            all_tickers = []
            if isinstance(tickers_data, dict):
                for category, tickers in tickers_data.items():
                    if isinstance(tickers, list):
                        all_tickers.extend(tickers)
            elif isinstance(tickers_data, list):
                all_tickers = tickers_data
            
            # Remove duplicates while preserving order
            unique_tickers = list(dict.fromkeys(all_tickers))
            
            self.logger.info(f"Loaded {len(unique_tickers)} tickers from crypto_patterns.json")
            return unique_tickers
            
        except Exception as e:
            self.logger.error(f"Error loading tickers: {e}")
            return []
    
    def _load_crypto_keywords(self) -> list[str]:
        """
        Load crypto keywords from JSON file.
        
        Returns:
            Flattened list of all keywords from all categories
        """
        try:
            keywords_file = Path(__file__).parent.parent / 'config' / 'crypto_keywords.json'
            
            if not keywords_file.exists():
                self.logger.warning(f"Keywords file not found: {keywords_file}")
                return []
            
            with open(keywords_file, 'r', encoding='utf-8') as f:
                keywords_data = json.load(f)
            
            # Flatten all categories into single list
            all_keywords = []
            for category, keywords in keywords_data.items():
                all_keywords.extend(keywords)
            
            # Remove duplicates while preserving order
            unique_keywords = list(dict.fromkeys(all_keywords))
            
            self.logger.info(f"Loaded {len(unique_keywords)} unique keywords from {len(keywords_data)} categories")
            return unique_keywords
            
        except Exception as e:
            self.logger.error(f"Error loading crypto keywords: {e}")
            return []
    
    def has_crypto_keywords(self, text: str) -> bool:
        """
        Check if text contains crypto-related keywords.
        
        Args:
            text: Message text to analyze
            
        Returns:
            True if crypto keywords found
        """
        if not text or not self.keyword_regex:
            return False
        
        keywords = self.keyword_regex.findall(text)
        if keywords:
            self.logger.debug(f"Crypto keywords detected: {keywords[:5]}")  # Log first 5 to avoid spam
            return True
        return False
    
    def is_crypto_relevant(self, mentions: list[str], text: str = "") -> bool:
        """
        Determine if message is crypto-relevant.
        
        Args:
            mentions: List of detected crypto mentions
            text: Original message text (for keyword detection)
            
        Returns:
            True if message contains crypto content
        """
        # Check mentions (tickers or addresses)
        has_mentions = len(mentions) > 0
        
        # Check keywords (pump, moon, etc.)
        has_keywords = self.has_crypto_keywords(text) if text else False
        
        is_relevant = has_mentions or has_keywords
        
        if is_relevant:
            reason = []
            if has_mentions:
                reason.append(f"{len(mentions)} mentions")
            if has_keywords:
                reason.append("crypto keywords")
            self.logger.debug(f"Message marked as crypto-relevant: {', '.join(reason)}")
        
        return is_relevant

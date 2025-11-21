"""Pattern-based sentiment analysis using regex matching."""

import re
import math
from typing import Tuple, List
from utils.logger import get_logger
from services.analytics.sentiment_config import SentimentConfig


class PatternMatcher:
    """
    Pattern-based sentiment analyzer.
    
    Classifies messages as positive, negative, or neutral based on
    indicator patterns and crypto-specific vocabulary.
    """
    
    # Negation keywords for context detection
    NEGATION_KEYWORDS = [
        'not', "don't", "doesn't", "didn't", "won't", "wouldn't",
        'never', 'no', 'none', 'nobody', 'nothing', 'neither',
        'nowhere', 'cannot', "can't", "couldn't", "shouldn't",
        "wouldn't", "isn't", "aren't", "wasn't", "weren't"
    ]
    
    # Sarcasm indicators
    SARCASM_EMOJIS = ['🙄', '🤡', '😏', '🤦', '🤷']
    
    # Positive sentiment indicators
    POSITIVE_PATTERNS = [
        'moon', 'bullish', 'pump', 'breakout', 'rally', 'surge',
        'rocket', '🚀', '📈', 'buy', 'long', 'calls', 'gem',
        'bullrun', 'lambo', 'gains', 'profit', 'up', 'green',
        'strong', 'support', 'bounce', 'recovery', 'momentum'
    ]
    
    # Crypto-specific positive vocabulary
    CRYPTO_POSITIVE = [
        'wagmi',        # We're All Gonna Make It
        'gm',           # Good Morning (community greeting)
        'lfg',          # Let's F***ing Go
        'degen',        # Degenerate (positive in crypto)
        'ape',          # Aping in (buying aggressively)
        'diamond hands', # Strong holders
        'hodl',         # Hold On for Dear Life
        'alpha',        # Exclusive information
        'based',        # Authentic, good
        'ser',          # Sir (respectful)
        'fren',         # Friend
        'chad',         # Successful trader
        'whale',        # Large holder (neutral/positive)
        'moonshot',     # High potential
        'to the moon'   # Price going up
    ]
    
    # Negative sentiment indicators
    NEGATIVE_PATTERNS = [
        'dump', 'bearish', 'crash', 'rug', 'scam', 'exit', 'sell',
        'short', '📉', 'warning', 'avoid', 'dead', 'rekt',
        'liquidated', 'ponzi', 'down', 'red', 'weak', 'resistance',
        'drop', 'fall', 'loss', 'bear'
    ]
    
    # Crypto-specific negative vocabulary
    CRYPTO_NEGATIVE = [
        'ngmi',         # Not Gonna Make It
        'paper hands',  # Weak holders
        'rekt',         # Wrecked/destroyed
        'fud',          # Fear, Uncertainty, Doubt
        'jeet',         # Weak seller
        'rugged',       # Rug pulled
        'honeypot',     # Scam contract
        'bagholder',    # Stuck with losses
        'cope',         # Coping with losses
        'salty',        # Bitter about losses
        'exit liquidity', # Being used by whales
        'vaporware',    # Non-existent product
        'shitcoin',     # Low quality token
        'pump and dump',
        'wash trading'
    ]
    
    def __init__(self, config: SentimentConfig):
        """
        Initialize pattern matcher.
        
        Args:
            config: Sentiment configuration
        """
        self.logger = get_logger('PatternMatcher')
        self.config = config
        
        # Build combined pattern lists
        positive_patterns = self.POSITIVE_PATTERNS.copy()
        negative_patterns = self.NEGATIVE_PATTERNS.copy()
        
        # Add crypto vocabulary if enabled
        if config.use_crypto_vocabulary:
            positive_patterns.extend(self.CRYPTO_POSITIVE)
            negative_patterns.extend(self.CRYPTO_NEGATIVE)
            self.logger.info("Crypto-specific vocabulary enabled")
        
        # Compile patterns for efficient matching
        self.positive_regex = re.compile(
            r'\b(' + '|'.join(re.escape(p) for p in positive_patterns) + r')\b',
            re.IGNORECASE
        )
        self.negative_regex = re.compile(
            r'\b(' + '|'.join(re.escape(p) for p in negative_patterns) + r')\b',
            re.IGNORECASE
        )
        
        self.logger.info(
            f"Pattern matcher initialized "
            f"({len(positive_patterns)} positive, {len(negative_patterns)} negative patterns)"
        )
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment using pattern matching.
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score)
            - sentiment_label: 'positive', 'negative', or 'neutral'
            - sentiment_score: -1.0 to 1.0
        """
        if not text:
            return ('neutral', 0.0)
        
        try:
            # Find positive and negative indicators
            positive_matches = self.positive_regex.findall(text)
            negative_matches = self.negative_regex.findall(text)
            
            positive_count = len(positive_matches)
            negative_count = len(negative_matches)
            
            if positive_matches:
                self.logger.debug(f"Positive indicators: {positive_matches}")
            if negative_matches:
                self.logger.debug(f"Negative indicators: {negative_matches}")
            
            # Calculate sentiment score
            if positive_count == 0 and negative_count == 0:
                sentiment = 'neutral'
                score = 0.0
            elif positive_count > negative_count:
                sentiment = 'positive'
                ratio = positive_count / (positive_count + negative_count)
                score = 0.5 + (ratio * 0.5)
            elif negative_count > positive_count:
                sentiment = 'negative'
                ratio = negative_count / (positive_count + negative_count)
                score = -0.5 - (ratio * 0.5)
            else:
                sentiment = 'neutral'
                score = 0.0
            
            self.logger.info(f"Pattern analysis: {sentiment} (score: {score:+.2f})")
            
            return (sentiment, score)
            
        except Exception as e:
            self.logger.warning(f"Error in pattern analysis: {e}")
            return ('neutral', 0.0)
    
    def analyze_with_confidence(self, text: str) -> Tuple[str, float, float, bool]:
        """
        Analyze sentiment with confidence score and conflict detection.
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score, confidence, has_conflict)
        """
        if not text:
            return ('neutral', 0.0, 0.0, False)
        
        try:
            # Find positive and negative indicators
            positive_matches = self.positive_regex.findall(text)
            negative_matches = self.negative_regex.findall(text)
            
            positive_count = len(positive_matches)
            negative_count = len(negative_matches)
            text_length = len(text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                positive_count, 
                negative_count, 
                text_length
            )
            
            # Detect conflicting signals
            has_conflict = self._has_conflicting_signals(
                positive_count, 
                negative_count
            )
            
            # Reduce confidence if signals conflict
            if has_conflict:
                confidence *= 0.5
                self.logger.debug("Conflicting signals detected, reducing confidence")
            
            # Calculate sentiment score
            if positive_count == 0 and negative_count == 0:
                sentiment = 'neutral'
                score = 0.0
            elif positive_count > negative_count:
                sentiment = 'positive'
                ratio = positive_count / (positive_count + negative_count)
                score = 0.5 + (ratio * 0.5)
            elif negative_count > positive_count:
                sentiment = 'negative'
                ratio = negative_count / (positive_count + negative_count)
                score = -0.5 - (ratio * 0.5)
            else:
                sentiment = 'neutral'
                score = 0.0
            
            self.logger.info(
                f"Pattern analysis: {sentiment} "
                f"(score: {score:+.2f}, confidence: {confidence:.2f}, "
                f"conflict: {has_conflict})"
            )
            
            return (sentiment, score, confidence, has_conflict)
            
        except Exception as e:
            self.logger.warning(f"Error in pattern analysis: {e}")
            return ('neutral', 0.0, 0.0, False)
    
    def _calculate_confidence(
        self, 
        positive_count: int, 
        negative_count: int,
        text_length: int
    ) -> float:
        """Calculate confidence score based on match strength and signal clarity."""
        total_count = positive_count + negative_count
        
        if total_count == 0:
            return 0.0
        
        dominant_count = max(positive_count, negative_count)
        signal_clarity = dominant_count / total_count
        match_strength = 1 + math.log(total_count + 1)
        confidence = signal_clarity * match_strength
        confidence = min(1.0, confidence)
        
        # Penalize very short texts
        if text_length < 10:
            confidence *= 0.5
        elif text_length < 30:
            confidence *= 0.7
        
        return confidence
    
    def _has_conflicting_signals(
        self, 
        positive_count: int, 
        negative_count: int
    ) -> bool:
        """Detect when both positive and negative patterns match significantly."""
        if positive_count == 0 or negative_count == 0:
            return False
        
        total = positive_count + negative_count
        smaller = min(positive_count, negative_count)
        ratio = smaller / total
        
        return ratio > 0.3
    
    def detect_negation(self, text: str) -> bool:
        """Detect negation keywords with context window."""
        text_lower = text.lower()
        
        for negation in self.NEGATION_KEYWORDS:
            pos = text_lower.find(negation)
            if pos == -1:
                continue
            
            context_start = pos + len(negation)
            context_end = context_start + 30
            context_text = text_lower[context_start:context_end]
            
            if self.positive_regex.search(context_text) or \
               self.negative_regex.search(context_text):
                self.logger.debug(f"Negation detected: '{negation}' near sentiment word")
                return True
        
        return False
    
    def detect_sarcasm(self, text: str) -> bool:
        """Detect sarcasm indicators in text."""
        # Check for sarcasm emojis
        for emoji in self.SARCASM_EMOJIS:
            if emoji in text:
                self.logger.debug(f"Sarcasm emoji detected: {emoji}")
                return True
        
        # Check for quotes around positive words
        quoted_pattern = r'["\']([^"\']+)["\']'
        quoted_matches = re.findall(quoted_pattern, text)
        for match in quoted_matches:
            if self.positive_regex.search(match):
                self.logger.debug(f"Quoted positive word detected: {match}")
                return True
        
        # Check for excessive punctuation
        if re.search(r'[!?]{3,}', text):
            self.logger.debug("Excessive punctuation detected")
            return True
        
        return False
    
    def extract_crypto_terms(self, text: str) -> List[str]:
        """Extract matched crypto-specific terms from text."""
        if not self.config.use_crypto_vocabulary:
            return []
        
        text_lower = text.lower()
        matched_terms = []
        
        for term in self.CRYPTO_POSITIVE:
            if term.lower() in text_lower:
                matched_terms.append(term)
        
        for term in self.CRYPTO_NEGATIVE:
            if term.lower() in text_lower and term not in matched_terms:
                matched_terms.append(term)
        
        return matched_terms

"""Confidence calculation service - business logic for signal confidence scoring."""
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger
from utils.prediction_cache import PredictionCache


class ConfidenceCalculator:
    """
    Calculates and adjusts confidence scores for crypto signals.
    
    Pure business logic - no I/O or presentation concerns.
    """
    
    def __init__(self, confidence_threshold: float = 0.7, reputation_engine=None, logger=None):
        """
        Initialize confidence calculator.
        
        Args:
            confidence_threshold: Threshold for high-confidence classification
            reputation_engine: Optional reputation engine for adjustments
            logger: Optional logger instance
        """
        self.confidence_threshold = confidence_threshold
        self.reputation_engine = reputation_engine
        self.prediction_cache = PredictionCache(ttl_seconds=300, logger=logger)
        self.logger = logger or get_logger('ConfidenceCalculator')
    
    def calculate_base_confidence(
        self,
        hdrb_score: float,
        crypto_mentions: list,
        sentiment_score: float,
        message_length: int
    ) -> float:
        """
        Calculate base confidence score from message features.
        
        Weights:
        - HDRB score: 40%
        - Crypto relevance: 30%
        - Sentiment clarity: 20%
        - Message length: 10%
        
        Args:
            hdrb_score: Normalized HDRB score (0-100)
            crypto_mentions: List of detected crypto mentions
            sentiment_score: Sentiment score (-1.0 to 1.0)
            message_length: Length of message text
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            # Component 1: HDRB score (40%)
            hdrb_component = (hdrb_score / 100.0) * 0.4
            
            # Component 2: Crypto relevance (30%)
            crypto_component = (1.0 if len(crypto_mentions) > 0 else 0.0) * 0.3
            
            # Component 3: Sentiment clarity (20%)
            sentiment_clarity = abs(sentiment_score)
            sentiment_component = sentiment_clarity * 0.2
            
            # Component 4: Message length (10%)
            length_normalized = min(1.0, message_length / 200.0)
            length_component = length_normalized * 0.1
            
            # Calculate total
            confidence = hdrb_component + crypto_component + sentiment_component + length_component
            confidence = max(0.0, min(1.0, confidence))
            
            self.logger.debug(
                f"Base confidence: HDRB={hdrb_component:.2f}, "
                f"crypto={crypto_component:.2f}, sentiment={sentiment_component:.2f}, "
                f"length={length_component:.2f} → {confidence:.2f}"
            )
            
            return confidence
            
        except Exception as e:
            self.logger.warning(f"Error calculating base confidence: {e}")
            return 0.0
    
    def adjust_with_reputation(
        self,
        base_confidence: float,
        channel_name: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Adjust confidence based on channel reputation.
        
        Uses Sharpe ratio-based adjustment:
        - Elite (Sharpe >1.5): +25% boost
        - Excellent (Sharpe 1.0-1.5): +20% boost
        - Good (Sharpe 0.5-1.0): +10% boost
        - Average (Sharpe 0.0-0.5): No adjustment
        - Poor (Sharpe <0.0): -10% reduction
        
        Args:
            base_confidence: Base confidence score (0.0-1.0)
            channel_name: Channel name
            
        Returns:
            Tuple of (adjusted_confidence, reputation_data)
        """
        reputation_data = {
            'reputation_score': 0.0,
            'reputation_tier': 'Unproven',
            'expected_roi': 1.5,
            'sharpe_ratio': 0.0,
            'adjustment_factor': 1.0,
            'prediction_source': 'none'
        }
        
        if not self.reputation_engine:
            return base_confidence, reputation_data
        
        try:
            # Check cache first
            reputation = self._get_cached_reputation(channel_name)
            
            if not reputation:
                return base_confidence, reputation_data
            
            # Update reputation data
            reputation_data.update({
                'reputation_score': reputation.reputation_score,
                'reputation_tier': reputation.reputation_tier,
                'expected_roi': reputation.expected_roi,
                'sharpe_ratio': reputation.sharpe_ratio,
                'prediction_source': 'overall'
            })
            
            # Calculate adjustment factor
            adjustment_factor = self._calculate_adjustment_factor(reputation.sharpe_ratio)
            reputation_data['adjustment_factor'] = adjustment_factor
            
            # Apply adjustment
            adjusted_confidence = base_confidence * adjustment_factor
            adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
            
            self.logger.info(
                f"Confidence adjusted: {base_confidence:.2f} → {adjusted_confidence:.2f} "
                f"({reputation.reputation_tier}, Sharpe={reputation.sharpe_ratio:.2f}, "
                f"factor={adjustment_factor:.2f})"
            )
            
            return adjusted_confidence, reputation_data
            
        except Exception as e:
            self.logger.warning(f"Error adjusting confidence with reputation: {e}")
            return base_confidence, reputation_data
    
    def classify_confidence_level(self, confidence: float) -> Tuple[bool, str]:
        """
        Classify confidence level.
        
        Args:
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            Tuple of (is_high_confidence, label)
        """
        is_high = confidence >= self.confidence_threshold
        label = "HIGH" if is_high else "LOW"
        return is_high, label
    
    def _get_cached_reputation(self, channel_name: str):
        """Get reputation from cache or engine."""
        # Check cache
        cached = self.prediction_cache.get(channel_name)
        if cached:
            self.logger.debug(f"Cache hit for {channel_name}")
            return cached
        
        # Load from engine
        reputation = self.reputation_engine.get_reputation(channel_name)
        if reputation:
            self.prediction_cache.set(channel_name, reputation)
            self.logger.debug(f"Cached reputation for {channel_name}")
        
        return reputation
    
    def _calculate_adjustment_factor(self, sharpe_ratio: float) -> float:
        """
        Calculate adjustment factor based on Sharpe ratio.
        
        Args:
            sharpe_ratio: Channel Sharpe ratio
            
        Returns:
            Adjustment factor (0.9 to 1.25)
        """
        if sharpe_ratio > 1.5:
            return 1.25  # Elite
        elif sharpe_ratio >= 1.0:
            return 1.20  # Excellent
        elif sharpe_ratio >= 0.5:
            return 1.10  # Good
        elif sharpe_ratio >= 0.0:
            return 1.0   # Average
        else:
            return 0.90  # Poor

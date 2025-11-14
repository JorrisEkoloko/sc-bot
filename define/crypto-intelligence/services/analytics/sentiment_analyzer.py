"""
Sentiment analyzer using pattern matching.

Classifies messages as positive, negative, or neutral based on indicator patterns.
"""

import re
from utils.logger import get_logger


class SentimentAnalyzer:
    """
    Sentiment analyzer using pattern matching.
    
    Classifies messages as positive, negative, or neutral based on
    indicator patterns.
    """
    
    # Positive sentiment indicators
    POSITIVE_PATTERNS = [
        'moon', 'bullish', 'pump', 'breakout', 'rally', 'surge',
        'rocket', '🚀', '📈', 'buy', 'long', 'calls', 'gem',
        'bullrun', 'lambo', 'gains', 'profit', 'up', 'green',
        'strong', 'support', 'bounce', 'recovery', 'momentum'
    ]
    
    # Negative sentiment indicators
    NEGATIVE_PATTERNS = [
        'dump', 'bearish', 'crash', 'rug', 'scam', 'exit', 'sell',
        'short', '📉', 'warning', 'avoid', 'dead', 'rekt',
        'liquidated', 'ponzi', 'down', 'red', 'weak', 'resistance',
        'drop', 'fall', 'loss', 'bear'
    ]
    
    def __init__(self):
        """Initialize sentiment analyzer."""
        self.logger = get_logger('SentimentAnalyzer')
        
        # Compile patterns for efficient matching
        self.positive_regex = re.compile(
            r'\b(' + '|'.join(re.escape(p) for p in self.POSITIVE_PATTERNS) + r')\b',
            re.IGNORECASE
        )
        self.negative_regex = re.compile(
            r'\b(' + '|'.join(re.escape(p) for p in self.NEGATIVE_PATTERNS) + r')\b',
            re.IGNORECASE
        )
        
        self.logger.info("Sentiment analyzer initialized")
    
    def analyze(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text.
        
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
                # Score between 0.5 and 1.0 based on ratio
                ratio = positive_count / (positive_count + negative_count)
                score = 0.5 + (ratio * 0.5)
            elif negative_count > positive_count:
                sentiment = 'negative'
                # Score between -0.5 and -1.0 based on ratio
                ratio = negative_count / (positive_count + negative_count)
                score = -0.5 - (ratio * 0.5)
            else:
                # Equal positive and negative
                sentiment = 'neutral'
                score = 0.0
            
            self.logger.info(f"Sentiment analysis: {sentiment} (score: {score:+.2f})")
            
            return (sentiment, score)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing sentiment: {e}")
            return ('neutral', 0.0)

"""
Message processor with HDRB scoring and analysis.

Coordinates the complete message processing pipeline.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from utils.logger import get_logger
from core.hdrb_scorer import HDRBScorer
from core.crypto_detector import CryptoDetector
from core.sentiment_analyzer import SentimentAnalyzer


@dataclass
class ProcessedMessage:
    """Enriched message data with HDRB scores and analysis."""
    # Original message data
    channel_id: str
    channel_name: str
    message_id: int
    message_text: str
    timestamp: datetime
    
    # Engagement metrics
    forwards: int
    reactions: int
    replies: int
    views: int
    
    # HDRB scoring
    hdrb_score: float          # 0-100 normalized
    hdrb_raw: float            # Raw IC value
    
    # Crypto detection
    crypto_mentions: list = field(default_factory=list)
    is_crypto_relevant: bool = False
    
    # Sentiment analysis
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    
    # Confidence (will be added in Task 4)
    confidence: float = 0.0
    is_high_confidence: bool = False
    
    # Processing metadata
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class MessageProcessor:
    """
    Main message processor coordinator.
    
    Processes Telegram messages through the complete pipeline:
    1. Extract engagement metrics
    2. Calculate HDRB score
    3. Detect crypto mentions
    4. Analyze sentiment
    5. Calculate confidence (Task 4)
    """
    
    def __init__(self, error_handler=None, max_ic: float = 1000.0, confidence_threshold: float = 0.7):
        """
        Initialize message processor.
        
        Args:
            error_handler: ErrorHandler instance for resilient processing
            max_ic: Maximum IC value for HDRB normalization
            confidence_threshold: Threshold for high-confidence classification (default: 0.7)
        """
        self.hdrb_scorer = HDRBScorer(max_ic=max_ic)
        self.crypto_detector = CryptoDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.error_handler = error_handler
        self.confidence_threshold = confidence_threshold
        self.logger = get_logger('MessageProcessor')
        self.logger.info(f"Message processor initialized (confidence_threshold={confidence_threshold})")
    
    def _calculate_confidence(
        self,
        hdrb_score: float,
        crypto_mentions: list[str],
        sentiment_score: float,
        message_length: int
    ) -> float:
        """
        Calculate holistic confidence score.
        
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
            # Component 1: HDRB score (40%) - normalize from 0-100 to 0-1
            hdrb_component = (hdrb_score / 100.0) * 0.4
            
            # Component 2: Crypto relevance (30%) - binary: has mentions or not
            crypto_component = (1.0 if len(crypto_mentions) > 0 else 0.0) * 0.3
            
            # Component 3: Sentiment clarity (20%) - absolute value of sentiment score
            sentiment_clarity = abs(sentiment_score)  # 0.0 to 1.0
            sentiment_component = sentiment_clarity * 0.2
            
            # Component 4: Message length (10%) - normalize to 0-1 (cap at 200 chars)
            length_normalized = min(1.0, message_length / 200.0)
            length_component = length_normalized * 0.1
            
            # Calculate total confidence
            confidence = hdrb_component + crypto_component + sentiment_component + length_component
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            self.logger.debug(
                f"Confidence calculation: HDRB={hdrb_component:.2f}, "
                f"crypto={crypto_component:.2f}, sentiment={sentiment_component:.2f}, "
                f"length={length_component:.2f} → total={confidence:.2f}"
            )
            
            return confidence
            
        except Exception as e:
            self.logger.warning(f"Error calculating confidence: {e}")
            return 0.0
    
    def _extract_engagement_metrics(self, message_obj: Any) -> dict:
        """
        Extract engagement metrics from Telegram message object.
        
        Args:
            message_obj: Telethon message object
            
        Returns:
            Dictionary with forwards, reactions, replies, views
        """
        try:
            # Extract forwards (default to 0 if None)
            forwards = getattr(message_obj, 'forwards', 0) or 0
            
            # Extract reactions (count all reaction types)
            reactions = 0
            if hasattr(message_obj, 'reactions') and message_obj.reactions:
                if hasattr(message_obj.reactions, 'results'):
                    reactions = sum(r.count for r in message_obj.reactions.results)
            
            # Extract replies
            replies = 0
            if hasattr(message_obj, 'replies') and message_obj.replies:
                replies = getattr(message_obj.replies, 'replies', 0) or 0
            
            # Extract views
            views = getattr(message_obj, 'views', 0) or 0
            
            self.logger.debug(
                f"Engagement metrics extracted: forwards={forwards}, "
                f"reactions={reactions}, replies={replies}, views={views}"
            )
            
            return {
                'forwards': forwards,
                'reactions': reactions,
                'replies': replies,
                'views': views
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting engagement metrics: {e}. Using zeros.")
            return {
                'forwards': 0,
                'reactions': 0,
                'replies': 0,
                'views': 0
            }
    
    async def process_message(
        self,
        channel_name: str,
        message_text: str,
        timestamp: datetime,
        message_id: int,
        message_obj: Any,
        channel_id: str = ""
    ) -> ProcessedMessage:
        """
        Process message through complete pipeline.
        
        Args:
            channel_name: Name of the channel
            message_text: Message text content
            timestamp: Message timestamp
            message_id: Message ID
            message_obj: Telethon message object for metric extraction
            channel_id: Channel ID (optional)
            
        Returns:
            ProcessedMessage with all analysis complete
        """
        start_time = time.perf_counter()
        
        self.logger.info(f"Processing message ID: {message_id} from channel: {channel_name}")
        
        try:
            # Step 1: Extract engagement metrics
            metrics = self._extract_engagement_metrics(message_obj)
            
            self.logger.info(
                f"Engagement metrics: forwards={metrics['forwards']}, "
                f"reactions={metrics['reactions']}, replies={metrics['replies']}"
            )
            
            # Step 2: Calculate HDRB score
            hdrb_result = self.hdrb_scorer.calculate_score(
                forwards=metrics['forwards'],
                reactions=metrics['reactions'],
                replies=metrics['replies']
            )
            
            # Step 3: Detect crypto mentions
            crypto_mentions = self.crypto_detector.detect_mentions(message_text)
            is_crypto_relevant = self.crypto_detector.is_crypto_relevant(crypto_mentions, message_text)
            
            # Step 4: Analyze sentiment
            sentiment, sentiment_score = self.sentiment_analyzer.analyze(message_text)
            
            # Step 5: Calculate confidence
            confidence = self._calculate_confidence(
                hdrb_score=hdrb_result['normalized_score'],
                crypto_mentions=crypto_mentions,
                sentiment_score=sentiment_score,
                message_length=len(message_text)
            )
            
            is_high_confidence = confidence >= self.confidence_threshold
            
            confidence_label = "HIGH" if is_high_confidence else "LOW"
            self.logger.info(f"Confidence: {confidence_label} ({confidence:.2f})")
            
            # Calculate processing time
            processing_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            self.logger.info(f"Processing completed in {processing_time:.2f}ms")
            
            # Create processed message
            processed = ProcessedMessage(
                channel_id=channel_id,
                channel_name=channel_name,
                message_id=message_id,
                message_text=message_text,
                timestamp=timestamp,
                forwards=metrics['forwards'],
                reactions=metrics['reactions'],
                replies=metrics['replies'],
                views=metrics['views'],
                hdrb_score=hdrb_result['normalized_score'],
                hdrb_raw=hdrb_result['raw_ic'],
                crypto_mentions=crypto_mentions,
                is_crypto_relevant=is_crypto_relevant,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                confidence=confidence,
                is_high_confidence=is_high_confidence,
                processing_time_ms=processing_time
            )
            
            return processed
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Error processing message: {e}")
            
            # Return message with error
            return ProcessedMessage(
                channel_id=channel_id,
                channel_name=channel_name,
                message_id=message_id,
                message_text=message_text,
                timestamp=timestamp,
                forwards=0,
                reactions=0,
                replies=0,
                views=0,
                hdrb_score=0.0,
                hdrb_raw=0.0,
                crypto_mentions=[],
                is_crypto_relevant=False,
                sentiment='neutral',
                sentiment_score=0.0,
                processing_time_ms=processing_time,
                error=str(e)
            )

"""
Message processor with HDRB scoring and analysis.

Coordinates the complete message processing pipeline.

Enhanced with Task 6:
- Reputation-based confidence adjustment
- Multi-dimensional ROI prediction
- Prediction caching for performance
"""

import time
from datetime import datetime
from typing import Any, Optional, Dict

from utils.logger import get_logger
from services.analytics.hdrb_scorer import HDRBScorer
from services.message_processing.crypto_detector import CryptoDetector
from services.analytics.sentiment_analyzer import SentimentAnalyzer
from services.message_processing.processed_message import ProcessedMessage
# Task 6: Reputation integration
from utils.prediction_cache import PredictionCache


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
    
    def __init__(self, error_handler=None, max_ic: float = 1000.0, confidence_threshold: float = 0.7,
                 reputation_engine=None, event_bus=None):
        """
        Initialize message processor.
        
        FIXED: Issue #11 - Uses EventPublisher for safe event publishing
        
        Args:
            error_handler: ErrorHandler instance for resilient processing
            max_ic: Maximum IC value for HDRB normalization
            confidence_threshold: Threshold for high-confidence classification (default: 0.7)
            reputation_engine: Optional ReputationEngine for confidence adjustment (Task 6)
            event_bus: Optional EventBus for publishing events (Task 6)
        """
        self.hdrb_scorer = HDRBScorer(max_ic=max_ic)
        self.crypto_detector = CryptoDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.error_handler = error_handler
        self.confidence_threshold = confidence_threshold
        self.logger = get_logger('MessageProcessor')
        
        # Task 6: Reputation integration and event publishing
        self.reputation_engine = reputation_engine
        self.event_bus = event_bus
        self.prediction_cache = PredictionCache(ttl_seconds=300, logger=self.logger)  # 5 min cache
        
        # FIXED: Issue #11 - Use EventPublisher with task tracking
        from utils.async_helpers import EventPublisher
        self.event_publisher = EventPublisher(event_bus, "MessageProcessor") if event_bus else None
        
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
    
    def _publish_prediction_event(
        self,
        channel_name: str,
        crypto_mentions: list[str],
        reputation_data: Dict[str, Any],
        confidence: float
    ) -> None:
        """
        Publish PredictionMadeEvent for analytics (Task 6).
        
        Args:
            channel_name: Channel name
            crypto_mentions: List of detected crypto mentions
            reputation_data: Reputation data dictionary
            confidence: Adjusted confidence score
        """
        try:
            from domain.events import PredictionMadeEvent
            from datetime import datetime, timezone
            
            # Use first crypto mention as primary symbol
            primary_symbol = crypto_mentions[0] if crypto_mentions else "unknown"
            
            event = PredictionMadeEvent(
                channel_name=channel_name,
                coin_symbol=primary_symbol,
                address="",  # Will be filled by address extractor later
                overall_prediction=reputation_data['expected_roi'],
                coin_specific_prediction=None,  # TODO: Implement coin-specific predictions
                cross_channel_prediction=None,  # TODO: Implement cross-channel predictions
                weighted_prediction=reputation_data['expected_roi'],
                confidence_interval=confidence,
                prediction_source=reputation_data['prediction_source'],
                timestamp=datetime.now(timezone.utc),
                metadata={
                    'reputation_score': reputation_data['reputation_score'],
                    'reputation_tier': reputation_data['reputation_tier'],
                    'sharpe_ratio': reputation_data['sharpe_ratio'],
                    'adjustment_factor': reputation_data['adjustment_factor']
                }
            )
            
            # Publish event safely (handles both sync and async contexts)
            self._publish_event_safe(event)
            
        except Exception as e:
            self.logger.warning(f"Failed to publish prediction event: {e}")
    
    def _publish_event_safe(self, event):
        """
        Publish event safely from any context (sync or async).
        
        FIXED: Issue #11 - Async/Sync Boundary Conflicts
        Uses EventPublisher with task tracking to prevent GC.
        
        Args:
            event: Event to publish
        """
        if not self.event_publisher:
            return
        
        self.event_publisher.publish_safe(event)
    
    def _adjust_confidence_with_reputation(
        self,
        base_confidence: float,
        channel_name: str
    ) -> tuple[float, Dict[str, Any]]:
        """
        Adjust confidence based on channel reputation (Task 6).
        
        Uses Sharpe ratio-based adjustment:
        - Elite (Sharpe >1.5): +25% confidence boost
        - Excellent (Sharpe 1.0-1.5): +20% confidence boost
        - Good (Sharpe 0.5-1.0): +10% confidence boost
        - Average (Sharpe 0.0-0.5): No adjustment
        - Poor (Sharpe <0.0): -10% confidence reduction
        
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
            cached = self.prediction_cache.get(channel_name)
            if cached:
                reputation = cached
                self.logger.debug(f"Cache hit for {channel_name}")
            else:
                # Load from reputation engine
                reputation = self.reputation_engine.get_reputation(channel_name)
                if reputation:
                    self.prediction_cache.set(channel_name, reputation)
                    self.logger.debug(f"Cached reputation for {channel_name}")
            
            if not reputation:
                return base_confidence, reputation_data
            
            # Update reputation data
            reputation_data['reputation_score'] = reputation.reputation_score
            reputation_data['reputation_tier'] = reputation.reputation_tier
            reputation_data['expected_roi'] = reputation.expected_roi
            reputation_data['sharpe_ratio'] = reputation.sharpe_ratio
            reputation_data['prediction_source'] = 'overall'
            
            # Calculate adjustment factor based on Sharpe ratio (MCP-validated)
            sharpe = reputation.sharpe_ratio
            if sharpe > 1.5:
                adjustment_factor = 1.25  # Elite
            elif sharpe >= 1.0:
                adjustment_factor = 1.20  # Excellent
            elif sharpe >= 0.5:
                adjustment_factor = 1.10  # Good
            elif sharpe >= 0.0:
                adjustment_factor = 1.0   # Average
            else:
                adjustment_factor = 0.90  # Poor
            
            reputation_data['adjustment_factor'] = adjustment_factor
            
            # Apply adjustment
            adjusted_confidence = base_confidence * adjustment_factor
            adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))  # Clamp to [0, 1]
            
            self.logger.info(
                f"Confidence adjusted: {base_confidence:.2f} → {adjusted_confidence:.2f} "
                f"({reputation.reputation_tier}, Sharpe={sharpe:.2f}, factor={adjustment_factor:.2f})"
            )
            
            return adjusted_confidence, reputation_data
            
        except Exception as e:
            self.logger.warning(f"Error adjusting confidence with reputation: {e}")
            return base_confidence, reputation_data
    
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
                self.logger.debug(f"Reactions object: {message_obj.reactions}")
                self.logger.debug(f"Reactions type: {type(message_obj.reactions)}")
                self.logger.debug(f"Reactions dir: {dir(message_obj.reactions)}")
                if hasattr(message_obj.reactions, 'results'):
                    self.logger.debug(f"Reactions results: {message_obj.reactions.results}")
                    reactions = sum(r.count for r in message_obj.reactions.results)
            else:
                self.logger.debug(f"No reactions attribute or reactions is None")
            
            # Extract replies
            replies = 0
            if hasattr(message_obj, 'replies') and message_obj.replies:
                self.logger.debug(f"Replies object: {message_obj.replies}")
                self.logger.debug(f"Replies type: {type(message_obj.replies)}")
                self.logger.debug(f"Replies dir: {dir(message_obj.replies)}")
                replies = getattr(message_obj.replies, 'replies', 0) or 0
            else:
                self.logger.debug(f"No replies attribute or replies is None")
            
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
            
            # Step 4: Analyze sentiment (using NLP-enhanced analysis)
            sentiment_result = self.sentiment_analyzer.analyze_detailed(message_text)
            sentiment = sentiment_result.label
            sentiment_score = sentiment_result.score
            
            # Log sentiment analysis details
            self.logger.info(
                f"Sentiment: {sentiment} ({sentiment_score:+.2f}) | "
                f"Method: {sentiment_result.method} | "
                f"Confidence: {sentiment_result.confidence:.2f} | "
                f"Time: {sentiment_result.processing_time_ms:.1f}ms"
            )
            
            # Step 5: Calculate base confidence
            base_confidence = self._calculate_confidence(
                hdrb_score=hdrb_result['normalized_score'],
                crypto_mentions=crypto_mentions,
                sentiment_score=sentiment_score,
                message_length=len(message_text)
            )
            
            # Task 6: Adjust confidence with reputation
            confidence, reputation_data = self._adjust_confidence_with_reputation(
                base_confidence,
                channel_name
            )
            
            # Task 6: Publish PredictionMadeEvent if we have crypto mentions
            if crypto_mentions and self.event_bus and reputation_data['prediction_source'] != 'none':
                self._publish_prediction_event(
                    channel_name=channel_name,
                    crypto_mentions=crypto_mentions,
                    reputation_data=reputation_data,
                    confidence=confidence
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
                # Task 6: Reputation fields
                channel_reputation_score=reputation_data['reputation_score'],
                channel_reputation_tier=reputation_data['reputation_tier'],
                channel_expected_roi=reputation_data['expected_roi'],
                prediction_source=reputation_data['prediction_source'],
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

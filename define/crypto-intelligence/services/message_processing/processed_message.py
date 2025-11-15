"""Processed message data structure."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    
    # Confidence
    confidence: float = 0.0
    is_high_confidence: bool = False
    
    # Reputation-based fields
    channel_reputation_score: float = 0.0
    channel_reputation_tier: str = "Unproven"
    channel_expected_roi: float = 1.5
    prediction_source: str = "none"
    
    # Processing metadata
    processing_time_ms: float = 0.0
    error: Optional[str] = None

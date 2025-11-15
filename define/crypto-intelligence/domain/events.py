"""Event classes for event-driven architecture.

These events enable loose coupling between components using the observer pattern.
All events are immutable dataclasses for thread safety.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class SignalStartedEvent:
    """
    Event emitted when a new signal tracking starts.
    
    Published by: OutcomeTracker
    Subscribers: Logger, Monitoring systems
    """
    signal_id: str
    address: str
    chain: str
    symbol: str
    entry_price: float
    entry_timestamp: datetime
    channel_name: str
    message_id: int
    signal_number: int  # 1, 2, 3, ... for repeated mentions
    previous_signals: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckpointReachedEvent:
    """
    Event emitted when a tracking checkpoint is reached (1h, 4h, 24h, 3d, 7d, 30d).
    
    Published by: PerformanceTracker or scheduled task
    Subscribers: OutcomeTracker
    """
    signal_id: str
    address: str
    checkpoint_name: str  # "1h", "4h", "24h", "3d", "7d", "30d"
    checkpoint_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckpointUpdatedEvent:
    """
    Event emitted when checkpoint data is updated with current price/ROI.
    
    Published by: OutcomeTracker
    Subscribers: Logger, DataOutput
    """
    signal_id: str
    address: str
    checkpoint_name: str
    current_price: float
    roi_percentage: float
    roi_multiplier: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SignalCompletedEvent:
    """
    Event emitted when a signal completes (30d reached or stop condition met).
    
    Published by: OutcomeTracker
    Subscribers: ReputationEngine (for TD learning)
    """
    signal_id: str
    address: str
    channel_name: str
    symbol: str
    entry_price: float
    ath_price: float
    ath_multiplier: float
    days_to_ath: float
    is_winner: bool
    outcome_category: str  # "winner", "loser", "break_even"
    signal_number: int
    entry_timestamp: datetime
    completion_timestamp: datetime
    market_tier: str
    all_checkpoints: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReputationUpdatedEvent:
    """
    Event emitted when channel reputation changes significantly (>5 points).
    
    Published by: ReputationEngine
    Subscribers: DataOutput, Logger
    """
    channel_name: str
    old_reputation_score: float
    new_reputation_score: float
    old_tier: str
    new_tier: str
    change_magnitude: float
    timestamp: datetime
    # Detailed metrics
    win_rate: float
    avg_roi: float
    expected_roi: float
    sharpe_ratio: float
    total_signals: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PredictionMadeEvent:
    """
    Event emitted when a multi-dimensional prediction is made.
    
    Published by: MessageProcessor
    Subscribers: Logger, Analytics
    """
    channel_name: str
    coin_symbol: str
    address: str
    overall_prediction: float
    coin_specific_prediction: Optional[float]
    cross_channel_prediction: Optional[float]
    weighted_prediction: float
    confidence_interval: float
    prediction_source: str  # "overall", "coin-specific", "multi-dimensional"
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

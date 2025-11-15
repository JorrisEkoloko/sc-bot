"""Signal outcome data models.

Data classes for tracking signal outcomes with ROI at checkpoints.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict


# Checkpoint intervals for ROI tracking
CHECKPOINTS = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30)
}


@dataclass
class CheckpointData:
    """Data for a single checkpoint in signal tracking."""
    timestamp: Optional[datetime] = None
    price: float = 0.0
    roi_percentage: float = 0.0  # e.g., 225.2 for 225.2% gain
    roi_multiplier: float = 0.0  # e.g., 3.252 for 3.252x gain
    reached: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'price': self.price,
            'roi_percentage': self.roi_percentage,
            'roi_multiplier': self.roi_multiplier,
            'reached': self.reached
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointData':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            price=data.get('price', 0.0),
            roi_percentage=data.get('roi_percentage', 0.0),
            roi_multiplier=data.get('roi_multiplier', 0.0),
            reached=data.get('reached', False)
        )


@dataclass
class SignalOutcome:
    """Complete signal outcome with ROI tracking at checkpoints.
    
    Supports fresh start re-monitoring: same coin can be tracked multiple times
    with different entry prices (Signal #1, #2, #3, etc.)
    """
    # Identity
    message_id: int
    channel_name: str
    address: str
    symbol: Optional[str] = None
    
    # Fresh start re-monitoring (Task 5)
    signal_number: int = 1  # 1st, 2nd, 3rd mention of this coin
    previous_signals: list = field(default_factory=list)  # List of previous signal IDs for this coin
    
    # Entry data
    entry_price: float = 0.0
    entry_timestamp: Optional[datetime] = None
    entry_confidence: float = 0.0
    entry_source: str = ""  # "message_text", "cryptocompare", "current_price"
    
    # Signal quality
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    hdrb_score: float = 0.0
    confidence: float = 0.0
    
    # Checkpoints (ROI at each time interval)
    checkpoints: Dict[str, CheckpointData] = field(default_factory=dict)
    
    # Outcome data (ATH = All-Time High)
    ath_price: float = 0.0
    ath_multiplier: float = 0.0  # Best ROI achieved
    ath_timestamp: Optional[datetime] = None
    days_to_ath: float = 0.0
    current_price: float = 0.0
    current_multiplier: float = 0.0
    
    # Time-based performance (Day 7 + Day 30 checkpoints)
    day_7_price: float = 0.0  # Price at day 7 checkpoint
    day_7_multiplier: float = 0.0  # ROI multiplier at day 7
    day_7_classification: str = ""  # Classification at day 7 (MOON/WINNER/GOOD/BREAK-EVEN/LOSER)
    day_30_price: float = 0.0  # Price at day 30 checkpoint
    day_30_multiplier: float = 0.0  # ROI multiplier at day 30
    day_30_classification: str = ""  # Final classification at day 30
    trajectory: str = ""  # Performance trend ("improved" or "crashed")
    peak_timing: str = ""  # When ATH occurred ("early_peaker" or "late_peaker")
    
    # Market context
    market_tier: str = ""  # micro, small, mid, large
    risk_level: str = ""
    risk_score: float = 0.0
    
    # Status
    status: str = "in_progress"  # "in_progress", "completed", "data_unavailable"
    is_complete: bool = False
    completion_reason: str = ""  # "30d_elapsed", "90%_loss", "zero_volume", "historical"
    is_winner: bool = False  # ROI ≥ 1.5x (50% gain)
    outcome_category: str = ""  # moon, great, good, moderate, break_even, loss
    
    def __post_init__(self):
        """Initialize checkpoints if not provided."""
        if not self.checkpoints:
            self.checkpoints = {
                name: CheckpointData() for name in CHECKPOINTS.keys()
            }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'message_id': self.message_id,
            'channel_name': self.channel_name,
            'address': self.address,
            'symbol': self.symbol,
            'signal_number': self.signal_number,
            'previous_signals': self.previous_signals,
            'entry_price': self.entry_price,
            'entry_timestamp': self.entry_timestamp.isoformat() if self.entry_timestamp else None,
            'entry_confidence': self.entry_confidence,
            'entry_source': self.entry_source,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'hdrb_score': self.hdrb_score,
            'confidence': self.confidence,
            'checkpoints': {name: cp.to_dict() for name, cp in self.checkpoints.items()},
            'ath_price': self.ath_price,
            'ath_multiplier': self.ath_multiplier,
            'ath_timestamp': self.ath_timestamp.isoformat() if self.ath_timestamp else None,
            'days_to_ath': self.days_to_ath,
            'current_price': self.current_price,
            'current_multiplier': self.current_multiplier,
            'day_7_price': self.day_7_price,
            'day_7_multiplier': self.day_7_multiplier,
            'day_7_classification': self.day_7_classification,
            'day_30_price': self.day_30_price,
            'day_30_multiplier': self.day_30_multiplier,
            'day_30_classification': self.day_30_classification,
            'trajectory': self.trajectory,
            'peak_timing': self.peak_timing,
            'market_tier': self.market_tier,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'status': self.status,
            'is_complete': self.is_complete,
            'completion_reason': self.completion_reason,
            'is_winner': self.is_winner,
            'outcome_category': self.outcome_category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SignalOutcome':
        """Create from dictionary."""
        checkpoints = {
            name: CheckpointData.from_dict(cp_data)
            for name, cp_data in data.get('checkpoints', {}).items()
        }
        
        return cls(
            message_id=data['message_id'],
            channel_name=data['channel_name'],
            address=data['address'],
            symbol=data.get('symbol'),
            signal_number=data.get('signal_number', 1),
            previous_signals=data.get('previous_signals', []),
            entry_price=data.get('entry_price', 0.0),
            entry_timestamp=datetime.fromisoformat(data['entry_timestamp']) if data.get('entry_timestamp') else None,
            entry_confidence=data.get('entry_confidence', 0.0),
            entry_source=data.get('entry_source', ''),
            sentiment=data.get('sentiment', 'neutral'),
            sentiment_score=data.get('sentiment_score', 0.0),
            hdrb_score=data.get('hdrb_score', 0.0),
            confidence=data.get('confidence', 0.0),
            checkpoints=checkpoints,
            ath_price=data.get('ath_price', 0.0),
            ath_multiplier=data.get('ath_multiplier', 0.0),
            ath_timestamp=datetime.fromisoformat(data['ath_timestamp']) if data.get('ath_timestamp') else None,
            days_to_ath=data.get('days_to_ath', 0.0),
            current_price=data.get('current_price', 0.0),
            current_multiplier=data.get('current_multiplier', 0.0),
            day_7_price=data.get('day_7_price', 0.0),
            day_7_multiplier=data.get('day_7_multiplier', 0.0),
            day_7_classification=data.get('day_7_classification', ''),
            day_30_price=data.get('day_30_price', 0.0),
            day_30_multiplier=data.get('day_30_multiplier', 0.0),
            day_30_classification=data.get('day_30_classification', ''),
            trajectory=data.get('trajectory', ''),
            peak_timing=data.get('peak_timing', ''),
            market_tier=data.get('market_tier', ''),
            risk_level=data.get('risk_level', ''),
            risk_score=data.get('risk_score', 0.0),
            status=data.get('status', 'in_progress'),
            is_complete=data.get('is_complete', False),
            completion_reason=data.get('completion_reason', ''),
            is_winner=data.get('is_winner', False),
            outcome_category=data.get('outcome_category', '')
        )

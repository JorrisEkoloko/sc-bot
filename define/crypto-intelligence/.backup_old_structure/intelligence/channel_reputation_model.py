"""Channel reputation data models.

Data classes for storing channel reputation metrics based on ROI outcomes.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TierPerformance:
    """Performance metrics for a specific market cap tier."""
    total_calls: int = 0
    winning_calls: int = 0  # ROI ≥ 2.0x
    win_rate: float = 0.0
    avg_roi: float = 0.0
    sharpe_ratio: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_calls': self.total_calls,
            'winning_calls': self.winning_calls,
            'win_rate': self.win_rate,
            'avg_roi': self.avg_roi,
            'sharpe_ratio': self.sharpe_ratio
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TierPerformance':
        """Create from dictionary."""
        return cls(
            total_calls=data.get('total_calls', 0),
            winning_calls=data.get('winning_calls', 0),
            win_rate=data.get('win_rate', 0.0),
            avg_roi=data.get('avg_roi', 0.0),
            sharpe_ratio=data.get('sharpe_ratio', 0.0)
        )


@dataclass
class ChannelReputation:
    """Channel reputation based on ROI outcomes."""
    # Identity
    channel_name: str
    
    # Outcome metrics
    total_signals: int = 0
    winning_signals: int = 0  # ROI ≥ 2.0x (100% gain)
    losing_signals: int = 0  # ROI < 1.0x
    neutral_signals: int = 0  # 1.0x ≤ ROI < 2.0x
    win_rate: float = 0.0  # % of signals with ROI ≥ 2.0x
    
    # ROI metrics (all in multiplier format)
    average_roi: float = 0.0  # Mean ROI multiplier (e.g., 1.85 = 85% average gain)
    median_roi: float = 0.0  # Median ROI multiplier
    best_roi: float = 0.0  # Best ROI multiplier
    worst_roi: float = 0.0  # Worst ROI multiplier
    roi_std_dev: float = 0.0  # Standard deviation of ROI
    
    # Risk-adjusted metrics
    sharpe_ratio: float = 0.0  # (avg_roi - 1.0) / std_dev
    risk_adjusted_roi: float = 0.0  # ROI weighted by risk level
    
    # Time metrics
    avg_time_to_ath: float = 0.0  # Average days to reach ATH
    avg_time_to_2x: float = 0.0  # Average days to 2x (winners only)
    speed_score: float = 0.0  # 0-100, faster = higher
    
    # Confidence metrics
    avg_confidence: float = 0.0  # Average entry price confidence
    avg_hdrb_score: float = 0.0  # Average HDRB score
    
    # Tier-specific performance
    tier_performance: Dict[str, TierPerformance] = field(default_factory=dict)
    
    # Reputation score
    reputation_score: float = 0.0  # 0-100
    reputation_tier: str = "Unproven"  # Elite/Excellent/Good/Average/Poor/Unreliable/Unproven
    
    # Learning data (for TD learning - Task 3)
    expected_roi: float = 1.0  # TD learning prediction (multiplier format)
    prediction_error_history: List[float] = field(default_factory=list)
    
    # Metadata
    first_signal_date: Optional[datetime] = None
    last_signal_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize tier performance if not provided."""
        if not self.tier_performance:
            self.tier_performance = {
                'micro': TierPerformance(),
                'small': TierPerformance(),
                'mid': TierPerformance(),
                'large': TierPerformance()
            }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'channel_name': self.channel_name,
            'total_signals': self.total_signals,
            'winning_signals': self.winning_signals,
            'losing_signals': self.losing_signals,
            'neutral_signals': self.neutral_signals,
            'win_rate': self.win_rate,
            'average_roi': self.average_roi,
            'median_roi': self.median_roi,
            'best_roi': self.best_roi,
            'worst_roi': self.worst_roi,
            'roi_std_dev': self.roi_std_dev,
            'sharpe_ratio': self.sharpe_ratio,
            'risk_adjusted_roi': self.risk_adjusted_roi,
            'avg_time_to_ath': self.avg_time_to_ath,
            'avg_time_to_2x': self.avg_time_to_2x,
            'speed_score': self.speed_score,
            'avg_confidence': self.avg_confidence,
            'avg_hdrb_score': self.avg_hdrb_score,
            'tier_performance': {name: perf.to_dict() for name, perf in self.tier_performance.items()},
            'reputation_score': self.reputation_score,
            'reputation_tier': self.reputation_tier,
            'expected_roi': self.expected_roi,
            'prediction_error_history': self.prediction_error_history,
            'first_signal_date': self.first_signal_date.isoformat() if self.first_signal_date else None,
            'last_signal_date': self.last_signal_date.isoformat() if self.last_signal_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelReputation':
        """Create from dictionary."""
        tier_performance = {
            name: TierPerformance.from_dict(perf_data)
            for name, perf_data in data.get('tier_performance', {}).items()
        }
        
        return cls(
            channel_name=data['channel_name'],
            total_signals=data.get('total_signals', 0),
            winning_signals=data.get('winning_signals', 0),
            losing_signals=data.get('losing_signals', 0),
            neutral_signals=data.get('neutral_signals', 0),
            win_rate=data.get('win_rate', 0.0),
            average_roi=data.get('average_roi', 0.0),
            median_roi=data.get('median_roi', 0.0),
            best_roi=data.get('best_roi', 0.0),
            worst_roi=data.get('worst_roi', 0.0),
            roi_std_dev=data.get('roi_std_dev', 0.0),
            sharpe_ratio=data.get('sharpe_ratio', 0.0),
            risk_adjusted_roi=data.get('risk_adjusted_roi', 0.0),
            avg_time_to_ath=data.get('avg_time_to_ath', 0.0),
            avg_time_to_2x=data.get('avg_time_to_2x', 0.0),
            speed_score=data.get('speed_score', 0.0),
            avg_confidence=data.get('avg_confidence', 0.0),
            avg_hdrb_score=data.get('avg_hdrb_score', 0.0),
            tier_performance=tier_performance,
            reputation_score=data.get('reputation_score', 0.0),
            reputation_tier=data.get('reputation_tier', 'Unproven'),
            expected_roi=data.get('expected_roi', 1.0),
            prediction_error_history=data.get('prediction_error_history', []),
            first_signal_date=datetime.fromisoformat(data['first_signal_date']) if data.get('first_signal_date') else None,
            last_signal_date=datetime.fromisoformat(data['last_signal_date']) if data.get('last_signal_date') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )


# Reputation tier thresholds
REPUTATION_TIERS = {
    "Elite": (90, 100),      # Top 10% performers
    "Excellent": (75, 90),   # Strong performance
    "Good": (60, 75),        # Above average
    "Average": (40, 60),     # Mixed results
    "Poor": (20, 40),        # Below average
    "Unreliable": (0, 20),   # Consistently poor
    "Unproven": None         # < 10 signals
}

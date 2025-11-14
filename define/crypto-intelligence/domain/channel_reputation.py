"""Channel reputation data models.

Data classes for storing channel reputation metrics based on ROI outcomes.

Enhanced with multi-dimensional TD learning:
- Overall channel TD learning
- Coin-specific TD learning
- Cross-channel insights
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PredictionError:
    """Detailed prediction error record for TD learning."""
    timestamp: str  # ISO format
    signal_id: str
    coin_symbol: str
    coin_address: str
    predicted_roi: float
    actual_roi: float
    error: float  # actual - predicted
    error_percentage: float  # (error / predicted) * 100
    entry_price: float
    ath_price: float
    days_to_ath: float
    outcome_category: str  # winner/loser/break_even
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp,
            'signal_id': self.signal_id,
            'coin_symbol': self.coin_symbol,
            'coin_address': self.coin_address,
            'predicted_roi': self.predicted_roi,
            'actual_roi': self.actual_roi,
            'error': self.error,
            'error_percentage': self.error_percentage,
            'entry_price': self.entry_price,
            'ath_price': self.ath_price,
            'days_to_ath': self.days_to_ath,
            'outcome_category': self.outcome_category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PredictionError':
        """Create from dictionary."""
        return cls(
            timestamp=data['timestamp'],
            signal_id=data['signal_id'],
            coin_symbol=data['coin_symbol'],
            coin_address=data['coin_address'],
            predicted_roi=data['predicted_roi'],
            actual_roi=data['actual_roi'],
            error=data['error'],
            error_percentage=data['error_percentage'],
            entry_price=data['entry_price'],
            ath_price=data['ath_price'],
            days_to_ath=data['days_to_ath'],
            outcome_category=data['outcome_category']
        )


@dataclass
class CoinSpecificPerformance:
    """Performance metrics for a specific coin called by this channel.
    
    Enables coin-specific TD learning: "Eric calling AVICI typically delivers 3.112x"
    """
    symbol: str
    address: str
    total_mentions: int = 0
    signals: List[str] = field(default_factory=list)  # List of signal IDs
    
    # ROI metrics
    average_roi: float = 0.0
    expected_roi: float = 1.0  # TD learning prediction for this coin
    win_rate: float = 0.0
    best_roi: float = 0.0
    worst_roi: float = 0.0
    
    # TD Learning tracking
    prediction_error_history: List[PredictionError] = field(default_factory=list)
    total_predictions: int = 0
    correct_predictions: int = 0  # Within 10% of actual
    overestimations: int = 0
    underestimations: int = 0
    mean_absolute_error: float = 0.0
    
    # Metadata
    last_mentioned: Optional[datetime] = None
    days_since_last_mention: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'address': self.address,
            'total_mentions': self.total_mentions,
            'signals': self.signals,
            'average_roi': self.average_roi,
            'expected_roi': self.expected_roi,
            'win_rate': self.win_rate,
            'best_roi': self.best_roi,
            'worst_roi': self.worst_roi,
            'prediction_error_history': [err.to_dict() for err in self.prediction_error_history],
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'overestimations': self.overestimations,
            'underestimations': self.underestimations,
            'mean_absolute_error': self.mean_absolute_error,
            'last_mentioned': self.last_mentioned.isoformat() if self.last_mentioned else None,
            'days_since_last_mention': self.days_since_last_mention
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CoinSpecificPerformance':
        """Create from dictionary."""
        return cls(
            symbol=data['symbol'],
            address=data['address'],
            total_mentions=data.get('total_mentions', 0),
            signals=data.get('signals', []),
            average_roi=data.get('average_roi', 0.0),
            expected_roi=data.get('expected_roi', 1.0),
            win_rate=data.get('win_rate', 0.0),
            best_roi=data.get('best_roi', 0.0),
            worst_roi=data.get('worst_roi', 0.0),
            prediction_error_history=[
                PredictionError.from_dict(err_data) 
                for err_data in data.get('prediction_error_history', [])
            ],
            total_predictions=data.get('total_predictions', 0),
            correct_predictions=data.get('correct_predictions', 0),
            overestimations=data.get('overestimations', 0),
            underestimations=data.get('underestimations', 0),
            mean_absolute_error=data.get('mean_absolute_error', 0.0),
            last_mentioned=datetime.fromisoformat(data['last_mentioned']) if data.get('last_mentioned') else None,
            days_since_last_mention=data.get('days_since_last_mention', 0)
        )


@dataclass
class TierPerformance:
    """Performance metrics for a specific market cap tier."""
    total_calls: int = 0
    winning_calls: int = 0  # ROI ≥ 1.5x
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
    winning_signals: int = 0  # ROI ≥ 1.5x (50% gain)
    losing_signals: int = 0  # ROI < 1.0x
    neutral_signals: int = 0  # 1.0x ≤ ROI < 1.5x
    win_rate: float = 0.0  # % of signals with ROI ≥ 1.5x
    
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
    
    # Level 1: Overall Channel TD Learning
    expected_roi: float = 1.5  # TD learning prediction (multiplier format), start at 1.5x (neutral)
    prediction_error_history: List[PredictionError] = field(default_factory=list)  # ALL errors with metadata
    total_predictions: int = 0
    correct_predictions: int = 0  # Within 10% of actual
    overestimations: int = 0
    underestimations: int = 0
    mean_absolute_error: float = 0.0
    mean_squared_error: float = 0.0
    
    # Level 2: Coin-Specific TD Learning
    coin_specific_performance: Dict[str, CoinSpecificPerformance] = field(default_factory=dict)
    
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
            'prediction_error_history': [err.to_dict() for err in self.prediction_error_history],
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'overestimations': self.overestimations,
            'underestimations': self.underestimations,
            'mean_absolute_error': self.mean_absolute_error,
            'mean_squared_error': self.mean_squared_error,
            'coin_specific_performance': {
                address: perf.to_dict() 
                for address, perf in self.coin_specific_performance.items()
            },
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
        
        # Handle both old format (List[float]) and new format (List[PredictionError])
        prediction_error_history = []
        error_history_data = data.get('prediction_error_history', [])
        if error_history_data and isinstance(error_history_data[0], dict):
            prediction_error_history = [
                PredictionError.from_dict(err_data)
                for err_data in error_history_data
            ]
        # If old format (List[float]), ignore it and start fresh
        
        coin_specific_performance = {
            address: CoinSpecificPerformance.from_dict(perf_data)
            for address, perf_data in data.get('coin_specific_performance', {}).items()
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
            expected_roi=data.get('expected_roi', 1.5),
            prediction_error_history=prediction_error_history,
            total_predictions=data.get('total_predictions', 0),
            correct_predictions=data.get('correct_predictions', 0),
            overestimations=data.get('overestimations', 0),
            underestimations=data.get('underestimations', 0),
            mean_absolute_error=data.get('mean_absolute_error', 0.0),
            mean_squared_error=data.get('mean_squared_error', 0.0),
            coin_specific_performance=coin_specific_performance,
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

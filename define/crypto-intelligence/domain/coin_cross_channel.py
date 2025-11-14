"""Cross-channel coin performance tracking.

Track how individual coins perform across multiple channels to identify
which channels are best at calling specific coins.

Based on verified TD learning concepts:
- TD Learning: https://en.wikipedia.org/wiki/Temporal_difference_learning
- Reinforcement Learning: https://en.wikipedia.org/wiki/Reinforcement_learning
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ChannelCoinPerformance:
    """How a specific channel performs on a specific coin."""
    channel_name: str
    total_mentions: int = 0
    signals: List[str] = field(default_factory=list)  # List of signal IDs
    average_roi: float = 0.0  # Mean ROI multiplier for this coin from this channel
    best_roi: float = 0.0
    worst_roi: float = 0.0
    win_rate: float = 0.0  # % of signals with ROI ≥ 1.5x
    last_mentioned: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'channel_name': self.channel_name,
            'total_mentions': self.total_mentions,
            'signals': self.signals,
            'average_roi': self.average_roi,
            'best_roi': self.best_roi,
            'worst_roi': self.worst_roi,
            'win_rate': self.win_rate,
            'last_mentioned': self.last_mentioned.isoformat() if self.last_mentioned else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelCoinPerformance':
        """Create from dictionary."""
        return cls(
            channel_name=data['channel_name'],
            total_mentions=data.get('total_mentions', 0),
            signals=data.get('signals', []),
            average_roi=data.get('average_roi', 0.0),
            best_roi=data.get('best_roi', 0.0),
            worst_roi=data.get('worst_roi', 0.0),
            win_rate=data.get('win_rate', 0.0),
            last_mentioned=datetime.fromisoformat(data['last_mentioned']) if data.get('last_mentioned') else None
        )


@dataclass
class CoinCrossChannel:
    """Coin performance across all channels.
    
    Tracks how a specific coin performs when called by different channels,
    enabling identification of which channels are best at calling this coin.
    """
    # Identity
    symbol: str
    address: str
    
    # Cross-channel aggregates
    total_mentions: int = 0
    total_channels: int = 0
    average_roi_all_channels: float = 0.0  # Overall average across all channels
    best_channel_roi: float = 0.0
    worst_channel_roi: float = 0.0
    
    # Channel-specific performance
    channel_performance: Dict[str, ChannelCoinPerformance] = field(default_factory=dict)
    
    # Best/worst channels for this coin
    best_channel: Optional[str] = None
    worst_channel: Optional[str] = None
    
    # Insights
    consensus_strength: float = 0.0  # 0-1, how consistent channels are (low std dev = high consensus)
    recommendation: str = ""  # e.g., "Follow Eric for AVICI calls"
    
    # TD Learning for cross-channel prediction
    expected_roi_cross_channel: float = 1.0  # Prediction based on all channels
    
    # Metadata
    first_mentioned: Optional[datetime] = None
    last_mentioned: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'address': self.address,
            'total_mentions': self.total_mentions,
            'total_channels': self.total_channels,
            'average_roi_all_channels': self.average_roi_all_channels,
            'best_channel_roi': self.best_channel_roi,
            'worst_channel_roi': self.worst_channel_roi,
            'channel_performance': {
                name: perf.to_dict() 
                for name, perf in self.channel_performance.items()
            },
            'best_channel': self.best_channel,
            'worst_channel': self.worst_channel,
            'consensus_strength': self.consensus_strength,
            'recommendation': self.recommendation,
            'expected_roi_cross_channel': self.expected_roi_cross_channel,
            'first_mentioned': self.first_mentioned.isoformat() if self.first_mentioned else None,
            'last_mentioned': self.last_mentioned.isoformat() if self.last_mentioned else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CoinCrossChannel':
        """Create from dictionary."""
        channel_performance = {
            name: ChannelCoinPerformance.from_dict(perf_data)
            for name, perf_data in data.get('channel_performance', {}).items()
        }
        
        return cls(
            symbol=data['symbol'],
            address=data['address'],
            total_mentions=data.get('total_mentions', 0),
            total_channels=data.get('total_channels', 0),
            average_roi_all_channels=data.get('average_roi_all_channels', 0.0),
            best_channel_roi=data.get('best_channel_roi', 0.0),
            worst_channel_roi=data.get('worst_channel_roi', 0.0),
            channel_performance=channel_performance,
            best_channel=data.get('best_channel'),
            worst_channel=data.get('worst_channel'),
            consensus_strength=data.get('consensus_strength', 0.0),
            recommendation=data.get('recommendation', ''),
            expected_roi_cross_channel=data.get('expected_roi_cross_channel', 1.0),
            first_mentioned=datetime.fromisoformat(data['first_mentioned']) if data.get('first_mentioned') else None,
            last_mentioned=datetime.fromisoformat(data['last_mentioned']) if data.get('last_mentioned') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )

"""Domain models for historical price data."""
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class OHLCCandle:
    """Single OHLC candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OHLCCandle':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data.get('volume', 0.0)
        )


@dataclass
class HistoricalPriceData:
    """Historical price data result."""
    symbol: str
    price_at_timestamp: float
    ath_in_window: float
    ath_timestamp: datetime
    days_to_ath: float
    candles: List[OHLCCandle]
    source: str
    cached: bool = False

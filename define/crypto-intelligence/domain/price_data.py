"""Domain model for price data."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PriceData:
    """Price information from API with market intelligence."""
    price_usd: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    liquidity_usd: Optional[float] = None
    pair_created_at: Optional[str] = None
    symbol: Optional[str] = None
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    
    # ATH (All-Time High) data
    ath: Optional[float] = None  # Coin's known all-time high price
    ath_date: Optional[str] = None  # Date when ATH was reached
    ath_change_percentage: Optional[float] = None  # % change from ATH
    
    # Market Intelligence fields
    market_tier: Optional[str] = None  # large, mid, small, micro, unknown
    tier_description: Optional[str] = None  # Human-readable description
    risk_level: Optional[str] = None  # low, moderate, high, extreme
    risk_score: Optional[float] = None  # 0-100 (higher = riskier)
    liquidity_ratio: Optional[float] = None  # liquidity_usd / market_cap
    volume_ratio: Optional[float] = None  # volume_24h / market_cap
    data_completeness: Optional[float] = None  # 0.0-1.0 (0.25 per factor)

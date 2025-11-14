"""Base API client interface."""
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
    
    # Market Intelligence fields (Part 7)
    market_tier: Optional[str] = None  # large, mid, small, micro, unknown
    tier_description: Optional[str] = None  # Human-readable description
    risk_level: Optional[str] = None  # low, moderate, high, extreme
    risk_score: Optional[float] = None  # 0-100 (higher = riskier)
    liquidity_ratio: Optional[float] = None  # liquidity_usd / market_cap
    volume_ratio: Optional[float] = None  # volume_24h / market_cap
    data_completeness: Optional[float] = None  # 0.0-1.0 (0.25 per factor)


class BaseAPIClient:
    """Base class for API clients."""
    
    def __init__(self):
        """Initialize base client."""
        self._session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        elif self._session.closed:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """
        Fetch price data from API.
        
        Args:
            address: Token contract address
            chain: Blockchain name ('evm' or 'solana')
            
        Returns:
            PriceData object or None if fetch fails
        """
        raise NotImplementedError

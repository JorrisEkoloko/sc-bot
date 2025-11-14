"""Base API client interface."""
from typing import Optional
from domain.price_data import PriceData


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

"""Base API client interface."""
from typing import Optional
from domain.price_data import PriceData


class BaseAPIClient:
    """Base class for API clients."""
    
    def __init__(self):
        """
        Initialize base client.
        
        FIXED: Issue #18 - Added session lock for thread safety.
        """
        self._session = None
        self._session_lock = None  # Initialized in async context
    
    async def _get_session(self):
        """
        Get or create aiohttp session (thread-safe).
        
        FIXED: Issue #18 - Resource Lifecycle Conflict
        Uses lock to prevent race conditions in session creation.
        
        Based on double-checked locking pattern.
        """
        # Ensure lock is initialized
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        
        # Double-checked locking
        if self._session is not None and not self._session.closed:
            return self._session
        
        async with self._session_lock:
            # Check again after acquiring lock
            if self._session is not None and not self._session.closed:
                return self._session
            
            # Close old session if it exists but is closed
            if self._session is not None and self._session.closed:
                try:
                    await self._session.close()
                except Exception:
                    pass  # Already closed
            
            # Create new session
            import aiohttp
            self._session = aiohttp.ClientSession()
            return self._session
    
    async def close(self):
        """
        Close aiohttp session (idempotent).
        
        FIXED: Issue #18 - Thread-safe close with lock.
        """
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
    
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

"""Moralis API client (EVM chains).

Verified endpoint: https://docs.moralis.io/
"""
import aiohttp
from typing import Optional

from domain.price_data import PriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class MoralisClient(BaseAPIClient):
    """Moralis API client for EVM chains with persistent session."""
    
    def __init__(self, api_key: str, request_timeout: int = 10, logger=None):
        """
        Initialize with API key.
        
        Args:
            api_key: Moralis API key
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.api_key = api_key
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('MoralisClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price from Moralis API."""
        await self._ensure_session()
        
        url = f"https://deep-index.moralis.io/api/v2/erc20/{address}/price"
        headers = {'X-API-Key': self.api_key}
        
        try:
            async with self._session.get(url, headers=headers, timeout=self.request_timeout) as response:
                self.logger.debug(f"Moralis response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    self.logger.debug(f"Moralis found data for {address}")
                    
                    return PriceData(
                        price_usd=safe_float(data.get('usdPrice'), 0.0),
                        market_cap=safe_float(data.get('usdMarketCap')),
                        volume_24h=safe_float(data.get('24hrVolume')),
                        price_change_24h=safe_float(data.get('24hrPercentChange')),
                        symbol=data.get('tokenSymbol')
                    )
                else:
                    response_text = await response.text()
                    self.logger.warning(f"Moralis HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"Moralis exception for {address}: {e}")
            raise
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

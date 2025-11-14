"""Birdeye API client (Solana-focused).

Verified endpoint: https://docs.birdeye.so/
"""
import aiohttp
from typing import Optional

from domain.price_data import PriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class BirdeyeClient(BaseAPIClient):
    """Birdeye API client for Solana tokens with persistent session."""
    
    def __init__(self, api_key: str, request_timeout: int = 10, logger=None):
        """
        Initialize with API key.
        
        Args:
            api_key: Birdeye API key
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.api_key = api_key
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('BirdeyeClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price from Birdeye API."""
        await self._ensure_session()
        
        url = "https://public-api.birdeye.so/defi/price"
        params = {'address': address}
        headers = {'X-API-KEY': self.api_key}
        
        try:
            async with self._session.get(url, params=params, headers=headers, timeout=self.request_timeout) as response:
                self.logger.debug(f"Birdeye response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success') and data.get('data'):
                        price_data = data['data']
                        self.logger.debug(f"Birdeye found data for {address}")
                        return PriceData(
                            price_usd=safe_float(price_data.get('value'), 0.0),
                            market_cap=safe_float(price_data.get('marketCap')),
                            volume_24h=safe_float(price_data.get('volume24h')),
                            price_change_24h=safe_float(price_data.get('priceChange24h')),
                            symbol=None  # Birdeye price endpoint doesn't return symbol
                        )
                    else:
                        self.logger.warning(f"Birdeye: success={data.get('success')}, has_data={bool(data.get('data'))} for {address}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"Birdeye HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"Birdeye exception for {address}: {e}")
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

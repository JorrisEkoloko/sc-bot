"""Blockscout API client (no key required).

Provides current price, holder count, and market data.
Verified endpoint: https://eth.blockscout.com/api/v2/tokens/{address}
"""
import aiohttp
from typing import Optional

from domain.price_data import PriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class BlockscoutClient(BaseAPIClient):
    """Blockscout API client with persistent session (no API key required)."""
    
    def __init__(self, logger=None):
        """Initialize client with persistent session."""
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('BlockscoutClient')
        
        # Chain-specific Blockscout endpoints
        self.chain_endpoints = {
            'ethereum': 'https://eth.blockscout.com/api/v2',
            'evm': 'https://eth.blockscout.com/api/v2',
            'optimism': 'https://optimism.blockscout.com/api/v2',
            'base': 'https://base.blockscout.com/api/v2',
            'arbitrum': 'https://arbitrum.blockscout.com/api/v2',
            'polygon': 'https://polygon.blockscout.com/api/v2',
            'bsc': 'https://bsc.blockscout.com/api/v2',
        }
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """
        Fetch price and metadata from Blockscout API.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            
        Returns:
            PriceData with current price and metadata, or None if not found
        """
        await self._ensure_session()
        
        # Get endpoint for chain
        base_url = self.chain_endpoints.get(chain.lower(), self.chain_endpoints['ethereum'])
        url = f"{base_url}/tokens/{address}"
        
        try:
            async with self._session.get(url, timeout=10) as response:
                self.logger.debug(f"Blockscout response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract price and metadata
                    exchange_rate = safe_float(data.get('exchange_rate'), 0.0)
                    
                    if exchange_rate > 0:
                        self.logger.debug(f"Blockscout found price for {address}: ${exchange_rate}")
                        
                        return PriceData(
                            price_usd=exchange_rate,
                            market_cap=safe_float(data.get('circulating_market_cap'), None),
                            volume_24h=safe_float(data.get('volume_24h'), None),
                            price_change_24h=None,  # Blockscout doesn't provide this
                            symbol=data.get('symbol'),
                            source='blockscout'
                        )
                    else:
                        self.logger.warning(f"Blockscout: No price data for {address}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"Blockscout HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"Blockscout exception for {address}: {e}")
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

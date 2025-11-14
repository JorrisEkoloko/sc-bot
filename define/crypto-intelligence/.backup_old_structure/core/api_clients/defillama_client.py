"""DefiLlama API client (no key required).

Verified endpoint: https://coins.llama.fi/prices/current/{chain}:{address}
"""
import aiohttp
from typing import Optional

from core.api_clients.base_client import BaseAPIClient, PriceData
from utils.type_converters import safe_float


class DefiLlamaClient(BaseAPIClient):
    """DefiLlama API client with persistent session (no API key required)."""
    
    def __init__(self, logger=None):
        """Initialize client with persistent session."""
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('DefiLlamaClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price from DefiLlama API."""
        await self._ensure_session()
        
        # Map chain to DefiLlama format
        chain_map = {
            'solana': 'solana',
            'evm': 'ethereum'  # Default EVM chains to ethereum
        }
        llama_chain = chain_map.get(chain, 'ethereum')
        
        # Build URL
        url = f"https://coins.llama.fi/prices/current/{llama_chain}:{address}"
        
        try:
            async with self._session.get(url, timeout=10) as response:
                self.logger.debug(f"DefiLlama response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract coin data
                    coin_key = f"{llama_chain}:{address}"
                    coins = data.get('coins', {})
                    
                    if coin_key in coins:
                        coin_data = coins[coin_key]
                        self.logger.debug(f"DefiLlama found data for {address}")
                        
                        return PriceData(
                            price_usd=safe_float(coin_data.get('price'), 0.0),
                            market_cap=None,  # DefiLlama doesn't provide market cap
                            volume_24h=None,  # DefiLlama doesn't provide volume
                            price_change_24h=None,  # DefiLlama doesn't provide price change
                            symbol=coin_data.get('symbol'),
                            source='defillama'
                        )
                    else:
                        self.logger.warning(f"DefiLlama: No data found for {coin_key}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"DefiLlama HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"DefiLlama exception for {address}: {e}")
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

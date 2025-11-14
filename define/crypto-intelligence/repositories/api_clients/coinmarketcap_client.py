"""CoinMarketCap API client for token metadata and price data.

API Documentation: https://coinmarketcap.com/api/documentation/v1/
Free Tier: 333 calls/day (10,000 calls/month)
"""
import aiohttp
from typing import Optional, Dict
from datetime import datetime

from domain.price_data import PriceData
from .base_client import BaseAPIClient
from utils.type_converters import safe_float


class CoinMarketCapClient(BaseAPIClient):
    """CoinMarketCap API client with persistent session."""
    
    BASE_URL = "https://pro-api.coinmarketcap.com"
    
    def __init__(self, api_key: str, logger=None):
        """Initialize with API key."""
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('CoinMarketCapClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            }
            self._session = aiohttp.ClientSession(headers=headers)
    
    async def get_token_metadata(self, address: str, chain: str = 'ethereum') -> Optional[Dict]:
        """
        Get token metadata including symbol from contract address.
        
        Args:
            address: Token contract address
            chain: Blockchain name (default: 'ethereum')
            
        Returns:
            Dictionary with token metadata or None if not found
            
        Example:
            metadata = await client.get_token_metadata('0x562E36288a9Dd867d5d8b0Aa48c2E8d2d215d5d')
            # Returns: {'symbol': 'OPTI', 'name': 'Optimus AI', 'slug': 'optimus-ai'}
        """
        await self._ensure_session()
        
        # Map chain names to CMC platform IDs
        platform_map = {
            'ethereum': 1,
            'evm': 1,
            'bsc': 56,
            'bnb': 56,
            'polygon': 137,
            'matic': 137,
            'avalanche': 43114,
            'avax': 43114
        }
        
        platform_id = platform_map.get(chain.lower(), 1)
        
        url = f"{self.BASE_URL}/v2/cryptocurrency/info"
        params = {
            'address': address,
            'aux': 'urls,logo,description,tags,platform,date_added,notice'
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                self.logger.debug(f"CoinMarketCap metadata response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status', {}).get('error_code') == 0:
                        # CMC returns data keyed by internal ID
                        token_data = data.get('data', {})
                        
                        if token_data:
                            # Get first token (should only be one)
                            token_info = list(token_data.values())[0]
                            
                            metadata = {
                                'symbol': token_info.get('symbol', '').upper(),
                                'name': token_info.get('name', ''),
                                'slug': token_info.get('slug', ''),
                                'cmc_id': token_info.get('id'),
                                'platform': token_info.get('platform', {}).get('name', ''),
                                'date_added': token_info.get('date_added', ''),
                                'tags': token_info.get('tags', [])
                            }
                            
                            self.logger.info(f"CoinMarketCap found metadata for {address}: {metadata['symbol']}")
                            return metadata
                    else:
                        error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                        self.logger.warning(f"CoinMarketCap API error: {error_msg}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CoinMarketCap HTTP {response.status}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CoinMarketCap metadata exception for {address}: {e}")
            return None
    
    async def get_price_by_symbol(self, symbol: str) -> Optional[PriceData]:
        """
        Get current price by symbol.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH', 'OPTI')
            
        Returns:
            PriceData object or None if not found
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/v2/cryptocurrency/quotes/latest"
        params = {
            'symbol': symbol.upper(),
            'convert': 'USD'
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                self.logger.debug(f"CoinMarketCap price response status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status', {}).get('error_code') == 0:
                        token_data = data.get('data', {}).get(symbol.upper())
                        
                        if token_data:
                            # Handle multiple tokens with same symbol (take first)
                            if isinstance(token_data, list):
                                token_data = token_data[0]
                            
                            quote = token_data.get('quote', {}).get('USD', {})
                            
                            return PriceData(
                                price_usd=safe_float(quote.get('price'), 0.0),
                                market_cap=safe_float(quote.get('market_cap')),
                                volume_24h=safe_float(quote.get('volume_24h')),
                                price_change_24h=safe_float(quote.get('percent_change_24h')),
                                symbol=symbol.upper(),
                                source='coinmarketcap'
                            )
                
                return None
        except Exception as e:
            self.logger.error(f"CoinMarketCap price exception for {symbol}: {e}")
            return None
    
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

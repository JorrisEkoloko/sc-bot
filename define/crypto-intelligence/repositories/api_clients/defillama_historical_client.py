"""DefiLlama historical price API client."""
import aiohttp
from datetime import datetime
from typing import Optional
from repositories.api_clients.base_client import BaseAPIClient
from utils.logger import setup_logger
from utils.chain_mapping import get_chain_for_api


class DefiLlamaHistoricalClient(BaseAPIClient):
    """DefiLlama API client for historical prices (best for small-cap tokens)."""
    
    def __init__(self, request_timeout: int = 10, logger=None):
        """
        Initialize client (no API key required).
        
        Args:
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.base_url = "https://coins.llama.fi"
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self.logger = logger or setup_logger('DefiLlamaHistoricalClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price_at_timestamp(
        self,
        address: str,
        chain: str,
        timestamp: datetime
    ) -> Optional[float]:
        """
        Fetch historical price from DefiLlama at specific timestamp.
        
        DefiLlama is the best source for historical data:
        - FREE (no API key required)
        - Extensive historical data
        - High confidence scores
        - Works for small-cap tokens
        
        Args:
            address: Token contract address
            chain: Blockchain name (ethereum, solana, etc.)
            timestamp: Timestamp to fetch price for
            
        Returns:
            Price in USD, or None if not found
        """
        await self._ensure_session()
        
        try:
            # Use shared chain mapping utility
            llama_chain = get_chain_for_api(chain, 'defillama')
            unix_ts = int(timestamp.timestamp())
            
            # Build URL: /prices/historical/{timestamp}/{chain}:{address}
            url = f"{self.base_url}/prices/historical/{unix_ts}/{llama_chain}:{address}"
            
            async with self._session.get(url, timeout=self.request_timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract price from response
                    coins = data.get('coins', {})
                    coin_key = f"{llama_chain}:{address}"
                    
                    if coin_key in coins:
                        coin_data = coins[coin_key]
                        price = coin_data.get('price')
                        confidence = coin_data.get('confidence', 0)
                        
                        if price and price > 0:
                            self.logger.debug(
                                f"DefiLlama: {address[:10]}... at {timestamp} = ${price:.8f} "
                                f"(confidence: {confidence:.2f})"
                            )
                            return float(price)
                    
                    self.logger.debug(f"DefiLlama: No price data for {address[:10]}... at {timestamp}")
                    return None
                else:
                    self.logger.debug(f"DefiLlama HTTP {response.status} for {address[:10]}...")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching DefiLlama price for {address}: {e}")
            return None
    
    async def get_ohlc_window(
        self,
        address: str,
        chain: str,
        start_timestamp: datetime,
        window_days: int = 30
    ) -> Optional[list]:
        """
        Fetch OHLC candles from DefiLlama chart endpoint.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            start_timestamp: Start of window
            window_days: Number of days to fetch
            
        Returns:
            List of candles with timestamp and price, or None
        """
        await self._ensure_session()
        
        try:
            llama_chain = get_chain_for_api(chain, 'defillama')
            unix_ts = int(start_timestamp.timestamp())
            
            # /chart/{chain}:{address}?start={timestamp}&span={days}&period=1d
            url = f"{self.base_url}/chart/{llama_chain}:{address}?start={unix_ts}&span={window_days}&period=1d"
            
            async with self._session.get(url, timeout=self.request_timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    coins = data.get('coins', {})
                    coin_key = f"{llama_chain}:{address}"
                    
                    if coin_key in coins:
                        prices = coins[coin_key].get('prices', [])
                        if prices:
                            self.logger.debug(f"DefiLlama chart: {len(prices)} candles for {address[:10]}...")
                            return prices
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching DefiLlama chart for {address}: {e}")
            return None
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

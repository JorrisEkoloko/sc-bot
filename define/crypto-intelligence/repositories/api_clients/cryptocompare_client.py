"""CryptoCompare API client for historical and current price data.

API Documentation: https://www.cryptocompare.com/coins/guides/how-to-use-our-api/
Free Tier: 100,000 calls/month

Key Endpoints:
- Current Price: /data/price
- Historical Daily OHLC: /data/v2/histoday
- Historical Hourly OHLC: /data/v2/histohour
- Price at Timestamp: /data/pricehistorical
"""
import aiohttp
from typing import Optional, List
from datetime import datetime

from domain.price_data import PriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class CryptoCompareClient(BaseAPIClient):
    """CryptoCompare API client with persistent session."""
    
    BASE_URL = "https://min-api.cryptocompare.com"
    
    def __init__(self, api_key: str, logger=None):
        """Initialize with API key."""
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('CryptoCompareClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, symbol: str, vs_currency: str = 'USD') -> Optional[PriceData]:
        """
        Fetch current price from CryptoCompare API.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH', 'SOL')
            vs_currency: Quote currency (default: 'USD')
            
        Returns:
            PriceData object or None if not found
            
        Example:
            price_data = await client.get_price('BTC', 'USD')
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/data/price"
        params = {
            'fsym': symbol.upper(),
            'tsyms': vs_currency.upper(),
            'api_key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                self.logger.debug(f"CryptoCompare response status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error response
                    if 'Response' in data and data['Response'] == 'Error':
                        self.logger.warning(f"CryptoCompare error for {symbol}: {data.get('Message', 'Unknown error')}")
                        return None
                    
                    price = data.get(vs_currency.upper())
                    if price:
                        self.logger.debug(f"CryptoCompare found price for {symbol}: ${price}")
                        return PriceData(
                            price_usd=safe_float(price, 0.0),
                            market_cap=None,
                            volume_24h=None,
                            price_change_24h=None,
                            symbol=symbol.upper(),
                            source='cryptocompare'
                        )
                    else:
                        self.logger.warning(f"CryptoCompare: No price for {symbol} in response")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CryptoCompare HTTP {response.status} for {symbol}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CryptoCompare exception for {symbol}: {e}")
            raise
    
    async def get_price_at_timestamp(self, symbol: str, timestamp: int, vs_currency: str = 'USD') -> Optional[float]:
        """
        Fetch price at specific timestamp (historical price).
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            timestamp: Unix timestamp (seconds)
            vs_currency: Quote currency (default: 'USD')
            
        Returns:
            Price as float or None if not found
            
        Example:
            # Get BTC price on Jan 1, 2021
            price = await client.get_price_at_timestamp('BTC', 1609459200)
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/data/pricehistorical"
        params = {
            'fsym': symbol.upper(),
            'tsyms': vs_currency.upper(),
            'ts': timestamp,
            'api_key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                self.logger.debug(f"CryptoCompare historical price status: {response.status} for {symbol} at {timestamp}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Response format: {"BTC": {"USD": 29388.94}}
                    token_data = data.get(symbol.upper(), {})
                    price = token_data.get(vs_currency.upper())
                    
                    if price:
                        self.logger.debug(f"CryptoCompare found historical price for {symbol}: ${price}")
                        return safe_float(price)
                    else:
                        self.logger.warning(f"CryptoCompare: No historical price for {symbol} at {timestamp}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CryptoCompare historical HTTP {response.status}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CryptoCompare historical exception for {symbol}: {e}")
            return None
    
    async def get_daily_ohlc(self, symbol: str, limit: int = 30, vs_currency: str = 'USD') -> Optional[List[dict]]:
        """
        Fetch daily OHLC (candlestick) data.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            limit: Number of days to fetch (default: 30, max: 2000)
            vs_currency: Quote currency (default: 'USD')
            
        Returns:
            List of OHLC dictionaries or None if error
            
        Example:
            # Get last 30 days of BTC daily candles
            ohlc_data = await client.get_daily_ohlc('BTC', limit=30)
            
        Response format:
            [
                {
                    'time': 1762387200,
                    'high': 104201.89,
                    'low': 100266.6,
                    'open': 103893.5,
                    'close': 101302.75,
                    'volumefrom': 32306.54,
                    'volumeto': 3300189453.88
                },
                ...
            ]
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/data/v2/histoday"
        params = {
            'fsym': symbol.upper(),
            'tsym': vs_currency.upper(),
            'limit': limit,
            'api_key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                self.logger.debug(f"CryptoCompare daily OHLC status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error response
                    if data.get('Response') == 'Error':
                        self.logger.warning(f"CryptoCompare OHLC error for {symbol}: {data.get('Message', 'Unknown error')}")
                        return None
                    
                    # Extract OHLC data
                    ohlc_data = data.get('Data', {}).get('Data', [])
                    
                    if ohlc_data:
                        self.logger.debug(f"CryptoCompare found {len(ohlc_data)} daily candles for {symbol}")
                        return ohlc_data
                    else:
                        self.logger.warning(f"CryptoCompare: No OHLC data for {symbol}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CryptoCompare OHLC HTTP {response.status}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CryptoCompare OHLC exception for {symbol}: {e}")
            return None
    
    async def get_hourly_ohlc(self, symbol: str, limit: int = 24, vs_currency: str = 'USD') -> Optional[List[dict]]:
        """
        Fetch hourly OHLC (candlestick) data.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            limit: Number of hours to fetch (default: 24, max: 2000)
            vs_currency: Quote currency (default: 'USD')
            
        Returns:
            List of OHLC dictionaries or None if error
            
        Example:
            # Get last 24 hours of BTC hourly candles
            ohlc_data = await client.get_hourly_ohlc('BTC', limit=24)
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/data/v2/histohour"
        params = {
            'fsym': symbol.upper(),
            'tsym': vs_currency.upper(),
            'limit': limit,
            'api_key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                self.logger.debug(f"CryptoCompare hourly OHLC status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error response
                    if data.get('Response') == 'Error':
                        self.logger.warning(f"CryptoCompare hourly OHLC error for {symbol}: {data.get('Message', 'Unknown error')}")
                        return None
                    
                    # Extract OHLC data
                    ohlc_data = data.get('Data', {}).get('Data', [])
                    
                    if ohlc_data:
                        self.logger.debug(f"CryptoCompare found {len(ohlc_data)} hourly candles for {symbol}")
                        return ohlc_data
                    else:
                        self.logger.warning(f"CryptoCompare: No hourly OHLC data for {symbol}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CryptoCompare hourly OHLC HTTP {response.status}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CryptoCompare hourly OHLC exception for {symbol}: {e}")
            return None
    
    async def get_historical_ohlc_range(self, symbol: str, start_timestamp: int, 
                                       end_timestamp: int, vs_currency: str = 'USD') -> Optional[List[dict]]:
        """
        Fetch daily OHLC data for a specific date range.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            start_timestamp: Start date as Unix timestamp (seconds)
            end_timestamp: End date as Unix timestamp (seconds)
            vs_currency: Quote currency (default: 'USD')
            
        Returns:
            List of OHLC dictionaries or None if error
            
        Example:
            # Get BTC data from Jan 1 to Jan 31, 2021
            start = int(datetime(2021, 1, 1).timestamp())
            end = int(datetime(2021, 1, 31).timestamp())
            ohlc_data = await client.get_historical_ohlc_range('BTC', start, end)
        """
        await self._ensure_session()
        
        # Calculate number of days
        days = (end_timestamp - start_timestamp) // 86400
        
        url = f"{self.BASE_URL}/data/v2/histoday"
        params = {
            'fsym': symbol.upper(),
            'tsym': vs_currency.upper(),
            'limit': days,
            'toTs': end_timestamp,
            'api_key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                self.logger.debug(f"CryptoCompare range OHLC status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error response
                    if data.get('Response') == 'Error':
                        self.logger.warning(f"CryptoCompare range OHLC error for {symbol}: {data.get('Message', 'Unknown error')}")
                        return None
                    
                    # Extract OHLC data
                    ohlc_data = data.get('Data', {}).get('Data', [])
                    
                    if ohlc_data:
                        self.logger.debug(f"CryptoCompare found {len(ohlc_data)} candles for {symbol} in range")
                        return ohlc_data
                    else:
                        self.logger.warning(f"CryptoCompare: No OHLC data for {symbol} in range")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CryptoCompare range OHLC HTTP {response.status}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CryptoCompare range OHLC exception for {symbol}: {e}")
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
        try:
            await self.close()
        except Exception as close_error:
            # Log but don't shadow original exception
            if exc_type is None:
                # No original exception, re-raise close error
                raise
            else:
                # Original exception exists, log close error but don't shadow
                self.logger.error(f"Error during context manager cleanup: {close_error}")
                # Return False to propagate original exception
                return False

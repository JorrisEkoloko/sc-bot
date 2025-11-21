"""CoinGecko API client.

Verified endpoint: https://docs.coingecko.com/reference/simple-token-price
"""
import aiohttp
from typing import Optional

from domain.price_data import PriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class CoinGeckoClient(BaseAPIClient):
    """CoinGecko API client with persistent session."""
    
    def __init__(self, api_key: str, request_timeout: int = 10, logger=None):
        """
        Initialize with API key.
        
        Args:
            api_key: CoinGecko API key
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.api_key = api_key
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('CoinGeckoClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price from CoinGecko API."""
        await self._ensure_session()
        
        # Map chain to CoinGecko platform ID
        platform_map = {
            'evm': 'ethereum',  # Default to ethereum for EVM
            'solana': 'solana'
        }
        platform = platform_map.get(chain, 'ethereum')
        
        # Determine if demo or pro key
        is_demo = self.api_key.startswith('CG-')
        base_url = "https://api.coingecko.com" if is_demo else "https://pro-api.coingecko.com"
        
        url = f"{base_url}/api/v3/simple/token_price/{platform}"
        params = {
            'contract_addresses': address,
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        
        # Use appropriate header based on key type
        headers = {
            'x-cg-demo-api-key' if is_demo else 'x-cg-pro-api-key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, headers=headers, timeout=self.request_timeout) as response:
                self.logger.debug(f"CoinGecko response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    token_data = data.get(address.lower())
                    
                    if token_data:
                        self.logger.debug(f"CoinGecko found data for {address}")
                        return PriceData(
                            price_usd=safe_float(token_data.get('usd'), 0.0),
                            market_cap=safe_float(token_data.get('usd_market_cap')),
                            volume_24h=safe_float(token_data.get('usd_24h_vol')),
                            price_change_24h=safe_float(token_data.get('usd_24h_change')),
                            symbol=None,  # CoinGecko simple/token_price doesn't return symbol
                            source='coingecko'
                        )
                    else:
                        self.logger.warning(f"CoinGecko: No data for {address} in response")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CoinGecko HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CoinGecko exception for {address}: {e}")
            raise
    
    async def get_token_info(self, address: str, chain: str) -> Optional[dict]:
        """
        Fetch token info including symbol from CoinGecko.
        
        Args:
            address: Token contract address
            chain: Blockchain name ('evm' or 'solana')
            
        Returns:
            Dictionary with token info (symbol, name, etc.) or None if not found
        """
        await self._ensure_session()
        
        # Map chain to CoinGecko platform ID
        platform_map = {
            'evm': 'ethereum',
            'solana': 'solana'
        }
        platform = platform_map.get(chain, 'ethereum')
        
        # Determine if demo or pro key
        is_demo = self.api_key.startswith('CG-')
        base_url = "https://api.coingecko.com" if is_demo else "https://pro-api.coingecko.com"
        
        # Get token data from contract address endpoint
        url = f"{base_url}/api/v3/coins/{platform}/contract/{address}"
        
        # Use appropriate header based on key type
        headers = {
            'x-cg-demo-api-key' if is_demo else 'x-cg-pro-api-key': self.api_key
        }
        
        try:
            async with self._session.get(url, headers=headers, timeout=self.request_timeout) as response:
                self.logger.debug(f"CoinGecko token info response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract ATH data from market_data
                    market_data = data.get('market_data', {})
                    ath_data = market_data.get('ath', {})
                    ath_date_data = market_data.get('ath_date', {})
                    ath_change_data = market_data.get('ath_change_percentage', {})
                    
                    token_info = {
                        'symbol': data.get('symbol', '').upper(),
                        'name': data.get('name', ''),
                        'coin_id': data.get('id', ''),
                        'ath': safe_float(ath_data.get('usd')),
                        'ath_date': ath_date_data.get('usd'),
                        'ath_change_percentage': safe_float(ath_change_data.get('usd'))
                    }
                    
                    self.logger.debug(f"CoinGecko found token info for {address}: {token_info['symbol']}")
                    return token_info
                elif response.status == 404:
                    self.logger.debug(f"CoinGecko: Token {address} not found in database")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CoinGecko token info HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CoinGecko token info exception for {address}: {e}")
            return None
    
    async def get_historical_data(self, address: str, chain: str) -> Optional[dict]:
        """
        Fetch historical ATH/ATL data from CoinGecko.
        
        Args:
            address: Token contract address
            chain: Blockchain name ('evm' or 'solana')
            
        Returns:
            Dictionary with historical data or None if not found
        """
        await self._ensure_session()
        
        # Map chain to CoinGecko platform ID
        platform_map = {
            'evm': 'ethereum',
            'solana': 'solana'
        }
        platform = platform_map.get(chain, 'ethereum')
        
        # Determine if demo or pro key
        is_demo = self.api_key.startswith('CG-')
        base_url = "https://api.coingecko.com" if is_demo else "https://pro-api.coingecko.com"
        
        # Get token data from contract address endpoint (includes symbol + historical data)
        url = f"{base_url}/api/v3/coins/{platform}/contract/{address}"
        
        # Use appropriate header based on key type
        headers = {
            'x-cg-demo-api-key' if is_demo else 'x-cg-pro-api-key': self.api_key
        }
        
        try:
            async with self._session.get(url, headers=headers, timeout=self.request_timeout) as response:
                self.logger.debug(f"CoinGecko historical response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract market data with ATH/ATL information
                    market_data = data.get('market_data', {})
                    
                    if market_data:
                        # Get ATH data
                        ath_data = market_data.get('ath', {})
                        ath_date_data = market_data.get('ath_date', {})
                        ath_change_data = market_data.get('ath_change_percentage', {})
                        
                        # Get ATL data
                        atl_data = market_data.get('atl', {})
                        atl_date_data = market_data.get('atl_date', {})
                        atl_change_data = market_data.get('atl_change_percentage', {})
                        
                        # Get current price for distance calculation
                        current_price_data = market_data.get('current_price', {})
                        current_price = safe_float(current_price_data.get('usd'))
                        
                        historical_data = {
                            'all_time_ath': safe_float(ath_data.get('usd')),
                            'all_time_ath_date': ath_date_data.get('usd', ''),
                            'distance_from_ath': safe_float(ath_change_data.get('usd')),
                            'all_time_atl': safe_float(atl_data.get('usd')),
                            'all_time_atl_date': atl_date_data.get('usd', ''),
                            'distance_from_atl': safe_float(atl_change_data.get('usd')),
                            'symbol': data.get('symbol', '').upper()  # Include symbol for Twelve Data fallback
                        }
                        
                        self.logger.debug(f"CoinGecko found historical data for {address}")
                        return historical_data
                    else:
                        self.logger.warning(f"CoinGecko: No market data for {address}")
                elif response.status == 404:
                    self.logger.debug(f"CoinGecko: Token {address} not found in database")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CoinGecko historical HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"CoinGecko historical exception for {address}: {e}")
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
        """
        Async context manager exit with proper exception handling.
        
        FIXED: Issue #16 - Context Manager Interference
        Properly chains exceptions instead of losing close errors.
        
        Based on PEP 343: Context manager exception handling.
        """
        close_error = None
        
        try:
            await self.close()
        except Exception as e:
            close_error = e
            self.logger.error(f"Error during context manager cleanup: {e}")
        
        # Handle exception chaining
        if exc_type is not None and close_error is not None:
            # Chain close error to original exception
            if hasattr(exc_val, '__context__'):
                exc_val.__context__ = close_error
            self.logger.error(
                f"Multiple errors: original={exc_type.__name__}, "
                f"cleanup={type(close_error).__name__}"
            )
            return False  # Propagate original exception with context
        
        # If only close error, raise it
        if close_error is not None:
            raise close_error
        
        # If only original error, propagate it
        return False

    async def get_coins_list(self, include_platform: bool = True) -> list:
        """
        Fetch list of all coins with their contract addresses.
        
        Args:
            include_platform: Include platform/contract address data
            
        Returns:
            List of coin dictionaries with id, symbol, name, and platforms
        """
        await self._ensure_session()
        
        # Determine if demo or pro key
        is_demo = self.api_key.startswith('CG-')
        base_url = "https://api.coingecko.com" if is_demo else "https://pro-api.coingecko.com"
        
        url = f"{base_url}/api/v3/coins/list"
        params = {
            'include_platform': 'true' if include_platform else 'false'
        }
        
        # Use appropriate header based on key type
        headers = {
            'x-cg-demo-api-key' if is_demo else 'x-cg-pro-api-key': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, headers=headers, timeout=30) as response:
                self.logger.debug(f"CoinGecko coins list response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"CoinGecko returned {len(data)} coins")
                    return data
                else:
                    response_text = await response.text()
                    self.logger.warning(f"CoinGecko coins list HTTP {response.status}: {response_text[:200]}")
                    return []
        except Exception as e:
            self.logger.error(f"CoinGecko coins list exception: {e}")
            return []

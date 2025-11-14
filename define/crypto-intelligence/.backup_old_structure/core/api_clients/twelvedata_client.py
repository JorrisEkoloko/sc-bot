"""Twelve Data API client for historical OHLCV data.

Verified endpoint: https://twelvedata.com/docs
"""
import aiohttp
from typing import Optional
from datetime import datetime

from core.api_clients.base_client import BaseAPIClient
from utils.type_converters import safe_float


class TwelveDataClient(BaseAPIClient):
    """Twelve Data API client for cryptocurrency historical data."""
    
    def __init__(self, api_key: str, logger=None):
        """Initialize with API key."""
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('TwelveDataClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_historical_ohlcv(self, symbol: str, interval: str = '1day', outputsize: int = 5000) -> Optional[dict]:
        """
        Fetch historical OHLCV data from Twelve Data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD', 'ETH/USD')
            interval: Time interval (default: '1day')
            outputsize: Number of data points (max: 5000)
            
        Returns:
            Dictionary with OHLCV data or None if not found
        """
        await self._ensure_session()
        
        url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                self.logger.debug(f"Twelve Data response status: {response.status} for {symbol}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'ok' and data.get('values'):
                        values = data['values']
                        self.logger.debug(f"Twelve Data found {len(values)} data points for {symbol}")
                        
                        # Calculate ATH/ATL from OHLCV data
                        highs = [safe_float(v['high']) for v in values if v.get('high')]
                        lows = [safe_float(v['low']) for v in values if v.get('low')]
                        
                        if highs and lows:
                            ath = max(highs)
                            atl = min(lows)
                            
                            # Find dates for ATH/ATL
                            ath_entry = next((v for v in values if safe_float(v['high']) == ath), None)
                            atl_entry = next((v for v in values if safe_float(v['low']) == atl), None)
                            
                            # Get current price from most recent data
                            current_price = safe_float(values[0]['close'])
                            
                            # Calculate distances
                            distance_from_ath = ((current_price - ath) / ath) * 100 if ath else 0
                            distance_from_atl = ((current_price - atl) / atl) * 100 if atl else 0
                            
                            return {
                                'all_time_ath': ath,
                                'all_time_ath_date': ath_entry['datetime'] if ath_entry else '',
                                'distance_from_ath': distance_from_ath,
                                'all_time_atl': atl,
                                'all_time_atl_date': atl_entry['datetime'] if atl_entry else '',
                                'distance_from_atl': distance_from_atl,
                                'data_points': len(values),
                                'source': 'twelvedata'
                            }
                        else:
                            self.logger.warning(f"Twelve Data: No valid OHLCV data for {symbol}")
                    else:
                        error_msg = data.get('message', 'Unknown error')
                        self.logger.warning(f"Twelve Data: {error_msg} for {symbol}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"Twelve Data HTTP {response.status} for {symbol}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"Twelve Data exception for {symbol}: {e}")
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

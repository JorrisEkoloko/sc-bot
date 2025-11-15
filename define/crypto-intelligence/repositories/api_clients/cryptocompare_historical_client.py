"""CryptoCompare historical data API client."""
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List
from domain.historical_price import OHLCCandle, HistoricalPriceData
from repositories.api_clients.base_client import BaseAPIClient
from utils.logger import setup_logger


class CryptoCompareHistoricalClient(BaseAPIClient):
    """CryptoCompare API client for historical OHLC data."""
    
    def __init__(self, api_key: str = "", request_timeout: int = 10, logger=None):
        """
        Initialize with API key.
        
        Args:
            api_key: CryptoCompare API key (optional)
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.api_key = api_key
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self.logger = logger or setup_logger('CryptoCompareHistoricalClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price_at_timestamp(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[float]:
        """Fetch price at specific timestamp."""
        await self._ensure_session()
        
        try:
            unix_ts = int(timestamp.timestamp())
            url = f"{self.base_url}/pricehistorical?fsym={symbol}&tsyms=USD&ts={unix_ts}"
            
            if self.api_key:
                url += f"&api_key={self.api_key}"
            
            async with self._session.get(url, timeout=self.request_timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('Response') == 'Error':
                        self.logger.debug(f"CryptoCompare error for {symbol}: {data.get('Message')}")
                        return None
                    
                    if symbol in data and 'USD' in data[symbol]:
                        price = data[symbol]['USD']
                        if price and price > 0:
                            self.logger.debug(f"CryptoCompare: {symbol} at {timestamp} = ${price:.6f}")
                            return float(price)
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching CryptoCompare price for {symbol}: {e}")
            return None
    
    async def get_ohlc_window(
        self,
        symbol: str,
        start_timestamp: datetime,
        window_days: int
    ) -> Optional[HistoricalPriceData]:
        """Fetch OHLC data for time window."""
        await self._ensure_session()
        
        try:
            # Calculate end timestamp (start + window_days)
            end_timestamp = start_timestamp + timedelta(days=window_days)
            unix_ts = int(end_timestamp.timestamp())
            
            url = f"{self.base_url}/v2/histoday"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': window_days,
                'toTs': unix_ts  # Fetch backwards from end_timestamp to start_timestamp
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            async with self._session.get(url, params=params, timeout=self.request_timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('Response') == 'Error':
                        self.logger.debug(f"CryptoCompare OHLC error for {symbol}: {data.get('Message')}")
                        return None
                    
                    if 'Data' in data and 'Data' in data['Data']:
                        candles_data = data['Data']['Data']
                        if not candles_data:
                            return None
                        
                        # Parse candles
                        candles = []
                        for candle in candles_data:
                            candles.append(OHLCCandle(
                                timestamp=datetime.fromtimestamp(candle['time']),
                                open=candle['open'],
                                high=candle['high'],
                                low=candle['low'],
                                close=candle['close'],
                                volume=candle.get('volumeto', 0.0)
                            ))
                        
                        # Find ATH in window
                        ath_candle = max(candles, key=lambda c: c.high)
                        entry_price = candles[0].open
                        
                        # Validate that we have real price data (not all zeros)
                        if ath_candle.high <= 0 or entry_price <= 0:
                            self.logger.warning(
                                f"CryptoCompare: {symbol} - {len(candles)} candles but all prices are zero (unlisted token)"
                            )
                            return None
                        
                        # Calculate days to ATH
                        days_to_ath = (ath_candle.timestamp - candles[0].timestamp).total_seconds() / 86400
                        
                        self.logger.info(
                            f"CryptoCompare: {symbol} - {len(candles)} candles, "
                            f"ATH ${ath_candle.high:.6f} on day {days_to_ath:.1f}"
                        )
                        
                        return HistoricalPriceData(
                            symbol=symbol,
                            price_at_timestamp=entry_price,
                            ath_in_window=ath_candle.high,
                            ath_timestamp=ath_candle.timestamp,
                            days_to_ath=days_to_ath,
                            candles=candles,
                            source='cryptocompare'
                        )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching CryptoCompare OHLC for {symbol}: {e}")
            return None
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

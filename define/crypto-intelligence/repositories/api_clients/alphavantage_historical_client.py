"""Alpha Vantage API client for historical OHLC data.

Free tier: 25 calls/day
Docs: https://www.alphavantage.co/documentation/
"""
import aiohttp
from typing import Optional, List
from datetime import datetime, timedelta
from domain.historical_price import OHLCCandle, HistoricalPriceData


class AlphaVantageHistoricalClient:
    """Alpha Vantage API client for OHLC data."""
    
    def __init__(self, api_key: str, logger=None):
        """Initialize client."""
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('AlphaVantageHistoricalClient')
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_ohlc_window(
        self,
        symbol: str,
        start_timestamp: datetime,
        window_days: int = 30
    ) -> Optional[HistoricalPriceData]:
        """
        Fetch OHLC data from Alpha Vantage.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            start_timestamp: Start time
            window_days: Number of days
            
        Returns:
            HistoricalPriceData or None
        """
        await self._ensure_session()
        
        url = "https://www.alphavantage.co/query"
        
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': 'USD',
            'apikey': self.api_key
        }
        
        try:
            async with self._session.get(url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error messages
                    if 'Error Message' in data:
                        self.logger.debug(f"AlphaVantage: {data['Error Message']}")
                        return None
                    
                    if 'Note' in data:
                        self.logger.warning(f"AlphaVantage rate limit: {data['Note']}")
                        return None
                    
                    time_series = data.get('Time Series (Digital Currency Daily)', {})
                    if not time_series:
                        self.logger.debug(f"AlphaVantage: No data for {symbol}")
                        return None
                    
                    # Parse candles within the time window
                    candles = []
                    end_timestamp = start_timestamp + timedelta(days=window_days)
                    
                    for date_str, values in sorted(time_series.items()):
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        if start_timestamp <= date <= end_timestamp:
                            candles.append(OHLCCandle(
                                timestamp=date,
                                open=float(values['1a. open (USD)']),
                                high=float(values['2a. high (USD)']),
                                low=float(values['3a. low (USD)']),
                                close=float(values['4a. close (USD)'])
                            ))
                    
                    if not candles:
                        self.logger.debug(f"AlphaVantage: No candles in time window for {symbol}")
                        return None
                    
                    # Calculate ATH
                    ath_price = max(c.high for c in candles)
                    ath_candle = next(c for c in candles if c.high == ath_price)
                    
                    from datetime import timezone
                    ath_ts = ath_candle.timestamp
                    start_ts = start_timestamp
                    if ath_ts.tzinfo is None:
                        ath_ts = ath_ts.replace(tzinfo=timezone.utc)
                    if start_ts.tzinfo is None:
                        start_ts = start_ts.replace(tzinfo=timezone.utc)
                    
                    days_to_ath = (ath_ts - start_ts).total_seconds() / 86400
                    
                    self.logger.info(f"AlphaVantage: {symbol} - {len(candles)} candles")
                    
                    return HistoricalPriceData(
                        symbol=symbol,
                        price_at_timestamp=candles[0].close,
                        ath_in_window=ath_price,
                        ath_timestamp=ath_candle.timestamp,
                        days_to_ath=days_to_ath,
                        candles=candles,
                        source='alphavantage'
                    )
                else:
                    self.logger.debug(f"AlphaVantage HTTP {response.status} for {symbol}")
                    return None
                    
        except Exception as e:
            self.logger.debug(f"AlphaVantage error for {symbol}: {e}")
            return None
    
    async def close(self):
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

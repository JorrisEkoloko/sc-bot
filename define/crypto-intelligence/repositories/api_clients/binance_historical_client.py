"""Binance API client for historical OHLC data.

Free, unlimited, no API key required.
Docs: https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
"""
import aiohttp
from typing import Optional, List
from datetime import datetime, timedelta
from domain.historical_price import OHLCCandle, HistoricalPriceData


class BinanceHistoricalClient:
    """Binance API client for OHLC data."""
    
    def __init__(self, logger=None):
        """Initialize client."""
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('BinanceHistoricalClient')
    
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
        Fetch OHLC data from Binance.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'ETHUSDT')
            start_timestamp: Start time
            window_days: Number of days
            
        Returns:
            HistoricalPriceData or None
        """
        await self._ensure_session()
        
        # Convert symbol to Binance format (e.g., BTC -> BTCUSDT)
        binance_symbol = self._format_symbol(symbol)
        
        url = "https://api.binance.com/api/v3/klines"
        
        # Convert to milliseconds
        start_ms = int(start_timestamp.timestamp() * 1000)
        end_ms = int((start_timestamp + timedelta(days=window_days)).timestamp() * 1000)
        
        params = {
            'symbol': binance_symbol,
            'interval': '1d',  # Daily candles
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': 1000
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data:
                        self.logger.debug(f"Binance: No data for {binance_symbol}")
                        return None
                    
                    # Parse candles
                    candles = []
                    for candle in data:
                        candles.append(OHLCCandle(
                            timestamp=datetime.fromtimestamp(candle[0] / 1000),
                            open=float(candle[1]),
                            high=float(candle[2]),
                            low=float(candle[3]),
                            close=float(candle[4])
                        ))
                    
                    if not candles:
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
                    
                    self.logger.info(f"Binance: {binance_symbol} - {len(candles)} candles")
                    
                    return HistoricalPriceData(
                        symbol=symbol,
                        price_at_timestamp=candles[0].close,
                        ath_in_window=ath_price,
                        ath_timestamp=ath_candle.timestamp,
                        days_to_ath=days_to_ath,
                        candles=candles,
                        source='binance'
                    )
                else:
                    self.logger.debug(f"Binance HTTP {response.status} for {binance_symbol}")
                    return None
                    
        except Exception as e:
            self.logger.debug(f"Binance error for {binance_symbol}: {e}")
            return None
    
    def _format_symbol(self, symbol: str) -> str:
        """Convert symbol to Binance format."""
        # Remove common suffixes
        symbol = symbol.upper().replace('USD', '').replace('USDT', '')
        # Add USDT
        return f"{symbol}USDT"
    
    async def close(self):
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

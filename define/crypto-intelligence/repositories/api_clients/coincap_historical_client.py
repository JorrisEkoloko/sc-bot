"""CoinCap API client for historical OHLC data.

Free, unlimited, no API key required.
Docs: https://docs.coincap.io/
"""
import aiohttp
from typing import Optional, List
from datetime import datetime, timedelta
from domain.historical_price import OHLCCandle, HistoricalPriceData


class CoinCapHistoricalClient:
    """CoinCap API client for OHLC data."""
    
    def __init__(self, logger=None):
        """Initialize client."""
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('CoinCapHistoricalClient')
        
        # Common symbol mappings
        self.symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binance-coin',
            'SOL': 'solana',
            'ADA': 'cardano',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche',
            'MATIC': 'polygon',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash'
        }
    
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
        Fetch OHLC data from CoinCap.
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            start_timestamp: Start time
            window_days: Number of days
            
        Returns:
            HistoricalPriceData or None
        """
        await self._ensure_session()
        
        # Convert symbol to CoinCap ID
        asset_id = self._get_asset_id(symbol)
        if not asset_id:
            self.logger.debug(f"CoinCap: Unknown symbol {symbol}")
            return None
        
        url = f"https://api.coincap.io/v2/assets/{asset_id}/history"
        
        # CoinCap uses milliseconds
        start_ms = int(start_timestamp.timestamp() * 1000)
        end_ms = int((start_timestamp + timedelta(days=window_days)).timestamp() * 1000)
        
        params = {
            'interval': 'd1',  # Daily interval
            'start': start_ms,
            'end': end_ms
        }
        
        try:
            async with self._session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data.get('data'):
                        self.logger.debug(f"CoinCap: No data for {asset_id}")
                        return None
                    
                    # Parse price history into candles
                    candles = []
                    for point in data['data']:
                        price = float(point['priceUsd'])
                        candles.append(OHLCCandle(
                            timestamp=datetime.fromtimestamp(point['time'] / 1000),
                            open=price,
                            high=price,
                            low=price,
                            close=price
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
                    
                    self.logger.info(f"CoinCap: {asset_id} - {len(candles)} candles")
                    
                    return HistoricalPriceData(
                        symbol=symbol,
                        price_at_timestamp=candles[0].close,
                        ath_in_window=ath_price,
                        ath_timestamp=ath_candle.timestamp,
                        days_to_ath=days_to_ath,
                        candles=candles,
                        source='coincap'
                    )
                else:
                    self.logger.debug(f"CoinCap HTTP {response.status} for {asset_id}")
                    return None
                    
        except Exception as e:
            self.logger.debug(f"CoinCap error for {asset_id}: {e}")
            return None
    
    def _get_asset_id(self, symbol: str) -> Optional[str]:
        """Convert symbol to CoinCap asset ID."""
        symbol = symbol.upper()
        
        # Check direct mapping
        if symbol in self.symbol_map:
            return self.symbol_map[symbol]
        
        # Try lowercase symbol as fallback
        return symbol.lower()
    
    async def close(self):
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

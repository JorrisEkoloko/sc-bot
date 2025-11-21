"""Historical API coordinator - manages multiple OHLC API clients with fallback."""
import os
from typing import Optional, List
from datetime import datetime

from domain.historical_price import OHLCCandle, HistoricalPriceData
from repositories.cache.historical_price_cache import HistoricalPriceCache
from repositories.api_clients.cryptocompare_historical_client import CryptoCompareHistoricalClient
from repositories.api_clients.defillama_historical_client import DefiLlamaHistoricalClient
from repositories.api_clients.binance_historical_client import BinanceHistoricalClient
from repositories.api_clients.coincap_historical_client import CoinCapHistoricalClient
from repositories.api_clients.alphavantage_historical_client import AlphaVantageHistoricalClient
from repositories.api_clients.coinmarketcap_client import CoinMarketCapClient
from repositories.api_clients.dexscreener_client import DexScreenerClient
from utils.logger import setup_logger
from utils.symbol_mapper import SymbolMapper


class HistoricalAPICoordinator:
    """
    Coordinates multiple historical price API clients with intelligent fallback.
    
    Responsibilities:
    - Initialize and manage API clients
    - Implement fallback strategy across APIs
    - Handle caching
    - Resolve symbols using multiple sources
    """
    
    def __init__(
        self,
        cryptocompare_api_key: Optional[str] = None,
        alphavantage_api_key: Optional[str] = None,
        cache_dir: str = "data/cache",
        symbol_mapping_path: str = "data/symbol_mapping.json",
        logger=None
    ):
        """
        Initialize API coordinator.
        
        Args:
            cryptocompare_api_key: CryptoCompare API key (optional)
            alphavantage_api_key: Alpha Vantage API key (optional)
            cache_dir: Directory for cache storage
            symbol_mapping_path: Path to symbol mapping JSON
            logger: Logger instance
        """
        self.logger = logger or setup_logger('HistoricalAPICoordinator')
        
        # Initialize cache
        self.cache = HistoricalPriceCache(cache_dir=cache_dir, logger=self.logger)
        
        # Initialize API clients (in priority order)
        self.cryptocompare_client = CryptoCompareHistoricalClient(
            api_key=cryptocompare_api_key or "",
            logger=self.logger
        )
        self.binance_client = BinanceHistoricalClient(logger=self.logger)
        self.coincap_client = CoinCapHistoricalClient(logger=self.logger)
        self.defillama_client = DefiLlamaHistoricalClient(logger=self.logger)
        
        # Alpha Vantage (rate limited, use last)
        self.alphavantage_client = None
        if alphavantage_api_key:
            self.alphavantage_client = AlphaVantageHistoricalClient(
                api_key=alphavantage_api_key,
                logger=self.logger
            )
        
        # Initialize symbol mapper
        self.symbol_mapper = SymbolMapper(symbol_mapping_path)
        
        self.logger.info("HistoricalAPICoordinator initialized with 5 OHLC sources")
    
    async def fetch_price_at_timestamp(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[float]:
        """
        Fetch price at specific timestamp using CryptoCompare.
        
        Args:
            symbol: Token symbol
            timestamp: Exact timestamp
            
        Returns:
            Price in USD or None
        """
        price = await self.cryptocompare_client.get_price_at_timestamp(symbol, timestamp)
        if price:
            return price
        
        self.logger.warning(f"No historical price found for {symbol} at {timestamp}")
        return None
    
    async def fetch_ohlc_window_with_fallback(
        self,
        symbol: str,
        start_timestamp: datetime,
        window_days: int = 30,
        address: str = None,
        chain: str = None
    ) -> Optional[HistoricalPriceData]:
        """
        Fetch OHLC data with multi-API fallback.
        
        Fallback order:
        1. CryptoCompare (100K calls/month)
        2. Binance (unlimited, free)
        3. CoinCap (unlimited, free)
        4. DefiLlama (for address-based lookup)
        5. Alpha Vantage (25 calls/day, if API key provided)
        
        Args:
            symbol: Token symbol
            start_timestamp: Start of window
            window_days: Number of days to fetch
            address: Token address (optional, for DefiLlama)
            chain: Blockchain chain (optional, for DefiLlama)
            
        Returns:
            HistoricalPriceData or None
        """
        # Check cache first
        cache_key = self.cache.get_cache_key(symbol, start_timestamp, window_days)
        cached_data = self.cache.get(cache_key)
        if cached_data:
            self.logger.debug(f"Cache hit: {symbol} at {start_timestamp}")
            return cached_data
        
        # Try CryptoCompare first
        data = await self.cryptocompare_client.get_ohlc_window(
            symbol, start_timestamp, window_days
        )
        
        if data:
            self.logger.info(f"✅ CryptoCompare: {symbol} - {len(data.candles)} candles")
            self.cache.set(cache_key, data)
            return data
        
        # Try Binance
        self.logger.debug(f"CryptoCompare failed, trying Binance for {symbol}")
        data = await self.binance_client.get_ohlc_window(
            symbol, start_timestamp, window_days
        )
        
        if data:
            self.logger.info(f"✅ Binance: {symbol} - {len(data.candles)} candles")
            self.cache.set(cache_key, data)
            return data
        
        # Try CoinCap
        self.logger.debug(f"Binance failed, trying CoinCap for {symbol}")
        data = await self.coincap_client.get_ohlc_window(
            symbol, start_timestamp, window_days
        )
        
        if data:
            self.logger.info(f"✅ CoinCap: {symbol} - {len(data.candles)} candles")
            self.cache.set(cache_key, data)
            return data
        
        # Try DefiLlama if address provided (good for small tokens)
        if address and chain:
            data = await self._try_defillama_ohlc(address, chain, start_timestamp, window_days, symbol)
            if data:
                self.cache.set(cache_key, data)
                return data
        
        # Try DexScreener for recent price history (good for new/small tokens)
        if address and chain:
            data = await self._try_dexscreener_ohlc(address, chain, start_timestamp, symbol)
            if data:
                self.cache.set(cache_key, data)
                return data
        
        # Try Alpha Vantage as last resort (rate limited)
        if self.alphavantage_client:
            self.logger.debug(f"Trying Alpha Vantage for {symbol}")
            data = await self.alphavantage_client.get_ohlc_window(
                symbol, start_timestamp, window_days
            )
            
            if data:
                self.logger.info(f"✅ AlphaVantage: {symbol} - {len(data.candles)} candles")
                self.cache.set(cache_key, data)
                return data
        
        # Log at debug level - caller will log at appropriate level
        self.logger.debug(f"No OHLC data found for {symbol} from any source")
        return None
    
    async def resolve_symbol(
        self,
        symbol: str,
        address: Optional[str],
        chain: Optional[str]
    ) -> str:
        """
        Resolve correct symbol using mapping and APIs.
        
        Args:
            symbol: Original symbol
            address: Token address (optional)
            chain: Blockchain name (optional)
            
        Returns:
            Resolved symbol
        """
        if not address:
            return symbol
        
        # Try local symbol mapping first
        mapped_symbol = self.symbol_mapper.get_symbol_for_api(
            address, 'cryptocompare', chain or 'ethereum', symbol
        )
        if mapped_symbol != symbol:
            self.logger.info(f"Symbol mapping: {symbol} → {mapped_symbol} (from local mapping)")
            return mapped_symbol
        
        # Try CoinMarketCap API
        if chain:
            try:
                coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY', '')
                if coinmarketcap_key:
                    cmc_client = CoinMarketCapClient(coinmarketcap_key, logger=self.logger)
                    metadata = await cmc_client.get_token_metadata(address, chain)
                    await cmc_client.close()
                    
                    if metadata and metadata.get('symbol'):
                        correct_symbol = metadata['symbol']
                        if correct_symbol != symbol:
                            self.logger.info(f"Symbol mapping: {symbol} → {correct_symbol} (from CoinMarketCap)")
                            return correct_symbol
            except Exception as e:
                self.logger.debug(f"CoinMarketCap symbol lookup failed: {e}")
            
            # Fallback to DexScreener
            try:
                dex_client = DexScreenerClient(logger=self.logger)
                price_data = await dex_client.get_price(address, chain)
                await dex_client.close()
                
                if price_data and price_data.symbol:
                    correct_symbol = price_data.symbol
                    if correct_symbol != symbol:
                        self.logger.info(f"Symbol mapping: {symbol} → {correct_symbol} (from DexScreener)")
                        return correct_symbol
            except Exception as e:
                self.logger.debug(f"DexScreener symbol lookup failed: {e}")
        
        return symbol
    
    async def try_defillama_historical_price(
        self,
        address: str,
        chain: str,
        message_timestamp: datetime
    ) -> Optional[float]:
        """
        Try DefiLlama for historical price.
        
        Args:
            address: Token address
            chain: Blockchain name
            message_timestamp: Target timestamp
            
        Returns:
            Price or None
        """
        self.logger.info(f"Trying DefiLlama for historical price ({address[:10]}...)")
        
        from datetime import timedelta
        time_windows = [
            timedelta(0),
            timedelta(hours=-1),
            timedelta(hours=-24)
        ]
        
        for delta in time_windows:
            target_time = message_timestamp + delta
            price = await self.defillama_client.get_price_at_timestamp(address, chain, target_time)
            if price and price > 0:
                self.logger.info(f"[OK] Found historical price from DefiLlama: ${price:.8f}")
                return price
        
        return None
    
    async def try_dexscreener_current_price(
        self,
        address: str,
        chain: str
    ) -> Optional[float]:
        """
        Try DexScreener for current price as last resort.
        
        Args:
            address: Token address
            chain: Blockchain name
            
        Returns:
            Price or None
        """
        self.logger.info(f"Trying DexScreener for current price ({address[:10]}...)")
        
        try:
            dex_client = DexScreenerClient(logger=self.logger)
            price_data = await dex_client.get_price(address, chain)
            await dex_client.close()
            
            if price_data and price_data.price_usd > 0:
                self.logger.info(f"[OK] Found current price from DexScreener: ${price_data.price_usd:.6f}")
                return price_data.price_usd
        except Exception as e:
            self.logger.warning(f"DexScreener fallback failed: {e}")
        
        return None
    
    async def _try_defillama_ohlc(
        self,
        address: str,
        chain: str,
        start_timestamp: datetime,
        window_days: int,
        symbol: str
    ) -> Optional[HistoricalPriceData]:
        """Try DefiLlama for OHLC data."""
        self.logger.debug(f"Trying DefiLlama for {address[:10]}... on {chain}")
        prices = await self.defillama_client.get_ohlc_window(address, chain, start_timestamp, window_days)
        
        if not prices:
            return None
        
        self.logger.info(f"DefiLlama returned {len(prices)} price points")
        
        # Convert to HistoricalPriceData format
        candles = [
            OHLCCandle(
                timestamp=datetime.fromtimestamp(p['timestamp']),
                open=p['price'],
                high=p['price'],
                low=p['price'],
                close=p['price']
            ) for p in prices
        ]
        
        # Validate that we have real price data (not all zeros)
        max_price = max(c.high for c in candles) if candles else 0
        if max_price <= 0:
            return None
        
        # Calculate ATH from candles
        ath_price = max_price
        ath_candle = next(c for c in candles if c.high == ath_price)
        
        # Ensure both timestamps are timezone-aware for comparison
        ath_ts = ath_candle.timestamp
        start_ts = start_timestamp
        if ath_ts.tzinfo is None:
            from datetime import timezone
            ath_ts = ath_ts.replace(tzinfo=timezone.utc)
        if start_ts.tzinfo is None:
            from datetime import timezone
            start_ts = start_ts.replace(tzinfo=timezone.utc)
        
        days_to_ath = (ath_ts - start_ts).total_seconds() / 86400
        
        data = HistoricalPriceData(
            symbol=symbol,
            price_at_timestamp=candles[0].close if candles else 0.0,
            ath_in_window=ath_price,
            ath_timestamp=ath_candle.timestamp,
            days_to_ath=days_to_ath,
            candles=candles,
            source='defillama'
        )
        
        self.logger.info(f"✅ DefiLlama: {symbol} - {len(candles)} candles, ATH ${ath_price:.6f} on day {days_to_ath:.1f}")
        return data
    
    async def _try_dexscreener_ohlc(
        self,
        address: str,
        chain: str,
        start_timestamp: datetime,
        symbol: str
    ) -> Optional[HistoricalPriceData]:
        """Try DexScreener for current price as baseline."""
        self.logger.debug(f"Trying DexScreener historical for {address[:10]}...")
        
        try:
            dex_client = DexScreenerClient(logger=self.logger)
            price_data = await dex_client.get_price(address, chain)
            await dex_client.close()
            
            if not price_data or price_data.price_usd <= 0:
                return None
            
            current_price = price_data.price_usd
            
            # Create a single candle at the start timestamp with current price
            candle = OHLCCandle(
                timestamp=start_timestamp,
                open=current_price,
                high=current_price,
                low=current_price,
                close=current_price
            )
            
            data = HistoricalPriceData(
                symbol=symbol,
                price_at_timestamp=current_price,
                ath_in_window=current_price,
                ath_timestamp=start_timestamp,
                days_to_ath=0.0,
                candles=[candle],
                source='dexscreener_current'
            )
            
            self.logger.info(
                f"✅ DexScreener: {symbol} - Using current price ${current_price:.8f} "
                f"as baseline (no historical data available)"
            )
            return data
            
        except Exception as e:
            self.logger.debug(f"DexScreener historical fallback failed: {e}")
            return None
    
    async def close(self):
        """Close all API client sessions and flush cache."""
        # Flush any pending cache entries
        self.cache.flush()
        
        # Close all API clients
        await self.cryptocompare_client.close()
        await self.binance_client.close()
        await self.coincap_client.close()
        await self.defillama_client.close()
        
        if self.alphavantage_client:
            await self.alphavantage_client.close()
        
        self.logger.info("HistoricalAPICoordinator closed")

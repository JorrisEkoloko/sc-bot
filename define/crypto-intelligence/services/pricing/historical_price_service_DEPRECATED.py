"""Historical price service for ROI calculation (business logic layer)."""
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from domain.historical_price import OHLCCandle, HistoricalPriceData
from repositories.cache.historical_price_cache import HistoricalPriceCache
from repositories.api_clients.cryptocompare_historical_client import CryptoCompareHistoricalClient
from repositories.api_clients.defillama_historical_client import DefiLlamaHistoricalClient
from repositories.api_clients.binance_historical_client import BinanceHistoricalClient
from repositories.api_clients.coincap_historical_client import CoinCapHistoricalClient
from repositories.api_clients.alphavantage_historical_client import AlphaVantageHistoricalClient
from repositories.api_clients.coinmarketcap_client import CoinMarketCapClient
from repositories.api_clients.dexscreener_client import DexScreenerClient
from repositories.api_clients.etherscan_client import EtherscanClient
from utils.logger import setup_logger
from utils.symbol_mapper import SymbolMapper


class HistoricalPriceService:
    """
    Business logic for historical price retrieval and ROI calculation.
    
    Coordinates between cache and API clients to fetch historical data.
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
        Initialize service.
        
        Args:
            cryptocompare_api_key: CryptoCompare API key (optional)
            alphavantage_api_key: Alpha Vantage API key (optional)
            cache_dir: Directory for cache storage
            symbol_mapping_path: Path to symbol mapping JSON
            logger: Logger instance
        """
        self.logger = logger or setup_logger('HistoricalPriceService')
        
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
        
        self.logger.info("HistoricalPriceService initialized with 5 OHLC sources")
    
    async def fetch_price_at_timestamp(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[float]:
        """
        Fetch price at specific timestamp.
        
        Args:
            symbol: Token symbol
            timestamp: Exact timestamp
            
        Returns:
            Price in USD or None
        """
        # Try CryptoCompare first
        price = await self.cryptocompare_client.get_price_at_timestamp(symbol, timestamp)
        if price:
            return price
        
        self.logger.warning(f"No historical price found for {symbol} at {timestamp}")
        return None
    
    async def fetch_closest_entry_price(
        self,
        symbol: str,
        message_timestamp: datetime,
        address: Optional[str] = None,
        chain: Optional[str] = None
    ) -> Tuple[Optional[float], str]:
        """
        Fetch the closest available price to message timestamp with smart fallback.
        
        Strategy:
        1. Get correct symbol from mapping/APIs
        2. Try exact message timestamp
        3. Try ±1 hour window
        4. Try ±6 hours window
        5. Try ±24 hours window
        6. Try DefiLlama for small tokens
        7. Try DexScreener current price
        
        Args:
            symbol: Token symbol
            message_timestamp: Message timestamp
            address: Optional token contract address
            chain: Optional blockchain name
            
        Returns:
            Tuple of (price, source_description)
        """
        self.logger.info(f"Fetching closest entry price for {symbol} at {message_timestamp}")
        
        # STEP 1: Get correct symbol
        correct_symbol = await self._resolve_symbol(symbol, address, chain)
        symbol = correct_symbol
        
        # STEP 2: Try historical prices with increasing time windows
        time_windows = [
            (timedelta(0), "exact_time"),
            (timedelta(hours=-1), "1h_before"),
            (timedelta(hours=1), "1h_after"),
            (timedelta(hours=-6), "6h_before"),
            (timedelta(hours=6), "6h_after"),
            (timedelta(hours=-24), "24h_before"),
            (timedelta(hours=24), "24h_after"),
        ]
        
        for delta, source in time_windows:
            target_time = message_timestamp + delta
            price = await self.fetch_price_at_timestamp(symbol, target_time)
            if price and price > 0:
                self.logger.info(f"[OK] Found price {source}: ${price:.6f}")
                return price, source
        
        # STEP 3: Try DefiLlama for small tokens
        if address and chain:
            price = await self._try_defillama_historical(address, chain, message_timestamp)
            if price:
                return price, "defillama_historical"
        
        # STEP 4: Try DexScreener current price as last resort
        if address and chain:
            price = await self._try_dexscreener_current(address, chain)
            if price:
                return price, "dexscreener_current"
        
        self.logger.warning(f"[WARNING] No historical price found for {symbol}")
        return None, "not_found"
    
    async def fetch_ohlc_window(
        self,
        symbol: str,
        start_timestamp: datetime,
        window_days: int = 30,
        address: str = None,
        chain: str = None
    ) -> Optional[HistoricalPriceData]:
        """
        Fetch OHLC data for a time window to find ATH with multi-API fallback.
        
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
            self.logger.debug(f"Trying DefiLlama for {address[:10]}... on {chain}")
            prices = await self.defillama_client.get_ohlc_window(address, chain, start_timestamp, window_days)
            if prices:
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
                if max_price > 0:
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
                    self.cache.set(cache_key, data)
                    return data
        
        # Try DexScreener for recent price history (good for new/small tokens)
        if address and chain:
            self.logger.debug(f"Trying DexScreener historical for {address[:10]}...")
            try:
                dex_client = DexScreenerClient(logger=self.logger)
                price_data = await dex_client.get_price(address, chain)
                await dex_client.close()
                
                if price_data and price_data.price_usd > 0:
                    # DexScreener doesn't provide historical candles, but we can create
                    # a synthetic candle using current price as a fallback
                    current_price = price_data.price_usd
                    
                    # Create a single candle at the start timestamp with current price
                    # This allows tracking to begin from this point forward
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
                    self.cache.set(cache_key, data)
                    return data
            except Exception as e:
                self.logger.debug(f"DexScreener historical fallback failed: {e}")
        
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
    
    async def fetch_forward_ohlc_with_ath(
        self,
        symbol: str,
        entry_timestamp: datetime,
        window_days: int = 30,
        address: str = None,
        chain: str = None
    ) -> Optional[Dict]:
        """
        Fetch forward OHLC data and calculate ATH from candles.
        
        Args:
            symbol: Token symbol
            entry_timestamp: Entry timestamp
            window_days: Number of days forward
            address: Token address (optional, for DefiLlama)
            chain: Blockchain chain (optional, for DefiLlama)
            
        Returns:
            Dictionary with ATH data or None
        """
        self.logger.info(f"Fetching forward OHLC for {symbol} from {entry_timestamp} ({window_days} days)")
        
        historical_data = await self.fetch_ohlc_window(symbol, entry_timestamp, window_days, address, chain)
        
        if not historical_data or not historical_data.candles:
            # Don't log here - caller will handle logging
            return None
        
        # Calculate data completeness
        expected_candles = window_days
        actual_candles = len(historical_data.candles)
        # Handle edge case where window_days is 0
        if expected_candles > 0:
            data_completeness = min(actual_candles / expected_candles, 1.0)
        else:
            data_completeness = 1.0 if actual_candles > 0 else 0.0
        
        self.logger.info(
            f"[OK] Found {actual_candles}/{expected_candles} candles "
            f"({data_completeness*100:.1f}% complete)"
        )
        
        return {
            'ath_price': historical_data.ath_in_window,
            'ath_timestamp': historical_data.ath_timestamp,
            'days_to_ath': historical_data.days_to_ath,
            'candles': historical_data.candles,
            'entry_price': historical_data.price_at_timestamp,
            'source': historical_data.source,
            'data_completeness': data_completeness
        }
    
    def calculate_checkpoint_rois_from_ohlc(
        self,
        entry_price: float,
        entry_timestamp: datetime,
        checkpoints: List[Tuple[str, timedelta]],
        candles: List[OHLCCandle]
    ) -> Dict[str, float]:
        """
        Calculate ROI at each checkpoint using OHLC candle data.
        
        Args:
            entry_price: Entry price
            entry_timestamp: Entry timestamp
            checkpoints: List of (checkpoint_name, timedelta) tuples
            candles: List of OHLC candles
            
        Returns:
            Dict of checkpoint_name -> roi_multiplier
        """
        self.logger.info(f"Calculating {len(checkpoints)} checkpoint ROIs from {len(candles)} candles")
        
        checkpoint_rois = {}
        
        for checkpoint_name, delta in checkpoints:
            checkpoint_time = entry_timestamp + delta
            
            # Find the closest candle to checkpoint time
            closest_candle = self._find_closest_candle(candles, checkpoint_time)
            
            if closest_candle:
                checkpoint_price = closest_candle.close
                roi_multiplier = checkpoint_price / entry_price
                
                checkpoint_rois[checkpoint_name] = roi_multiplier
                
                self.logger.debug(
                    f"  {checkpoint_name}: ${checkpoint_price:.6f} "
                    f"({roi_multiplier:.3f}x, {(roi_multiplier-1)*100:+.1f}%)"
                )
            else:
                self.logger.warning(f"  {checkpoint_name}: No candle found near {checkpoint_time}")
        
        return checkpoint_rois
    
    def calculate_smart_checkpoints(
        self,
        message_date: datetime,
        current_date: Optional[datetime] = None
    ) -> List[Tuple[str, timedelta]]:
        """
        Calculate which checkpoints have been reached based on elapsed time.
        
        Args:
            message_date: Date of the original message
            current_date: Current date (default: now)
            
        Returns:
            List of (checkpoint_name, timedelta) for reached checkpoints
        """
        from datetime import timezone
        
        if current_date is None:
            current_date = datetime.now(timezone.utc)
        
        # Ensure both datetimes are timezone-aware
        msg_date = message_date if message_date.tzinfo else message_date.replace(tzinfo=timezone.utc)
        
        elapsed = current_date - msg_date
        
        # All possible checkpoints
        all_checkpoints = [
            ('1h', timedelta(hours=1)),
            ('4h', timedelta(hours=4)),
            ('24h', timedelta(hours=24)),
            ('3d', timedelta(days=3)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30))
        ]
        
        # Return only reached checkpoints
        reached = [(name, delta) for name, delta in all_checkpoints if elapsed >= delta]
        
        self.logger.debug(
            f"Elapsed: {elapsed.days} days - "
            f"Reached checkpoints: {[name for name, _ in reached]}"
        )
        
        return reached
    
    async def fetch_batch_prices_at_timestamp(
        self,
        symbols: List[str],
        timestamp: datetime,
        max_concurrent: int = 5
    ) -> Dict[str, Optional[float]]:
        """
        Fetch prices for multiple tokens at specific timestamp (batch processing).
        
        Args:
            symbols: List of token symbols
            timestamp: Exact timestamp
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dict of symbol -> price
        """
        self.logger.info(f"Batch fetching prices for {len(symbols)} tokens at {timestamp}")
        
        results = {}
        
        for i in range(0, len(symbols), max_concurrent):
            batch = symbols[i:i + max_concurrent]
            
            tasks = [
                self.fetch_price_at_timestamp(symbol, timestamp)
                for symbol in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error fetching {symbol}: {result}")
                    results[symbol] = None
                else:
                    results[symbol] = result
            
            if i + max_concurrent < len(symbols):
                await asyncio.sleep(0.5)
        
        successful = sum(1 for r in results.values() if r is not None and r > 0)
        self.logger.info(f"Batch complete: {successful}/{len(symbols)} successful")
        
        return results
    
    async def _resolve_symbol(
        self,
        symbol: str,
        address: Optional[str],
        chain: Optional[str]
    ) -> str:
        """Resolve correct symbol using mapping and APIs."""
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
    
    async def _try_defillama_historical(
        self,
        address: str,
        chain: str,
        message_timestamp: datetime
    ) -> Optional[float]:
        """Try DefiLlama for historical price."""
        self.logger.info(f"Trying DefiLlama for historical price ({address[:10]}...)")
        
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
    
    async def _try_dexscreener_current(
        self,
        address: str,
        chain: str
    ) -> Optional[float]:
        """Try DexScreener for current price as last resort."""
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
    
    def _find_closest_candle(
        self,
        candles: List[OHLCCandle],
        target_time: datetime
    ) -> Optional[OHLCCandle]:
        """Find the candle closest to target time."""
        if not candles:
            return None
        
        # Determine if these are daily or hourly candles
        is_daily_candles = False
        if len(candles) > 1:
            candle_interval = abs((candles[1].timestamp - candles[0].timestamp).total_seconds())
            is_daily_candles = candle_interval > 43200  # More than 12 hours = daily candles
        
        if is_daily_candles:
            # For daily candles, match by calendar day
            target_date = target_time.date()
            for candle in candles:
                candle_date = candle.timestamp.date()
                day_diff = abs((candle_date - target_date).days)
                if day_diff <= 1:
                    return candle
            return None
        else:
            # For hourly/minute candles, find closest by timestamp
            closest = min(
                candles,
                key=lambda c: abs((c.timestamp - target_time).total_seconds())
            )
            
            time_diff = abs((closest.timestamp - target_time).total_seconds())
            max_diff = 7200  # Allow 2 hours for hourly candles
            
            if time_diff <= max_diff:
                return closest
            
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
        
        self.logger.info("HistoricalPriceService closed")

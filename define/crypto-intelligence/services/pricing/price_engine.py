"""Price engine with multi-API failover.

Orchestrates price fetching across multiple APIs with caching and rate limiting.
"""
import asyncio
from typing import Optional
from cachetools import TTLCache

from config.price_config import PriceConfig
from domain.price_data import PriceData
from repositories.api_clients import (
    CoinGeckoClient,
    BirdeyeClient,
    MoralisClient,
    DexScreenerClient,
    DefiLlamaClient,
    CryptoCompareClient,
    TwelveDataClient,
    BlockscoutClient,
    GoPlusClient
)
from infrastructure.blockchain import ContractReader
from utils.rate_limiter import RateLimiter
from utils.logger import setup_logger
import os


class PriceEngine:
    """Multi-API price fetching with failover and caching."""
    
    def __init__(self, config: PriceConfig, logger=None):
        """
        Initialize price engine.
        
        FIXED: Issue #10 - Added _closing flag to track partial cleanup
        
        Args:
            config: Price configuration
            logger: Optional logger instance
        """
        # Initialize close lock immediately to prevent race conditions
        self._close_lock = asyncio.Lock()
        self._closed = False
        self._closing = False  # Track if currently closing
        
        self.config = config
        self.logger = logger or setup_logger('PriceEngine')
        
        # Initialize API clients
        self.clients = {
            'coingecko': CoinGeckoClient(config.coingecko_api_key),
            'birdeye': BirdeyeClient(config.birdeye_api_key),
            'moralis': MoralisClient(config.moralis_api_key),
            'defillama': DefiLlamaClient(),
            'dexscreener': DexScreenerClient(),
            'blockscout': BlockscoutClient(),
            'goplus': GoPlusClient()
        }
        
        # Initialize CryptoCompare client for historical data (optional)
        cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        if cryptocompare_key:
            self.cryptocompare_client = CryptoCompareClient(cryptocompare_key, self.logger)
            self.logger.info("CryptoCompare client initialized for historical data (100K calls/month FREE)")
        else:
            self.cryptocompare_client = None
            self.logger.debug("CryptoCompare client not initialized (no API key)")
        
        # Initialize Twelve Data client for historical data fallback (optional)
        twelvedata_key = os.getenv('TWELVEDATA_API_KEY')
        if twelvedata_key:
            self.twelvedata_client = TwelveDataClient(twelvedata_key, self.logger)
            self.logger.info("Twelve Data client initialized for historical data fallback")
        else:
            self.twelvedata_client = None
            self.logger.debug("Twelve Data client not initialized (no API key)")
        
        # Initialize cache (5-minute TTL)
        self.cache = TTLCache(maxsize=1000, ttl=config.cache_ttl)
        
        # Initialize contract reader for blockchain interactions
        self.contract_reader = ContractReader(logger=self.logger)
        
        # Initialize rate limiters (90% of actual limits)
        self.rate_limiters = {
            'coingecko': RateLimiter(int(50 * config.rate_limit_buffer), 60),
            'birdeye': RateLimiter(int(60 * config.rate_limit_buffer), 60),
            'moralis': RateLimiter(int(25 * config.rate_limit_buffer), 60),
            'defillama': RateLimiter(int(100 * config.rate_limit_buffer), 60),  # Conservative limit (no official docs)
            'dexscreener': RateLimiter(int(300 * config.rate_limit_buffer), 60),
            'blockscout': RateLimiter(int(9 * config.rate_limit_buffer), 1),  # 10 req/sec = 9 with buffer
            'goplus': RateLimiter(int(90 * config.rate_limit_buffer), 60),  # Conservative 90/min (no official limit)
            'cryptocompare': RateLimiter(int(55 * config.rate_limit_buffer), 60)  # ~3,333/day = 55/min
        }
        
        self.logger.info("Price engine initialized with 7 APIs (CoinGecko, Birdeye, Moralis, DefiLlama, DexScreener, Blockscout, GoPlus)")
    
    async def close(self):
        """
        Close all API client sessions (idempotent).
        
        FIXED: Issue #10 - Resource Lifecycle Conflict
        Tracks which clients were successfully closed.
        Only marks as closed if ALL clients close successfully.
        
        Based on RAII pattern and resource management best practices.
        """
        # Use async lock to prevent concurrent closes
        async with self._close_lock:
            if self._closed:
                if hasattr(self, 'logger'):
                    self.logger.debug("Price engine already closed")
                return
            
            # Mark as closing (not closed yet)
            self._closing = True
        
        if hasattr(self, 'logger'):
            self.logger.info("Closing API client sessions...")
        
        # Track successful closures
        closed_clients = set()
        failed_clients = []
        
        # Safely close clients only if they exist
        clients = getattr(self, 'clients', {})
        for name in ['coingecko', 'birdeye', 'moralis', 'defillama', 'dexscreener', 'blockscout', 'goplus']:
            client = clients.get(name)
            if client:
                try:
                    await client.close()
                    closed_clients.add(name)
                    if hasattr(self, 'logger'):
                        self.logger.debug(f"✓ Closed {name} client")
                except Exception as e:
                    failed_clients.append((name, e))
                    if hasattr(self, 'logger'):
                        self.logger.error(f"✗ Error closing {name} client: {e}")
        
        # Close optional clients
        optional_clients = [
            ('cryptocompare_client', 'cryptocompare'),
            ('twelvedata_client', 'twelvedata')
        ]
        
        for attr_name, display_name in optional_clients:
            client = getattr(self, attr_name, None)
            if client:
                try:
                    await client.close()
                    closed_clients.add(display_name)
                    if hasattr(self, 'logger'):
                        self.logger.debug(f"✓ Closed {display_name} client")
                except Exception as e:
                    failed_clients.append((display_name, e))
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"✗ Error closing {display_name} client: {e}")
        
        # Update state based on results
        async with self._close_lock:
            self._closing = False
            if failed_clients:
                # Partial failure - log but mark as closed to prevent retry loops
                if hasattr(self, 'logger'):
                    self.logger.warning(
                        f"Price engine closed with {len(failed_clients)} failures: "
                        f"{[name for name, _ in failed_clients]}"
                    )
                self._closed = True
            else:
                # Complete success
                self._closed = True
                if hasattr(self, 'logger'):
                    self.logger.info(f"✅ Price engine closed ({len(closed_clients)} clients)")
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """
        Get price with failover and data enrichment.
        
        Strategy:
        1. Try APIs in sequence to get price
        2. If price found but missing critical fields (symbol), try DexScreener for enrichment
        3. Merge data from multiple sources
        
        Args:
            address: Token contract address
            chain: Blockchain name ('evm' or 'solana')
            
        Returns:
            PriceData object or None if all APIs fail
        """
        cache_key = f"{chain}:{address}"
        
        # Check cache first
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        self.logger.debug(f"Cache miss for {cache_key}, fetching from APIs")
        
        # Try APIs in sequence based on chain
        api_sequence = self._get_api_sequence(chain)
        price_data = None
        
        for api_name in api_sequence:
            try:
                await self.rate_limiters[api_name].acquire()
                client = self.clients[api_name]
                data = await client.get_price(address, chain)
                
                if data:
                    data.source = api_name
                    price_data = data
                    self.logger.info(f"Price fetched from {api_name}: ${data.price_usd:.6f}")
                    break  # Got price data, exit loop
                    
            except asyncio.CancelledError:
                # System is shutting down - stop immediately
                self.logger.debug(f"Price fetch cancelled for {address}")
                raise  # Re-raise to propagate cancellation
            except Exception as e:
                self.logger.warning(f"{api_name} failed for {address}: {e}")
                continue
        
        if not price_data:
            self.logger.error(f"All APIs failed for {address} on {chain}")
            return None
        
        # Enrich missing fields with parallel API calls (DexScreener + Blockscout)
        needs_enrichment = (
            (not price_data.symbol or price_data.symbol == 'UNKNOWN') or
            not price_data.market_cap or
            not price_data.volume_24h
        )
        
        if price_data.source != 'dexscreener' and needs_enrichment:
            missing_fields = []
            if not price_data.symbol or price_data.symbol == 'UNKNOWN':
                missing_fields.append('symbol')
            if not price_data.market_cap:
                missing_fields.append('market_cap')
            if not price_data.volume_24h:
                missing_fields.append('volume_24h')
            
            self.logger.debug(f"Missing fields from {price_data.source}: {', '.join(missing_fields)}. Trying enrichment APIs in parallel")
            
            # Call DexScreener and Blockscout in parallel for faster enrichment
            enrichment_tasks = []
            
            # DexScreener task
            async def fetch_dexscreener():
                try:
                    await self.rate_limiters['dexscreener'].acquire()
                    return await self.clients['dexscreener'].get_price(address, chain)
                except Exception as e:
                    self.logger.debug(f"DexScreener enrichment failed: {e}")
                    return None
            
            enrichment_tasks.append(fetch_dexscreener())
            
            # Blockscout task (EVM only)
            if chain != 'solana':
                async def fetch_blockscout():
                    try:
                        await self.rate_limiters['blockscout'].acquire()
                        return await self.clients['blockscout'].get_price(address, chain)
                    except Exception as e:
                        self.logger.debug(f"Blockscout enrichment failed: {e}")
                        return None
                
                enrichment_tasks.append(fetch_blockscout())
            
            # Execute enrichment calls in parallel
            enrichment_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            # Process DexScreener results
            dex_data = enrichment_results[0] if len(enrichment_results) > 0 and not isinstance(enrichment_results[0], Exception) else None
            if dex_data:
                if dex_data.symbol and dex_data.symbol != 'UNKNOWN':
                    price_data.symbol = dex_data.symbol
                    self.logger.info(f"Enriched symbol from DexScreener: {dex_data.symbol}")
                
                if not price_data.market_cap and dex_data.market_cap:
                    price_data.market_cap = dex_data.market_cap
                    self.logger.debug(f"Enriched market_cap from DexScreener: ${dex_data.market_cap:,.0f}")
                
                if not price_data.volume_24h and dex_data.volume_24h:
                    price_data.volume_24h = dex_data.volume_24h
                    self.logger.debug(f"Enriched volume_24h from DexScreener")
                
                if not price_data.liquidity_usd and dex_data.liquidity_usd:
                    price_data.liquidity_usd = dex_data.liquidity_usd
                    self.logger.debug(f"Enriched liquidity from DexScreener")
                
                if not price_data.pair_created_at and dex_data.pair_created_at:
                    price_data.pair_created_at = dex_data.pair_created_at
                    self.logger.debug(f"Enriched pair_created_at from DexScreener")
                
                price_data.source = f"{price_data.source}+dexscreener"
            
            # Process Blockscout results (if symbol still missing)
            if (not price_data.symbol or price_data.symbol == 'UNKNOWN') and len(enrichment_results) > 1:
                blockscout_data = enrichment_results[1] if not isinstance(enrichment_results[1], Exception) else None
                if blockscout_data and blockscout_data.symbol:
                    price_data.symbol = blockscout_data.symbol
                    self.logger.info(f"Enriched symbol from Blockscout: {blockscout_data.symbol}")
                    
                    # Update source to indicate Blockscout enrichment
                    if '+' in price_data.source:
                        price_data.source = f"{price_data.source}+blockscout"
                    else:
                        price_data.source = f"{price_data.source}+blockscout"
        
        # If symbol STILL missing, try reading from blockchain contract (EVM only)
        if (not price_data.symbol or price_data.symbol == 'UNKNOWN') and chain != 'solana':
            self.logger.debug(f"Symbol still missing. Trying to read from contract for {address}")
            try:
                symbol_from_contract = await self.contract_reader.read_symbol_from_contract(address, chain)
                if symbol_from_contract:
                    price_data.symbol = symbol_from_contract
                    self.logger.info(f"Enriched symbol from contract: {symbol_from_contract}")
                    price_data.source = f"{price_data.source}+contract"
            except Exception as e:
                self.logger.debug(f"Contract symbol read failed: {e}")
        
        # If symbol STILL missing, try GoPlus as fallback (multi-chain support)
        if not price_data.symbol or price_data.symbol == 'UNKNOWN':
            self.logger.debug(f"Symbol still missing after contract read. Trying GoPlus for {address}")
            try:
                await self.rate_limiters['goplus'].acquire()
                goplus_data = await self.clients['goplus'].get_price(address, chain)
                
                if goplus_data and goplus_data.symbol:
                    price_data.symbol = goplus_data.symbol
                    self.logger.info(f"Enriched symbol from GoPlus: {goplus_data.symbol}")
                    
                    # Update source to indicate GoPlus enrichment
                    if '+' in price_data.source:
                        price_data.source = f"{price_data.source}+goplus"
                    else:
                        price_data.source = f"{price_data.source}+goplus"
                        
            except Exception as e:
                self.logger.debug(f"GoPlus enrichment failed: {e}")
        
        # If symbol STILL missing, try DefiLlama as final fallback (multi-chain support)
        if not price_data.symbol or price_data.symbol == 'UNKNOWN':
            self.logger.debug(f"Symbol still missing after GoPlus. Trying DefiLlama for {address}")
            try:
                await self.rate_limiters['defillama'].acquire()
                defillama_data = await self.clients['defillama'].get_price(address, chain)
                
                if defillama_data and defillama_data.symbol:
                    price_data.symbol = defillama_data.symbol
                    self.logger.info(f"Enriched symbol from DefiLlama: {defillama_data.symbol}")
                    
                    # Update source to indicate DefiLlama enrichment
                    if '+' in price_data.source:
                        price_data.source = f"{price_data.source}+defillama"
                    else:
                        price_data.source = f"{price_data.source}+defillama"
                        
            except Exception as e:
                self.logger.debug(f"DefiLlama enrichment failed: {e}")
        
        # Fetch ATH data from CoinGecko if not already present (for all tokens, not just CoinGecko-sourced)
        if not price_data.ath:
            try:
                self.logger.debug(f"Fetching ATH data from CoinGecko for {address}")
                await self.rate_limiters['coingecko'].acquire()
                token_info = await self.clients['coingecko'].get_token_info(address, chain)
                if token_info:
                    price_data.ath = token_info.get('ath')
                    price_data.ath_date = token_info.get('ath_date')
                    price_data.ath_change_percentage = token_info.get('ath_change_percentage')
                    if price_data.ath:
                        self.logger.info(f"Fetched ATH from CoinGecko: ${price_data.ath:.6f}")
            except Exception as e:
                self.logger.debug(f"Failed to fetch ATH data: {e}")
        
        # Cache and return (market intelligence enrichment moved to DataEnrichmentService)
        self.cache[cache_key] = price_data
        return price_data
    
    async def get_historical_data(self, address: str, chain: str, symbol: str = None) -> Optional[dict]:
        """
        Get historical ATH/ATL data with fallback strategy.
        
        Primary: CoinGecko (works with contract addresses, provides exact timestamps)
        Fallback: Twelve Data (requires symbol, for major coins, daily granularity)
        
        Note: Historical data is optional. If unavailable, the HISTORICAL table will
        remain empty, which is acceptable as this data is supplementary.
        
        Args:
            address: Token contract address
            chain: Blockchain name ('evm' or 'solana')
            symbol: Token symbol (optional, for Twelve Data fallback)
            
        Returns:
            Dictionary with historical data or None if not available
        """
        # Primary: Try CoinGecko
        try:
            await self.rate_limiters['coingecko'].acquire()
            coingecko_client = self.clients['coingecko']
            historical_data = await coingecko_client.get_historical_data(address, chain)
            
            if historical_data:
                self.logger.info(f"Historical data fetched from CoinGecko for {address}")
                return historical_data
            else:
                self.logger.debug(f"CoinGecko: No historical data for {address}")
                
        except Exception as e:
            self.logger.debug(f"CoinGecko historical data failed for {address}: {e}")
        
        # Fallback: Try Twelve Data (only for major cryptocurrencies)
        # Twelve Data only supports major coins, not obscure tokens or LP pairs
        # Skip if: no symbol, LP pair (contains '/'), or unknown symbol
        if symbol and self.twelvedata_client and '/' not in symbol and symbol != 'UNKNOWN':
            # Only try Twelve Data for major crypto symbols
            major_symbols = {
                'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOT', 'DOGE', 'MATIC', 'AVAX',
                'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'ALGO', 'VET', 'FIL', 'TRX'
            }
            if symbol.upper() in major_symbols:
                try:
                    self.logger.debug(f"Attempting Twelve Data fallback for {symbol}/USD")
                    historical_data = await self.twelvedata_client.get_historical_ohlcv(f"{symbol}/USD")
                    
                    if historical_data:
                        self.logger.info(f"Historical data fetched from Twelve Data for {symbol}/USD")
                        return historical_data
                    else:
                        self.logger.debug(f"Twelve Data: No historical data for {symbol}/USD")
                        
                except Exception as e:
                    self.logger.debug(f"Twelve Data historical data failed for {symbol}/USD: {e}")
            else:
                self.logger.debug(f"Skipping Twelve Data for non-major crypto: {symbol}")
        
        self.logger.debug(f"No historical data available for {address}")
        return None
    
    async def get_historical_ohlc(self, symbol: str, days: int = 30) -> Optional[list]:
        """
        Get historical OHLC (candlestick) data for a token.
        
        Primary: CryptoCompare (100K calls/month FREE, supports most tokens)
        Fallback: Twelve Data (paid, major coins only)
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH', 'SOL')
            days: Number of days of historical data (default: 30)
            
        Returns:
            List of OHLC dictionaries or None if not available
            
        Example usage:
            # Get 30 days of BTC price history
            ohlc_data = await price_engine.get_historical_ohlc('BTC', days=30)
            
            # Find ATH in the data
            if ohlc_data:
                ath_price = max(candle['high'] for candle in ohlc_data)
                ath_candle = next(c for c in ohlc_data if c['high'] == ath_price)
        """
        # Primary: Try CryptoCompare (FREE, 100K calls/month)
        if self.cryptocompare_client:
            try:
                self.logger.debug(f"Fetching {days} days of OHLC data for {symbol} from CryptoCompare")
                ohlc_data = await self.cryptocompare_client.get_daily_ohlc(symbol, limit=days)
                
                if ohlc_data:
                    self.logger.info(f"Historical OHLC fetched from CryptoCompare: {len(ohlc_data)} candles for {symbol}")
                    return ohlc_data
                else:
                    self.logger.debug(f"CryptoCompare: No OHLC data for {symbol}")
                    
            except Exception as e:
                self.logger.debug(f"CryptoCompare OHLC failed for {symbol}: {e}")
        else:
            self.logger.debug("CryptoCompare client not initialized, skipping")
        
        # Fallback: Try Twelve Data (paid, major coins only)
        if symbol and self.twelvedata_client and '/' not in symbol and symbol != 'UNKNOWN':
            major_symbols = {
                'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOT', 'DOGE', 'MATIC', 'AVAX',
                'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'ALGO', 'VET', 'FIL', 'TRX'
            }
            if symbol.upper() in major_symbols:
                try:
                    self.logger.debug(f"Attempting Twelve Data fallback for {symbol}/USD OHLC")
                    # Note: Twelve Data client would need a get_ohlc method
                    # For now, log that fallback is available but not implemented
                    self.logger.debug(f"Twelve Data OHLC fallback available but not implemented for {symbol}")
                except Exception as e:
                    self.logger.debug(f"Twelve Data OHLC failed for {symbol}: {e}")
            else:
                self.logger.debug(f"Skipping Twelve Data for non-major crypto: {symbol}")
        
        self.logger.debug(f"No historical OHLC data available for {symbol}")
        return None
    
    async def get_price_at_timestamp(self, symbol: str, timestamp: int) -> Optional[float]:
        """
        Get price at a specific timestamp (historical price).
        
        Primary: CryptoCompare (100K calls/month FREE)
        Fallback: Twelve Data (paid, major coins only)
        
        Args:
            symbol: Token symbol (e.g., 'BTC', 'ETH')
            timestamp: Unix timestamp in seconds
            
        Returns:
            Price as float or None if not available
            
        Example usage:
            # Get BTC price on Jan 1, 2021
            from datetime import datetime
            timestamp = int(datetime(2021, 1, 1).timestamp())
            price = await price_engine.get_price_at_timestamp('BTC', timestamp)
        """
        # Primary: Try CryptoCompare (FREE, 100K calls/month)
        if self.cryptocompare_client:
            try:
                self.logger.debug(f"Fetching price for {symbol} at timestamp {timestamp} from CryptoCompare")
                price = await self.cryptocompare_client.get_price_at_timestamp(symbol, timestamp)
                
                if price:
                    self.logger.info(f"Historical price fetched from CryptoCompare: ${price:.6f} for {symbol}")
                    return price
                else:
                    self.logger.debug(f"CryptoCompare: No price for {symbol} at timestamp {timestamp}")
                    
            except Exception as e:
                self.logger.debug(f"CryptoCompare price at timestamp failed for {symbol}: {e}")
        else:
            self.logger.debug("CryptoCompare client not initialized, skipping")
        
        # Fallback: Try Twelve Data (paid, major coins only)
        # Note: Twelve Data would need a similar method
        self.logger.debug(f"No historical price available for {symbol} at timestamp {timestamp}")
        return None
    

    def _get_api_sequence(self, chain: str) -> list[str]:
        """
        Get API sequence based on chain.
        
        Args:
            chain: Blockchain name
            
        Returns:
            List of API names in priority order
        """
        if chain == 'solana':
            return ['birdeye', 'coingecko', 'defillama', 'dexscreener']
        else:  # evm chains
            return ['coingecko', 'moralis', 'defillama', 'dexscreener']

    async def get_prices_batch(self, addresses: list[tuple[str, str]]) -> dict[str, Optional[PriceData]]:
        """
        Fetch prices for multiple addresses in parallel for better performance.
        
        Args:
            addresses: List of (address, chain) tuples
            
        Returns:
            Dictionary mapping address to PriceData (or None if failed)
            
        Example:
            addresses = [
                ("0x123...", "ethereum"),
                ("0x456...", "ethereum"),
                ("ABC123...", "solana")
            ]
            results = await price_engine.get_prices_batch(addresses)
        """
        if not addresses:
            return {}
        
        self.logger.info(f"Fetching {len(addresses)} prices in parallel")
        
        # Create tasks for parallel execution
        tasks = [self.get_price(addr, chain) for addr, chain in addresses]
        
        # Execute all price fetches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        price_map = {}
        for (addr, chain), result in zip(addresses, results):
            if isinstance(result, Exception):
                self.logger.warning(f"Failed to fetch price for {addr}: {result}")
                price_map[addr] = None
            else:
                price_map[addr] = result
        
        success_count = sum(1 for v in price_map.values() if v is not None)
        self.logger.info(f"Batch fetch complete: {success_count}/{len(addresses)} successful")
        
        return price_map

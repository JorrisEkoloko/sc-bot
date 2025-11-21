"""Price fetching service - handles price and historical data retrieval."""
import time
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from config.processing_config import ProcessingConfig
from utils.logger import get_logger


class PriceFetchingService:
    """Handles price fetching and historical data retrieval."""
    
    def __init__(
        self,
        price_engine,
        data_enrichment,
        historical_price_retriever,
        processing_config=None,
        logger=None
    ):
        """Initialize price fetching service."""
        self.price_engine = price_engine
        self.data_enrichment = data_enrichment
        self.historical_price_retriever = historical_price_retriever
        self.processing_config = processing_config or ProcessingConfig.load_from_env()
        self.logger = logger or get_logger('PriceFetchingService')
    
    async def fetch_current_price(self, address: str, chain: str) -> Optional[Any]:
        """
        Fetch current price with enrichment.
        
        Args:
            address: Token address
            chain: Blockchain name
            
        Returns:
            Enriched PriceData or None
        """
        price_start = time.time()
        price_data = await self.price_engine.get_price(address, chain)
        price_time = (time.time() - price_start) * 1000
        self.logger.debug(f"⏱️  Price fetch: {price_time:.0f}ms")
        
        if not price_data:
            return None
        
        # Enrich with market intelligence
        enrich_start = time.time()
        price_data = self.data_enrichment.enrich_price_data(price_data)
        enrich_time = (time.time() - enrich_start) * 1000
        self.logger.debug(f"⏱️  Data enrichment: {enrich_time:.0f}ms")
        
        return price_data
    
    async def fetch_historical_data(
        self,
        address: str,
        chain: str,
        symbol: str = None
    ) -> Optional[dict]:
        """
        Fetch historical ATH/ATL data.
        
        Args:
            address: Token address
            chain: Blockchain name
            symbol: Token symbol (optional)
            
        Returns:
            Historical data dictionary or None
        """
        hist_start = time.time()
        try:
            historical_data = await self.price_engine.get_historical_data(
                address=address,
                chain=chain,
                symbol=symbol
            )
            
            if historical_data:
                # Add symbol if not present
                if 'symbol' not in historical_data or not historical_data['symbol']:
                    historical_data['symbol'] = symbol
                
                hist_time = (time.time() - hist_start) * 1000
                self.logger.debug(f"⏱️  Historical data fetch: {hist_time:.0f}ms")
                return historical_data
            else:
                self.logger.debug(f"No historical data available for {address[:10]}...")
                return None
                
        except Exception as e:
            self.logger.debug(f"Failed to fetch historical data: {e}")
            return None
    
    async def fetch_entry_price(
        self,
        symbol: str,
        message_timestamp: datetime,
        address: str,
        chain: str,
        message_age_hours: float
    ) -> tuple[float, str]:
        """
        Fetch historical entry price if message is old.
        
        Args:
            symbol: Token symbol
            message_timestamp: When message was sent
            address: Token address
            chain: Blockchain name
            message_age_hours: Age of message in hours
            
        Returns:
            Tuple of (entry_price, source)
        """
        if message_age_hours <= 1.0 or not symbol:
            return None, "current"
        
        self.logger.info(f"Fetching historical entry price for {symbol}")
        hist_start = time.time()
        
        try:
            historical_entry_price, price_source = await asyncio.wait_for(
                self.historical_price_retriever.fetch_closest_entry_price(
                    symbol=symbol,
                    message_timestamp=message_timestamp,
                    address=address,
                    chain=chain
                ),
                timeout=self.processing_config.historical_price_timeout
            )
            
            hist_time = (time.time() - hist_start) * 1000
            self.logger.info(f"⏱️  Historical entry price fetch: {hist_time:.0f}ms")
            
            if historical_entry_price and historical_entry_price > 0:
                self.logger.info(f"[OK] Historical entry price: ${historical_entry_price:.6f} (source: {price_source})")
                return historical_entry_price, price_source
            else:
                self.logger.warning(f"[WARNING] No historical price for {symbol} - using current price")
                return None, "fallback"
                
        except asyncio.TimeoutError:
            hist_time = (time.time() - hist_start) * 1000
            self.logger.warning(
                f"⏱️  Historical entry price fetch TIMED OUT after {hist_time:.0f}ms "
                f"(timeout: {self.processing_config.historical_price_timeout}s)"
            )
            return None, "timeout"
    
    async def fetch_ohlc_with_ath(
        self,
        symbol: str,
        entry_timestamp: datetime,
        window_days: int = 30,
        address: str = None,
        chain: str = None
    ) -> Optional[dict]:
        """
        Fetch OHLC data with ATH calculation.
        
        Args:
            symbol: Token symbol
            entry_timestamp: Signal entry time
            window_days: Days to fetch
            address: Token address (optional)
            chain: Blockchain name (optional)
            
        Returns:
            OHLC result with ATH data or None
        """
        if not symbol:
            self.logger.warning(f"❌ No symbol available - cannot fetch OHLC data")
            return None
        
        try:
            ohlc_result = await asyncio.wait_for(
                self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                    symbol,
                    entry_timestamp,
                    window_days=window_days,
                    address=address,
                    chain=chain
                ),
                timeout=self.processing_config.ohlc_fetch_timeout
            )
            
            return ohlc_result
            
        except asyncio.TimeoutError:
            self.logger.warning(
                f"⏱️  OHLC fetch TIMED OUT "
                f"(timeout: {self.processing_config.ohlc_fetch_timeout}s)"
            )
            return None
        except Exception as e:
            self.logger.error(f"Error fetching OHLC: {e}")
            return None
    
    async def create_dead_token_price_data(self, address: str) -> Any:
        """
        Create minimal price data for dead tokens.
        
        Args:
            address: Token address
            
        Returns:
            PriceData with minimal values
        """
        from domain.price_data import PriceData
        return PriceData(
            price_usd=0.000001,
            symbol=address[:10],
            source="dead_token",
            market_cap=0,
            volume_24h=0,
            liquidity_usd=0
        )

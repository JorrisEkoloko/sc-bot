"""Price enrichment service - enriches price data with missing fields."""
import asyncio
from typing import Optional

from domain.price_data import PriceData
from utils.logger import setup_logger


class PriceEnrichmentService:
    """
    Enriches price data with missing fields using multiple APIs.
    
    Responsibilities:
    - Enrich missing symbols
    - Enrich missing market data (market_cap, volume)
    - Fetch ATH data
    - Coordinate parallel enrichment calls
    """
    
    def __init__(self, price_engine_clients: dict, rate_limiters: dict, contract_reader, logger=None):
        """
        Initialize enrichment service.
        
        Args:
            price_engine_clients: Dictionary of API clients from PriceEngine
            rate_limiters: Dictionary of rate limiters from PriceEngine
            contract_reader: ContractReader for blockchain interactions
            logger: Optional logger instance
        """
        self.clients = price_engine_clients
        self.rate_limiters = rate_limiters
        self.contract_reader = contract_reader
        self.logger = logger or setup_logger('PriceEnrichmentService')
    
    async def enrich_price_data(
        self,
        price_data: PriceData,
        address: str,
        chain: str
    ) -> PriceData:
        """
        Enrich price data with missing fields.
        
        Strategy:
        1. Check what fields are missing
        2. Try DexScreener for symbol/market data
        3. Try Blockscout for symbol (EVM only)
        4. Try contract reading for symbol (EVM only)
        5. Try GoPlus for symbol
        6. Try DefiLlama for symbol
        7. Fetch ATH data from CoinGecko
        
        Args:
            price_data: PriceData to enrich
            address: Token address
            chain: Blockchain name
            
        Returns:
            Enriched PriceData
        """
        # Check if enrichment is needed
        needs_enrichment = (
            (not price_data.symbol or price_data.symbol == 'UNKNOWN') or
            not price_data.market_cap or
            not price_data.volume_24h
        )
        
        if not needs_enrichment:
            # Still fetch ATH data if missing
            if not price_data.ath:
                await self._enrich_ath_data(price_data, address, chain)
            return price_data
        
        # Log missing fields
        missing_fields = []
        if not price_data.symbol or price_data.symbol == 'UNKNOWN':
            missing_fields.append('symbol')
        if not price_data.market_cap:
            missing_fields.append('market_cap')
        if not price_data.volume_24h:
            missing_fields.append('volume_24h')
        
        self.logger.debug(
            f"Missing fields from {price_data.source}: {', '.join(missing_fields)}. "
            f"Trying enrichment APIs in parallel"
        )
        
        # Enrich with parallel API calls
        await self._enrich_with_parallel_apis(price_data, address, chain)
        
        # If symbol still missing, try additional sources
        if not price_data.symbol or price_data.symbol == 'UNKNOWN':
            await self._enrich_symbol_fallback(price_data, address, chain)
        
        # Fetch ATH data if not present
        if not price_data.ath:
            await self._enrich_ath_data(price_data, address, chain)
        
        return price_data
    
    async def _enrich_with_parallel_apis(
        self,
        price_data: PriceData,
        address: str,
        chain: str
    ):
        """Enrich with DexScreener and Blockscout in parallel."""
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
            self._merge_dexscreener_data(price_data, dex_data)
        
        # Process Blockscout results (if symbol still missing)
        if (not price_data.symbol or price_data.symbol == 'UNKNOWN') and len(enrichment_results) > 1:
            blockscout_data = enrichment_results[1] if not isinstance(enrichment_results[1], Exception) else None
            if blockscout_data and blockscout_data.symbol:
                price_data.symbol = blockscout_data.symbol
                self.logger.info(f"Enriched symbol from Blockscout: {blockscout_data.symbol}")
                
                # Update source
                if '+' in price_data.source:
                    price_data.source = f"{price_data.source}+blockscout"
                else:
                    price_data.source = f"{price_data.source}+blockscout"
    
    def _merge_dexscreener_data(self, price_data: PriceData, dex_data: PriceData):
        """Merge DexScreener data into price_data."""
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
    
    async def _enrich_symbol_fallback(
        self,
        price_data: PriceData,
        address: str,
        chain: str
    ):
        """Try additional sources for symbol enrichment."""
        # Try reading from blockchain contract (EVM only)
        if chain != 'solana':
            self.logger.debug(f"Symbol still missing. Trying to read from contract for {address}")
            try:
                symbol_from_contract = await self.contract_reader.read_symbol_from_contract(address, chain)
                if symbol_from_contract:
                    price_data.symbol = symbol_from_contract
                    self.logger.info(f"Enriched symbol from contract: {symbol_from_contract}")
                    price_data.source = f"{price_data.source}+contract"
                    return  # Success, exit early
            except Exception as e:
                self.logger.debug(f"Contract symbol read failed: {e}")
        
        # Try GoPlus as fallback (multi-chain support)
        self.logger.debug(f"Symbol still missing after contract read. Trying GoPlus for {address}")
        try:
            await self.rate_limiters['goplus'].acquire()
            goplus_data = await self.clients['goplus'].get_price(address, chain)
            
            if goplus_data and goplus_data.symbol:
                price_data.symbol = goplus_data.symbol
                self.logger.info(f"Enriched symbol from GoPlus: {goplus_data.symbol}")
                
                # Update source
                if '+' in price_data.source:
                    price_data.source = f"{price_data.source}+goplus"
                else:
                    price_data.source = f"{price_data.source}+goplus"
                return  # Success, exit early
                    
        except Exception as e:
            self.logger.debug(f"GoPlus enrichment failed: {e}")
        
        # Try DefiLlama as final fallback (multi-chain support)
        self.logger.debug(f"Symbol still missing after GoPlus. Trying DefiLlama for {address}")
        try:
            await self.rate_limiters['defillama'].acquire()
            defillama_data = await self.clients['defillama'].get_price(address, chain)
            
            if defillama_data and defillama_data.symbol:
                price_data.symbol = defillama_data.symbol
                self.logger.info(f"Enriched symbol from DefiLlama: {defillama_data.symbol}")
                
                # Update source
                if '+' in price_data.source:
                    price_data.source = f"{price_data.source}+defillama"
                else:
                    price_data.source = f"{price_data.source}+defillama"
                    
        except Exception as e:
            self.logger.debug(f"DefiLlama enrichment failed: {e}")
    
    async def _enrich_ath_data(
        self,
        price_data: PriceData,
        address: str,
        chain: str
    ):
        """Fetch ATH data from CoinGecko."""
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

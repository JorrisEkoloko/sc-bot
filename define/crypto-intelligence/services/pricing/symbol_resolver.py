"""
Symbol-to-address resolver with date validation.

Resolves ticker symbols (BTC, ETH, HBAR, etc.) to contract addresses
with validation that the token existed at the signal date.
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from cachetools import TTLCache

from services.message_processing.address_extractor import Address
from utils.logger import setup_logger


class SymbolResolver:
    """
    Resolve ticker symbols to contract addresses with date validation.
    
    Strategy:
    1. Get all possible addresses for symbol from CoinGecko
    2. For each address, validate it existed at signal_date using OHLC data
    3. Return validated addresses with entry prices
    """
    
    def __init__(
        self,
        coingecko_client,
        historical_price_service,
        logger=None
    ):
        """
        Initialize symbol resolver.
        
        Args:
            coingecko_client: CoinGecko API client
            historical_price_service: Historical price service for validation
            logger: Logger instance
        """
        self.coingecko_client = coingecko_client
        self.historical_price_service = historical_price_service
        self.logger = logger or setup_logger('SymbolResolver')
        
        # Cache: (symbol, date) -> List[Address]
        # TTL: 24 hours (symbol mappings don't change often)
        self.cache = TTLCache(maxsize=1000, ttl=86400)
        
        self.logger.info("SymbolResolver initialized with date validation")
    
    async def resolve_symbols(
        self,
        symbols: List[str],
        signal_date: datetime,
        chain_hint: Optional[str] = None
    ) -> List[Address]:
        """
        Resolve multiple symbols to validated addresses.
        
        Args:
            symbols: List of ticker symbols (e.g., ['BTC', 'HBAR', 'ENJ'])
            signal_date: Date of the signal (for validation)
            chain_hint: Optional chain hint to prioritize
            
        Returns:
            List of validated Address objects with entry prices
        """
        if not symbols:
            return []
        
        self.logger.info(
            f"Resolving {len(symbols)} symbols to addresses "
            f"(signal_date: {signal_date.strftime('%Y-%m-%d %H:%M')})"
        )
        
        # Filter out common stablecoins and base currencies (no need to track)
        skip_symbols = {'USDT', 'USDC', 'USD', 'BUSD', 'DAI', 'TUSD'}
        symbols_to_resolve = [s for s in symbols if s.upper() not in skip_symbols]
        
        if len(symbols_to_resolve) < len(symbols):
            skipped = set(symbols) - set(symbols_to_resolve)
            self.logger.info(f"Skipping stablecoins: {', '.join(skipped)}")
        
        if not symbols_to_resolve:
            return []
        
        # Resolve each symbol
        tasks = [
            self._resolve_single_symbol(symbol, signal_date, chain_hint)
            for symbol in symbols_to_resolve
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out errors
        addresses = []
        for symbol, result in zip(symbols_to_resolve, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error resolving {symbol}: {result}")
            elif result:
                addresses.extend(result)
        
        self.logger.info(
            f"Resolved {len(addresses)} addresses from {len(symbols_to_resolve)} symbols"
        )
        
        return addresses
    
    async def _resolve_single_symbol(
        self,
        symbol: str,
        signal_date: datetime,
        chain_hint: Optional[str] = None
    ) -> List[Address]:
        """
        Resolve a single symbol to validated address(es).
        
        Args:
            symbol: Ticker symbol
            signal_date: Date of the signal
            chain_hint: Optional chain hint
            
        Returns:
            List of validated Address objects
        """
        # Check cache
        cache_key = (symbol.upper(), signal_date.date())
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for {symbol}")
            return self.cache[cache_key]
        
        self.logger.info(f"Resolving symbol: {symbol}")
        
        # Step 1: Get all possible addresses from CoinGecko
        possible_addresses = await self._get_addresses_from_coingecko(symbol)
        
        if not possible_addresses:
            self.logger.warning(f"No addresses found for symbol: {symbol}")
            self.cache[cache_key] = []
            return []
        
        self.logger.info(
            f"Found {len(possible_addresses)} possible addresses for {symbol}"
        )
        
        # Filter to main token for major cryptocurrencies
        possible_addresses = self._filter_to_main_token(symbol, possible_addresses)
        
        # Step 2: Validate each address existed at signal_date
        validated_addresses = []
        
        for addr_info in possible_addresses:
            validated = await self._validate_address_at_date(
                symbol=symbol,
                address=addr_info['address'],
                chain=addr_info['chain'],
                signal_date=signal_date
            )
            
            if validated:
                validated_addresses.append(validated)
                
                # If we have a chain hint and found a match, prioritize it
                if chain_hint and addr_info['chain'] == chain_hint:
                    self.logger.info(
                        f"✅ Found {symbol} on preferred chain: {chain_hint}"
                    )
                    break
        
        if validated_addresses:
            self.logger.info(
                f"✅ Validated {len(validated_addresses)} address(es) for {symbol}"
            )
        else:
            self.logger.warning(
                f"❌ No validated addresses for {symbol} at {signal_date.date()}"
            )
        
        # Cache result
        self.cache[cache_key] = validated_addresses
        
        return validated_addresses
    
    def _filter_to_main_token(
        self,
        symbol: str,
        possible_addresses: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Filter to main/native token for major cryptocurrencies.
        
        For major tokens like ETH, BTC, SOL, etc., only return the main token
        on its native chain, not wrapped versions or scam tokens.
        
        Args:
            symbol: Token symbol
            possible_addresses: List of possible addresses
            
        Returns:
            Filtered list (single main token for major cryptos)
        """
        # Define major tokens and their native chains
        MAJOR_TOKENS = {
            'ETH': 'ethereum',      # Ethereum on Ethereum mainnet
            'BTC': 'bitcoin',       # Bitcoin (no contract address)
            'SOL': 'solana',        # Solana native
            'BNB': 'binance-smart-chain',  # BNB on BSC
            'MATIC': 'polygon-pos', # MATIC on Polygon
            'AVAX': 'avalanche',    # AVAX on Avalanche
            'ADA': 'cardano',       # Cardano native
            'DOT': 'polkadot',      # Polkadot native
            'LINK': 'ethereum',     # Chainlink on Ethereum
            'UNI': 'ethereum',      # Uniswap on Ethereum
            'ATOM': 'cosmos',       # Cosmos native
            'XRP': 'ripple',        # Ripple native
            'LTC': 'litecoin',      # Litecoin native
            'DOGE': 'dogecoin',     # Dogecoin native
        }
        
        symbol_upper = symbol.upper()
        
        # If not a major token, return all addresses
        if symbol_upper not in MAJOR_TOKENS:
            return possible_addresses
        
        native_chain = MAJOR_TOKENS[symbol_upper]
        
        # Filter to native chain only
        main_tokens = [
            addr for addr in possible_addresses
            if addr.get('chain') == native_chain
        ]
        
        if main_tokens:
            self.logger.info(
                f"✅ Filtered {symbol} to main token on {native_chain} "
                f"(excluded {len(possible_addresses) - len(main_tokens)} wrapped/fake tokens)"
            )
            return main_tokens
        
        # Fallback: if native chain not found, return the first address
        # (better than nothing, but log a warning)
        self.logger.warning(
            f"⚠️ Could not find {symbol} on native chain {native_chain}, "
            f"using first available address"
        )
        return possible_addresses[:1] if possible_addresses else []
    
    async def _get_addresses_from_coingecko(
        self,
        symbol: str
    ) -> List[Dict[str, str]]:
        """
        Get all possible contract addresses for a symbol from CoinGecko.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            List of dicts with 'address' and 'chain' keys
        """
        try:
            # CoinGecko /coins/list endpoint with platforms
            # This returns all coins with their contract addresses
            coins_list = await self.coingecko_client.get_coins_list(
                include_platform=True
            )
            
            # Find coins matching the symbol
            matching_coins = [
                coin for coin in coins_list
                if coin.get('symbol', '').upper() == symbol.upper()
            ]
            
            if not matching_coins:
                return []
            
            # Extract addresses from platforms
            addresses = []
            for coin in matching_coins:
                platforms = coin.get('platforms', {})
                
                for chain, address in platforms.items():
                    if address and address.strip():
                        # Map CoinGecko chain names to our chain names
                        chain_mapped = self._map_chain_name(chain)
                        if chain_mapped:
                            addresses.append({
                                'address': address,
                                'chain': chain_mapped,
                                'coin_id': coin.get('id'),
                                'coin_name': coin.get('name')
                            })
            
            return addresses
            
        except Exception as e:
            self.logger.error(f"Error fetching addresses from CoinGecko: {e}")
            return []
    
    async def _validate_address_at_date(
        self,
        symbol: str,
        address: str,
        chain: str,
        signal_date: datetime
    ) -> Optional[Address]:
        """
        Validate that an address existed and had trading activity at signal_date.
        
        Uses the same fallback chain as price fetching:
        1. CryptoCompare historical
        2. DefiLlama historical  
        3. DexScreener current price
        
        Args:
            symbol: Ticker symbol
            address: Contract address
            chain: Blockchain name
            signal_date: Date to validate
            
        Returns:
            Address object if validated, None otherwise
        """
        try:
            # Use fetch_closest_entry_price which has all the fallbacks
            # (CryptoCompare -> DefiLlama -> DexScreener)
            price, source = await self.historical_price_service.fetch_closest_entry_price(
                symbol=symbol,
                message_timestamp=signal_date,
                address=address,
                chain=chain
            )
            
            if price and price > 0:
                self.logger.info(
                    f"✅ Validated {symbol} ({address[:10]}...) on {chain}: "
                    f"${price:.6f} (source: {source})"
                )
                
                # Create Address object
                return Address(
                    address=address,
                    chain=chain,
                    is_valid=True,
                    ticker=symbol,
                    chain_specific=chain
                )
            else:
                self.logger.debug(
                    f"❌ No price data for {symbol} ({address[:10]}...) "
                    f"on {chain} at {signal_date.date()}"
                )
                return None
                
        except Exception as e:
            self.logger.debug(
                f"Error validating {symbol} ({address[:10]}...): {e}"
            )
            return None
    
    def _map_chain_name(self, coingecko_chain: str) -> Optional[str]:
        """
        Map CoinGecko chain names to our internal chain names.
        
        Args:
            coingecko_chain: Chain name from CoinGecko
            
        Returns:
            Mapped chain name or None if unsupported
        """
        chain_mapping = {
            'ethereum': 'evm',
            'binance-smart-chain': 'evm',
            'bsc': 'evm',
            'polygon-pos': 'evm',
            'polygon': 'evm',
            'arbitrum-one': 'evm',
            'arbitrum': 'evm',
            'avalanche': 'evm',
            'optimistic-ethereum': 'evm',
            'optimism': 'evm',
            'base': 'evm',
            'solana': 'solana',
        }
        
        return chain_mapping.get(coingecko_chain.lower())
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'maxsize': self.cache.maxsize,
            'hits': getattr(self.cache, 'hits', 0),
            'misses': getattr(self.cache, 'misses', 0)
        }

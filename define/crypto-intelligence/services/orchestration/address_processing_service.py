"""Address processing service - handles address extraction and validation."""
import asyncio
from typing import Optional, List
from datetime import datetime

from domain.message_event import MessageEvent
from services.message_processing.processed_message import ProcessedMessage
from services.filtering.token_filter import TokenFilter
from utils.logger import get_logger


class AddressProcessingService:
    """Handles address extraction, validation, and filtering."""
    
    def __init__(
        self,
        address_extractor,
        symbol_resolver=None,
        logger=None
    ):
        """Initialize address processing service."""
        self.address_extractor = address_extractor
        self.symbol_resolver = symbol_resolver
        self.token_filter = TokenFilter(logger=logger)
        self.logger = logger or get_logger('AddressProcessingService')
        
        # Log filtering configuration
        from config.token_registry import TokenRegistry
        config = TokenRegistry.get_config_info()
        self.logger.info(
            f"🔍 Token Filter initialized: "
            f"Min market cap=${config['min_market_cap']:,}, "
            f"Min price=${config['min_price']:.8f}, "
            f"Major tokens={config['total_major_tokens']}"
        )
    
    async def extract_and_validate_addresses(
        self,
        event: MessageEvent,
        processed: ProcessedMessage
    ) -> List:
        """
        Extract and validate addresses from message.
        
        Args:
            event: Message event
            processed: Processed message with crypto mentions
            
        Returns:
            List of validated Address objects
        """
        if not processed.is_crypto_relevant or not processed.crypto_mentions:
            return []
        
        # Check if message should be skipped (market commentary detection)
        if processed.crypto_mentions:
            symbols = [m for m in processed.crypto_mentions if not m.startswith('0x') and len(m) < 20]
            should_skip, skip_reason = self.token_filter.should_skip_processing(
                event.message_text or "", symbols
            )
            if should_skip:
                self.logger.info(f"⏭️ Skipping message processing: {skip_reason}")
                return []
        
        # Extract addresses
        addresses = await self.address_extractor.extract_addresses_async(processed.crypto_mentions)
        
        # Validate and link symbols with addresses
        if addresses and processed.crypto_mentions and self.symbol_resolver:
            addresses = await self._link_symbols_to_addresses(
                addresses, processed.crypto_mentions, event.timestamp
            )
        
        # Try symbol resolution if no addresses found
        if not addresses and self.symbol_resolver and processed.crypto_mentions:
            addresses = await self._resolve_symbols_to_addresses(
                processed.crypto_mentions, event.timestamp
            )
        
        return addresses
    
    async def filter_addresses(self, addresses: list, message_text: str, price_engine) -> list:
        """
        Filter addresses using token filtering logic.
        
        Args:
            addresses: List of addresses to filter
            message_text: Original message text
            price_engine: Price engine for fetching price data
            
        Returns:
            List of filtered addresses
        """
        if not addresses:
            return []
        
        # Group addresses by symbol
        symbol_groups = {}
        for addr in addresses:
            symbol = addr.ticker or "UNKNOWN"
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(addr)
        
        filtered_addresses = []
        
        # Process each symbol group
        for symbol, addr_list in symbol_groups.items():
            self.logger.debug(f"Filtering {len(addr_list)} addresses for symbol '{symbol}'")
            
            # Convert addresses to token candidates
            candidates = await self._create_token_candidates(addr_list, symbol, price_engine)
            
            # Filter candidates
            filtered_candidates = self.token_filter.filter_symbol_candidates(
                symbol, candidates, message_text
            )
            
            # Log filtering results
            if len(filtered_candidates) < len(candidates):
                filtered_out = len(candidates) - len(filtered_candidates)
                self.logger.info(
                    f"🔍 Token Filter: {symbol} - "
                    f"Kept {len(filtered_candidates)}/{len(candidates)} candidates "
                    f"(filtered {filtered_out} scam/invalid tokens)"
                )
            
            # Convert back to Address objects
            for candidate in filtered_candidates:
                for addr in addr_list:
                    if addr.address == candidate.address:
                        filtered_addresses.append(addr)
                        break
        
        return filtered_addresses
    
    async def _link_symbols_to_addresses(
        self,
        addresses: list,
        crypto_mentions: list,
        signal_date: datetime
    ) -> list:
        """Link symbols to addresses using symbol resolver."""
        symbols_in_message = [m for m in crypto_mentions if not m.startswith('0x') and len(m) < 20]
        
        if not symbols_in_message:
            return addresses
        
        self.logger.debug(f"Validating symbol-address connections for: {symbols_in_message}")
        
        for addr in addresses:
            if addr.ticker:
                continue  # Already has a ticker
            
            # Try to find matching symbol
            matched_symbol = await self._find_matching_symbol_for_address(
                addr, symbols_in_message, signal_date
            )
            if matched_symbol:
                addr.ticker = matched_symbol
        
        return addresses
    
    async def _find_matching_symbol_for_address(
        self,
        addr,
        symbols_in_message: list,
        signal_date: datetime
    ) -> Optional[str]:
        """Find and validate symbol for address."""
        for symbol in symbols_in_message:
            try:
                resolved = await self.symbol_resolver.resolve_symbols(
                    symbols=[symbol],
                    signal_date=signal_date,
                    chain_hint=addr.chain
                )
                
                for resolved_addr in resolved:
                    if resolved_addr.address.lower() == addr.address.lower():
                        self.logger.info(
                            f"✅ Verified and linked symbol '{symbol}' with address {addr.address[:10]}..."
                        )
                        return symbol
                        
            except Exception as e:
                self.logger.debug(f"Could not validate {symbol} for {addr.address[:10]}...: {e}")
        
        return None
    
    async def _resolve_symbols_to_addresses(
        self,
        crypto_mentions: list,
        signal_date: datetime
    ) -> list:
        """Resolve symbols to addresses when no addresses found."""
        self.logger.info(
            f"No addresses found, attempting symbol resolution for: "
            f"{', '.join(crypto_mentions)}"
        )
        
        resolved_addresses = await self.symbol_resolver.resolve_symbols(
            symbols=crypto_mentions,
            signal_date=signal_date,
            chain_hint=None
        )
        
        if resolved_addresses:
            self.logger.info(
                f"✅ Resolved {len(resolved_addresses)} addresses from symbols"
            )
        else:
            self.logger.warning(
                f"❌ Could not resolve any addresses for symbols: "
                f"{', '.join(crypto_mentions)}"
            )
        
        return resolved_addresses
    
    async def _create_token_candidates(self, addr_list: list, symbol: str, price_engine) -> list:
        """Create token candidates with price data for filtering."""
        candidates = []
        
        for addr in addr_list:
            try:
                price_data = await price_engine.get_price(addr.address, addr.chain)
                
                from services.filtering.token_filter import TokenCandidate
                candidate = TokenCandidate(
                    address=addr.address,
                    chain=addr.chain,
                    symbol=symbol,
                    price_usd=price_data.price_usd if price_data else None,
                    market_cap=price_data.market_cap if price_data else None,
                    supply=getattr(price_data, 'supply', None) if price_data else None,
                    volume_24h=price_data.volume_24h if price_data else None,
                    source="price_engine"
                )
                candidates.append(candidate)
                
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Failed to get price data for filtering {symbol} "
                    f"({addr.address[:10]}...): {e}"
                )
                from services.filtering.token_filter import TokenCandidate
                candidate = TokenCandidate(
                    address=addr.address,
                    chain=addr.chain,
                    symbol=symbol,
                    source="no_price_data"
                )
                candidates.append(candidate)
        
        return candidates

"""Signal processing service - coordinates address extraction, pricing, and tracking."""
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from domain.message_event import MessageEvent
from services.message_processing.processed_message import ProcessedMessage
from services.filtering.token_filter import TokenFilter
from config.processing_config import ProcessingConfig
from utils.logger import get_logger


class SignalProcessingService:
    """Coordinates the complete signal processing workflow."""
    
    def __init__(
        self,
        address_extractor,
        price_engine,
        data_enrichment,
        performance_tracker,
        outcome_tracker,
        historical_price_retriever,
        dead_token_detector,
        historical_bootstrap,
        data_output,
        symbol_resolver=None,
        processing_config=None,
        logger=None
    ):
        """Initialize signal processing service with dependencies."""
        self.address_extractor = address_extractor
        self.price_engine = price_engine
        self.data_enrichment = data_enrichment
        self.performance_tracker = performance_tracker
        self.outcome_tracker = outcome_tracker
        self.historical_price_retriever = historical_price_retriever
        self.dead_token_detector = dead_token_detector
        self.historical_bootstrap = historical_bootstrap
        self.data_output = data_output
        self.symbol_resolver = symbol_resolver
        self.processing_config = processing_config or ProcessingConfig.load_from_env()
        self.logger = logger or get_logger('SignalProcessingService')
        self.token_filter = TokenFilter(logger=self.logger)
        
        # Log filtering configuration on startup
        from config.token_registry import TokenRegistry
        config = TokenRegistry.get_config_info()
        self.logger.info(
            f"🔍 Token Filter initialized: "
            f"Min market cap=${config['min_market_cap']:,}, "
            f"Min price=${config['min_price']:.8f}, "
            f"Major tokens={config['total_major_tokens']}"
        )
    
    async def process_addresses(
        self,
        event: MessageEvent,
        processed: ProcessedMessage
    ) -> List[Dict[str, Any]]:
        """
        Process crypto addresses from message.
        
        Returns list of address data for display.
        """
        addresses_data = []
        
        if not processed.is_crypto_relevant or not processed.crypto_mentions:
            return addresses_data
        
        # Check if message should be skipped (market commentary detection)
        # Do this BEFORE any processing to avoid wasted API calls
        if processed.crypto_mentions:
            symbols = [m for m in processed.crypto_mentions if not m.startswith('0x') and len(m) < 20]
            should_skip, skip_reason = self.token_filter.should_skip_processing(
                event.message_text or "", symbols
            )
            if should_skip:
                self.logger.info(f"⏭️ Skipping message processing: {skip_reason}")
                return addresses_data
        
        # Extract addresses
        addresses = await self.address_extractor.extract_addresses_async(processed.crypto_mentions)
        
        # Validate and link symbols with addresses using SymbolResolver
        # This ensures we only link symbols that actually match the address
        if addresses and processed.crypto_mentions and self.symbol_resolver:
            symbols_in_message = [m for m in processed.crypto_mentions if not m.startswith('0x') and len(m) < 20]
            
            if symbols_in_message:
                self.logger.debug(f"Validating symbol-address connections for: {symbols_in_message}")
                
                # For each address, check if any symbol in the message actually resolves to it
                for addr in addresses:
                    if addr.ticker:
                        continue  # Already has a ticker
                    
                    # Try to find matching symbol (extracted to method for clarity)
                    matched_symbol = await self._find_matching_symbol_for_address(
                        addr, symbols_in_message, event.timestamp
                    )
                    if matched_symbol:
                        addr.ticker = matched_symbol
        
        # If no addresses found, try symbol resolution
        if not addresses and self.symbol_resolver and processed.crypto_mentions:
            self.logger.info(
                f"No addresses found, attempting symbol resolution for: "
                f"{', '.join(processed.crypto_mentions)}"
            )
            
            resolved_addresses = await self.symbol_resolver.resolve_symbols(
                symbols=processed.crypto_mentions,
                signal_date=event.timestamp,
                chain_hint=None
            )
            
            if resolved_addresses:
                self.logger.info(
                    f"✅ Resolved {len(resolved_addresses)} addresses from symbols"
                )
                addresses.extend(resolved_addresses)
            else:
                self.logger.warning(
                    f"❌ Could not resolve any addresses for symbols: "
                    f"{', '.join(processed.crypto_mentions)}"
                )
        
        # Filter addresses using token filtering logic
        if addresses:
            original_count = len(addresses)
            addresses = await self._filter_addresses(addresses, event.message_text or "")
            if not addresses:
                self.logger.info(f"🚫 All {original_count} address(es) filtered out - no processing needed")
                return addresses_data
            filtered_count = original_count - len(addresses)
            if filtered_count > 0:
                self.logger.info(f"🔍 Filtered out {filtered_count} address(es), processing {len(addresses)}")
            else:
                self.logger.info(f"✅ Processing {len(addresses)} address(es) (no filtering needed)")
        
        for addr in addresses:
            if not addr.is_valid:
                continue
            
            # Check if dead token (but DON'T skip - track it for 30 days as a failed signal)
            is_dead_token = False
            dead_token_reason = None
            
            if self.dead_token_detector.is_blacklisted(addr.address):
                is_dead_token = True
                dead_token_reason = self.dead_token_detector.get_blacklist_reason(addr.address)
                self.logger.info(f"[DEAD TOKEN] {addr.address[:10]}... is blacklisted: {dead_token_reason}")
            else:
                # Check if dead (adds to blacklist if dead)
                stats = await self.dead_token_detector.check_and_blacklist_if_dead(addr.address, addr.chain)
                if stats.is_dead:
                    is_dead_token = True
                    dead_token_reason = stats.reason
                    self.logger.warning(f"[DEAD TOKEN] Detected {addr.address[:10]}...: {dead_token_reason}")
            
            # Process dead tokens normally - they need 30-day tracking for fair channel ROI
            if is_dead_token:
                self.logger.info(f"[TRACKING DEAD TOKEN] Will track for 30 days to count as failed signal")
            
            # Process this address (including dead tokens for fair ROI tracking)
            addr_data = await self._process_single_address(event, processed, addr, is_dead_token, dead_token_reason)
            if addr_data:
                addresses_data.append(addr_data)
        
        return addresses_data
    
    async def _find_matching_symbol_for_address(
        self,
        addr,
        symbols_in_message: list,
        signal_date
    ) -> Optional[str]:
        """
        Find and validate symbol for address.
        
        Args:
            addr: Address object to find symbol for
            symbols_in_message: List of potential symbols from message
            signal_date: Date of the signal
            
        Returns:
            Matched symbol or None
        """
        for symbol in symbols_in_message:
            try:
                # Use SymbolResolver to get the actual address for this symbol
                resolved = await self.symbol_resolver.resolve_symbols(
                    symbols=[symbol],
                    signal_date=signal_date,
                    chain_hint=addr.chain
                )
                
                # Check if any resolved address matches our address
                for resolved_addr in resolved:
                    if resolved_addr.address.lower() == addr.address.lower():
                        self.logger.info(
                            f"✅ Verified and linked symbol '{symbol}' with address {addr.address[:10]}..."
                        )
                        return symbol
                        
            except Exception as e:
                self.logger.debug(f"Could not validate {symbol} for {addr.address[:10]}...: {e}")
        
        return None
    
    async def _filter_addresses(self, addresses: list, message_text: str) -> list:
        """
        Filter addresses using token filtering logic.
        
        Args:
            addresses: List of addresses to filter
            message_text: Original message text for context
            
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
            candidates = []
            for addr in addr_list:
                # Fetch basic price data for filtering
                try:
                    price_data = await self.price_engine.get_price(addr.address, addr.chain)
                    
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
                    # Create candidate without price data (will likely be filtered)
                    from services.filtering.token_filter import TokenCandidate
                    candidate = TokenCandidate(
                        address=addr.address,
                        chain=addr.chain,
                        symbol=symbol,
                        source="no_price_data"
                    )
                    candidates.append(candidate)
            
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
                # Find the original Address object
                for addr in addr_list:
                    if addr.address == candidate.address:
                        filtered_addresses.append(addr)
                        break
        
        return filtered_addresses
    
    async def _process_single_address(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr,
        is_dead_token: bool = False,
        dead_token_reason: str = None
    ) -> Optional[Dict[str, Any]]:
        """Process a single address through the complete pipeline."""
        total_start = time.time()
        
        # Fetch price (even for dead tokens - they may still have price data)
        price_start = time.time()
        price_data = await self.price_engine.get_price(addr.address, addr.chain)
        price_time = (time.time() - price_start) * 1000
        self.logger.debug(f"⏱️  Price fetch: {price_time:.0f}ms")
        
        if not price_data:
            # Dead tokens without price data: use $0.000001 as entry price
            if is_dead_token:
                self.logger.info(f"[DEAD TOKEN] No price data, using $0.000001 as entry price")
                # Create minimal price data for dead token
                from domain.price_data import PriceData
                price_data = PriceData(
                    price_usd=0.000001,
                    symbol=addr.address[:10],
                    source="dead_token",
                    market_cap=0,
                    volume_24h=0,
                    liquidity_usd=0
                )
            else:
                return None
        
        # Enrich with market intelligence
        enrich_start = time.time()
        price_data = self.data_enrichment.enrich_price_data(price_data)
        enrich_time = (time.time() - enrich_start) * 1000
        self.logger.debug(f"⏱️  Data enrichment: {enrich_time:.0f}ms")
        
        # Write to TOKEN_PRICES table
        write_start = time.time()
        await self.data_output.write_token_price(
            address=addr.address,
            chain=addr.chain,
            price_data=price_data
        )
        write_time = (time.time() - write_start) * 1000
        self.logger.debug(f"⏱️  Write token price: {write_time:.0f}ms")
        
        # Fetch and write historical ATH/ATL data to HISTORICAL table
        hist_start = time.time()
        try:
            historical_data = await self.price_engine.get_historical_data(
                address=addr.address,
                chain=addr.chain,
                symbol=price_data.symbol if price_data.symbol != 'UNKNOWN' else None
            )
            
            if historical_data:
                # Add symbol to historical data if not present
                if 'symbol' not in historical_data or not historical_data['symbol']:
                    historical_data['symbol'] = price_data.symbol
                
                await self.data_output.write_historical(
                    address=addr.address,
                    chain=addr.chain,
                    historical_data=historical_data
                )
                hist_time = (time.time() - hist_start) * 1000
                self.logger.debug(f"⏱️  Write historical data: {hist_time:.0f}ms")
            else:
                self.logger.debug(f"No historical data available for {addr.address[:10]}...")
        except Exception as e:
            self.logger.debug(f"Failed to fetch/write historical data: {e}")
        
        # Determine message age
        now_utc = datetime.now(timezone.utc)
        msg_date = event.timestamp if event.timestamp.tzinfo else event.timestamp.replace(tzinfo=timezone.utc)
        message_age_hours = (now_utc - msg_date).total_seconds() / 3600
        message_age_days = message_age_hours / 24
        
        # Get symbol - use actual symbol if available, otherwise None (don't use address)
        symbol = price_data.symbol if price_data.symbol and price_data.symbol != 'UNKNOWN' else None
        
        # For display/logging, show symbol or truncated address
        display_name = symbol if symbol else f"{addr.address[:10]}..."
        
        # Log if we don't have a valid symbol (OHLC fetch will be skipped)
        if not symbol:
            self.logger.warning(
                f"⚠️  No valid symbol for {addr.address[:10]}... - "
                f"Historical price data will not be available. "
                f"Token will be tracked with current price only."
            )
        
        # Check if signal is complete (≥30 days old)
        signal_complete = message_age_days >= 30
        
        if signal_complete:
            await self._handle_complete_signal(event, processed, addr, price_data, symbol, message_age_days)
            return None  # Don't track completed signals in PerformanceTracker
        
        # Handle ongoing signal
        signal_start = time.time()
        result = await self._handle_ongoing_signal(event, processed, addr, price_data, symbol, message_age_hours, message_age_days, is_dead_token, dead_token_reason)
        signal_time = (time.time() - signal_start) * 1000
        
        total_time = (time.time() - total_start) * 1000
        self.logger.debug(f"⏱️  Handle ongoing signal: {signal_time:.0f}ms")
        self.logger.info(f"⏱️  TOTAL address processing: {total_time:.0f}ms")
        
        return result

    async def _handle_complete_signal(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr,
        price_data,
        symbol: str,
        message_age_days: float
    ):
        """Handle signals that are ≥30 days old."""
        self.logger.info(
            f"Signal complete ({message_age_days:.1f} days old) - "
            f"checking OutcomeTracker for {symbol}"
        )
        
        # Check if outcome exists with OHLC data
        outcome = self.outcome_tracker.outcomes.get(addr.address)
        if outcome:
            try:
                ath_price_val = getattr(outcome, 'ath_price', 0)
                entry_price_val = getattr(outcome, 'entry_price', 0)
                if isinstance(ath_price_val, (int, float)) and isinstance(entry_price_val, (int, float)):
                    if ath_price_val > entry_price_val:
                        self.logger.debug(f"Outcome already has OHLC data (ATH: ${ath_price_val:.6f})")
                        return
            except (TypeError, AttributeError) as e:
                self.logger.warning(f"Invalid ath_price for outcome: {e}")
        
        # Populate OHLC data
        await self._populate_ohlc_data(event, processed, addr, price_data, symbol, outcome)

    async def _populate_ohlc_data(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr,
        price_data,
        symbol: str,
        outcome
    ):
        """Fetch and populate OHLC data for complete signal."""
        self.logger.info(f"Populating OHLC data for complete signal: {symbol}")
        
        # Fetch historical entry price
        historical_entry_price, price_source = await self.historical_price_retriever.fetch_closest_entry_price(
            symbol=symbol,
            message_timestamp=event.timestamp,
            address=addr.address,
            chain=addr.chain
        )
        
        entry_price = historical_entry_price if historical_entry_price and historical_entry_price > 0 else price_data.price_usd
        
        # Create or update outcome
        if not outcome:
            outcome = self.outcome_tracker.track_signal(
                message_id=event.message_id,
                channel_name=event.channel_name,
                address=addr.address,
                entry_price=entry_price,
                entry_confidence=1.0,
                entry_source=price_data.source,
                symbol=symbol,
                sentiment="neutral",
                sentiment_score=0.0,
                hdrb_score=0.0,
                confidence=0.0,
                market_tier=getattr(price_data, 'market_tier', ""),
                risk_level=getattr(price_data, 'risk_level', ""),
                risk_score=getattr(price_data, 'risk_score', 0.0),
                entry_timestamp=event.timestamp
            )
        
        # Fetch OHLC data for 30-day window
        # Skip if no valid symbol (OHLC APIs require symbol)
        if not symbol:
            self.logger.warning(f"❌ No symbol available for {addr.address[:10]}... - cannot fetch OHLC data")
            # Fallback: use entry price as ATH
            outcome.ath_price = entry_price
            outcome.ath_timestamp = event.timestamp
            outcome.ath_multiplier = 1.0
            outcome.days_to_ath = 0.0
            outcome.is_complete = True
            outcome.status = "completed"
            outcome.is_winner = False
            outcome.outcome_category = "break_even"
            outcome.completion_reason = "no_symbol"
            self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
            return
        
        try:
            ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                symbol,
                event.timestamp,
                window_days=30,
                address=addr.address,
                chain=addr.chain
            )
            
            if ohlc_result and isinstance(ohlc_result, dict):
                ath_price_from_ohlc = ohlc_result.get('ath_price')
                
                if ath_price_from_ohlc and isinstance(ath_price_from_ohlc, (int, float)) and ath_price_from_ohlc > 0:
                    # Update outcome with OHLC ATH
                    outcome.ath_price = ath_price_from_ohlc
                    outcome.ath_timestamp = ohlc_result.get('ath_timestamp')
                    outcome.ath_multiplier = ath_price_from_ohlc / entry_price
                    outcome.days_to_ath = ohlc_result.get('days_to_ath', 0)
                    outcome.is_complete = True
                    outcome.status = "completed"
                    
                    # Populate checkpoint prices using helper method with already-fetched OHLC data
                    await self._populate_checkpoints_from_ohlc(
                        outcome=outcome,
                        entry_price=entry_price,
                        entry_timestamp=event.timestamp,
                        symbol=symbol,
                        address=addr.address,
                        chain=addr.chain,
                        window_days=30,
                        ohlc_result=ohlc_result  # Pass the already-fetched data
                    )
                    
                    # Classify outcome
                    winner_threshold = self._get_winner_threshold(outcome.market_tier)
                    
                    if outcome.ath_multiplier >= winner_threshold:
                        outcome.is_winner = True
                        outcome.outcome_category = "winner"
                    elif outcome.ath_multiplier < 1.0:
                        outcome.is_winner = False
                        outcome.outcome_category = "loser"
                    else:
                        outcome.is_winner = False
                        outcome.outcome_category = "break_even"
                    
                    # Save outcome
                    self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
                    
                    self.logger.info(
                        f"[OHLC] Complete signal: {outcome.outcome_category.upper()} - "
                        f"ATH {outcome.ath_multiplier:.3f}x at day {outcome.days_to_ath:.1f}"
                    )
                    return  # Success - exit early
            
            # Fallback: No valid OHLC data (log once at this level)
            self.logger.warning(f"❌ No OHLC data available for {symbol} - using entry price as ATH")
            
            outcome.ath_price = entry_price
            outcome.ath_timestamp = event.timestamp
            outcome.ath_multiplier = 1.0
            outcome.days_to_ath = 0.0
            outcome.is_complete = True
            outcome.status = "completed"
            outcome.is_winner = False
            outcome.outcome_category = "break_even"
            outcome.completion_reason = "no_data"
            
            # Save outcome
            self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
            
            self.logger.info(
                f"[FALLBACK] Complete signal: BREAK_EVEN - "
                f"ATH {outcome.ath_multiplier:.3f}x (no data, assumed no movement)"
            )
        except Exception as e:
            import traceback
            self.logger.error(f"Error fetching OHLC for complete signal: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    async def _handle_ongoing_signal(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr,
        price_data,
        symbol: str,
        message_age_hours: float,
        message_age_days: float,
        is_dead_token: bool = False,
        dead_token_reason: str = None
    ) -> Optional[Dict[str, Any]]:
        """Handle signals that are <30 days old."""
        entry_price = price_data.price_usd
        
        # Fetch historical entry price if message is old
        if message_age_hours > 1.0 and symbol:
            self.logger.info(f"Fetching historical entry price for {symbol}")
            hist_start = time.time()
            try:
                # Use configurable timeout for historical price fetch
                import asyncio
                historical_entry_price, price_source = await asyncio.wait_for(
                    self.historical_price_retriever.fetch_closest_entry_price(
                        symbol=symbol,
                        message_timestamp=event.timestamp,
                        address=addr.address,
                        chain=addr.chain
                    ),
                    timeout=self.processing_config.historical_price_timeout
                )
                hist_time = (time.time() - hist_start) * 1000
                self.logger.info(f"⏱️  Historical entry price fetch: {hist_time:.0f}ms")
            except asyncio.TimeoutError:
                hist_time = (time.time() - hist_start) * 1000
                self.logger.warning(
                    f"⏱️  Historical entry price fetch TIMED OUT after {hist_time:.0f}ms "
                    f"(timeout: {self.processing_config.historical_price_timeout}s)"
                )
                historical_entry_price = None
                price_source = "timeout"
            
            if historical_entry_price and historical_entry_price > 0:
                entry_price = historical_entry_price
                self.logger.info(f"[OK] Historical entry price: ${entry_price:.6f} (source: {price_source})")
            else:
                self.logger.warning(f"[WARNING] No historical price for {symbol} - using current price")
        
        # Get known ATH from price_data
        known_ath = getattr(price_data, 'ath', None)
        
        # Start or update PerformanceTracker
        if addr.address not in self.performance_tracker.tracking_data:
            await self.performance_tracker.start_tracking(
                address=addr.address,
                chain=addr.chain,
                initial_price=price_data.price_usd,
                message_id=str(event.message_id),
                known_ath=known_ath,
                symbol=symbol
            )
        else:
            await self.performance_tracker.update_price(
                address=addr.address,
                current_price=price_data.price_usd
            )
        
        # After 7 days: Replace known_ath with OHLC ATH
        if message_age_days >= 7:
            ohlc_start = time.time()
            try:
                # Use configurable timeout for OHLC fetch
                await asyncio.wait_for(
                    self._update_ohlc_ath_if_needed(event, addr, symbol, message_age_days, known_ath),
                    timeout=self.processing_config.ohlc_fetch_timeout
                )
                ohlc_time = (time.time() - ohlc_start) * 1000
                self.logger.info(f"⏱️  OHLC ATH update: {ohlc_time:.0f}ms")
            except asyncio.TimeoutError:
                ohlc_time = (time.time() - ohlc_start) * 1000
                self.logger.warning(
                    f"⏱️  OHLC ATH update TIMED OUT after {ohlc_time:.0f}ms "
                    f"(timeout: {self.processing_config.ohlc_fetch_timeout}s), skipping"
                )
        
        # Check for duplicates
        is_duplicate, signal_number, previous_signals = self.historical_bootstrap.check_for_duplicate(addr.address)
        
        if is_duplicate:
            self.logger.info(f"Duplicate: {addr.address[:10]}... already tracked, skipping")
            return None
        
        if signal_number > 1:
            self.logger.info(
                f"Fresh start: {addr.address[:10]}... Signal #{signal_number} "
                f"with entry price ${entry_price:.6f}"
            )
        
        # Track signal outcome (including dead tokens for fair channel ROI)
        outcome = self.outcome_tracker.track_signal(
            message_id=event.message_id,
            channel_name=event.channel_name,
            address=addr.address,
            entry_price=entry_price,
            entry_confidence=1.0 if not is_dead_token else 0.0,  # Low confidence for dead tokens
            entry_source=price_data.source,
            symbol=symbol,
            sentiment=processed.sentiment,
            sentiment_score=processed.sentiment_score,
            hdrb_score=processed.hdrb_score,
            confidence=processed.confidence,
            market_tier=getattr(price_data, 'market_tier', ""),
            risk_level="dead_token" if is_dead_token else getattr(price_data, 'risk_level', ""),
            risk_score=1.0 if is_dead_token else getattr(price_data, 'risk_score', 0.0),
            entry_timestamp=event.timestamp
        )
        
        # Mark as dead token in outcome
        if is_dead_token:
            outcome.is_dead_token = True
            outcome.dead_token_reason = dead_token_reason
            outcome.is_winner = False  # Dead tokens are always losers
            outcome.outcome_category = "dead_token"
            self.logger.info(f"[DEAD TOKEN] Marked outcome as dead_token: {dead_token_reason}")
        
        outcome.signal_number = signal_number
        outcome.previous_signals = previous_signals if previous_signals else []
        
        # Determine signal status
        signal_status = self.historical_bootstrap.determine_signal_status(event.timestamp)
        outcome.status = signal_status
        outcome.is_complete = (signal_status == "completed")
        
        self.logger.info(
            f"OutcomeTracker: Tracking signal {addr.address[:10]}... "
            f"(Signal #{signal_number}) at entry price ${entry_price:.6f} "
            f"[Status: {signal_status}]"
        )
        
        # 🔧 FIX: Populate checkpoints with historical prices for old messages
        if message_age_hours > 1.0 and symbol:
            days_elapsed = min(int(message_age_days), 30)
            self.logger.info(f"Historical signal ({message_age_days:.1f} days old) - populating {days_elapsed} days of checkpoint data")
            
            checkpoint_success = await self._populate_checkpoints_from_ohlc(
                outcome=outcome,
                entry_price=entry_price,
                entry_timestamp=event.timestamp,
                symbol=symbol,
                address=addr.address,
                chain=addr.chain,
                window_days=days_elapsed
            )
            
            if checkpoint_success:
                # Save updated outcome with populated checkpoints
                self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
                self.logger.info(f"✅ Checkpoints populated with real historical prices for {symbol}")
                
                # Transfer checkpoint data from outcome to performance_tracker
                perf_data = self.performance_tracker.get_performance(addr.address)
                if perf_data and outcome:
                    # Update performance_tracker with checkpoint data from outcome
                    for checkpoint_name, checkpoint in outcome.checkpoints.items():
                        if checkpoint.reached and checkpoint.price:
                            # Update the corresponding checkpoint in performance data
                            if hasattr(perf_data, checkpoint_name):
                                perf_checkpoint = getattr(perf_data, checkpoint_name)
                                perf_checkpoint.timestamp = checkpoint.timestamp
                                perf_checkpoint.price = checkpoint.price
                                perf_checkpoint.roi_percentage = checkpoint.roi_percentage
                                perf_checkpoint.roi_multiplier = checkpoint.roi_multiplier
                                perf_checkpoint.reached = True
                    
                    # Update ATH data in performance_tracker
                    if outcome.ath_price and outcome.ath_price > perf_data.ath_since_mention:
                        perf_data.ath_since_mention = outcome.ath_price
                        perf_data.ath_time = outcome.ath_timestamp.isoformat() if outcome.ath_timestamp else ""
                        perf_data.ath_multiplier = outcome.ath_multiplier
                    
                    self.logger.debug(f"✅ Transferred checkpoint data to performance_tracker for {symbol}")
            else:
                self.logger.warning(f"⚠️ Could not populate checkpoints for {symbol} - using entry price")
        
        # Get performance data
        perf_data = self.performance_tracker.get_performance(addr.address)
        
        if perf_data:
            # Write to PERFORMANCE table
            await self.data_output.write_performance(
                address=addr.address,
                chain=addr.chain,
                performance_data=perf_data
            )
            
            # Return for display
            return {
                'address': addr.address,
                'chain': addr.chain,
                'price': price_data.price_usd,
                'ath_multiplier': perf_data['ath_multiplier'] if isinstance(perf_data, dict) else getattr(perf_data, 'ath_multiplier', 1.0),
                'days_tracked': perf_data['days_tracked'] if isinstance(perf_data, dict) else getattr(perf_data, 'days_tracked', 0)
            }
        
        return None

    async def _update_ohlc_ath_if_needed(
        self,
        event: MessageEvent,
        addr,
        symbol: str,
        message_age_days: float,
        known_ath: Optional[float]
    ):
        """Update known_ath with OHLC data after 7 days."""
        tracking_entry = self.performance_tracker.tracking_data.get(addr.address)
        
        if tracking_entry and not tracking_entry.get('ohlc_fetched', False):
            self.logger.info(f"Signal 7+ days old - fetching OHLC ATH for {symbol}")
            try:
                days_to_fetch = min(int(message_age_days), 30)
                ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                    symbol,
                    event.timestamp,
                    window_days=days_to_fetch,
                    address=addr.address,
                    chain=addr.chain
                )
                
                if ohlc_result and ohlc_result.get('ath_price'):
                    ohlc_ath = ohlc_result['ath_price']
                    
                    # Replace known_ath with OHLC ATH
                    tracking_entry['known_ath'] = ohlc_ath
                    tracking_entry['ohlc_fetched'] = True
                    await self.performance_tracker.save_to_disk_async()
                    self.logger.info(
                        f"[OHLC] Updated known_ath from historical data: ${ohlc_ath:.6f} "
                        f"(was: ${known_ath:.6f if known_ath else 0:.6f})"
                    )
                else:
                    self.logger.warning(f"No historical ATH data available for {symbol}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch historical ATH: {e}")
    
    def _get_winner_threshold(self, market_tier: str) -> float:
        """Get winner threshold based on market tier."""
        if market_tier == "large":
            return 1.2
        elif market_tier == "mid":
            return 1.5
        else:
            return 2.0  # micro/small cap

    async def _populate_checkpoints_from_ohlc(
        self,
        outcome,
        entry_price: float,
        entry_timestamp: datetime,
        symbol: str,
        address: str,
        chain: str,
        window_days: int,
        ohlc_result: dict = None
    ) -> bool:
        """
        Populate checkpoint prices from OHLC historical data.
        
        This uses actual historical prices at each checkpoint time
        instead of using the entry price for all checkpoints.
        
        Args:
            outcome: SignalOutcome to populate
            entry_price: Entry price
            entry_timestamp: Entry timestamp
            symbol: Token symbol (can be None)
            address: Token address
            chain: Blockchain
            window_days: Number of days to fetch
            ohlc_result: Optional pre-fetched OHLC data (to avoid duplicate fetches)
            
        Returns:
            bool: True if checkpoints were populated successfully
        """
        # Skip if no valid symbol (OHLC APIs require symbol)
        if not symbol:
            self.logger.warning(f"⚠️ No symbol available for {address[:10]}... - cannot populate checkpoints")
            return False
        
        try:
            # Use provided OHLC data if available, otherwise fetch it
            if ohlc_result is None:
                self.logger.debug(f"Fetching OHLC data to populate checkpoints for {symbol}")
                
                # Fetch OHLC data
                ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                    symbol,
                    entry_timestamp,
                    window_days=window_days,
                    address=address,
                    chain=chain
                )
            else:
                self.logger.debug(f"Using pre-fetched OHLC data to populate checkpoints for {symbol}")
            
            if not ohlc_result or not isinstance(ohlc_result, dict):
                # Don't log here - already logged by caller
                return False
            
            candles = ohlc_result.get('candles', [])
            
            if not candles:
                # Don't log here - already logged by caller
                return False
            
            # Import here to avoid circular dependency
            from domain.signal_outcome import CHECKPOINTS
            from utils.roi_calculator import ROICalculator
            from datetime import timezone
            
            checkpoints_populated = 0
            now_utc = datetime.now(timezone.utc)
            
            self.logger.debug(f"Processing {len(CHECKPOINTS)} checkpoints with {len(candles)} candles")
            
            # Populate each checkpoint with actual historical price
            for checkpoint_name, interval in CHECKPOINTS.items():
                checkpoint = outcome.checkpoints[checkpoint_name]
                checkpoint_time = entry_timestamp + interval
                
                # Skip if checkpoint is in the future
                if checkpoint_time > now_utc:
                    self.logger.debug(f"Skipping {checkpoint_name} (in future)")
                    continue
                
                # Find closest candle to checkpoint time
                closest_candle = None
                min_time_diff = float('inf')
                
                try:
                    for candle in candles:
                        # Ensure candle timestamp is timezone-aware for comparison
                        if not hasattr(candle, 'timestamp') or candle.timestamp is None:
                            continue
                        
                        candle_time = candle.timestamp
                        if candle_time.tzinfo is None:
                            candle_time = candle_time.replace(tzinfo=timezone.utc)
                        
                        time_diff = abs((candle_time - checkpoint_time).total_seconds())
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            closest_candle = candle
                except Exception as e:
                    self.logger.error(f"Error finding closest candle for {checkpoint_name}: {e}")
                    continue
                
                if closest_candle:
                    checkpoint_price = closest_candle.close
                    roi_pct, roi_mult = ROICalculator.calculate_roi(entry_price, checkpoint_price)
                    
                    self.logger.debug(
                        f"{checkpoint_name}: ${checkpoint_price:.6f} ({roi_mult:.3f}x, {roi_pct:+.1f}%)"
                    )
                    
                    checkpoint.timestamp = checkpoint_time
                    checkpoint.price = checkpoint_price
                    checkpoint.roi_percentage = roi_pct
                    checkpoint.roi_multiplier = roi_mult
                    checkpoint.reached = True
                    
                    checkpoints_populated += 1
            
            if checkpoints_populated > 0:
                # Update ATH from OHLC data
                ath_price_from_ohlc = ohlc_result.get('ath_price')
                ath_timestamp_from_ohlc = ohlc_result.get('ath_timestamp')
                days_to_ath_from_ohlc = ohlc_result.get('days_to_ath')
                
                if ath_price_from_ohlc and ath_price_from_ohlc > 0:
                    outcome.ath_price = ath_price_from_ohlc
                    outcome.ath_timestamp = ath_timestamp_from_ohlc
                    # Safe division - handle edge case where entry_price is 0 or invalid
                    if entry_price > 0:
                        outcome.ath_multiplier = ath_price_from_ohlc / entry_price
                    else:
                        outcome.ath_multiplier = 1.0  # No movement if entry price is invalid
                    outcome.days_to_ath = days_to_ath_from_ohlc
                    outcome.current_price = ath_price_from_ohlc
                    outcome.current_multiplier = outcome.ath_multiplier
                    
                    self.logger.info(
                        f"✅ Populated {checkpoints_populated} checkpoints - "
                        f"ATH: ${ath_price_from_ohlc:.6f} ({outcome.ath_multiplier:.3f}x) on day {days_to_ath_from_ohlc:.1f}"
                    )
                
                return True
            else:
                return False
                
        except Exception as e:
            import traceback
            self.logger.error(f"Error populating checkpoints from OHLC: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

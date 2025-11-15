"""Signal processing service - coordinates address extraction, pricing, and tracking."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from domain.message_event import MessageEvent
from services.message_processing.processed_message import ProcessedMessage
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
        self.logger = logger or get_logger('SignalProcessingService')
    
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
        
        # Extract addresses
        addresses = await self.address_extractor.extract_addresses_async(processed.crypto_mentions)
        
        for addr in addresses:
            if not addr.is_valid:
                continue
            
            # Check blacklist
            if self.dead_token_detector.is_blacklisted(addr.address):
                reason = self.dead_token_detector.get_blacklist_reason(addr.address)
                self.logger.info(f"[SKIP] Token {addr.address[:10]}... is blacklisted: {reason}")
                continue
            
            # Check if dead
            stats = await self.dead_token_detector.check_and_blacklist_if_dead(addr.address, addr.chain)
            if stats.is_dead:
                self.logger.warning(f"[DEAD TOKEN] Skipping {addr.address[:10]}...: {stats.reason}")
                continue
            
            # Process this address
            addr_data = await self._process_single_address(event, processed, addr)
            if addr_data:
                addresses_data.append(addr_data)
        
        return addresses_data
    
    async def _process_single_address(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr
    ) -> Optional[Dict[str, Any]]:
        """Process a single address through the complete pipeline."""
        # Fetch price
        price_data = await self.price_engine.get_price(addr.address, addr.chain)
        
        if not price_data:
            return None
        
        # Enrich with market intelligence
        price_data = self.data_enrichment.enrich_price_data(price_data)
        
        # Write to TOKEN_PRICES table
        await self.data_output.write_token_price(
            address=addr.address,
            chain=addr.chain,
            price_data=price_data
        )
        
        # Determine message age
        now_utc = datetime.now(timezone.utc)
        msg_date = event.timestamp if event.timestamp.tzinfo else event.timestamp.replace(tzinfo=timezone.utc)
        message_age_hours = (now_utc - msg_date).total_seconds() / 3600
        message_age_days = message_age_hours / 24
        
        # Get symbol
        symbol = price_data.symbol if price_data.symbol else addr.address[:10]
        
        # Check if signal is complete (≥30 days old)
        signal_complete = message_age_days >= 30
        
        if signal_complete:
            await self._handle_complete_signal(event, processed, addr, price_data, symbol, message_age_days)
            return None  # Don't track completed signals in PerformanceTracker
        
        # Handle ongoing signal
        return await self._handle_ongoing_signal(event, processed, addr, price_data, symbol, message_age_hours, message_age_days)

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
                    
                    # Populate checkpoint prices using helper method
                    await self._populate_checkpoints_from_ohlc(
                        outcome=outcome,
                        entry_price=entry_price,
                        entry_timestamp=event.timestamp,
                        symbol=symbol,
                        address=addr.address,
                        chain=addr.chain,
                        window_days=30
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
                else:
                    # Final fallback: No valid OHLC data from any source
                    # Use entry price as ATH (token never went up)
                    self.logger.warning(f"No OHLC data available for complete signal: {symbol}")
                    self.logger.info(f"[FALLBACK] Using entry price as ATH for {symbol} (no price movement detected)")
                    
                    outcome.ath_price = entry_price
                    outcome.ath_timestamp = event.timestamp
                    outcome.ath_multiplier = 1.0
                    outcome.days_to_ath = 0.0
                    outcome.is_complete = True
                    outcome.status = "completed"
                    outcome.is_winner = False
                    outcome.outcome_category = "break_even"
                    outcome.completion_reason = "30d_elapsed"
                    
                    # Save outcome
                    self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
                    
                    self.logger.info(
                        f"[FALLBACK] Complete signal: BREAK_EVEN - "
                        f"ATH {outcome.ath_multiplier:.3f}x (no data, assumed no movement)"
                    )
            else:
                # No OHLC result at all
                self.logger.warning(f"No OHLC result returned for {symbol}")
                self.logger.info(f"[FALLBACK] Using entry price as ATH for {symbol} (no data sources available)")
                
                outcome.ath_price = entry_price
                outcome.ath_timestamp = event.timestamp
                outcome.ath_multiplier = 1.0
                outcome.days_to_ath = 0.0
                outcome.is_complete = True
                outcome.status = "completed"
                outcome.is_winner = False
                outcome.outcome_category = "break_even"
                outcome.completion_reason = "30d_elapsed"
                
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
        message_age_days: float
    ) -> Optional[Dict[str, Any]]:
        """Handle signals that are <30 days old."""
        entry_price = price_data.price_usd
        
        # Fetch historical entry price if message is old
        if message_age_hours > 1.0 and symbol:
            self.logger.info(f"Fetching historical entry price for {symbol}")
            historical_entry_price, price_source = await self.historical_price_retriever.fetch_closest_entry_price(
                symbol=symbol,
                message_timestamp=event.timestamp,
                address=addr.address,
                chain=addr.chain
            )
            
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
                known_ath=known_ath
            )
        else:
            await self.performance_tracker.update_price(
                address=addr.address,
                current_price=price_data.price_usd
            )
        
        # After 7 days: Replace known_ath with OHLC ATH
        if message_age_days >= 7:
            await self._update_ohlc_ath_if_needed(event, addr, symbol, message_age_days, known_ath)
        
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
        
        # Track signal outcome
        outcome = self.outcome_tracker.track_signal(
            message_id=event.message_id,
            channel_name=event.channel_name,
            address=addr.address,
            entry_price=entry_price,
            entry_confidence=1.0,
            entry_source=price_data.source,
            symbol=symbol,
            sentiment=processed.sentiment,
            sentiment_score=processed.sentiment_score,
            hdrb_score=processed.hdrb_score,
            confidence=processed.confidence,
            market_tier=getattr(price_data, 'market_tier', ""),
            risk_level=getattr(price_data, 'risk_level', ""),
            risk_score=getattr(price_data, 'risk_score', 0.0),
            entry_timestamp=event.timestamp
        )
        
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
        window_days: int
    ) -> bool:
        """
        Populate checkpoint prices from OHLC historical data.
        
        This fetches actual historical prices at each checkpoint time
        instead of using the entry price for all checkpoints.
        
        Args:
            outcome: SignalOutcome to populate
            entry_price: Entry price
            entry_timestamp: Entry timestamp
            symbol: Token symbol
            address: Token address
            chain: Blockchain
            window_days: Number of days to fetch
            
        Returns:
            bool: True if checkpoints were populated successfully
        """
        try:
            self.logger.info(f"🔍 [DEBUG] Fetching OHLC data to populate checkpoints for {symbol}")
            self.logger.info(f"🔍 [DEBUG] Entry timestamp: {entry_timestamp}, Window: {window_days} days")
            
            # Fetch OHLC data
            ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                symbol,
                entry_timestamp,
                window_days=window_days,
                address=address,
                chain=chain
            )
            
            self.logger.info(f"🔍 [DEBUG] OHLC result type: {type(ohlc_result)}")
            if ohlc_result:
                self.logger.info(f"🔍 [DEBUG] OHLC result keys: {ohlc_result.keys() if isinstance(ohlc_result, dict) else 'Not a dict'}")
            
            if not ohlc_result or not isinstance(ohlc_result, dict):
                self.logger.warning(f"❌ No OHLC data available for {symbol}")
                return False
            
            candles = ohlc_result.get('candles', [])
            self.logger.info(f"🔍 [DEBUG] Number of candles received: {len(candles)}")
            
            if not candles:
                self.logger.warning(f"❌ No candles in OHLC data for {symbol}")
                return False
            
            # Show first and last candle for debugging
            if len(candles) > 0:
                first_candle = candles[0]
                last_candle = candles[-1]
                self.logger.info(f"🔍 [DEBUG] First candle: {first_candle.timestamp} @ ${first_candle.close:.6f}")
                self.logger.info(f"🔍 [DEBUG] Last candle: {last_candle.timestamp} @ ${last_candle.close:.6f}")
                self.logger.info(f"🔍 [DEBUG] Candle type: {type(first_candle)}")
            
            # Import here to avoid circular dependency
            from domain.signal_outcome import CHECKPOINTS
            from utils.roi_calculator import ROICalculator
            from datetime import timezone
            
            checkpoints_populated = 0
            now_utc = datetime.now(timezone.utc)
            
            self.logger.info(f"🔍 [DEBUG] Processing {len(CHECKPOINTS)} checkpoints...")
            
            # Populate each checkpoint with actual historical price
            for checkpoint_name, interval in CHECKPOINTS.items():
                checkpoint = outcome.checkpoints[checkpoint_name]
                checkpoint_time = entry_timestamp + interval
                
                self.logger.info(f"🔍 [DEBUG] Checkpoint '{checkpoint_name}': target time = {checkpoint_time}")
                
                # Skip if checkpoint is in the future
                if checkpoint_time > now_utc:
                    self.logger.info(f"  ⏭️  Skipping {checkpoint_name} (in future: {checkpoint_time} > {now_utc})")
                    continue
                
                # Find closest candle to checkpoint time
                closest_candle = None
                min_time_diff = float('inf')
                
                for candle in candles:
                    # Ensure candle timestamp is timezone-aware for comparison
                    candle_time = candle.timestamp
                    if candle_time.tzinfo is None:
                        candle_time = candle_time.replace(tzinfo=timezone.utc)
                    
                    time_diff = abs((candle_time - checkpoint_time).total_seconds())
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_candle = candle
                
                if closest_candle:
                    checkpoint_price = closest_candle.close
                    roi_pct, roi_mult = ROICalculator.calculate_roi(entry_price, checkpoint_price)
                    
                    self.logger.info(
                        f"  ✅ {checkpoint_name}: Found candle at {closest_candle.timestamp} "
                        f"(diff: {min_time_diff/3600:.1f}h) - ${checkpoint_price:.6f} ({roi_mult:.3f}x, {roi_pct:+.1f}%)"
                    )
                    
                    checkpoint.timestamp = checkpoint_time
                    checkpoint.price = checkpoint_price
                    checkpoint.roi_percentage = roi_pct
                    checkpoint.roi_multiplier = roi_mult
                    checkpoint.reached = True
                    
                    checkpoints_populated += 1
                else:
                    self.logger.warning(f"  ❌ {checkpoint_name}: No matching candle found!")
            
            if checkpoints_populated > 0:
                # Update ATH from OHLC data
                ath_price_from_ohlc = ohlc_result.get('ath_price')
                ath_timestamp_from_ohlc = ohlc_result.get('ath_timestamp')
                days_to_ath_from_ohlc = ohlc_result.get('days_to_ath')
                
                if ath_price_from_ohlc and ath_price_from_ohlc > 0:
                    outcome.ath_price = ath_price_from_ohlc
                    outcome.ath_timestamp = ath_timestamp_from_ohlc
                    outcome.ath_multiplier = ath_price_from_ohlc / entry_price
                    outcome.days_to_ath = days_to_ath_from_ohlc
                    outcome.current_price = ath_price_from_ohlc
                    outcome.current_multiplier = outcome.ath_multiplier
                    
                    self.logger.info(
                        f"📈 Updated ATH from OHLC: ${ath_price_from_ohlc:.6f} "
                        f"({outcome.ath_multiplier:.3f}x) on day {days_to_ath_from_ohlc:.1f}"
                    )
                
                self.logger.info(f"✅ Populated {checkpoints_populated}/{len(CHECKPOINTS)} checkpoints with historical prices")
                return True
            else:
                self.logger.warning(f"❌ No checkpoints could be populated for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error populating checkpoints from OHLC: {e}")
            return False

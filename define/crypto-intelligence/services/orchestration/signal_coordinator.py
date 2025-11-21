"""Signal coordinator - thin orchestration layer for signal processing."""
import time
from typing import List, Dict, Any

from domain.message_event import MessageEvent
from services.message_processing.processed_message import ProcessedMessage
from utils.logger import get_logger


class SignalCoordinator:
    """
    Thin coordinator that orchestrates signal processing workflow.
    
    Delegates to specialized services:
    - AddressProcessingService: Address extraction and validation
    - PriceFetchingService: Price and historical data
    - SignalTrackingService: Performance and outcome tracking
    """
    
    def __init__(
        self,
        address_processing_service,
        price_fetching_service,
        signal_tracking_service,
        data_output,
        logger=None
    ):
        """Initialize signal coordinator with service dependencies."""
        self.address_service = address_processing_service
        self.price_service = price_fetching_service
        self.tracking_service = signal_tracking_service
        self.data_output = data_output
        self.logger = logger or get_logger('SignalCoordinator')
    
    async def process_signal(
        self,
        event: MessageEvent,
        processed: ProcessedMessage
    ) -> List[Dict[str, Any]]:
        """
        Process signal through complete pipeline.
        
        Args:
            event: Message event
            processed: Processed message
            
        Returns:
            List of address data for display
        """
        total_start = time.time()
        addresses_data = []
        
        if not processed.is_crypto_relevant or not processed.crypto_mentions:
            return addresses_data
        
        # Step 1: Extract and validate addresses
        addresses = await self.address_service.extract_and_validate_addresses(event, processed)
        
        if not addresses:
            return addresses_data
        
        # Step 2: Filter addresses
        addresses = await self.address_service.filter_addresses(
            addresses,
            event.message_text or "",
            self.price_service.price_engine
        )
        
        if not addresses:
            original_count = len(addresses)
            self.logger.info(f"🚫 All {original_count} address(es) filtered out")
            return addresses_data
        
        # Step 3: Process each address
        for addr in addresses:
            if not addr.is_valid:
                continue
            
            addr_data = await self._process_single_address(event, processed, addr)
            if addr_data:
                addresses_data.append(addr_data)
        
        total_time = (time.time() - total_start) * 1000
        self.logger.info(f"⏱️  Total signal processing: {total_time:.0f}ms")
        
        return addresses_data
    
    async def _process_single_address(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr
    ) -> Dict[str, Any]:
        """Process a single address through the pipeline."""
        # Check if dead token
        is_dead_token, dead_token_reason = await self.tracking_service.check_dead_token(
            addr.address, addr.chain
        )
        
        if is_dead_token:
            self.logger.info(f"[TRACKING DEAD TOKEN] Will track for 30 days as failed signal")
        
        # Fetch current price
        price_data = await self.price_service.fetch_current_price(addr.address, addr.chain)
        
        if not price_data and is_dead_token:
            # Dead token without price - use minimal price
            price_data = await self.price_service.create_dead_token_price_data(addr.address)
        elif not price_data:
            return None
        
        # Write token price
        await self.data_output.write_token_price(
            address=addr.address,
            chain=addr.chain,
            price_data=price_data
        )
        
        # Fetch and write historical data
        symbol = price_data.symbol if price_data.symbol != 'UNKNOWN' else None
        historical_data = await self.price_service.fetch_historical_data(
            addr.address, addr.chain, symbol
        )
        
        if historical_data:
            if 'symbol' not in historical_data or not historical_data['symbol']:
                historical_data['symbol'] = symbol
            await self.data_output.write_historical(addr.address, addr.chain, historical_data)
        
        # Calculate message age
        message_age_hours, message_age_days = self.tracking_service.calculate_message_age(
            event.timestamp
        )
        
        # Check if signal is complete
        if self.tracking_service.is_signal_complete(message_age_days):
            await self._handle_complete_signal(
                event, processed, addr, price_data, symbol, message_age_days
            )
            return None  # Don't track completed signals
        
        # Handle ongoing signal
        return await self._handle_ongoing_signal(
            event, processed, addr, price_data, symbol,
            message_age_hours, message_age_days,
            is_dead_token, dead_token_reason
        )
    
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
        
        # Get or create outcome
        outcome = self.tracking_service.create_or_get_outcome(
            event, processed, addr.address,
            price_data.price_usd, price_data, symbol
        )
        
        # Check if already has OHLC data
        if hasattr(outcome, 'ath_price') and outcome.ath_price > price_data.price_usd:
            self.logger.debug(f"Outcome already has OHLC data")
            return
        
        # Fetch OHLC data
        ohlc_result = await self.price_service.fetch_ohlc_with_ath(
            symbol, event.timestamp, window_days=30,
            address=addr.address, chain=addr.chain
        )
        
        if ohlc_result and ohlc_result.get('ath_price'):
            # Update outcome with OHLC data
            entry_price = price_data.price_usd
            outcome.ath_price = ohlc_result['ath_price']
            outcome.ath_timestamp = ohlc_result.get('ath_timestamp')
            outcome.ath_multiplier = ohlc_result['ath_price'] / entry_price
            outcome.days_to_ath = ohlc_result.get('days_to_ath', 0)
            outcome.is_complete = True
            outcome.status = "completed"
            
            # Populate checkpoints
            await self.tracking_service.populate_checkpoints_from_ohlc(
                outcome, entry_price, event.timestamp, symbol,
                addr.address, addr.chain, 30, ohlc_result
            )
            
            # Classify outcome
            outcome.outcome_category = self.tracking_service.classify_outcome(
                outcome, getattr(price_data, 'market_tier', 'small')
            )
            
            self.logger.info(
                f"[OHLC] Complete signal: {outcome.outcome_category.upper()} - "
                f"ATH {outcome.ath_multiplier:.3f}x at day {outcome.days_to_ath:.1f}"
            )
        else:
            # Fallback: no OHLC data
            outcome.ath_price = price_data.price_usd
            outcome.ath_timestamp = event.timestamp
            outcome.ath_multiplier = 1.0
            outcome.is_complete = True
            outcome.status = "completed"
            outcome.outcome_category = "break_even"
            
            self.logger.info(f"[FALLBACK] Complete signal: BREAK_EVEN (no data)")
    
    async def _handle_ongoing_signal(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        addr,
        price_data,
        symbol: str,
        message_age_hours: float,
        message_age_days: float,
        is_dead_token: bool,
        dead_token_reason: str
    ) -> Dict[str, Any]:
        """Handle signals that are <30 days old."""
        entry_price = price_data.price_usd
        
        # Fetch historical entry price if message is old
        if message_age_hours > 1.0 and symbol:
            historical_entry, source = await self.price_service.fetch_entry_price(
                symbol, event.timestamp, addr.address, addr.chain, message_age_hours
            )
            if historical_entry and historical_entry > 0:
                entry_price = historical_entry
        
        # Track performance
        known_ath = getattr(price_data, 'ath', None)
        await self.tracking_service.track_ongoing_signal(
            addr.address, addr.chain, price_data.price_usd,
            str(event.message_id), known_ath, symbol
        )
        
        # Get performance data
        perf_data = self.tracking_service.get_performance_data(addr.address)
        
        # Return display data
        return {
            'address': addr.address,
            'chain': addr.chain,
            'price': price_data.price_usd,
            'symbol': symbol or addr.address[:10],
            'ath_multiplier': perf_data['ath_multiplier'] if perf_data else 1.0,
            'days_tracked': perf_data['days_tracked'] if perf_data else 0,
            'is_dead_token': is_dead_token,
            'dead_token_reason': dead_token_reason
        }

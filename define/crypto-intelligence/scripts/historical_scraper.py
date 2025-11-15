"""
Historical Message Scraper for End-to-End Verification

Fetches historical messages from Telegram channels and processes them through
the complete Part 2 pipeline to verify all components work correctly with real data.
"""

import asyncio
import argparse
import sys
import os
import aiohttp
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from config.price_config import PriceConfig
from config.performance_config import PerformanceConfig
from config.output_config import OutputConfig
from infrastructure.telegram.telegram_monitor import TelegramMonitor
from services.message_processing.message_processor import MessageProcessor
from services.message_processing.address_extractor import AddressExtractor
from services.pricing.price_engine import PriceEngine
from services.tracking.performance_tracker import PerformanceTracker
from infrastructure.output.data_output import MultiTableDataOutput
from utils.logger import setup_logger
from utils.error_handler import ErrorHandler, RetryConfig
from utils.report_generator import ReportGenerator
# Part 8: Channel Reputation + Outcome Learning
from services.tracking.outcome_tracker import OutcomeTracker
from services.reputation.reputation_engine import ReputationEngine
# Part 8 - Task 4: Historical price retrieval
from services.pricing import HistoricalPriceRetriever
from utils.roi_calculator import ROICalculator
# Part 8 - Task 5: Historical bootstrap with two-file tracking
from services.reputation import HistoricalBootstrap
from domain.bootstrap_status import BootstrapStatus


class HistoricalScraper:
    """Historical message scraper for verification."""
    
    def __init__(self, config: Config):
        """
        Initialize scraper.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.logger = setup_logger('HistoricalScraper', config.log_level)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(
            RetryConfig(
                max_attempts=config.retry.max_attempts,
                base_delay=config.retry.base_delay,
                exponential_base=config.retry.exponential_base,
                jitter=config.retry.jitter
            )
        )
        
        # Initialize message processor
        self.message_processor = MessageProcessor(
            error_handler=self.error_handler,
            max_ic=config.processing.hdrb_max_ic,
            confidence_threshold=config.processing.confidence_threshold
        )
        
        # Initialize pair resolver for LP pair detection
        from services.message_processing.pair_resolver import PairResolver
        self.pair_resolver = PairResolver(logger=self.logger)
        
        # Initialize address extractor (Part 3) with pair resolver
        self.address_extractor = AddressExtractor(pair_resolver=self.pair_resolver)
        
        # Initialize price engine (Part 3)
        price_config = PriceConfig.load_from_env()
        self.price_engine = PriceEngine(price_config)
        
        # Initialize performance tracker (Part 3 - Task 3)
        performance_config = PerformanceConfig.load_from_env()
        self.performance_tracker = PerformanceTracker(
            data_dir=performance_config.data_dir,
            tracking_days=performance_config.tracking_days,
            csv_output_dir="output",
            enable_csv=False  # Disable CSV in tracker, use MultiTableDataOutput instead
        )
        
        # Initialize multi-table data output (Part 3 - Task 4)
        output_config = OutputConfig.load_from_env()
        self.data_output = MultiTableDataOutput(output_config, self.logger)
        
        # Initialize Part 8 components
        self.outcome_tracker = OutcomeTracker(data_dir="data/reputation", logger=self.logger)
        self.reputation_engine = ReputationEngine(data_dir="data/reputation", logger=self.logger)
        
        # Part 8 - Task 5: Initialize historical bootstrap with two-file tracking
        self.historical_bootstrap = None  # Will be initialized when needed
        
        # Part 8 - Task 4: Initialize historical price retriever
        self.historical_price_retriever = HistoricalPriceRetriever(
            cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
            cache_dir="data/cache",
            symbol_mapping_path="data/symbol_mapping.json",  # Add symbol mapping
            logger=self.logger
        )
        
        # Part 8 - Task 4: Initialize dead token detector
        from services.validation import DeadTokenDetector
        self.dead_token_detector = DeadTokenDetector(
            etherscan_api_key=os.getenv('ETHERSCAN_API_KEY', ''),
            blacklist_path="data/dead_tokens_blacklist.json",
            logger=self.logger
        )
        
        # Initialize Telegram monitor
        self.telegram_monitor = TelegramMonitor(
            config.telegram,
            config.channels
        )
        
        # Statistics
        self.stats = {
            'total_messages': 0,
            'processed_messages': 0,
            'crypto_relevant': 0,
            'high_confidence': 0,
            'positive_sentiment': 0,
            'negative_sentiment': 0,
            'neutral_sentiment': 0,
            'hdrb_scores': [],
            'confidence_scores': [],
            'processing_times': [],
            'errors': 0,
            # Part 3 statistics
            'addresses_found': 0,
            'evm_addresses': 0,
            'solana_addresses': 0,
            'invalid_addresses': 0,
            'prices_fetched': 0,
            'price_failures': 0,
            'api_usage': {},
            # Part 3 - Task 3: Performance tracking statistics
            'tracking_started': 0,
            'tracking_updated': 0,
            'performance_ath_updates': 0,
            # Part 3 - Task 4: Multi-table output statistics
            'messages_written': 0,
            'token_prices_written': 0,
            'performance_written': 0,
            'historical_written': 0,
            # Part 8: Channel Reputation + Outcome Learning statistics
            'signals_tracked': 0,
            'roi_checkpoints_reached': 0,
            'outcome_ath_updates': 0,
            'winners_classified': 0,
            'losers_classified': 0,
            'reputations_calculated': 0,
            # Part 8 - Task 4: Dead token detection statistics
            'dead_tokens_detected': 0,
            'dead_tokens_skipped': 0,
        }
        
        # Connection state tracking
        self._connected = False
        self._disconnected = False
        
        self.logger.info("Historical scraper initialized")
    
    async def __aenter__(self):
        """Context manager entry - connect to Telegram."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        await self.disconnect()
        return False  # Don't suppress exceptions
    
    async def connect(self) -> bool:
        """
        Connect to Telegram.
        
        Returns:
            True if connected successfully
        """
        self.logger.info("Connecting to Telegram...")
        result = await self.telegram_monitor.connect()
        if result:
            self._connected = True
        return result
    
    async def disconnect(self):
        """Disconnect from Telegram and cleanup resources."""
        # Prevent double-cleanup
        if self._disconnected:
            return
        
        # Set flag IMMEDIATELY to prevent re-entry
        self._disconnected = True
        
        self.logger.info("Disconnecting from Telegram...")
        
        # Cleanup Telegram connection
        if self._connected:
            try:
                await self.telegram_monitor.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting Telegram: {e}")
        
        # Cleanup price engine sessions
        if hasattr(self, 'price_engine'):
            try:
                await self.price_engine.close()
            except Exception as e:
                self.logger.error(f"Error closing price engine: {e}")
        
        # Cleanup pair resolver session
        if hasattr(self, 'pair_resolver'):
            try:
                await self.pair_resolver.close()
            except Exception as e:
                self.logger.error(f"Error closing pair resolver: {e}")
        
        # Cleanup historical price retriever session
        if hasattr(self, 'historical_price_retriever'):
            try:
                await self.historical_price_retriever.close()
            except Exception as e:
                self.logger.error(f"Error closing historical price retriever: {e}")
        
        # Cleanup dead token detector
        if hasattr(self, 'dead_token_detector'):
            try:
                await self.dead_token_detector.close()
            except Exception as e:
                self.logger.error(f"Error closing dead token detector: {e}")
    
    async def _fetch_historical_checkpoint_prices(self, outcome, symbol: str, address: str, chain: str):
        """
        Fetch historical prices at each checkpoint to calculate real ATH.
        
        Args:
            outcome: SignalOutcome object
            symbol: Token symbol
            address: Token address
            chain: Blockchain chain
        """
        try:
            from datetime import timedelta
            
            # Fetch price at each checkpoint
            for checkpoint_name, checkpoint_data in outcome.checkpoints.items():
                if not checkpoint_data.reached or not checkpoint_data.timestamp:
                    continue
                
                # Fetch historical price at this checkpoint
                historical_price, price_source = await self.historical_price_retriever.fetch_closest_entry_price(
                    symbol=symbol,
                    message_timestamp=checkpoint_data.timestamp,
                    address=address,
                    chain=chain
                )
                
                if historical_price and historical_price > 0:
                    # Update checkpoint with real price
                    checkpoint_data.price = historical_price
                    roi_percentage, roi_multiplier = ROICalculator.calculate_roi(outcome.entry_price, historical_price)
                    checkpoint_data.roi_percentage = roi_percentage
                    checkpoint_data.roi_multiplier = roi_multiplier
                    
                    # Update ATH if this checkpoint has higher price
                    if historical_price > outcome.ath_price:
                        outcome.ath_price = historical_price
                        outcome.ath_multiplier = roi_multiplier
                        outcome.ath_timestamp = checkpoint_data.timestamp
                        
                        # Calculate days to ATH
                        if outcome.entry_timestamp:
                            outcome.days_to_ath = (checkpoint_data.timestamp - outcome.entry_timestamp).total_seconds() / 86400
                    
                    self.logger.debug(f"  {checkpoint_name}: ${historical_price:.6f} ({roi_multiplier:.3f}x)")
                else:
                    self.logger.debug(f"  {checkpoint_name}: No price data available")
            
            # Update current price to last checkpoint price
            last_checkpoint = list(outcome.checkpoints.values())[-1]
            if last_checkpoint.price > 0:
                outcome.current_price = last_checkpoint.price
                outcome.current_multiplier = outcome.current_price / outcome.entry_price
            
            self.logger.info(f"Historical ATH calculated: {outcome.ath_multiplier:.3f}x at {outcome.days_to_ath:.1f} days")
            
        except Exception as e:
            self.logger.error(f"Error fetching historical checkpoint prices: {e}")
    
    async def fetch_messages(self, channel_id: str, limit: int = 100, offset_date=None) -> list:
        """
        Fetch historical messages from a channel.
        
        Args:
            channel_id: Channel ID or username
            limit: Maximum number of messages to fetch
            offset_date: Optional datetime to start fetching from (fetches older messages from this date)
            
        Returns:
            List of messages
        """
        if offset_date:
            self.logger.info(f"Fetching {limit} messages from {channel_id} starting from {offset_date}...")
        else:
            self.logger.info(f"Fetching {limit} messages from {channel_id}...")
        
        messages = []
        channel = None
        
        try:
            # Get the channel entity
            channel = await self.telegram_monitor.client.get_entity(channel_id)
            
            # Fetch messages
            async for message in self.telegram_monitor.client.iter_messages(channel, limit=limit, offset_date=offset_date):
                if message.text:  # Only process text messages
                    messages.append(message)
            
            self.logger.info(f"Fetched {len(messages)} messages")
            if messages:
                self.logger.info(f"Date range: {messages[-1].date} to {messages[0].date}")
            return messages
            
        except asyncio.CancelledError:
            self.logger.info(f"Message fetching cancelled, returning {len(messages)} partial results")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching messages: {e}")
            return []
    
    def _increment_stat(self, key: str, value: int = 1):
        """
        Safely increment a statistic with validation.
        
        Args:
            key: Statistics key to increment
            value: Amount to increment by (default: 1)
        """
        if key not in self.stats:
            self.logger.error(f"Unknown statistic key: {key}")
            raise KeyError(f"Unknown statistic key: {key}")
        self.stats[key] += value
    

    
    async def update_signal_checkpoints(self, address: str, symbol: str):
        """
        Update signal outcome checkpoints with real historical prices using HistoricalPriceRetriever.
        
        Uses forward OHLC data to calculate accurate entry price, ATH, and checkpoint ROIs.
        
        Args:
            address: Token address
            symbol: Token symbol for price lookup
        """
        try:
            outcome = self.outcome_tracker.outcomes.get(address)
            if not outcome:
                return
            
            self.logger.info(f"Updating checkpoints for {symbol} ({address[:10]}...)")
            self.logger.info(f"Message date: {outcome.entry_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # STEP 1: Get closest entry price to message time
            # Pass address and chain for DexScreener fallback (for small tokens)
            entry_price, entry_source = await self.historical_price_retriever.fetch_closest_entry_price(
                symbol,
                outcome.entry_timestamp,
                address=address,
                chain='evm' if address.startswith('0x') else 'solana'
            )
            
            if not entry_price:
                self.logger.warning(f"No entry price found for {symbol}, keeping existing: ${outcome.entry_price:.6f}")
                entry_price = outcome.entry_price
            else:
                self.logger.info(f"Entry price: ${entry_price:.6f} (source: {entry_source})")
                # Update outcome with accurate entry price
                outcome.entry_price = entry_price
            
            # STEP 2: Get forward OHLC data and calculate ATH
            ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                symbol,
                outcome.entry_timestamp,
                window_days=30,
                address=address,
                chain='evm' if address.startswith('0x') else 'solana'
            )
            
            if not ohlc_result:
                self.logger.warning(f"No OHLC data found for {symbol}, skipping forward analysis")
                return
            
            self.logger.info(
                f"OHLC data: {len(ohlc_result['candles'])} candles "
                f"({ohlc_result['data_completeness']*100:.1f}% complete)"
            )
            
            # STEP 3: Update ATH from OHLC data
            ath_price = ohlc_result['ath_price']
            ath_timestamp = ohlc_result['ath_timestamp']
            days_to_ath = ohlc_result['days_to_ath']
            
            outcome.ath_price = ath_price
            outcome.ath_timestamp = ath_timestamp
            outcome.ath_multiplier = ath_price / entry_price
            outcome.days_to_ath = days_to_ath
            
            self.logger.info(
                f"ATH: ${ath_price:.6f} ({outcome.ath_multiplier:.3f}x) "
                f"reached on day {days_to_ath:.1f}"
            )
            
            # STEP 4: Update checkpoint prices from OHLC data
            # Extract prices at day 7 and day 30 from OHLC candles
            candles = ohlc_result.get('candles', [])
            if candles:
                # Find closest candle to day 7 (around day 7)
                day_7_candle = None
                day_30_candle = None
                
                for candle in candles:
                    # Calculate days elapsed from entry timestamp
                    # Ensure both timestamps are timezone-aware
                    candle_ts = candle.timestamp
                    entry_ts = outcome.entry_timestamp
                    if candle_ts.tzinfo is None:
                        from datetime import timezone
                        candle_ts = candle_ts.replace(tzinfo=timezone.utc)
                    if entry_ts.tzinfo is None:
                        from datetime import timezone
                        entry_ts = entry_ts.replace(tzinfo=timezone.utc)
                    
                    days_elapsed = (candle_ts - entry_ts).total_seconds() / 86400
                    
                    if 6.5 <= days_elapsed <= 7.5 and not day_7_candle:
                        day_7_candle = candle
                    if 29.5 <= days_elapsed <= 30.5 and not day_30_candle:
                        day_30_candle = candle
                
                # Update day 7 checkpoint with actual price
                if day_7_candle and outcome.checkpoints.get("7d"):
                    day_7_price = day_7_candle.close
                    outcome.checkpoints["7d"].price = day_7_price
                    outcome.checkpoints["7d"].roi_multiplier = day_7_price / entry_price
                    outcome.checkpoints["7d"].roi_percentage = ((day_7_price - entry_price) / entry_price) * 100
                    self.logger.debug(f"Updated day 7 checkpoint: ${day_7_price:.6f} ({outcome.checkpoints['7d'].roi_multiplier:.3f}x)")
                
                # Update day 30 checkpoint with actual price
                if day_30_candle and outcome.checkpoints.get("30d"):
                    day_30_price = day_30_candle.close
                    outcome.checkpoints["30d"].price = day_30_price
                    outcome.checkpoints["30d"].roi_multiplier = day_30_price / entry_price
                    outcome.checkpoints["30d"].roi_percentage = ((day_30_price - entry_price) / entry_price) * 100
                    self.logger.debug(f"Updated day 30 checkpoint: ${day_30_price:.6f} ({outcome.checkpoints['30d'].roi_multiplier:.3f}x)")
                
                # If no exact match, use last candle for day 30 if signal is complete
                if not day_30_candle and outcome.checkpoints.get("30d") and len(candles) >= 30:
                    last_candle = candles[-1]
                    day_30_price = last_candle.close
                    outcome.checkpoints["30d"].price = day_30_price
                    outcome.checkpoints["30d"].roi_multiplier = day_30_price / entry_price
                    outcome.checkpoints["30d"].roi_percentage = ((day_30_price - entry_price) / entry_price) * 100
                    self.logger.debug(f"Updated day 30 checkpoint (last candle): ${day_30_price:.6f} ({outcome.checkpoints['30d'].roi_multiplier:.3f}x)")
            
            self.logger.info(f"Updated ATH from OHLC: ${ath_price:.6f} ({outcome.ath_multiplier:.3f}x)")
            
            # Update current price to ATH (for completed signals)
            outcome.current_price = ath_price
            outcome.current_multiplier = outcome.ath_multiplier
            
            # Classify outcome based on market tier (industry standard: 1:3 risk/reward)
            # Large-cap: 20%+ gain, Mid-cap: 50%+ gain, Small/Micro-cap: 100%+ gain
            winner_threshold = 2.0  # Default: 2x for micro/small cap
            if outcome.market_tier == "large":
                winner_threshold = 1.2  # 20% gain for large cap (BTC, ETH)
            elif outcome.market_tier == "mid":
                winner_threshold = 1.5  # 50% gain for mid cap
            
            # Determine if signal is actually complete (≥30 days elapsed)
            signal_status = self.historical_bootstrap.determine_signal_status(outcome.entry_timestamp)
            outcome.status = signal_status
            outcome.is_complete = (signal_status == "completed")
            
            # Process time-based checkpoints (Task 3: Dual-metric performance classification)
            # Check which checkpoints have been reached and process them
            if outcome.checkpoints.get("7d") and outcome.checkpoints["7d"].reached:
                self.outcome_tracker._process_day_7_checkpoint(outcome)
            
            if outcome.checkpoints.get("30d") and outcome.checkpoints["30d"].reached:
                self.outcome_tracker._process_day_30_checkpoint(outcome)
            
            # Only classify as winner/loser if signal is complete (≥30 days)
            if outcome.is_complete:
                if outcome.ath_multiplier >= winner_threshold:
                    outcome.is_winner = True
                    outcome.outcome_category = "winner"
                    self._increment_stat('winners_classified')
                elif outcome.ath_multiplier < 1.0:
                    outcome.is_winner = False
                    outcome.outcome_category = "loser"
                    self._increment_stat('losers_classified')
                else:
                    outcome.is_winner = False
                    outcome.outcome_category = "break_even"
                
                outcome.completion_reason = "30d_elapsed"
                self.logger.info(f"Signal COMPLETED: {outcome.outcome_category.upper()} - ATH {outcome.ath_multiplier:.3f}x")
            else:
                # Signal still in progress, just update ATH data
                self.logger.info(f"Signal IN PROGRESS: ATH {outcome.ath_multiplier:.3f}x (not yet 30 days)")
            
            # Save updated outcome
            self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
            
        except Exception as e:
            self.logger.error(f"Error updating checkpoints for {address}: {e}")
    
    async def process_messages(self, messages: list, channel_name: str):
        """
        Process messages through the pipeline.
        
        Args:
            messages: List of Telegram messages
            channel_name: Name of the channel
        """
        self.logger.info(f"Processing {len(messages)} messages...")
        
        # Part 8 - Task 5: Initialize historical bootstrap with two-file tracking
        if self.historical_bootstrap is None:
            from services.pricing import HistoricalPriceService
            historical_price_service = HistoricalPriceService(
                cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
                cache_dir="data/cache",
                symbol_mapping_path="data/symbol_mapping.json",
                logger=self.logger
            )
            self.historical_bootstrap = HistoricalBootstrap(
                data_dir="data/reputation",
                historical_price_service=historical_price_service,
                logger=self.logger
            )
            # Load existing data
            self.historical_bootstrap.load_existing_data()
            # Load progress for resumability
            self.bootstrap_status = self.historical_bootstrap.load_progress()
            if self.bootstrap_status:
                self.logger.info(f"Resuming from message ID: {self.bootstrap_status.last_processed_message_id}")
            else:
                # Create new bootstrap status
                self.bootstrap_status = BootstrapStatus(
                    total_messages=len(messages),
                    channel_name=channel_name,
                    started_at=datetime.now()
                )
        
        for msg_idx, message in enumerate(messages, 1):
            try:
                self._increment_stat('total_messages')
                
                # Log progress
                if msg_idx % 10 == 0:
                    self.logger.info(f"Processing message {msg_idx}/{len(messages)}")
                
                # Process message
                processed = await self.message_processor.process_message(
                    channel_name=channel_name,
                    message_text=message.text,
                    timestamp=message.date,
                    message_id=message.id,
                    message_obj=message,
                    channel_id=str(message.peer_id.channel_id) if hasattr(message.peer_id, 'channel_id') else ""
                )
                
                # Part 3 - Task 4: Write message to MESSAGES table
                if processed.is_crypto_relevant:
                    # Log the actual message date for debugging
                    self.logger.debug(f"Message {message.id} date: {message.date} (type: {type(message.date)})")
                    
                    await self.data_output.write_message({
                        'message_id': str(message.id),
                        'timestamp': message.date.isoformat(),
                        'channel_name': channel_name,
                        'message_text': message.text,
                        'hdrb_score': processed.hdrb_score,
                        'crypto_mentions': processed.crypto_mentions,
                        'sentiment': processed.sentiment,
                        'confidence': processed.confidence
                    })
                    self._increment_stat('messages_written')
                
                # Part 3: Extract addresses from crypto mentions (with LP pair resolution)
                if processed.is_crypto_relevant and processed.crypto_mentions:
                    addresses = await self.address_extractor.extract_addresses_async(processed.crypto_mentions)
                    
                    for addr_idx, addr in enumerate(addresses):
                        self._increment_stat('addresses_found')
                        if addr.chain == 'evm':
                            self._increment_stat('evm_addresses')
                        elif addr.chain == 'solana':
                            self._increment_stat('solana_addresses')
                        
                        if not addr.is_valid:
                            self._increment_stat('invalid_addresses')
                        
                        # Part 3: Fetch price for valid addresses
                        if addr.is_valid:
                            # Part 8 - Task 4: Check if token is blacklisted as dead
                            if self.dead_token_detector.is_blacklisted(addr.address):
                                reason = self.dead_token_detector.get_blacklist_reason(addr.address)
                                self.logger.info(f"[SKIP] Token {addr.address[:10]}... is blacklisted: {reason}")
                                self._increment_stat('dead_tokens_skipped')
                                continue
                            
                            # Check if token is dead and blacklist if so
                            stats = await self.dead_token_detector.check_and_blacklist_if_dead(addr.address, addr.chain)
                            if stats.is_dead:
                                self.logger.warning(f"[DEAD TOKEN] Skipping {addr.address[:10]}...: {stats.reason}")
                                self._increment_stat('dead_tokens_detected')
                                continue
                            
                            price_data = await self.price_engine.get_price(addr.address, addr.chain)
                            
                            if price_data:
                                self._increment_stat('prices_fetched')
                                # Track API usage
                                api_source = price_data.source
                                self.stats['api_usage'][api_source] = self.stats['api_usage'].get(api_source, 0) + 1
                                
                                # Part 3 - Task 4: Write token price to TOKEN_PRICES table
                                await self.data_output.write_token_price(
                                    address=addr.address,
                                    chain=addr.chain,
                                    price_data=price_data
                                )
                                self._increment_stat('token_prices_written')
                                
                                # Part 8 - Task 4: For historical messages, fetch historical entry price
                                # This is THE KEY FIX for accurate ROI calculation!
                                entry_price = price_data.price_usd  # Default to current price
                                symbol = price_data.symbol if price_data.symbol else addr.address[:10]
                                
                                # Check if this is a historical message (more than 1 hour old)
                                from datetime import timezone
                                now_utc = datetime.now(timezone.utc)
                                # Ensure message.date is timezone-aware
                                msg_date = message.date if message.date.tzinfo else message.date.replace(tzinfo=timezone.utc)
                                message_age = (now_utc - msg_date).total_seconds() / 3600  # hours
                                if message_age > 1.0 and symbol:
                                    # Fetch historical price from message date with symbol mapping support
                                    self.logger.info(f"Historical message ({message_age:.1f}h old) - fetching historical entry price for {symbol}")
                                    historical_entry_price, price_source = await self.historical_price_retriever.fetch_closest_entry_price(
                                        symbol=symbol,
                                        message_timestamp=message.date,
                                        address=addr.address,  # Pass address for symbol mapping
                                        chain=addr.chain
                                    )
                                    
                                    if historical_entry_price and historical_entry_price > 0:
                                        entry_price = historical_entry_price
                                        self.logger.info(f"[OK] Historical entry price: ${entry_price:.6f} (source: {price_source}, vs current: ${price_data.price_usd:.6f})")
                                    else:
                                        self.logger.warning(f"[WARNING] No historical price for {symbol} - using current price as fallback")
                                
                                # Part 3 - Task 3: Performance tracking
                                # Extract known_ath from price_data (CoinGecko's all-time ATH)
                                # Note: For historical analysis, we calculate the 30-day forward ATH separately,
                                # but we store the known_ath for reference/comparison
                                known_ath = price_data.ath if hasattr(price_data, 'ath') and price_data.ath else None
                                
                                # Check if address is already tracked in performance tracker
                                if addr.address not in self.performance_tracker.tracking_data:
                                    # Start tracking new address (with known_ath for reference)
                                    await self.performance_tracker.start_tracking(
                                        address=addr.address,
                                        chain=addr.chain,
                                        initial_price=entry_price,  # Use historical entry price!
                                        message_id=str(message.id),
                                        known_ath=known_ath  # Store CoinGecko's all-time ATH for reference
                                    )
                                    self._increment_stat('tracking_started')
                                
                                # Part 8 - Task 5: Deduplication logic with two-file tracking
                                is_duplicate, signal_number, previous_signals = self.historical_bootstrap.check_for_duplicate(addr.address)
                                
                                if is_duplicate:
                                    self.logger.info(f"Duplicate: {addr.address[:10]}... already tracked")
                                    
                                    # Even for duplicates, sync OHLC ATH to PerformanceTracker if not already synced
                                    if addr.address in self.performance_tracker.tracking_data:
                                        tracking_entry = self.performance_tracker.tracking_data[addr.address]
                                        if not tracking_entry.get('ohlc_fetched', False):
                                            # Get outcome from historical_bootstrap (uses two-file system)
                                            outcome = self.historical_bootstrap.active_outcomes.get(addr.address)
                                            if outcome and outcome.ath_price > 0:
                                                old_ath = tracking_entry['ath_since_mention']
                                                tracking_entry['known_ath'] = outcome.ath_price
                                                tracking_entry['ohlc_fetched'] = True
                                                if outcome.ath_price > tracking_entry['ath_since_mention']:
                                                    tracking_entry['ath_since_mention'] = outcome.ath_price
                                                    tracking_entry['ath_time'] = outcome.ath_timestamp.isoformat() if outcome.ath_timestamp else tracking_entry['ath_time']
                                                await self.performance_tracker.save_to_disk_async()
                                                self.logger.info(f"[SYNC] Synced duplicate signal to PerformanceTracker: ${old_ath:.6f} → ${outcome.ath_price:.6f}")
                                    
                                    continue
                                
                                # Determine signal status based on elapsed time
                                signal_status = self.historical_bootstrap.determine_signal_status(message.date)
                                
                                if signal_number > 1:
                                    self.logger.info(
                                        f"Fresh start: {addr.address[:10]}... Signal #{signal_number} "
                                        f"with entry price ${entry_price:.6f}"
                                    )
                                
                                # Part 8 - Task 1: Start tracking signal outcome (with Task 5 enhancements)
                                outcome = self.outcome_tracker.track_signal(
                                    message_id=message.id,
                                    channel_name=channel_name,
                                    address=addr.address,
                                    entry_price=entry_price,  # Use historical entry price!
                                    entry_confidence=1.0,
                                    entry_source=price_data.source,
                                    symbol=symbol,
                                    sentiment=processed.sentiment,
                                    sentiment_score=processed.sentiment_score,
                                    hdrb_score=processed.hdrb_score,
                                    confidence=processed.confidence,
                                    market_tier=price_data.market_tier if hasattr(price_data, 'market_tier') else "",
                                    risk_level=price_data.risk_level if hasattr(price_data, 'risk_level') else "",
                                    risk_score=price_data.risk_score if hasattr(price_data, 'risk_score') else 0.0,
                                    entry_timestamp=message.date  # Use historical message timestamp
                                )
                                
                                # Task 5: Set signal number and previous signals
                                outcome.signal_number = signal_number
                                outcome.previous_signals = previous_signals if previous_signals else []
                                outcome.status = signal_status
                                outcome.is_complete = (signal_status == "completed")
                                
                                self._increment_stat('signals_tracked')
                                self.logger.info(
                                    f"OutcomeTracker: Tracking signal {addr.address[:10]}... "
                                    f"(Signal #{signal_number}) at entry price ${entry_price:.6f}"
                                )
                                
                                # Force OHLC for signals past 7 days but under 30 days to populate missing data we didn't monitor
                                # Signals under 7 days use real-time tracking, signals over 7 days need OHLC backfill
                                if message_age > 168.0:  # 7 days in hours (7 * 24 = 168)
                                    await self.update_signal_checkpoints(addr.address, symbol)
                                    
                                    # Sync PerformanceTracker with OHLC ATH (so report shows correct ATH)
                                    if addr.address in self.performance_tracker.tracking_data and outcome.ath_price > 0:
                                        tracking_entry = self.performance_tracker.tracking_data[addr.address]
                                        tracking_entry['known_ath'] = outcome.ath_price  # Use OHLC ATH
                                        tracking_entry['ohlc_fetched'] = True  # Mark as fetched
                                        # Also update ath_since_mention if OHLC ATH is higher
                                        if outcome.ath_price > tracking_entry['ath_since_mention']:
                                            tracking_entry['ath_since_mention'] = outcome.ath_price
                                            tracking_entry['ath_time'] = outcome.ath_timestamp.isoformat() if outcome.ath_timestamp else tracking_entry['ath_time']
                                        await self.performance_tracker.save_to_disk_async()
                                        self.logger.debug(f"Synced PerformanceTracker with OHLC ATH: ${outcome.ath_price:.6f}")
                                    
                                    # Only classify as winner/loser if signal is complete (≥30 days)
                                    if outcome.is_complete:
                                        # Reclassify outcome based on real ATH
                                        is_winner, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
                                        outcome.is_winner = is_winner
                                        outcome.outcome_category = category
                                        
                                        if outcome.is_winner:
                                            self._increment_stat('winners_classified')
                                            self.logger.info(f"Signal complete: WINNER (ROI ≥ 1.5x)")
                                        else:
                                            self._increment_stat('losers_classified')
                                            self.logger.info(f"Signal complete: LOSER (ROI < 1.5x)")
                                        
                                        # Task 5: Add to completed outcomes
                                        self.historical_bootstrap.completed_outcomes[addr.address] = outcome
                                    else:
                                        # Signal still in progress, add to active outcomes
                                        self.historical_bootstrap.add_signal(addr.address, outcome)
                                        self.logger.info(f"Signal in progress: {symbol or addr.address[:10]} - continuing to track")
                                    
                                    # Save updated outcome
                                    self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
                                else:
                                    # Update existing tracking
                                    old_ath = self.performance_tracker.tracking_data[addr.address]['ath_since_mention']
                                    await self.performance_tracker.update_price(
                                        address=addr.address,
                                        current_price=price_data.price_usd
                                    )
                                    new_ath = self.performance_tracker.tracking_data[addr.address]['ath_since_mention']
                                    
                                    self._increment_stat('tracking_updated')
                                    if new_ath > old_ath:
                                        self._increment_stat('performance_ath_updates')
                                    
                                    # Part 8 - Task 1: Update signal outcome with new price
                                    outcome = self.outcome_tracker.update_price(addr.address, price_data.price_usd)
                                    if outcome:
                                        # Check if ATH was updated
                                        if outcome.ath_price == price_data.price_usd:
                                            self._increment_stat('outcome_ath_updates')
                                            self.logger.info(f"ATH reached: {outcome.ath_multiplier:.3f}x at checkpoint")
                                        
                                        # Check if signal completed
                                        if outcome.is_complete:
                                            if outcome.is_winner:
                                                self._increment_stat('winners_classified')
                                                self.logger.info(f"Signal complete: WINNER (ROI ≥ 1.5x)")
                                            else:
                                                self._increment_stat('losers_classified')
                                                self.logger.info(f"Signal complete: LOSER (ROI < 1.5x)")
                                
                                # Part 3 - Task 4: Write performance to PERFORMANCE table
                                perf_data = self.performance_tracker.get_performance(addr.address)
                                if perf_data:
                                    await self.data_output.write_performance(
                                        address=addr.address,
                                        chain=addr.chain,
                                        performance_data=perf_data
                                    )
                                    self._increment_stat('performance_written')
                                
                                # Part 3 - Task 4: Fetch and write historical data to HISTORICAL table
                                # Try to get symbol from price data for fallback
                                symbol = price_data.symbol if price_data and price_data.symbol else None
                                historical_data = await self.price_engine.get_historical_data(addr.address, addr.chain, symbol)
                                if historical_data:
                                    await self.data_output.write_historical(
                                        address=addr.address,
                                        chain=addr.chain,
                                        historical_data=historical_data
                                    )
                                    self._increment_stat('historical_written')
                                    # Track source
                                    source = historical_data.get('source', 'coingecko')
                                    if source not in self.stats:
                                        self.stats[source] = 0
                                    self.stats[source] += 1
                            else:
                                self._increment_stat('price_failures')
                                
                                # Even if price fetch failed, try Twelve Data fallback for historical data
                                # Extract potential symbol from crypto mentions
                                symbol = None
                                if processed.crypto_mentions:
                                    # Look for ticker symbols (uppercase, 2-5 chars)
                                    import re
                                    for mention in processed.crypto_mentions:
                                        if re.match(r'^[A-Z]{2,5}$', mention):
                                            symbol = mention
                                            break
                                
                                if symbol:
                                    self.logger.info(f"Attempting Twelve Data fallback for failed address with symbol: {symbol}")
                                    historical_data = await self.price_engine.get_historical_data(addr.address, addr.chain, symbol)
                                    if historical_data:
                                        await self.data_output.write_historical(
                                            address=addr.address,
                                            chain=addr.chain,
                                            historical_data=historical_data
                                        )
                                        self._increment_stat('historical_written')
                                        # Track source (dynamic key, so direct access is acceptable)
                                        source = historical_data.get('source', 'twelvedata')
                                        if source not in self.stats:
                                            self.stats[source] = 0
                                        self.stats[source] += 1
                
                # Update statistics
                self._increment_stat('processed_messages')
                self.stats['hdrb_scores'].append(processed.hdrb_score)
                self.stats['confidence_scores'].append(processed.confidence)
                self.stats['processing_times'].append(processed.processing_time_ms)
                
                if processed.is_crypto_relevant:
                    self._increment_stat('crypto_relevant')
                
                if processed.is_high_confidence:
                    self._increment_stat('high_confidence')
                
                if processed.sentiment == 'positive':
                    self._increment_stat('positive_sentiment')
                elif processed.sentiment == 'negative':
                    self._increment_stat('negative_sentiment')
                else:
                    self._increment_stat('neutral_sentiment')
                
                if processed.error:
                    self._increment_stat('errors')
                
                # Part 8 - Task 5: Save progress checkpoint every 100 messages
                if msg_idx % 100 == 0:
                    self.bootstrap_status.processed_messages = msg_idx
                    self.bootstrap_status.last_processed_message_id = message.id
                    self.bootstrap_status.last_processed_timestamp = message.date
                    self.historical_bootstrap.save_progress(self.bootstrap_status)
                    self.historical_bootstrap.save_all()
                    self.logger.info(f"Checkpoint saved: {msg_idx} messages, {self.stats['signals_tracked']} tokens")
                
            except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
                # Don't catch these - allow graceful shutdown
                raise
            except Exception as e:
                self.logger.error(f"Error processing message {message.id}: {e}")
                self._increment_stat('errors')
        
        # Part 8 - Task 5: Save final state and clear progress
        self.historical_bootstrap.save_all()
        self.historical_bootstrap.clear_progress()
        self.logger.info("Bootstrap complete: Clearing progress file")
        
        # Log two-file tracking statistics
        stats = self.historical_bootstrap.get_statistics()
        self.logger.info(
            f"Active signals: {stats['active_signals']}, "
            f"Completed signals: {stats['completed_signals']}"
        )
        
        # Part 8 - Task 2: Calculate channel reputation after processing all messages
        self.logger.info(f"Calculating reputation for channel: {channel_name}")
        channel_outcomes = self.outcome_tracker.get_channel_outcomes(channel_name, completed_only=True)
        if channel_outcomes:
            reputation = self.reputation_engine.update_reputation(channel_name, channel_outcomes)
            self._increment_stat('reputations_calculated')
            self.logger.info(
                f"ReputationEngine: Calculating reputation for {channel_name}\n"
                f"Win Rate: {reputation.win_rate:.1f}% ({reputation.winning_signals}/{reputation.total_signals} signals ≥2x)\n"
                f"Average ROI: {reputation.average_roi:.3f}x ({(reputation.average_roi - 1) * 100:.1f}% average gain)\n"
                f"Reputation Score: {reputation.reputation_score:.1f}/100 → {reputation.reputation_tier}"
            )
            
            # Part 8 - Task 3: Apply multi-dimensional TD learning
            self.logger.info(f"\n=== Applying Multi-Dimensional TD Learning for {channel_name} ===")
            for outcome in channel_outcomes:
                # Level 1: Overall Channel TD Learning
                self.reputation_engine.apply_td_learning(channel_name, outcome)
                
                # Level 2: Coin-Specific TD Learning
                self.reputation_engine.apply_coin_specific_td_learning(channel_name, outcome)
                
                # Level 3: Cross-Channel Coin Tracking
                self.reputation_engine.update_cross_channel_coin_performance(channel_name, outcome)
            
            # Save updated reputation with TD learning data
            self.reputation_engine.save_reputations()
            
            # Display TD learning summary
            self.logger.info(f"\n=== TD Learning Summary for {channel_name} ===")
            self.logger.info(f"Overall Expected ROI: {reputation.expected_roi:.3f}x")
            self.logger.info(f"Total Predictions: {reputation.total_predictions}")
            self.logger.info(f"Accuracy (within 10%): {(reputation.correct_predictions / reputation.total_predictions * 100) if reputation.total_predictions > 0 else 0:.1f}%")
            self.logger.info(f"Mean Absolute Error: {reputation.mean_absolute_error:.3f}x")
            self.logger.info(f"Overestimations: {reputation.overestimations}, Underestimations: {reputation.underestimations}")
            
            if reputation.coin_specific_performance:
                self.logger.info(f"\nCoin-Specific Performance ({len(reputation.coin_specific_performance)} coins):")
                for address, coin_perf in list(reputation.coin_specific_performance.items())[:5]:  # Show top 5
                    self.logger.info(
                        f"  {coin_perf.symbol}: Expected ROI {coin_perf.expected_roi:.3f}x, "
                        f"Avg ROI {coin_perf.average_roi:.3f}x, "
                        f"Mentions: {coin_perf.total_mentions}"
                    )
    
    def generate_report(self) -> str:
        """
        Generate verification report.
        
        Returns:
            Report text
        """
        # Use ReportGenerator for presentation logic
        return ReportGenerator.generate_verification_report(
            self.stats,
            self.reputation_engine,
            self.performance_tracker
        )
    
    async def backfill_historical_prices(self):
        """
        Backfill historical prices for all existing signal outcomes using CryptoCompare.
        """
        self.logger.info("Starting historical price backfill...")
        
        total_signals = len(self.outcome_tracker.outcomes)
        if total_signals == 0:
            self.logger.warning("No signals found to backfill")
            return
        
        self.logger.info(f"Found {total_signals} signals to backfill")
        
        for idx, (address, outcome) in enumerate(self.outcome_tracker.outcomes.items(), 1):
            self.logger.info(f"\n[{idx}/{total_signals}] Processing {outcome.symbol} ({address[:10]}...)")
            await self.update_signal_checkpoints(address, outcome.symbol)
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.2)
        
        self.logger.info(f"\nBackfill complete! Updated {total_signals} signals")
        
        # Recalculate channel reputations with updated data
        self.logger.info("\nRecalculating channel reputations...")
        channels = set(outcome.channel_name for outcome in self.outcome_tracker.outcomes.values())
        
        for channel_name in channels:
            channel_outcomes = self.outcome_tracker.get_channel_outcomes(channel_name, completed_only=True)
            if channel_outcomes:
                reputation = self.reputation_engine.update_reputation(channel_name, channel_outcomes)
                self._increment_stat('reputations_calculated')
                
                # Part 8 - Task 3: Apply multi-dimensional TD learning
                self.logger.info(f"\nApplying TD Learning for {channel_name}...")
                for outcome in channel_outcomes:
                    self.reputation_engine.apply_td_learning(channel_name, outcome)
                    self.reputation_engine.apply_coin_specific_td_learning(channel_name, outcome)
                    self.reputation_engine.update_cross_channel_coin_performance(channel_name, outcome)
                
                self.reputation_engine.save_reputations()
                
                self.logger.info(
                    f"\n{channel_name}:\n"
                    f"  Reputation Score: {reputation.reputation_score:.1f}/100 ({reputation.reputation_tier})\n"
                    f"  Total Signals: {reputation.total_signals}\n"
                    f"  Win Rate: {reputation.win_rate:.1f}% ({reputation.winning_signals} winners)\n"
                    f"  Average ROI: {reputation.average_roi:.3f}x ({(reputation.average_roi - 1) * 100:.1f}% gain)\n"
                    f"  Sharpe Ratio: {reputation.sharpe_ratio:.2f}\n"
                    f"  Speed Score: {reputation.speed_score:.1f}\n"
                    f"  Expected ROI (TD Learning): {reputation.expected_roi:.3f}x\n"
                    f"  TD Predictions: {reputation.total_predictions}, Accuracy: {(reputation.correct_predictions / reputation.total_predictions * 100) if reputation.total_predictions > 0 else 0:.1f}%\n"
                    f"  MAE: {reputation.mean_absolute_error:.3f}x, MSE: {reputation.mean_squared_error:.3f}x\n"
                    f"  Coin-Specific Tracking: {len(reputation.coin_specific_performance)} coins"
                )
    
    async def run(self, channel_id: str, limit: int = 100, offset_date=None):
        """
        Run the historical scraper.
        
        Args:
            channel_id: Channel ID or username
            limit: Maximum number of messages to fetch
            offset_date: Optional datetime to start fetching from
        """
        try:
            # Connect to Telegram
            if not await self.connect():
                self.logger.error("Failed to connect to Telegram")
                return False  # No cleanup needed - connection failed
            
            # Find channel name
            channel_name = channel_id
            for channel in self.config.channels:
                if channel.id == channel_id:
                    channel_name = channel.name
                    break
            
            # Fetch messages
            messages = await self.fetch_messages(channel_id, limit, offset_date)
            
            # Connection succeeded, cleanup guaranteed by finally block
            if not messages:
                self.logger.warning("No messages fetched")
                return False
            
            # Process messages
            await self.process_messages(messages, channel_name)
            
            # Generate report
            report = self.generate_report()
            
            # Print report (handle Windows encoding)
            try:
                print("\n" + report)
            except UnicodeEncodeError:
                # Fallback for Windows console
                print("\n" + report.encode('ascii', 'replace').decode('ascii'))
            
            # Save report to file
            try:
                report_path = Path("scripts/verification_report.md")
                report_path.parent.mkdir(exist_ok=True)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.logger.info(f"Report saved to {report_path}")
            except IOError as e:
                self.logger.error(f"Failed to save report to {report_path}: {e}")
            
            return True
            
        except asyncio.CancelledError:
            self.logger.info("Historical scraping cancelled")
            raise
        finally:
            # Always cleanup if connected
            await self.disconnect()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Historical message scraper for verification')
    parser.add_argument('--channel', type=str, help='Channel ID or username (e.g., @channel_name)')
    parser.add_argument('--limit', type=int, default=100, help='Number of messages to fetch (default: 100)')
    parser.add_argument('--from-date', type=str, help='Fetch messages from this date backwards (format: YYYY-MM-DD, e.g., 2024-03-12)')
    parser.add_argument('--backfill', action='store_true', help='Backfill historical prices for existing signals using CryptoCompare')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config.load()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Setup logging
    setup_logger('TelegramMonitor', config.log_level)
    setup_logger('MessageProcessor', config.log_level)
    setup_logger('HDRBScorer', config.log_level)
    setup_logger('CryptoDetector', config.log_level)
    setup_logger('SentimentAnalyzer', config.log_level)
    setup_logger('ErrorHandler', config.log_level)
    setup_logger('AddressExtractor', config.log_level)
    setup_logger('PriceEngine', config.log_level)
    setup_logger('PerformanceTracker', config.log_level)
    setup_logger('CSVTableWriter[performance]', config.log_level)
    
    # Determine channel
    if args.channel:
        channel_id = args.channel
    elif config.channels:
        channel_id = config.channels[0].id
        print(f"No channel specified, using first configured channel: {channel_id}")
    else:
        print("Error: No channel specified and no channels configured")
        return 1
    
    # Parse offset date if provided
    offset_date = None
    if args.from_date:
        from datetime import datetime
        try:
            offset_date = datetime.strptime(args.from_date, '%Y-%m-%d')
            print(f"Fetching messages from {offset_date} backwards")
        except ValueError:
            print(f"Invalid date format: {args.from_date}. Use YYYY-MM-DD format.")
            return 1
    
    # Create scraper
    scraper = HistoricalScraper(config)
    
    try:
        # Handle backfill mode
        if args.backfill:
            print("Running historical price backfill using CryptoCompare...")
            await scraper.backfill_historical_prices()
            print("\n✓ Backfill complete!")
            return 0
        
        # Normal scraping mode
        success = await scraper.run(channel_id, args.limit, offset_date)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

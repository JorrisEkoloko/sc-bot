"""Main orchestration for crypto intelligence system."""
import asyncio
import signal
import sys
from datetime import datetime
from config.settings import Config
from config.price_config import PriceConfig
from config.performance_config import PerformanceConfig
from config.output_config import OutputConfig
from config.historical_scraper_config import HistoricalScraperConfig
from infrastructure.telegram.telegram_monitor import TelegramMonitor
from domain.message_event import MessageEvent
from services.message_processing.message_processor import MessageProcessor
from services.message_processing.address_extractor import AddressExtractor
from services.message_processing.pair_resolver import PairResolver
from services.pricing.price_engine import PriceEngine
from services.tracking.performance_tracker import PerformanceTracker
from infrastructure.output.data_output import MultiTableDataOutput
from services.pricing.data_enrichment import DataEnrichmentService
from infrastructure.scrapers.historical_scraper import HistoricalScraper
from utils.logger import setup_logger
# Part 8: Channel Reputation + Outcome Learning
from services.tracking.outcome_tracker import OutcomeTracker
from services.reputation.reputation_engine import ReputationEngine
from services.pricing import HistoricalPriceRetriever
from services.reputation import ROICalculator
from services.reputation import HistoricalBootstrap
from services.validation import DeadTokenDetector
import os


class CryptoIntelligenceSystem:
    """Main system orchestrator."""
    
    def __init__(self):
        """Initialize the system."""
        self.logger = None
        self.config = None
        self.telegram_monitor = None
        self.message_processor = None
        # Part 3 components
        self.pair_resolver = None
        self.address_extractor = None
        self.price_engine = None
        self.data_enrichment = None
        self.performance_tracker = None
        self.data_output = None
        self.historical_scraper = None
        # Part 8 components
        self.outcome_tracker = None
        self.reputation_engine = None
        self.historical_price_retriever = None
        self.dead_token_detector = None
        self.historical_bootstrap = None
        self._state = "stopped"  # stopped, starting, running, stopping
        self._shutdown_lock = None  # Will be initialized in async context
    
    async def _ensure_locks_initialized(self):
        """Initialize async locks safely (thread-safe with double-checked locking)."""
        if self._shutdown_lock is not None:
            return
        
        # Use a temporary lock for initialization
        if not hasattr(self, '_init_lock'):
            self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            # Double-check after acquiring lock
            if self._shutdown_lock is not None:
                return
            
            # Create lock directly in async context (safe)
            self._shutdown_lock = asyncio.Lock()
    
    async def start(self):
        """Start the system."""
        # Initialize locks in async context (thread-safe)
        await self._ensure_locks_initialized()
        
        # Check current state and determine action
        async with self._shutdown_lock:
            if self._state == "running":
                # Verify components are still healthy
                if self.telegram_monitor and self.telegram_monitor.is_connected():
                    if self.logger:
                        self.logger.info("System already running and healthy")
                    return True
                # Unhealthy - mark for restart
                if self.logger:
                    self.logger.warning("System marked as running but components unhealthy, restarting...")
                self._state = "restarting"
            elif self._state == "stopping":
                raise RuntimeError("Cannot start while stopping - wait for shutdown to complete")
            elif self._state == "starting":
                raise RuntimeError("Already starting")
            elif self._state == "stopped":
                self._state = "starting"
            else:
                raise RuntimeError(f"Cannot start from state: {self._state}")
            
            current_state = self._state
        
        # Perform restart cleanup if needed (outside lock to avoid deadlock)
        if current_state == "restarting":
            try:
                await self._shutdown_internal()
                async with self._shutdown_lock:
                    self._state = "starting"
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Shutdown failed during restart: {e}")
                async with self._shutdown_lock:
                    self._state = "stopped"
                raise
        
        try:
            # Load configuration
            self.config = Config.load()
            
            # Initialize logger
            self.logger = setup_logger('CryptoIntelligence', self.config.log_level)
            
            # Initialize component loggers
            setup_logger('TelegramMonitor', self.config.log_level)
            setup_logger('MessageProcessor', self.config.log_level)
            setup_logger('HDRBScorer', self.config.log_level)
            setup_logger('CryptoDetector', self.config.log_level)
            setup_logger('SentimentAnalyzer', self.config.log_level)
            setup_logger('ErrorHandler', self.config.log_level)
            # Part 3 component loggers
            setup_logger('PairResolver', self.config.log_level)
            setup_logger('AddressExtractor', self.config.log_level)
            setup_logger('PriceEngine', self.config.log_level)
            setup_logger('PerformanceTracker', self.config.log_level)
            setup_logger('MultiTableDataOutput', self.config.log_level)
            setup_logger('HistoricalScraper', self.config.log_level)
            
            self.logger.info("Configuration loaded successfully")
            self.logger.info(f"Processing config: confidence_threshold={self.config.processing.confidence_threshold}")
            self.logger.info(f"Retry config: max_attempts={self.config.retry.max_attempts}")
            
            # Initialize message processor with configuration
            self.message_processor = MessageProcessor(
                max_ic=self.config.processing.hdrb_max_ic,
                confidence_threshold=self.config.processing.confidence_threshold
            )
            self.logger.info("Message processor initialized")
            
            # Initialize Part 3 components
            self.logger.info("Initializing Part 3 components...")
            
            # Pair resolver (for LP pair detection)
            self.pair_resolver = PairResolver()
            self.logger.info("Pair resolver initialized")
            
            # Address extractor (with pair resolver)
            self.address_extractor = AddressExtractor(pair_resolver=self.pair_resolver)
            self.logger.info("Address extractor initialized with LP pair resolution")
            
            # Price engine
            price_config = PriceConfig.load_from_env()
            self.price_engine = PriceEngine(price_config)
            self.logger.info("Price engine initialized")
            
            # Data enrichment service (separates business logic from data access)
            self.data_enrichment = DataEnrichmentService(self.logger)
            self.logger.info("Data enrichment service initialized")
            
            # Part 8: Initialize outcome tracking and reputation FIRST
            self.logger.info("Initializing Part 8 components...")
            
            self.outcome_tracker = OutcomeTracker(data_dir="data/reputation", logger=self.logger)
            self.logger.info("Outcome tracker initialized")
            
            # Performance tracker (7-day monitoring with known ATH from APIs)
            performance_config = PerformanceConfig.load_from_env()
            self.performance_tracker = PerformanceTracker(
                data_dir=performance_config.data_dir,
                tracking_days=performance_config.tracking_days,
                csv_output_dir="output",
                enable_csv=False  # Disable CSV in tracker, use MultiTableDataOutput instead
            )
            self.logger.info("Performance tracker initialized for 7-day monitoring")
            
            # Multi-table data output
            output_config = OutputConfig.load_from_env()
            self.data_output = MultiTableDataOutput(output_config, self.logger)
            self.logger.info("Multi-table data output initialized")
            
            self.reputation_engine = ReputationEngine(data_dir="data/reputation", logger=self.logger)
            self.logger.info("Reputation engine initialized")
            
            self.historical_price_retriever = HistoricalPriceRetriever(
                cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
                cache_dir="data/cache",
                symbol_mapping_path="data/symbol_mapping.json",
                logger=self.logger
            )
            self.logger.info("Historical price retriever initialized")
            
            self.dead_token_detector = DeadTokenDetector(
                etherscan_api_key=os.getenv('ETHERSCAN_API_KEY', ''),
                blacklist_path="data/dead_tokens_blacklist.json",
                logger=self.logger
            )
            self.logger.info("Dead token detector initialized")
            
            # Historical bootstrap will be initialized on first use
            self.historical_bootstrap = None
            
            # Create Telegram monitor
            self.telegram_monitor = TelegramMonitor(
                self.config.telegram,
                self.config.channels
            )
            
            # Connect to Telegram
            connected = await self.telegram_monitor.connect()
            if not connected:
                await self.shutdown()
                return False
            
            # Initialize historical scraper
            historical_config = HistoricalScraperConfig.load_from_env()
            if historical_config.enabled:
                self.historical_scraper = HistoricalScraper(
                    historical_config,
                    self.telegram_monitor,
                    self.handle_message
                )
                self.logger.info("Historical scraper initialized")
            else:
                self.logger.info("Historical scraping disabled")
            
            # Mark as running BEFORE starting monitoring (release lock first)
            async with self._shutdown_lock:
                self._state = "running"
            
            # Start monitoring OUTSIDE the lock (may run indefinitely)
            try:
                # Scrape historical data if enabled
                if historical_config.enabled:
                    try:
                        for channel in self.config.channels:
                            if channel.enabled:
                                await self.historical_scraper.scrape_if_needed(channel)
                    except asyncio.CancelledError:
                        self.logger.info("Historical scraping cancelled, proceeding to real-time monitoring")
                        # Don't raise - allow system to continue
                
                await self.telegram_monitor.start_monitoring(self.handle_message)
            except asyncio.CancelledError:
                self.logger.info("Monitoring cancelled")
                raise
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Transition to stopping state
            async with self._shutdown_lock:
                if self._state != "stopped":
                    self._state = "stopping"
            
            # Attempt shutdown with error recovery
            try:
                await self.shutdown()
            except Exception as shutdown_error:
                if self.logger:
                    self.logger.error(f"Shutdown during error recovery failed: {shutdown_error}")
                # Force state to stopped to allow retry
                async with self._shutdown_lock:
                    self._state = "stopped"
            raise
    
    def display_processed_message(self, processed, addresses_data=None):
        """
        Display processed message with enhanced console output including Part 3 data.
        
        Args:
            processed: ProcessedMessage object with all analysis
            addresses_data: List of address data dicts with price and performance info
        """
        # Format timestamp
        formatted_time = processed.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Print separator
        print("\n" + "="*80)
        print(f"[{formatted_time}] [{processed.channel_name}] (ID: {processed.message_id})")
        print("="*80)
        
        # HDRB Score
        print(f"📊 HDRB Score: {processed.hdrb_score:.1f}/100 (IC: {processed.hdrb_raw:.1f})")
        print(f"   Engagement: {processed.forwards} forwards, {processed.reactions} reactions, {processed.replies} replies")
        
        # Crypto Detection
        if processed.is_crypto_relevant and processed.crypto_mentions:
            mentions_str = ', '.join(processed.crypto_mentions)
            print(f"💰 Crypto Mentions: {mentions_str}")
        else:
            print(f"💰 Crypto Mentions: None")
        
        # Part 3: Address and Price Data
        if addresses_data:
            print(f"\n💎 Addresses:")
            for addr_data in addresses_data:
                short_addr = addr_data['address'][:10] + '...'
                print(f"   • {short_addr} ({addr_data['chain']}) - ${addr_data['price']:.6f}")
                if addr_data['ath_multiplier'] > 1.0:
                    print(f"     📊 Performance: {addr_data['ath_multiplier']:.2f}x ATH (tracked {addr_data['days_tracked']} days)")
        
        # Sentiment
        sentiment_emoji = {
            'positive': '📈',
            'negative': '📉',
            'neutral': '➡️'
        }
        emoji = sentiment_emoji.get(processed.sentiment, '➡️')
        print(f"\n{emoji} Sentiment: {processed.sentiment.capitalize()} ({processed.sentiment_score:+.2f})")
        
        # Confidence
        if processed.is_high_confidence:
            conf_indicator = "🟢 HIGH"
        else:
            conf_indicator = "🟡 LOW"
        print(f"🎯 Confidence: {conf_indicator} ({processed.confidence:.2f})")
        
        # Message text
        print(f"\n{processed.message_text}")
        
        # Processing metadata
        print(f"\n⏱️  Processed in {processed.processing_time_ms:.2f}ms")
        
        # Error if any
        if processed.error:
            print(f"⚠️  Error: {processed.error}")
        
        print("="*80 + "\n")
    
    async def handle_message(self, event: MessageEvent):
        """
        Handle received message through complete Part 1-3 pipeline.
        
        Args:
            event: Message event data
        """
        if not self.message_processor:
            self.logger.warning("Message processor not initialized, skipping message")
            return
        
        try:
            # Part 1-2: Process the message
            processed = await self.message_processor.process_message(
                channel_name=event.channel_name,
                message_text=event.message_text,
                timestamp=event.timestamp,
                message_id=event.message_id,
                message_obj=event.message_obj,
                channel_id=event.channel_id
            )
            
            # Part 3: Process through address extraction, price fetching, and performance tracking
            addresses_data = []
            
            if processed.is_crypto_relevant and processed.crypto_mentions:
                # Write message to MESSAGES table
                await self.data_output.write_message({
                    'message_id': str(event.message_id),
                    'timestamp': event.timestamp.isoformat(),
                    'channel_name': event.channel_name,
                    'message_text': event.message_text,
                    'hdrb_score': processed.hdrb_score,
                    'crypto_mentions': processed.crypto_mentions,
                    'sentiment': processed.sentiment,
                    'confidence': processed.confidence
                })
                
                # Extract addresses (with async LP pair resolution)
                addresses = await self.address_extractor.extract_addresses_async(processed.crypto_mentions)
                
                for addr in addresses:
                    if not addr.is_valid:
                        continue
                    
                    # Part 8: Check if token is blacklisted as dead
                    if self.dead_token_detector.is_blacklisted(addr.address):
                        reason = self.dead_token_detector.get_blacklist_reason(addr.address)
                        self.logger.info(f"[SKIP] Token {addr.address[:10]}... is blacklisted: {reason}")
                        continue
                    
                    # Check if token is dead and blacklist if so
                    stats = await self.dead_token_detector.check_and_blacklist_if_dead(addr.address, addr.chain)
                    if stats.is_dead:
                        self.logger.warning(f"[DEAD TOKEN] Skipping {addr.address[:10]}...: {stats.reason}")
                        continue
                    
                    # Fetch price
                    price_data = await self.price_engine.get_price(addr.address, addr.chain)
                    
                    if price_data:
                        # Enrich with market intelligence (business logic layer)
                        price_data = self.data_enrichment.enrich_price_data(price_data)
                        
                        # Write to TOKEN_PRICES table
                        await self.data_output.write_token_price(
                            address=addr.address,
                            chain=addr.chain,
                            price_data=price_data
                        )
                        
                        # Part 8: Smart tracking based on message age
                        entry_price = price_data.price_usd
                        symbol = price_data.symbol if price_data.symbol else addr.address[:10]
                        
                        from datetime import timezone
                        now_utc = datetime.now(timezone.utc)
                        msg_date = event.timestamp if event.timestamp.tzinfo else event.timestamp.replace(tzinfo=timezone.utc)
                        message_age_hours = (now_utc - msg_date).total_seconds() / 3600
                        message_age_days = message_age_hours / 24
                        
                        # Check if signal is already complete (≥30 days old)
                        signal_complete = message_age_days >= 30
                        
                        if signal_complete:
                            # Signal is complete - check if OutcomeTracker has OHLC data
                            self.logger.info(
                                f"Signal complete ({message_age_days:.1f} days old) - "
                                f"checking OutcomeTracker for {symbol}"
                            )
                            
                            # Check if outcome exists and has OHLC data
                            outcome = self.outcome_tracker.outcomes.get(addr.address)
                            if outcome:
                                # Check if ath_price is set and valid (must be numeric and > entry_price)
                                try:
                                    ath_price_val = getattr(outcome, 'ath_price', 0)
                                    entry_price_val = getattr(outcome, 'entry_price', 0)
                                    if isinstance(ath_price_val, (int, float)) and isinstance(entry_price_val, (int, float)):
                                        if ath_price_val > entry_price_val:
                                            # Outcome exists with real OHLC data (ATH > entry), skip
                                            self.logger.debug(f"Outcome already has OHLC data (ATH: ${ath_price_val:.6f})")
                                            continue
                                except (TypeError, AttributeError) as e:
                                    self.logger.warning(f"Invalid ath_price for outcome: {e}")
                            
                            # Need to populate OHLC data for this complete signal
                            self.logger.info(f"Populating OHLC data for complete signal: {symbol}")
                            
                            # Fetch historical entry price
                            historical_entry_price, price_source = await self.historical_price_retriever.fetch_closest_entry_price(
                                symbol=symbol,
                                message_timestamp=event.timestamp,
                                address=addr.address,
                                chain=addr.chain
                            )
                            
                            if historical_entry_price and historical_entry_price > 0:
                                entry_price = historical_entry_price
                            else:
                                entry_price = price_data.price_usd
                            
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
                                    market_tier=price_data.market_tier if hasattr(price_data, 'market_tier') else "",
                                    risk_level=price_data.risk_level if hasattr(price_data, 'risk_level') else "",
                                    risk_score=price_data.risk_score if hasattr(price_data, 'risk_score') else 0.0,
                                    entry_timestamp=event.timestamp
                                )
                            
                            # Fetch OHLC data for 30-day window
                            try:
                                self.logger.info(f"Fetching OHLC data for complete signal: {symbol}")
                                ohlc_result = await self.historical_price_retriever.fetch_forward_ohlc_with_ath(
                                    symbol,
                                    event.timestamp,
                                    window_days=30,
                                    address=addr.address,
                                    chain=addr.chain
                                )
                                
                                self.logger.debug(f"OHLC result type: {type(ohlc_result)}, value: {ohlc_result}")
                                
                                if ohlc_result and isinstance(ohlc_result, dict):
                                    ath_price_from_ohlc = ohlc_result.get('ath_price')
                                    self.logger.debug(f"ATH price from OHLC: {ath_price_from_ohlc} (type: {type(ath_price_from_ohlc)})")
                                    # Validate that ath_price is a valid number
                                    if ath_price_from_ohlc and isinstance(ath_price_from_ohlc, (int, float)) and ath_price_from_ohlc > 0:
                                        # Update outcome with OHLC ATH
                                        outcome.ath_price = ath_price_from_ohlc
                                        outcome.ath_timestamp = ohlc_result.get('ath_timestamp')
                                        outcome.ath_multiplier = ath_price_from_ohlc / entry_price
                                        outcome.days_to_ath = ohlc_result.get('days_to_ath', 0)
                                        outcome.is_complete = True
                                        outcome.status = "completed"
                                    
                                    # Classify outcome
                                    winner_threshold = 2.0  # Default for micro/small cap
                                    if outcome.market_tier == "large":
                                        winner_threshold = 1.2
                                    elif outcome.market_tier == "mid":
                                        winner_threshold = 1.5
                                    
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
                                    self.logger.warning(f"No OHLC data available for complete signal: {symbol}")
                            except Exception as e:
                                import traceback
                                self.logger.error(f"Error fetching OHLC for complete signal: {e}")
                                self.logger.error(f"Traceback: {traceback.format_exc()}")
                            
                            # Don't start PerformanceTracker for completed signals
                            continue
                        
                        # Signal is ongoing (<30 days) - fetch historical entry price if needed
                        if message_age_hours > 1.0 and symbol:
                            self.logger.info(
                                f"Historical message ({message_age_hours:.1f}h old) - "
                                f"fetching historical entry price for {symbol}"
                            )
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
                        
                        # Fetch known ATH from price_data (CoinGecko provides this)
                        known_ath = price_data.ath if hasattr(price_data, 'ath') else None
                        
                        # Start PerformanceTracker for 7-day monitoring (with known ATH)
                        if addr.address not in self.performance_tracker.tracking_data:
                            await self.performance_tracker.start_tracking(
                                address=addr.address,
                                chain=addr.chain,
                                initial_price=price_data.price_usd,  # Use current price for monitoring
                                message_id=str(event.message_id),
                                known_ath=known_ath
                            )
                        else:
                            await self.performance_tracker.update_price(
                                address=addr.address,
                                current_price=price_data.price_usd
                            )
                        
                        # After 7 days: Replace known_ath with OHLC ATH (one-time operation)
                        if message_age_days >= 7:
                            tracking_entry = self.performance_tracker.tracking_data.get(addr.address)
                            # Only fetch if we haven't already (check for ohlc_fetched flag)
                            if tracking_entry and not tracking_entry.get('ohlc_fetched', False):
                                self.logger.info(f"Signal 7+ days old - fetching OHLC ATH for {symbol}")
                                try:
                                    # Use HistoricalPriceService for better API coverage
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
                                        tracking_entry['ohlc_fetched'] = True  # Mark as fetched
                                        await self.performance_tracker.save_to_disk_async()
                                        self.logger.info(
                                            f"[OHLC] Updated known_ath from historical data: ${ohlc_ath:.6f} "
                                            f"(was: ${known_ath:.6f if known_ath else 0:.6f})"
                                        )
                                    else:
                                        self.logger.warning(f"No historical ATH data available for {symbol}")
                                except Exception as e:
                                    self.logger.warning(f"Failed to fetch historical ATH: {e}")         
                        
                        # Part 8: Initialize historical bootstrap on first use
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
                            self.historical_bootstrap.load_existing_data()
                        
                        # Part 8: Check for duplicates with two-file tracking
                        is_duplicate, signal_number, previous_signals = self.historical_bootstrap.check_for_duplicate(addr.address)
                        
                        if is_duplicate:
                            self.logger.info(f"Duplicate: {addr.address[:10]}... already tracked, skipping")
                            continue
                        
                        if signal_number > 1:
                            self.logger.info(
                                f"Fresh start: {addr.address[:10]}... Signal #{signal_number} "
                                f"with entry price ${entry_price:.6f}"
                            )
                        
                        # Part 8: Track signal outcome
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
                            market_tier=price_data.market_tier if hasattr(price_data, 'market_tier') else "",
                            risk_level=price_data.risk_level if hasattr(price_data, 'risk_level') else "",
                            risk_score=price_data.risk_score if hasattr(price_data, 'risk_score') else 0.0,
                            entry_timestamp=event.timestamp
                        )
                        
                        outcome.signal_number = signal_number
                        outcome.previous_signals = previous_signals if previous_signals else []
                        
                        # Determine signal status based on elapsed time (30-day completion)
                        signal_status = self.historical_bootstrap.determine_signal_status(event.timestamp)
                        outcome.status = signal_status
                        outcome.is_complete = (signal_status == "completed")
                        
                        self.logger.info(
                            f"OutcomeTracker: Tracking signal {addr.address[:10]}... "
                            f"(Signal #{signal_number}) at entry price ${entry_price:.6f} "
                            f"[Status: {signal_status}]"
                        )
                        
                        # Get performance data
                        perf_data = self.performance_tracker.get_performance(addr.address)
                        
                        if perf_data:
                            # Write to PERFORMANCE table
                            await self.data_output.write_performance(
                                address=addr.address,
                                chain=addr.chain,
                                performance_data=perf_data
                            )
                            
                            # Store for display
                            addresses_data.append({
                                'address': addr.address,
                                'chain': addr.chain,
                                'price': price_data.price_usd,
                                'ath_multiplier': perf_data['ath_multiplier'] if isinstance(perf_data, dict) else getattr(perf_data, 'ath_multiplier', 1.0),
                                'days_tracked': perf_data['days_tracked'] if isinstance(perf_data, dict) else getattr(perf_data, 'days_tracked', 0)
                            })
                        
                        # Optionally fetch and write historical data
                        symbol = price_data.symbol if price_data and price_data.symbol else None
                        historical_data = await self.price_engine.get_historical_data(
                            addr.address, addr.chain, symbol
                        )
                        if historical_data:
                            await self.data_output.write_historical(
                                address=addr.address,
                                chain=addr.chain,
                                historical_data=historical_data
                            )
            
            # Display enhanced console output with Part 3 data
            self.display_processed_message(processed, addresses_data)
            
            # Log processing results
            self.logger.info(
                f"Message processed: ID={processed.message_id}, "
                f"HDRB={processed.hdrb_score:.2f}, "
                f"crypto_relevant={processed.is_crypto_relevant}, "
                f"sentiment={processed.sentiment}, "
                f"confidence={processed.confidence:.2f}, "
                f"mentions={len(processed.crypto_mentions)}, "
                f"addresses={len(addresses_data)}, "
                f"time={processed.processing_time_ms:.2f}ms"
            )
            
            # Log crypto mentions if found
            if processed.crypto_mentions:
                self.logger.info(f"Crypto mentions detected: {', '.join(processed.crypto_mentions)}")
            
            # Log any processing errors
            if processed.error:
                self.logger.error(f"Processing error: {processed.error}")
            
        except Exception as e:
            self.logger.error(f"Error handling message {event.message_id}: {e}", exc_info=True)
    
    async def shutdown(self):
        """Shutdown the system gracefully (idempotent)."""
        # Ensure locks are initialized
        await self._ensure_locks_initialized()
        
        async with self._shutdown_lock:
            # Check if already stopped
            if self._state == "stopped":
                return
            
            # Mark as stopping
            self._state = "stopping"
        
        # Perform shutdown outside lock
        await self._shutdown_internal()
        
        # Mark as stopped
        async with self._shutdown_lock:
            self._state = "stopped"
    
    async def _shutdown_internal(self):
        """Internal shutdown logic (called with lock released)."""
        if self.logger:
            self.logger.info("Shutting down system...")
        
        # Disconnect Telegram monitor
        if self.telegram_monitor:
            try:
                await self.telegram_monitor.disconnect()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error disconnecting Telegram: {e}")
        
        # Close Part 3 components
        if self.pair_resolver:
            try:
                await self.pair_resolver.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing pair resolver: {e}")
        
        if self.price_engine:
            try:
                await self.price_engine.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing price engine: {e}")
        
        if self.performance_tracker:
            try:
                # Save tracking data one final time
                self.performance_tracker.save_to_disk()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error saving performance tracker: {e}")
        
        # Close Part 8 components
        if self.historical_price_retriever:
            try:
                await self.historical_price_retriever.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing historical price retriever: {e}")
        
        if self.dead_token_detector:
            try:
                await self.dead_token_detector.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing dead token detector: {e}")
        
        if self.outcome_tracker:
            try:
                self.outcome_tracker.save_outcomes()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error saving outcome tracker: {e}")
        
        if self.reputation_engine:
            try:
                self.reputation_engine.save_reputations()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error saving reputation engine: {e}")
        
        if self.historical_bootstrap:
            try:
                self.historical_bootstrap.save_all()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error saving historical bootstrap: {e}")
        
        if self.logger:
            self.logger.info("Shutdown complete")


async def main():
    """Main entry point."""
    # Create system instance
    system = CryptoIntelligenceSystem()
    
    # Start system
    try:
        await system.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n⚠️  Interrupted by user")
        await system.shutdown()  # Idempotent, safe to call
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await system.shutdown()  # Idempotent, safe to call
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()

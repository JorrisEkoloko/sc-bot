"""Main orchestration for crypto intelligence system."""
import asyncio
import os
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
from infrastructure.output.data_output_coordinator import DataOutputCoordinator
from services.pricing.data_enrichment import DataEnrichmentService
from infrastructure.scrapers.historical_scraper import HistoricalScraper
from services.tracking.outcome_tracker import OutcomeTracker
from services.reputation.reputation_engine import ReputationEngine
from services.pricing import HistoricalPriceRetriever, HistoricalPriceService
from services.reputation import HistoricalBootstrap
from services.validation import DeadTokenDetector
from infrastructure.event_bus import EventBus
# New orchestration services (refactored)
from services.orchestration import (
    SignalCoordinator,
    AddressProcessingService,
    PriceFetchingService,
    SignalTrackingService,
    MessageHandler,
    ReputationScheduler,
    ShutdownCoordinator
)
from utils.logger import setup_logger
# Multi-channel enhancements
from infrastructure.message_queue import PriorityMessageQueue
from infrastructure.scrapers.parallel_historical_scraper import ParallelHistoricalScraper


# Module-level lock for thread-safe initialization across instances
_global_init_lock = None


class CryptoIntelligenceSystem:
    """Main system orchestrator."""
    
    def __init__(self):
        """Initialize the system."""
        self.logger = None
        self.config = None
        self.telegram_monitor = None
        self.message_processor = None
        # Core components
        self.pair_resolver = None
        self.address_extractor = None
        self.price_engine = None
        self.data_enrichment = None
        self.performance_tracker = None
        self.data_output = None
        self.historical_scraper = None
        self.outcome_tracker = None
        self.reputation_engine = None
        self.historical_price_retriever = None
        self.dead_token_detector = None
        self.historical_bootstrap = None
        self.event_bus = None
        # Orchestration services (refactored)
        self.address_processing_service = None
        self.price_fetching_service = None
        self.signal_tracking_service = None
        self.signal_coordinator = None
        self.message_handler = None
        # Multi-channel enhancements
        self.priority_queue = None
        self.parallel_scraper = None
        # Refactored coordinators
        self.reputation_scheduler = None
        self.shutdown_coordinator = None
        self._state = "stopped"
        self._shutdown_lock = None
    
    async def _ensure_locks_initialized(self):
        """Initialize async locks safely (thread-safe with module-level lock)."""
        if self._shutdown_lock is not None:
            return
        
        # Use module-level lock for initialization (prevents race conditions)
        global _global_init_lock
        if _global_init_lock is None:
            _global_init_lock = asyncio.Lock()
        
        async with _global_init_lock:
            # Double-check after acquiring lock
            if self._shutdown_lock is not None:
                return
            
            # Create lock directly in async context (safe)
            self._shutdown_lock = asyncio.Lock()
    
    async def _transition_state(self, from_states: list, to_state: str) -> bool:
        """
        Atomically transition state with validation.
        
        Args:
            from_states: List of valid source states
            to_state: Target state
            
        Returns:
            True if transition succeeded, False otherwise
        """
        async with self._shutdown_lock:
            if self._state not in from_states:
                return False
            self._state = to_state
            return True
    
    async def _get_state(self) -> str:
        """Get current state atomically."""
        async with self._shutdown_lock:
            return self._state
    
    async def start(self):
        """Start the system."""
        # Initialize locks in async context (thread-safe)
        await self._ensure_locks_initialized()
        
        # Perform state check and health check atomically
        needs_restart = False
        async with self._shutdown_lock:
            if self._state == "running":
                # Health check inside lock to prevent race conditions
                if self.telegram_monitor and self.telegram_monitor.is_connected():
                    if self.logger:
                        self.logger.info("System already running and healthy")
                    return True
                # Unhealthy - transition to restarting
                if self.logger:
                    self.logger.warning("System marked as running but components unhealthy, restarting...")
                self._state = "restarting"
                needs_restart = True
            elif self._state == "stopping":
                raise RuntimeError("Cannot start while stopping - wait for shutdown to complete")
            elif self._state == "starting":
                raise RuntimeError("Already starting")
            elif self._state == "stopped":
                self._state = "starting"
                needs_restart = False
            else:
                raise RuntimeError(f"Cannot start from state: {self._state}")
        
        # Perform restart cleanup if needed (outside lock to avoid deadlock)
        if needs_restart:
            try:
                await self._shutdown_internal()
                if not await self._transition_state(["restarting"], "starting"):
                    raise RuntimeError("Failed to transition to starting state after restart")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Shutdown failed during restart: {e}")
                await self._transition_state(["restarting"], "stopped")
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
            setup_logger('PatternMatcher', self.config.log_level)
            setup_logger('NLPAnalyzer', self.config.log_level)
            setup_logger('ErrorHandler', self.config.log_level)
            # Part 3 component loggers
            setup_logger('PairResolver', self.config.log_level)
            setup_logger('AddressExtractor', self.config.log_level)
            setup_logger('PriceEngine', self.config.log_level)
            setup_logger('PerformanceTracker', self.config.log_level)
            setup_logger('DataOutputCoordinator', self.config.log_level)
            setup_logger('HistoricalScraper', self.config.log_level)
            
            self.logger.info("Configuration loaded successfully")
            self.logger.info(f"Processing config: confidence_threshold={self.config.processing.confidence_threshold}")
            self.logger.info(f"Retry config: max_attempts={self.config.retry.max_attempts}")
            
            # Task 6: Initialize EventBus FIRST (foundation for all components)
            self.event_bus = EventBus(logger=self.logger)
            self.logger.info("EventBus initialized for event-driven architecture")
            
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
            
            # Part 8: Initialize outcome tracking and reputation with EventBus
            self.logger.info("Initializing Part 8 components...")
            
            self.outcome_tracker = OutcomeTracker(
                data_dir="data/reputation",
                logger=self.logger,
                event_bus=self.event_bus  # Task 6
            )
            self.logger.info("Outcome tracker initialized with event publishing")
            
            # Performance tracker (7-day monitoring with known ATH from APIs)
            performance_config = PerformanceConfig.load_from_env()
            self.performance_tracker = PerformanceTracker(
                data_dir=performance_config.data_dir,
                tracking_days=performance_config.tracking_days,
                csv_output_dir="output",
                enable_csv=False  # Disable CSV in tracker, use DataOutputCoordinator instead
            )
            self.logger.info("Performance tracker initialized for 7-day monitoring")
            
            self.reputation_engine = ReputationEngine(
                data_dir="data/reputation",
                logger=self.logger,
                event_bus=self.event_bus  # Task 6
            )
            self.logger.info("Reputation engine initialized with event subscription")
            
            # Multi-table data output (needs reputation_engine for table updates)
            output_config = OutputConfig.load_from_env()
            self.data_output = DataOutputCoordinator(
                output_config,
                self.logger,
                event_bus=self.event_bus,  # Task 6
                reputation_engine=self.reputation_engine  # Task 6
            )
            self.logger.info("Data output coordinator initialized with specialized writers")
            
            # Initialize message processor with reputation engine and event bus
            self.message_processor = MessageProcessor(
                max_ic=self.config.processing.hdrb_max_ic,
                confidence_threshold=self.config.processing.confidence_threshold,
                reputation_engine=self.reputation_engine,  # Task 6
                event_bus=self.event_bus  # Task 6
            )
            self.logger.info("Message processor initialized with reputation integration")
            
            # Log NLP sentiment analysis status
            nlp_enabled = os.getenv('SENTIMENT_NLP_ENABLED', 'true').lower() == 'true'
            if nlp_enabled:
                nlp_model = os.getenv('SENTIMENT_NLP_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
                nlp_device = os.getenv('SENTIMENT_NLP_DEVICE', 'cpu')
                self.logger.info(f"✨ NLP-enhanced sentiment analysis ENABLED (model: {nlp_model}, device: {nlp_device})")
            else:
                self.logger.info("Pattern-only sentiment analysis enabled (NLP disabled)")
            
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
            
            # Initialize historical bootstrap
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
            self.logger.info("Historical bootstrap initialized")
            
            # Initialize symbol resolver for symbol-to-address resolution
            from services.pricing.symbol_resolver import SymbolResolver
            self.symbol_resolver = SymbolResolver(
                coingecko_client=self.price_engine.clients['coingecko'],
                historical_price_service=historical_price_service,
                logger=self.logger
            )
            self.logger.info("Symbol resolver initialized with date validation")
            
            # Initialize refactored orchestration services
            self.logger.info("Initializing refactored orchestration services...")
            
            # Address processing service
            self.address_processing_service = AddressProcessingService(
                address_extractor=self.address_extractor,
                symbol_resolver=self.symbol_resolver,
                logger=self.logger
            )
            self.logger.info("Address processing service initialized")
            
            # Price fetching service
            self.price_fetching_service = PriceFetchingService(
                price_engine=self.price_engine,
                data_enrichment=self.data_enrichment,
                historical_price_retriever=self.historical_price_retriever,
                logger=self.logger
            )
            self.logger.info("Price fetching service initialized")
            
            # Signal tracking service
            self.signal_tracking_service = SignalTrackingService(
                performance_tracker=self.performance_tracker,
                outcome_tracker=self.outcome_tracker,
                dead_token_detector=self.dead_token_detector,
                historical_bootstrap=self.historical_bootstrap,
                logger=self.logger
            )
            self.logger.info("Signal tracking service initialized")
            
            # Signal coordinator (replaces old SignalProcessingService)
            self.signal_coordinator = SignalCoordinator(
                address_processing_service=self.address_processing_service,
                price_fetching_service=self.price_fetching_service,
                signal_tracking_service=self.signal_tracking_service,
                data_output=self.data_output,
                logger=self.logger
            )
            self.logger.info("Signal coordinator initialized (refactored architecture)")
            
            # Message handler (now uses SignalCoordinator)
            self.message_handler = MessageHandler(
                message_processor=self.message_processor,
                signal_processing_service=self.signal_coordinator,  # Uses new coordinator
                data_output=self.data_output,
                logger=self.logger
            )
            self.logger.info("Message handler initialized with refactored services")
            
            # Initialize priority message queue (multi-channel enhancement)
            self.priority_queue = PriorityMessageQueue(
                reputation_engine=self.reputation_engine,
                max_queue_size=5000,  # Increased for ALL messages scraping
                messages_per_second=2.0,  # Global rate limit: 2 msg/s = 120 msg/min
                logger=self.logger
            )
            self.logger.info("Priority message queue initialized for multi-channel processing (queue_size=5000)")
            
            # Initialize reputation scheduler
            self.reputation_scheduler = ReputationScheduler(
                reputation_engine=self.reputation_engine,
                outcome_tracker=self.outcome_tracker,
                data_output=self.data_output,
                update_interval=1800,  # 30 minutes
                logger=self.logger
            )
            self.logger.info("Reputation scheduler initialized")
            
            # Initialize shutdown coordinator
            self.shutdown_coordinator = ShutdownCoordinator(logger=self.logger)
            self.logger.info("Shutdown coordinator initialized")
            
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
            
            # Initialize historical scraper (keep original for compatibility)
            historical_config = HistoricalScraperConfig.load_from_env()
            if historical_config.enabled:
                self.historical_scraper = HistoricalScraper(
                    historical_config,
                    self.telegram_monitor,
                    self.handle_message
                )
                self.logger.info("Historical scraper initialized")
                
                # Initialize parallel scraper (multi-channel enhancement)
                self.parallel_scraper = ParallelHistoricalScraper(
                    historical_config,
                    self.telegram_monitor,
                    self.handle_message,
                    self.reputation_engine,
                    max_concurrent=10,  # Scrape 10 channels in parallel (increased for ALL messages)
                    logger=self.logger
                )
                self.logger.info("Parallel historical scraper initialized (10 concurrent, unlimited messages)")
            else:
                self.logger.info("Historical scraping disabled")
            
            # Start all components BEFORE marking as running (prevents race conditions)
            self.logger.info("Starting priority queue consumer...")
            await self.priority_queue.start_consumer(self.message_handler.handle_message)
            self.logger.info("Priority queue consumer started")
            
            # Mark as running AFTER components are started (atomic transition)
            if not await self._transition_state(["starting"], "running"):
                # Rollback: stop components we just started
                self.logger.error("Failed to transition to running state, rolling back...")
                try:
                    await self.priority_queue.stop_consumer(timeout=5.0)
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
                raise RuntimeError("Failed to transition to running state")
            
            # Start monitoring OUTSIDE the lock (may run indefinitely)
            try:
                # Scrape historical data if enabled
                if historical_config.enabled:
                    try:
                        # Use parallel scraper for faster startup (multi-channel enhancement)
                        if self.parallel_scraper:
                            self.logger.info("Using parallel historical scraper (10 concurrent channels, ALL messages)")
                            self.logger.info("⚠️  First run may take 2-8 hours depending on channel history")
                            scrape_results = await self.parallel_scraper.scrape_all_channels(self.config.channels)
                            self.logger.info(f"Parallel scraping results: {scrape_results}")
                        else:
                            # Fallback to sequential scraping
                            self.logger.info("Using sequential historical scraper")
                            for channel in self.config.channels:
                                if channel.enabled:
                                    await self.historical_scraper.scrape_if_needed(channel)
                    except asyncio.CancelledError:
                        self.logger.info("Historical scraping cancelled")
                        # Check if this is a shutdown cancellation
                        current_state = await self._get_state()
                        if current_state != "running":
                            self.logger.info("System is shutting down, not starting monitoring")
                            raise  # Re-raise to complete shutdown
                        # Otherwise, proceed to monitoring
                        self.logger.info("Proceeding to real-time monitoring")
                
                # Update all reputation tables on startup (for any completed signals)
                self.logger.info("Updating reputation tables on startup...")
                await self.reputation_scheduler.update_all_reputation_tables()
                
                # Start reputation scheduler
                await self.reputation_scheduler.start()
                
                # Start real-time monitoring with queue-based handler
                try:
                    await self.telegram_monitor.start_monitoring(self.handle_message_queued)
                finally:
                    # Stop reputation scheduler when monitoring stops
                    await self.reputation_scheduler.stop()
            except asyncio.CancelledError:
                self.logger.info("Monitoring cancelled")
                raise
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Transition to stopping state atomically
            current_state = await self._get_state()
            if current_state != "stopped":
                await self._transition_state([current_state], "stopping")
            
            # Attempt shutdown with error recovery
            try:
                await self.shutdown()
            except Exception as shutdown_error:
                if self.logger:
                    self.logger.error(f"Shutdown during error recovery failed: {shutdown_error}")
                # Force state to stopped to allow retry
                await self._transition_state(["stopping"], "stopped")
            raise
    
    async def handle_message(self, event: MessageEvent):
        """
        Handle received message - delegates to MessageHandler service.
        
        Used for historical scraping (direct processing).
        
        Args:
            event: Message event data
        """
        await self.message_handler.handle_message(event)
    
    async def handle_message_queued(self, event: MessageEvent):
        """
        Handle received message via priority queue (multi-channel enhancement).
        
        Used for real-time monitoring (queued processing with priority).
        
        Args:
            event: Message event data
        """
        # Enqueue message with priority based on channel reputation
        enqueued = await self.priority_queue.enqueue(event)
        
        if not enqueued:
            # Queue full - message dropped (backpressure)
            self.logger.warning(
                f"Message dropped due to queue backpressure: "
                f"{event.channel_name} (ID: {event.message_id})"
            )
            
            # Log queue stats periodically
            stats = self.priority_queue.get_stats()
            if stats['total_dropped'] % 10 == 0:  # Every 10 drops
                self.logger.warning(
                    f"Queue stats: "
                    f"enqueued={stats['total_enqueued']}, "
                    f"processed={stats['total_processed']}, "
                    f"dropped={stats['total_dropped']}, "
                    f"queue_size={stats['queue_size']}"
                )
    
    async def update_channel_reputations(self):
        """
        Update channel reputations based on completed signals.
        
        Delegates to ReputationScheduler.
        """
        if self.reputation_scheduler:
            await self.reputation_scheduler.update_channel_reputations()
        else:
            self.logger.warning("Reputation scheduler not initialized")
    
    async def shutdown(self):
        """Shutdown the system gracefully (idempotent)."""
        # Ensure locks are initialized
        await self._ensure_locks_initialized()
        
        # Atomic state check and transition
        async with self._shutdown_lock:
            if self._state == "stopped":
                if self.logger:
                    self.logger.debug("System already stopped")
                return
            
            if self._state not in ["running", "starting", "restarting", "stopping"]:
                if self.logger:
                    self.logger.warning(f"Cannot shutdown from state: {self._state}")
                return
            
            # Transition to stopping state
            self._state = "stopping"
        
        # Perform shutdown outside lock to avoid deadlock
        try:
            await self._shutdown_internal()
        finally:
            # Always mark as stopped, even if shutdown fails
            async with self._shutdown_lock:
                self._state = "stopped"
    
    async def _shutdown_internal(self):
        """Internal shutdown logic with guaranteed cleanup (called with lock released)."""
        # Use shutdown coordinator for clean, organized shutdown
        if self.shutdown_coordinator:
            components = {
                'priority_queue': self.priority_queue,
                'telegram_monitor': self.telegram_monitor,
                'pair_resolver': self.pair_resolver,
                'price_engine': self.price_engine,
                'historical_price_retriever': self.historical_price_retriever,
                'dead_token_detector': self.dead_token_detector,
                'performance_tracker': self.performance_tracker,
                'outcome_tracker': self.outcome_tracker,
                'reputation_engine': self.reputation_engine,
                'historical_bootstrap': self.historical_bootstrap,
                'reputation_scheduler': self.reputation_scheduler
            }
            await self.shutdown_coordinator.shutdown_all(components)
        else:
            # Fallback if coordinator not initialized
            if self.logger:
                self.logger.warning("Shutdown coordinator not available, using basic cleanup")
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
        await system.shutdown()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await system.shutdown()
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cancel all remaining tasks to prevent "Task was destroyed but it is pending" warnings
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            print(f"Cancelling {len(tasks)} remaining tasks...")
            for task in tasks:
                task.cancel()
            # Wait for all tasks to be cancelled
            await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()

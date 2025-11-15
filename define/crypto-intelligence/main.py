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
from infrastructure.output.data_output import MultiTableDataOutput
from services.pricing.data_enrichment import DataEnrichmentService
from infrastructure.scrapers.historical_scraper import HistoricalScraper
from services.tracking.outcome_tracker import OutcomeTracker
from services.reputation.reputation_engine import ReputationEngine
from services.pricing import HistoricalPriceRetriever, HistoricalPriceService
from services.reputation import HistoricalBootstrap
from services.validation import DeadTokenDetector
from infrastructure.event_bus import EventBus
# New orchestration services
from services.orchestration import SignalProcessingService, MessageHandler
from utils.logger import setup_logger


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
        # Orchestration services
        self.signal_processing_service = None
        self.message_handler = None
        self._state = "stopped"
        self._shutdown_lock = None
    
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
        
        # Check current state and determine action (minimize critical section)
        needs_health_check = False
        async with self._shutdown_lock:
            if self._state == "running":
                needs_health_check = True
            elif self._state == "stopping":
                raise RuntimeError("Cannot start while stopping - wait for shutdown to complete")
            elif self._state == "starting":
                raise RuntimeError("Already starting")
            elif self._state == "stopped":
                self._state = "starting"
            else:
                raise RuntimeError(f"Cannot start from state: {self._state}")
            
            current_state = self._state
        
        # Perform health check outside lock to avoid deadlock
        if needs_health_check:
            if self.telegram_monitor and self.telegram_monitor.is_connected():
                if self.logger:
                    self.logger.info("System already running and healthy")
                return True
            # Unhealthy - mark for restart
            if self.logger:
                self.logger.warning("System marked as running but components unhealthy, restarting...")
            async with self._shutdown_lock:
                self._state = "restarting"
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
                enable_csv=False  # Disable CSV in tracker, use MultiTableDataOutput instead
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
            self.data_output = MultiTableDataOutput(
                output_config,
                self.logger,
                event_bus=self.event_bus,  # Task 6
                reputation_engine=self.reputation_engine  # Task 6
            )
            self.logger.info("Multi-table data output initialized with event subscription")
            
            # Initialize message processor with reputation engine
            self.message_processor = MessageProcessor(
                max_ic=self.config.processing.hdrb_max_ic,
                confidence_threshold=self.config.processing.confidence_threshold,
                reputation_engine=self.reputation_engine,  # Task 6
                event_bus=self.event_bus  # Task 6
            )
            self.logger.info("Message processor initialized with reputation integration")
            
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
            
            # Initialize orchestration services
            self.signal_processing_service = SignalProcessingService(
                address_extractor=self.address_extractor,
                price_engine=self.price_engine,
                data_enrichment=self.data_enrichment,
                performance_tracker=self.performance_tracker,
                outcome_tracker=self.outcome_tracker,
                historical_price_retriever=self.historical_price_retriever,
                dead_token_detector=self.dead_token_detector,
                historical_bootstrap=self.historical_bootstrap,
                data_output=self.data_output,
                logger=self.logger
            )
            self.logger.info("Signal processing service initialized")
            
            self.message_handler = MessageHandler(
                message_processor=self.message_processor,
                signal_processing_service=self.signal_processing_service,
                data_output=self.data_output,
                logger=self.logger
            )
            self.logger.info("Message handler initialized")
            
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
    
    async def handle_message(self, event: MessageEvent):
        """
        Handle received message - delegates to MessageHandler service.
        
        Args:
            event: Message event data
        """
        await self.message_handler.handle_message(event)
    
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
        
        # Close components
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
        await system.shutdown()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await system.shutdown()
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()

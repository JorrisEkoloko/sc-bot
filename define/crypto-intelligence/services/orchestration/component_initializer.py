"""Component initializer - handles dependency injection and component setup."""
import os
from dataclasses import dataclass
from typing import Optional

from config.settings import Config
from config.price_config import PriceConfig
from config.performance_config import PerformanceConfig
from config.output_config import OutputConfig
from config.historical_scraper_config import HistoricalScraperConfig
from utils.logger import setup_logger, get_logger


@dataclass
class SystemComponents:
    """Container for all system components."""
    # Core components
    config: Config
    telegram_monitor: any
    message_processor: any
    pair_resolver: any
    address_extractor: any
    price_engine: any
    data_enrichment: any
    performance_tracker: any
    data_output: any
    outcome_tracker: any
    reputation_engine: any
    historical_price_retriever: any
    dead_token_detector: any
    historical_bootstrap: any
    event_bus: any
    symbol_resolver: any
    
    # Orchestration services
    address_processing_service: any
    price_fetching_service: any
    signal_tracking_service: any
    signal_coordinator: any
    message_handler: any
    
    # Multi-channel enhancements
    priority_queue: any
    parallel_scraper: Optional[any] = None
    historical_scraper: Optional[any] = None


class ComponentInitializer:
    """
    Initializes all system components with proper dependency injection.
    
    Separates initialization logic from orchestration.
    """
    
    def __init__(self, logger=None):
        """Initialize component initializer."""
        self.logger = logger or get_logger('ComponentInitializer')
    
    async def initialize_all(self) -> SystemComponents:
        """
        Initialize all system components.
        
        Returns:
            SystemComponents container with all initialized components
        """
        self.logger.info("Initializing system components...")
        
        # Load configuration
        config = Config.load()
        
        # Initialize loggers
        self._initialize_loggers(config.log_level)
        
        # Initialize event bus (foundation)
        from infrastructure.event_bus import EventBus
        event_bus = EventBus(logger=self.logger)
        self.logger.info("EventBus initialized")
        
        # Initialize core components
        pair_resolver = self._initialize_pair_resolver()
        address_extractor = self._initialize_address_extractor(pair_resolver)
        price_engine = self._initialize_price_engine()
        data_enrichment = self._initialize_data_enrichment()
        
        # Initialize tracking components
        outcome_tracker = self._initialize_outcome_tracker(event_bus)
        performance_tracker = self._initialize_performance_tracker()
        reputation_engine = self._initialize_reputation_engine(event_bus)
        
        # Initialize data output
        data_output = self._initialize_data_output(event_bus, reputation_engine)
        
        # Initialize message processor
        message_processor = self._initialize_message_processor(
            config, reputation_engine, event_bus
        )
        
        # Initialize historical services
        historical_price_retriever = self._initialize_historical_price_retriever()
        dead_token_detector = self._initialize_dead_token_detector()
        historical_bootstrap = self._initialize_historical_bootstrap()
        symbol_resolver = self._initialize_symbol_resolver(
            price_engine, historical_bootstrap
        )
        
        # Initialize orchestration services (new refactored services)
        address_processing_service = self._initialize_address_processing_service(
            address_extractor, symbol_resolver
        )
        price_fetching_service = self._initialize_price_fetching_service(
            price_engine, data_enrichment, historical_price_retriever
        )
        signal_tracking_service = self._initialize_signal_tracking_service(
            performance_tracker, outcome_tracker, dead_token_detector, historical_bootstrap
        )
        signal_coordinator = self._initialize_signal_coordinator(
            address_processing_service, price_fetching_service,
            signal_tracking_service, data_output
        )
        message_handler = self._initialize_message_handler(
            message_processor, signal_coordinator, data_output
        )
        
        # Initialize multi-channel components
        priority_queue = self._initialize_priority_queue(reputation_engine)
        
        # Initialize Telegram monitor
        telegram_monitor = self._initialize_telegram_monitor(config)
        
        # Initialize historical scrapers
        historical_scraper, parallel_scraper = self._initialize_historical_scrapers(
            telegram_monitor, message_handler, reputation_engine
        )
        
        self.logger.info("✅ All components initialized successfully")
        
        return SystemComponents(
            config=config,
            telegram_monitor=telegram_monitor,
            message_processor=message_processor,
            pair_resolver=pair_resolver,
            address_extractor=address_extractor,
            price_engine=price_engine,
            data_enrichment=data_enrichment,
            performance_tracker=performance_tracker,
            data_output=data_output,
            outcome_tracker=outcome_tracker,
            reputation_engine=reputation_engine,
            historical_price_retriever=historical_price_retriever,
            dead_token_detector=dead_token_detector,
            historical_bootstrap=historical_bootstrap,
            event_bus=event_bus,
            symbol_resolver=symbol_resolver,
            address_processing_service=address_processing_service,
            price_fetching_service=price_fetching_service,
            signal_tracking_service=signal_tracking_service,
            signal_coordinator=signal_coordinator,
            message_handler=message_handler,
            priority_queue=priority_queue,
            parallel_scraper=parallel_scraper,
            historical_scraper=historical_scraper
        )
    
    def _initialize_loggers(self, log_level: str):
        """Initialize all component loggers."""
        loggers = [
            'TelegramMonitor', 'MessageProcessor', 'HDRBScorer', 'CryptoDetector',
            'SentimentAnalyzer', 'PatternMatcher', 'NLPAnalyzer', 'ErrorHandler',
            'PairResolver', 'AddressExtractor', 'PriceEngine', 'PerformanceTracker',
            'MultiTableDataOutput', 'HistoricalScraper'
        ]
        
        for logger_name in loggers:
            setup_logger(logger_name, log_level)
    
    def _initialize_pair_resolver(self):
        """Initialize pair resolver."""
        from services.message_processing.pair_resolver import PairResolver
        self.logger.info("Pair resolver initialized")
        return PairResolver()
    
    def _initialize_address_extractor(self, pair_resolver):
        """Initialize address extractor."""
        from services.message_processing.address_extractor import AddressExtractor
        self.logger.info("Address extractor initialized")
        return AddressExtractor(pair_resolver=pair_resolver)
    
    def _initialize_price_engine(self):
        """Initialize price engine."""
        from services.pricing.price_engine import PriceEngine
        price_config = PriceConfig.load_from_env()
        self.logger.info("Price engine initialized")
        return PriceEngine(price_config)
    
    def _initialize_data_enrichment(self):
        """Initialize data enrichment service."""
        from services.pricing.data_enrichment import DataEnrichmentService
        self.logger.info("Data enrichment service initialized")
        return DataEnrichmentService(self.logger)
    
    def _initialize_outcome_tracker(self, event_bus):
        """Initialize outcome tracker."""
        from services.tracking.outcome_tracker import OutcomeTracker
        self.logger.info("Outcome tracker initialized")
        return OutcomeTracker(
            data_dir="data/reputation",
            logger=self.logger,
            event_bus=event_bus
        )
    
    def _initialize_performance_tracker(self):
        """Initialize performance tracker."""
        from services.tracking.performance_tracker import PerformanceTracker
        performance_config = PerformanceConfig.load_from_env()
        self.logger.info("Performance tracker initialized")
        return PerformanceTracker(
            data_dir=performance_config.data_dir,
            tracking_days=performance_config.tracking_days,
            csv_output_dir="output",
            enable_csv=False
        )
    
    def _initialize_reputation_engine(self, event_bus):
        """Initialize reputation engine."""
        from services.reputation.reputation_engine import ReputationEngine
        self.logger.info("Reputation engine initialized")
        return ReputationEngine(
            data_dir="data/reputation",
            logger=self.logger,
            event_bus=event_bus
        )
    
    def _initialize_data_output(self, event_bus, reputation_engine):
        """Initialize data output."""
        from infrastructure.output.data_output import MultiTableDataOutput
        output_config = OutputConfig.load_from_env()
        self.logger.info("Multi-table data output initialized")
        return MultiTableDataOutput(
            output_config,
            self.logger,
            event_bus=event_bus,
            reputation_engine=reputation_engine
        )
    
    def _initialize_message_processor(self, config, reputation_engine, event_bus):
        """Initialize message processor."""
        from services.message_processing.message_processor import MessageProcessor
        self.logger.info("Message processor initialized")
        return MessageProcessor(
            max_ic=config.processing.hdrb_max_ic,
            confidence_threshold=config.processing.confidence_threshold,
            reputation_engine=reputation_engine,
            event_bus=event_bus
        )
    
    def _initialize_historical_price_retriever(self):
        """Initialize historical price retriever."""
        from services.pricing import HistoricalPriceRetriever
        self.logger.info("Historical price retriever initialized")
        return HistoricalPriceRetriever(
            cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
            cache_dir="data/cache",
            symbol_mapping_path="data/symbol_mapping.json",
            logger=self.logger
        )
    
    def _initialize_dead_token_detector(self):
        """Initialize dead token detector."""
        from services.validation import DeadTokenDetector
        self.logger.info("Dead token detector initialized")
        return DeadTokenDetector(
            etherscan_api_key=os.getenv('ETHERSCAN_API_KEY', ''),
            blacklist_path="data/dead_tokens_blacklist.json",
            logger=self.logger
        )
    
    def _initialize_historical_bootstrap(self):
        """Initialize historical bootstrap."""
        from services.pricing import HistoricalPriceService
        from services.reputation import HistoricalBootstrap
        
        historical_price_service = HistoricalPriceService(
            cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
            cache_dir="data/cache",
            symbol_mapping_path="data/symbol_mapping.json",
            logger=self.logger
        )
        
        bootstrap = HistoricalBootstrap(
            data_dir="data/reputation",
            historical_price_service=historical_price_service,
            logger=self.logger
        )
        bootstrap.load_existing_data()
        
        self.logger.info("Historical bootstrap initialized")
        return bootstrap
    
    def _initialize_symbol_resolver(self, price_engine, historical_bootstrap):
        """Initialize symbol resolver."""
        from services.pricing.symbol_resolver import SymbolResolver
        self.logger.info("Symbol resolver initialized")
        return SymbolResolver(
            coingecko_client=price_engine.clients['coingecko'],
            historical_price_service=historical_bootstrap.historical_price_service,
            logger=self.logger
        )
    
    def _initialize_address_processing_service(self, address_extractor, symbol_resolver):
        """Initialize address processing service."""
        from services.orchestration.address_processing_service import AddressProcessingService
        self.logger.info("Address processing service initialized")
        return AddressProcessingService(
            address_extractor=address_extractor,
            symbol_resolver=symbol_resolver,
            logger=self.logger
        )
    
    def _initialize_price_fetching_service(
        self, price_engine, data_enrichment, historical_price_retriever
    ):
        """Initialize price fetching service."""
        from services.orchestration.price_fetching_service import PriceFetchingService
        self.logger.info("Price fetching service initialized")
        return PriceFetchingService(
            price_engine=price_engine,
            data_enrichment=data_enrichment,
            historical_price_retriever=historical_price_retriever,
            logger=self.logger
        )
    
    def _initialize_signal_tracking_service(
        self, performance_tracker, outcome_tracker, dead_token_detector, historical_bootstrap
    ):
        """Initialize signal tracking service."""
        from services.orchestration.signal_tracking_service import SignalTrackingService
        self.logger.info("Signal tracking service initialized")
        return SignalTrackingService(
            performance_tracker=performance_tracker,
            outcome_tracker=outcome_tracker,
            dead_token_detector=dead_token_detector,
            historical_bootstrap=historical_bootstrap,
            logger=self.logger
        )
    
    def _initialize_signal_coordinator(
        self, address_service, price_service, tracking_service, data_output
    ):
        """Initialize signal coordinator."""
        from services.orchestration.signal_coordinator import SignalCoordinator
        self.logger.info("Signal coordinator initialized")
        return SignalCoordinator(
            address_processing_service=address_service,
            price_fetching_service=price_service,
            signal_tracking_service=tracking_service,
            data_output=data_output,
            logger=self.logger
        )
    
    def _initialize_message_handler(self, message_processor, signal_coordinator, data_output):
        """Initialize message handler."""
        from services.orchestration.message_handler import MessageHandler
        self.logger.info("Message handler initialized")
        return MessageHandler(
            message_processor=message_processor,
            signal_processing_service=signal_coordinator,
            data_output=data_output,
            logger=self.logger
        )
    
    def _initialize_priority_queue(self, reputation_engine):
        """Initialize priority message queue."""
        from infrastructure.message_queue import PriorityMessageQueue
        self.logger.info("Priority message queue initialized")
        return PriorityMessageQueue(
            reputation_engine=reputation_engine,
            max_queue_size=5000,
            messages_per_second=2.0,
            logger=self.logger
        )
    
    def _initialize_telegram_monitor(self, config):
        """Initialize Telegram monitor."""
        from infrastructure.telegram.telegram_monitor import TelegramMonitor
        self.logger.info("Telegram monitor initialized")
        return TelegramMonitor(config.telegram, config.channels)
    
    def _initialize_historical_scrapers(
        self, telegram_monitor, message_handler, reputation_engine
    ):
        """Initialize historical scrapers."""
        historical_config = HistoricalScraperConfig.load_from_env()
        
        if not historical_config.enabled:
            self.logger.info("Historical scraping disabled")
            return None, None
        
        from infrastructure.scrapers.historical_scraper import HistoricalScraper
        from infrastructure.scrapers.parallel_historical_scraper import ParallelHistoricalScraper
        
        historical_scraper = HistoricalScraper(
            historical_config,
            telegram_monitor,
            message_handler.handle_message
        )
        
        parallel_scraper = ParallelHistoricalScraper(
            historical_config,
            telegram_monitor,
            message_handler.handle_message,
            reputation_engine,
            max_concurrent=10,
            logger=self.logger
        )
        
        self.logger.info("Historical scrapers initialized")
        return historical_scraper, parallel_scraper

"""Data enrichment service for adding market intelligence to price data.

Separates business logic (market analysis) from data access (price fetching).
"""
from typing import Optional
from core.api_clients import PriceData
from utils.logger import setup_logger

# Try to import market analyzer
try:
    from intelligence.market_analyzer import MarketAnalyzer
    MARKET_ANALYZER_AVAILABLE = True
except ImportError:
    MARKET_ANALYZER_AVAILABLE = False


class DataEnrichmentService:
    """Enriches price data with market intelligence analysis."""
    
    def __init__(self, logger=None):
        """
        Initialize data enrichment service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('DataEnrichmentService')
        self.market_analyzer = None
        
        if MARKET_ANALYZER_AVAILABLE:
            self.market_analyzer = MarketAnalyzer()
            self.logger.info("Market analyzer initialized for data enrichment")
        else:
            self.logger.warning("Market analyzer not available - enrichment will be skipped")
    
    def enrich_price_data(self, price_data: PriceData) -> PriceData:
        """
        Add market intelligence to price data.
        
        Args:
            price_data: Raw price data from API
            
        Returns:
            Enriched price data with market intelligence fields populated
        """
        if not self.market_analyzer:
            self.logger.debug("Market analyzer not available, skipping enrichment")
            return price_data
        
        try:
            intel = self.market_analyzer.analyze(
                market_cap=price_data.market_cap,
                liquidity_usd=price_data.liquidity_usd,
                volume_24h=price_data.volume_24h,
                price_change_24h=price_data.price_change_24h
            )
            
            # Populate PriceData with market intelligence
            price_data.market_tier = intel.market_tier
            price_data.tier_description = intel.tier_description
            price_data.risk_level = intel.risk_level
            price_data.risk_score = intel.risk_score
            price_data.liquidity_ratio = intel.liquidity_ratio
            price_data.volume_ratio = intel.volume_ratio
            price_data.data_completeness = intel.data_completeness
            
            self.logger.info(
                f"Market intelligence: {intel.market_tier} tier, "
                f"{intel.risk_level} risk ({int(intel.data_completeness*100)}% data)"
            )
            
        except Exception as e:
            self.logger.warning(f"Market intelligence analysis failed: {e}")
            # Continue without intelligence - graceful degradation
        
        return price_data

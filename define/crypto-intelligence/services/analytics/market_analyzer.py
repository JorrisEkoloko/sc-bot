"""
Market Intelligence Analyzer

Classifies tokens into market cap tiers and assesses risk using multiple factors.
Implements crypto-adjusted thresholds (10x lower than traditional stocks).

Market Cap Tiers (Crypto-Adjusted):
- Large-cap: $1B+ (established, lower risk)
- Mid-cap: $100M-$1B (growth potential, moderate risk)
- Small-cap: $10M-$100M (higher risk, higher potential)
- Micro-cap: <$10M (highest risk, speculative)

Risk Assessment (4 factors, weighted):
- Tier Risk (40%): Based on market cap size
- Liquidity Risk (30%): liquidity_usd / market_cap ratio
- Volume Risk (20%): volume_24h / market_cap ratio
- Volatility Risk (10%): Based on price_change_24h

Reference: https://www.investopedia.com/terms/m/marketcapitalization.asp
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketIntelligence:
    """Market intelligence data for a token"""
    market_tier: str  # large, mid, small, micro, unknown
    tier_description: str  # Human-readable description
    risk_level: str  # low, moderate, high, extreme
    risk_score: float  # 0-100 (higher = riskier)
    liquidity_ratio: Optional[float] = None  # liquidity_usd / market_cap
    volume_ratio: Optional[float] = None  # volume_24h / market_cap
    data_completeness: float = 0.0  # 0.0-1.0 (0.25 per factor)


class MarketAnalyzer:
    """
    Analyzes token market data to provide intelligence and risk assessment.
    
    Uses crypto-adjusted market cap thresholds (10x lower than traditional stocks)
    and multi-factor risk scoring with graceful degradation for missing data.
    """
    
    # Crypto-adjusted market cap thresholds (in USD)
    LARGE_CAP_THRESHOLD = 1_000_000_000  # $1B
    MID_CAP_THRESHOLD = 100_000_000      # $100M
    SMALL_CAP_THRESHOLD = 10_000_000     # $10M
    
    # Risk level thresholds
    RISK_LOW_THRESHOLD = 25.0
    RISK_MODERATE_THRESHOLD = 50.0
    RISK_HIGH_THRESHOLD = 75.0
    
    def __init__(self):
        """Initialize the market analyzer"""
        logger.info("Market analyzer initialized")
    
    def analyze(
        self,
        market_cap: Optional[float] = None,
        liquidity_usd: Optional[float] = None,
        volume_24h: Optional[float] = None,
        price_change_24h: Optional[float] = None
    ) -> MarketIntelligence:
        """
        Analyze market data and return intelligence assessment.
        
        Args:
            market_cap: Market capitalization in USD
            liquidity_usd: Liquidity in USD
            volume_24h: 24-hour trading volume in USD
            price_change_24h: 24-hour price change percentage
            
        Returns:
            MarketIntelligence object with tier and risk assessment
        """
        # Classify tier (requires market_cap)
        tier, tier_desc = self._classify_tier(market_cap)
        
        # Calculate ratios
        liquidity_ratio = self._calculate_liquidity_ratio(liquidity_usd, market_cap)
        volume_ratio = self._calculate_volume_ratio(volume_24h, market_cap)
        
        # Assess risk using available factors
        risk_score, data_completeness = self._assess_risk(
            market_cap=market_cap,
            liquidity_ratio=liquidity_ratio,
            volume_ratio=volume_ratio,
            price_change_24h=price_change_24h
        )
        
        risk_level = self._get_risk_level(risk_score)
        
        # Log analysis results
        if market_cap:
            logger.info(f"Classified as {tier} tier: ${market_cap/1_000_000:.1f}M market cap")
        if liquidity_ratio:
            logger.info(f"Liquidity ratio: {liquidity_ratio:.3f}")
        if volume_ratio:
            logger.info(f"Volume ratio: {volume_ratio:.3f}")
        
        factors_used = int(data_completeness * 4)
        logger.info(f"Risk assessment: {factors_used} factors used ({int(data_completeness*100)}% data)")
        logger.info(f"Risk level: {risk_level} (score: {risk_score:.1f})")
        
        return MarketIntelligence(
            market_tier=tier,
            tier_description=tier_desc,
            risk_level=risk_level,
            risk_score=risk_score,
            liquidity_ratio=liquidity_ratio,
            volume_ratio=volume_ratio,
            data_completeness=data_completeness
        )
    
    def _classify_tier(self, market_cap: Optional[float]) -> tuple[str, str]:
        """
        Classify token into market cap tier using crypto-adjusted thresholds.
        
        Args:
            market_cap: Market capitalization in USD
            
        Returns:
            Tuple of (tier, description)
        """
        if market_cap is None:
            return "unknown", "Unknown market cap"
        
        if market_cap >= self.LARGE_CAP_THRESHOLD:
            return "large", "Large-cap (>$1B) - Established, lower risk"
        elif market_cap >= self.MID_CAP_THRESHOLD:
            return "mid", "Mid-cap ($100M-$1B) - Growth potential, moderate risk"
        elif market_cap >= self.SMALL_CAP_THRESHOLD:
            return "small", "Small-cap ($10M-$100M) - Higher risk, higher potential"
        else:
            return "micro", "Micro-cap (<$10M) - Highest risk, speculative"
    
    def _calculate_liquidity_ratio(
        self,
        liquidity_usd: Optional[float],
        market_cap: Optional[float]
    ) -> Optional[float]:
        """
        Calculate liquidity ratio (liquidity / market_cap).
        
        Higher ratio = better liquidity = lower risk
        
        Args:
            liquidity_usd: Liquidity in USD
            market_cap: Market capitalization in USD
            
        Returns:
            Liquidity ratio or None if data unavailable
        """
        if liquidity_usd is None or market_cap is None or market_cap == 0:
            return None
        
        return liquidity_usd / market_cap
    
    def _calculate_volume_ratio(
        self,
        volume_24h: Optional[float],
        market_cap: Optional[float]
    ) -> Optional[float]:
        """
        Calculate volume ratio (volume_24h / market_cap).
        
        Higher ratio = more trading activity = better price discovery
        
        Args:
            volume_24h: 24-hour trading volume in USD
            market_cap: Market capitalization in USD
            
        Returns:
            Volume ratio or None if data unavailable
        """
        if volume_24h is None or market_cap is None or market_cap == 0:
            return None
        
        return volume_24h / market_cap
    
    def _assess_risk(
        self,
        market_cap: Optional[float],
        liquidity_ratio: Optional[float],
        volume_ratio: Optional[float],
        price_change_24h: Optional[float]
    ) -> tuple[float, float]:
        """
        Assess risk using available factors with weighted scoring.
        
        Weights:
        - Tier Risk: 40%
        - Liquidity Risk: 30%
        - Volume Risk: 20%
        - Volatility Risk: 10%
        
        Args:
            market_cap: Market capitalization in USD
            liquidity_ratio: Liquidity / market_cap ratio
            volume_ratio: Volume / market_cap ratio
            price_change_24h: 24-hour price change percentage
            
        Returns:
            Tuple of (risk_score 0-100, data_completeness 0-1)
        """
        risk_components = []
        factors_available = 0
        
        # Factor 1: Tier Risk (40% weight)
        if market_cap is not None:
            tier_risk = self._calculate_tier_risk(market_cap)
            risk_components.append(tier_risk * 0.40)
            factors_available += 1
        
        # Factor 2: Liquidity Risk (30% weight)
        if liquidity_ratio is not None:
            liquidity_risk = self._calculate_liquidity_risk(liquidity_ratio)
            risk_components.append(liquidity_risk * 0.30)
            factors_available += 1
        
        # Factor 3: Volume Risk (20% weight)
        if volume_ratio is not None:
            volume_risk = self._calculate_volume_risk(volume_ratio)
            risk_components.append(volume_risk * 0.20)
            factors_available += 1
        
        # Factor 4: Volatility Risk (10% weight)
        if price_change_24h is not None:
            volatility_risk = self._calculate_volatility_risk(price_change_24h)
            risk_components.append(volatility_risk * 0.10)
            factors_available += 1
        
        # Calculate total risk score
        if factors_available == 0:
            return 50.0, 0.0  # Default moderate risk with no data
        
        # Normalize by available factors
        total_weight = sum([0.40, 0.30, 0.20, 0.10][:factors_available])
        risk_score = sum(risk_components) / total_weight
        
        # Data completeness (0.25 per factor)
        data_completeness = factors_available / 4.0
        
        return risk_score, data_completeness
    
    def _calculate_tier_risk(self, market_cap: float) -> float:
        """
        Calculate risk based on market cap tier.
        
        Larger market cap = lower risk
        
        Args:
            market_cap: Market capitalization in USD
            
        Returns:
            Risk score 0-100
        """
        if market_cap >= self.LARGE_CAP_THRESHOLD:
            return 15.0  # Low risk
        elif market_cap >= self.MID_CAP_THRESHOLD:
            return 40.0  # Moderate risk
        elif market_cap >= self.SMALL_CAP_THRESHOLD:
            return 65.0  # High risk
        else:
            return 90.0  # Extreme risk
    
    def _calculate_liquidity_risk(self, liquidity_ratio: float) -> float:
        """
        Calculate risk based on liquidity ratio.
        
        Higher liquidity ratio = lower risk
        Typical ranges: >0.1 = good, 0.01-0.1 = moderate, <0.01 = poor
        
        Args:
            liquidity_ratio: Liquidity / market_cap ratio
            
        Returns:
            Risk score 0-100
        """
        if liquidity_ratio >= 0.1:
            return 20.0  # Good liquidity
        elif liquidity_ratio >= 0.05:
            return 40.0  # Moderate liquidity
        elif liquidity_ratio >= 0.01:
            return 65.0  # Low liquidity
        else:
            return 85.0  # Very low liquidity
    
    def _calculate_volume_risk(self, volume_ratio: float) -> float:
        """
        Calculate risk based on volume ratio.
        
        Higher volume ratio = better price discovery = lower risk
        Typical ranges: >0.5 = high, 0.1-0.5 = moderate, <0.1 = low
        
        Args:
            volume_ratio: Volume / market_cap ratio
            
        Returns:
            Risk score 0-100
        """
        if volume_ratio >= 0.5:
            return 25.0  # High volume
        elif volume_ratio >= 0.1:
            return 45.0  # Moderate volume
        elif volume_ratio >= 0.05:
            return 65.0  # Low volume
        else:
            return 80.0  # Very low volume
    
    def _calculate_volatility_risk(self, price_change_24h: float) -> float:
        """
        Calculate risk based on 24-hour price volatility.
        
        Higher volatility = higher risk
        
        Args:
            price_change_24h: 24-hour price change percentage
            
        Returns:
            Risk score 0-100
        """
        abs_change = abs(price_change_24h)
        
        if abs_change >= 50.0:
            return 90.0  # Extreme volatility
        elif abs_change >= 25.0:
            return 70.0  # High volatility
        elif abs_change >= 10.0:
            return 45.0  # Moderate volatility
        else:
            return 20.0  # Low volatility
    
    def _get_risk_level(self, risk_score: float) -> str:
        """
        Convert risk score to categorical risk level.
        
        Args:
            risk_score: Risk score 0-100
            
        Returns:
            Risk level: low, moderate, high, or extreme
        """
        if risk_score < self.RISK_LOW_THRESHOLD:
            return "low"
        elif risk_score < self.RISK_MODERATE_THRESHOLD:
            return "moderate"
        elif risk_score < self.RISK_HIGH_THRESHOLD:
            return "high"
        else:
            return "extreme"

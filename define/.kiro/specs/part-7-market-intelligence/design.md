# Design Document - Part 7: Market Intelligence & Tier Classification

## Overview

Part 7 extends the crypto intelligence pipeline with market analysis capabilities. The design emphasizes graceful degradation (works with partial data), multi-factor risk assessment (beyond just market cap), and seamless integration with existing components. All analysis is performed in-memory with no additional API calls.

## Architecture

### System Context

```
Part 3 Output (PriceData with market_cap, liquidity, volume)
    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Part 7: Market Intelligence                   │
│                                                                  │
│  Price Engine → Market Analyzer → Enriched PriceData           │
│                      ↓                                           │
│              ┌──────────────────┐                               │
│              │ Tier Classifier  │                               │
│              │ Risk Assessor    │                               │
│              │ Ratio Calculator │                               │
│              └──────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
    ↓
Enhanced PriceData (with market_tier, risk_level, risk_score, ratios)
    ↓
Data Output (TOKEN_PRICES table with 6 new columns)
```

### Component Interaction

```
┌──────────────────┐
│  Price Engine    │
│  (existing)      │
└────────┬─────────┘
         │ PriceData
         ↓
┌────────────────────┐
│ Market Analyzer    │
│ (NEW)              │
│                    │
│ analyze(price_data)│
│   ├─ classify_tier │
│   ├─ calc_liquidity│
│   ├─ calc_volume   │
│   ├─ calc_volatility│
│   └─ calc_risk_score│
└────────┬───────────┘
         │ MarketIntelligence
         ↓
┌────────────────────┐
│ Enhanced PriceData │
│ + market_tier      │
│ + risk_level       │
│ + risk_score       │
│ + liquidity_ratio  │
│ + volume_ratio     │
│ + data_completeness│
└────────┬───────────┘
         │
         ↓
┌────────────────────┐
│ Data Output        │
│ (existing)         │
│ TOKEN_PRICES table │
│ + 6 new columns    │
└────────────────────┘
```

## Components and Interfaces

### 1. Market Analyzer

**File:** `intelligence/market_analyzer.py`

**Purpose:** Analyze market cap data and provide tier classification and risk assessment.

**Class Design:**

```python
from dataclasses import dataclass
from typing import Optional
from core.api_clients import PriceData


@dataclass
class MarketIntelligence:
    """Market intelligence analysis results."""
    # Tier classification
    market_tier: str  # "large", "mid", "small", "micro", "unknown"
    tier_description: str  # Human-readable description

    # Risk assessment
    risk_level: str  # "low", "moderate", "high", "extreme", "unknown"
    risk_score: Optional[float]  # 0-100 scale

    # Ratio analysis
    liquidity_ratio: Optional[float]  # liquidity_usd / market_cap
    volume_ratio: Optional[float]  # volume_24h / market_cap

    # Metadata
    factors_used: list[str]  # Which factors were available
    data_completeness: float  # 0.0-1.0 (percentage of factors available)


class MarketAnalyzer:
    """Market intelligence analyzer."""

    # Tier thresholds (crypto-adjusted)
    LARGE_CAP_THRESHOLD = 1_000_000_000  # $1B
    MID_CAP_THRESHOLD = 100_000_000      # $100M
    SMALL_CAP_THRESHOLD = 10_000_000     # $10M

    # Liquidity ratio thresholds
    LIQUIDITY_HEALTHY = 0.10  # 10%+
    LIQUIDITY_MODERATE = 0.05  # 5-10%

    # Volume ratio thresholds
    VOLUME_HEALTHY = 0.20  # 20%+
    VOLUME_MODERATE = 0.05  # 5-20%

    # Volatility thresholds
    VOLATILITY_LOW = 10.0  # <10% change
    VOLATILITY_MODERATE = 30.0  # 10-30% change

    # Risk score weights
    TIER_WEIGHT = 0.4
    LIQUIDITY_WEIGHT = 0.3
    VOLUME_WEIGHT = 0.2
    VOLATILITY_WEIGHT = 0.1

    def __init__(self, logger=None):
        """Initialize market analyzer."""
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('MarketAnalyzer')

    def analyze(self, price_data: PriceData) -> MarketIntelligence:
        """
        Perform complete market intelligence analysis.

        Args:
            price_data: Price data from API

        Returns:
            MarketIntelligence with all available analysis
        """
        # Classify tier
        tier, tier_desc = self._classify_tier(price_data.market_cap)

        # Calculate ratios
        liquidity_ratio = self._calculate_liquidity_ratio(
            price_data.liquidity_usd,
            price_data.market_cap
        )
        volume_ratio = self._calculate_volume_ratio(
            price_data.volume_24h,
            price_data.market_cap
        )

        # Assess risk
        risk_result = self._assess_risk(
            tier=tier,
            market_cap=price_data.market_cap,
            liquidity_ratio=liquidity_ratio,
            volume_ratio=volume_ratio,
            price_change_24h=price_data.price_change_24h
        )

        return MarketIntelligence(
            market_tier=tier,
            tier_description=tier_desc,
            risk_level=risk_result['risk_level'],
            risk_score=risk_result['risk_score'],
            liquidity_ratio=liquidity_ratio,
            volume_ratio=volume_ratio,
            factors_used=risk_result['factors_used'],
            data_completeness=risk_result['data_completeness']
        )

    def _classify_tier(self, market_cap: Optional[float]) -> tuple[str, str]:
        """
        Classify market cap tier.

        Args:
            market_cap: Market capitalization in USD

        Returns:
            Tuple of (tier_code, tier_description)
        """
        if market_cap is None:
            return ("unknown", "Market cap unavailable")

        if market_cap >= self.LARGE_CAP_THRESHOLD:
            return ("large", f"Large-cap (${market_cap/1e9:.2f}B)")
        elif market_cap >= self.MID_CAP_THRESHOLD:
            return ("mid", f"Mid-cap (${market_cap/1e6:.1f}M)")
        elif market_cap >= self.SMALL_CAP_THRESHOLD:
            return ("small", f"Small-cap (${market_cap/1e6:.1f}M)")
        else:
            return ("micro", f"Micro-cap (${market_cap/1e6:.2f}M)")

    def _calculate_liquidity_ratio(
        self,
        liquidity_usd: Optional[float],
        market_cap: Optional[float]
    ) -> Optional[float]:
        """Calculate liquidity to market cap ratio."""
        if liquidity_usd is None or market_cap is None or market_cap == 0:
            return None
        return liquidity_usd / market_cap

    def _calculate_volume_ratio(
        self,
        volume_24h: Optional[float],
        market_cap: Optional[float]
    ) -> Optional[float]:
        """Calculate 24h volume to market cap ratio."""
        if volume_24h is None or market_cap is None or market_cap == 0:
            return None
        return volume_24h / market_cap

    def _assess_risk(
        self,
        tier: str,
        market_cap: Optional[float],
        liquidity_ratio: Optional[float],
        volume_ratio: Optional[float],
        price_change_24h: Optional[float]
    ) -> dict:
        """
        Multi-factor risk assessment with graceful degradation.

        Returns:
            Dict with risk_level, risk_score, factors_used, data_completeness
        """
        risk_factors = []

        # Factor 1: Tier risk (if market cap available)
        if market_cap is not None:
            tier_risk = self._calculate_tier_risk(tier)
            risk_factors.append(("tier", tier_risk, self.TIER_WEIGHT))

        # Factor 2: Liquidity risk (if ratio available)
        if liquidity_ratio is not None:
            liquidity_risk = self._calculate_liquidity_risk(liquidity_ratio)
            risk_factors.append(("liquidity", liquidity_risk, self.LIQUIDITY_WEIGHT))

        # Factor 3: Volume risk (if ratio available)
        if volume_ratio is not None:
            volume_risk = self._calculate_volume_risk(volume_ratio)
            risk_factors.append(("volume", volume_risk, self.VOLUME_WEIGHT))

        # Factor 4: Volatility risk (if price change available)
        if price_change_24h is not None:
            volatility_risk = self._calculate_volatility_risk(price_change_24h)
            risk_factors.append(("volatility", volatility_risk, self.VOLATILITY_WEIGHT))

        # Calculate weighted risk score
        if risk_factors:
            total_weight = sum(weight for _, _, weight in risk_factors)
            risk_score = sum(
                risk * weight for _, risk, weight in risk_factors
            ) / total_weight

            risk_level = self._get_risk_level(risk_score)
            factors_used = [name for name, _, _ in risk_factors]
            data_completeness = len(risk_factors) / 4.0  # 4 possible factors

            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "factors_used": factors_used,
                "data_completeness": data_completeness
            }
        else:
            return {
                "risk_score": None,
                "risk_level": "unknown",
                "factors_used": [],
                "data_completeness": 0.0
            }

    def _calculate_tier_risk(self, tier: str) -> float:
        """Convert tier to risk score (0-100)."""
        tier_risk_map = {
            "large": 20,    # Low risk
            "mid": 40,      # Moderate risk
            "small": 60,    # High risk
            "micro": 80,    # Extreme risk
            "unknown": 50   # Default moderate
        }
        return tier_risk_map.get(tier, 50)

    def _calculate_liquidity_risk(self, liquidity_ratio: float) -> float:
        """Convert liquidity ratio to risk score (0-100)."""
        if liquidity_ratio >= self.LIQUIDITY_HEALTHY:
            return 20  # Low risk
        elif liquidity_ratio >= self.LIQUIDITY_MODERATE:
            return 50  # Moderate risk
        else:
            return 80  # High risk

    def _calculate_volume_risk(self, volume_ratio: float) -> float:
        """Convert volume ratio to risk score (0-100)."""
        if volume_ratio >= self.VOLUME_HEALTHY:
            return 20  # Low risk
        elif volume_ratio >= self.VOLUME_MODERATE:
            return 50  # Moderate risk
        else:
            return 80  # High risk

    def _calculate_volatility_risk(self, price_change_24h: float) -> float:
        """Convert price change to risk score (0-100)."""
        abs_change = abs(price_change_24h)
        if abs_change < self.VOLATILITY_LOW:
            return 20  # Low risk
        elif abs_change < self.VOLATILITY_MODERATE:
            return 50  # Moderate risk
        else:
            return 80  # High risk

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to categorical level."""
        if risk_score <= 25:
            return "low"
        elif risk_score <= 50:
            return "moderate"
        elif risk_score <= 75:
            return "high"
        else:
            return "extreme"
```

### 2. Enhanced PriceData

**File:** `core/api_clients/base_client.py` (modify existing)

**Changes:**

```python
@dataclass
class PriceData:
    """Price information from API with market intelligence."""
    # Existing fields
    price_usd: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    liquidity_usd: Optional[float] = None
    pair_created_at: Optional[str] = None
    symbol: Optional[str] = None
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)

    # NEW: Market intelligence fields
    market_tier: Optional[str] = None
    tier_description: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    liquidity_ratio: Optional[float] = None
    volume_ratio: Optional[float] = None
    data_completeness: Optional[float] = None
```

### 3. Price Engine Integration

**File:** `core/price_engine.py` (modify existing)

**Integration Point:**

```python
async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
    """Get price with failover and market intelligence enrichment."""
    # ... existing price fetching logic ...

    if not price_data:
        return None

    # ... existing data enrichment fallback ...

    # NEW: Add market intelligence
    try:
        from intelligence.market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer(self.logger)
        intelligence = analyzer.analyze(price_data)

        # Enrich PriceData with market intelligence
        price_data.market_tier = intelligence.market_tier
        price_data.tier_description = intelligence.tier_description
        price_data.risk_level = intelligence.risk_level
        price_data.risk_score = intelligence.risk_score
        price_data.liquidity_ratio = intelligence.liquidity_ratio
        price_data.volume_ratio = intelligence.volume_ratio
        price_data.data_completeness = intelligence.data_completeness

        self.logger.info(
            f"Market intelligence: {intelligence.market_tier} tier, "
            f"{intelligence.risk_level} risk "
            f"({intelligence.data_completeness*100:.0f}% data)"
        )
    except Exception as e:
        self.logger.warning(f"Market intelligence enrichment failed: {e}")
        # Continue with price data only

    # Cache and return
    self.cache[cache_key] = price_data
    return price_data
```

### 4. Data Output Extension

**File:** `core/data_output.py` (modify existing)

**Changes:**

```python
TOKEN_PRICES_COLUMNS = [
    'address', 'chain', 'symbol', 'price_usd', 'market_cap',
    'volume_24h', 'price_change_24h', 'liquidity_usd', 'pair_created_at',
    # NEW: Market intelligence columns
    'market_tier', 'risk_level', 'risk_score',
    'liquidity_ratio', 'volume_ratio', 'data_completeness'
]

async def write_token_price(self, address: str, chain: str, price_data: PriceData):
    """Write/update token price with market intelligence."""
    row = [
        address,
        chain,
        price_data.symbol or 'UNKNOWN',
        price_data.price_usd,
        price_data.market_cap,
        price_data.volume_24h,
        price_data.price_change_24h,
        price_data.liquidity_usd,
        price_data.pair_created_at,
        # NEW: Market intelligence
        price_data.market_tier or '',
        price_data.risk_level or '',
        price_data.risk_score if price_data.risk_score is not None else '',
        price_data.liquidity_ratio if price_data.liquidity_ratio is not None else '',
        price_data.volume_ratio if price_data.volume_ratio is not None else '',
        price_data.data_completeness if price_data.data_completeness is not None else ''
    ]

    # ... existing write logic ...
```

## Data Models

### MarketIntelligence

```python
@dataclass
class MarketIntelligence:
    """Market intelligence analysis results."""
    market_tier: str
    tier_description: str
    risk_level: str
    risk_score: Optional[float]
    liquidity_ratio: Optional[float]
    volume_ratio: Optional[float]
    factors_used: list[str]
    data_completeness: float
```

## Error Handling

### Strategy

1. **Missing Data**: Graceful degradation - analyze with available data
2. **Calculation Errors**: Log and return partial results
3. **Integration Failures**: Continue with price data only
4. **Invalid Values**: Treat as None and skip that factor

### Error Propagation

```python
try:
    intelligence = analyzer.analyze(price_data)
    # Enrich price_data
except Exception as e:
    logger.warning(f"Market intelligence failed: {e}")
    # price_data continues without intelligence fields
```

## Testing Strategy

### Unit Tests

- **Tier Classification**: Test all thresholds and edge cases
- **Ratio Calculations**: Test with various market cap/liquidity/volume combinations
- **Risk Scoring**: Test weighted calculations and graceful degradation
- **Edge Cases**: Test with None values, zero values, extreme values

### Integration Tests

- **Price Engine Integration**: Verify enrichment doesn't break price fetching
- **Data Output**: Verify new columns appear in CSV and Google Sheets
- **Caching**: Verify market intelligence is cached with price data

### Performance Tests

- **Speed**: Verify analysis completes in < 5ms
- **Memory**: Verify no memory leaks with repeated analysis
- **Throughput**: Process 100 tokens and measure total time

## Performance Targets

- Tier classification: < 1ms
- Full risk assessment: < 5ms
- Price Engine integration overhead: < 10ms
- No additional API calls (uses existing price data)

## Deployment Considerations

### Dependencies

No new dependencies required - uses existing Python standard library.

### Configuration

No new configuration required - uses hardcoded thresholds based on research.

### Directory Structure

```
crypto-intelligence/
├── intelligence/           # NEW directory
│   ├── __init__.py
│   └── market_analyzer.py
├── core/
│   ├── api_clients/
│   │   └── base_client.py  # Modified: Enhanced PriceData
│   ├── price_engine.py     # Modified: Add intelligence enrichment
│   └── data_output.py      # Modified: Add 6 columns
└── output/
    └── YYYY-MM-DD/
        └── token_prices.csv  # Now has 15 columns (was 9)
```

## Validation Criteria

### Console Output

```
[2025-11-10 23:00:00] [INFO] [PriceEngine] Price fetched from dexscreener: $50.60M
[2025-11-10 23:00:00] [INFO] [PriceEngine] Market intelligence: mid tier, moderate risk (75% data)
```

### CSV Output

```csv
address,chain,symbol,price_usd,market_cap,volume_24h,price_change_24h,liquidity_usd,pair_created_at,market_tier,risk_level,risk_score,liquidity_ratio,volume_ratio,data_completeness
5gb4npgfb3...,solana,AVICI,3.92,50587715.0,2361161.26,38.38,1804744.18,1760806818000,mid,high,62.5,0.036,0.047,1.0
```

### Google Sheets

- New columns visible with data
- Conditional formatting possible on risk_level
- Sortable by market_tier and risk_score

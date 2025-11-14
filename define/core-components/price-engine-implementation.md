# PriceEngine - Deep Implementation Guide

## Overview

Multi-API price fetching system with intelligent failover, market cap intelligence, and production-grade reliability.

## Architecture Design

### Core Responsibilities

- Multi-API price data collection (CoinGecko, Birdeye, Moralis, DexScreener)
- Intelligent API selection and failover
- Rate limiting and health monitoring
- Market cap intelligence integration
- Caching and performance optimization

### Component Structure

```
PriceEngine/
├── api_providers/
│   ├── coingecko_api.py     # CoinGecko integration
│   ├── birdeye_api.py       # Birdeye (Solana focus)
│   ├── moralis_api.py       # Moralis multi-chain
│   └── dexscreener_api.py   # DexScreener aggregator
├── failover_manager.py      # Intelligent API selection
├── rate_limiter.py          # Rate limiting system
├── cache_manager.py         # Caching and optimization
└── market_intelligence.py   # Market cap analysis
```

## Multi-API Implementation

### 1. CoinGecko Integration

```python
class CoinGeckoAPI:
    """CoinGecko API integration with rate limiting"""

    def __init__(self, api_key=None):
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.rate_limit = 50  # calls per minute
        self.timeout = 10

    async def fetch_token_price(self, address, chain):
        # Chain mapping: ethereum, solana, binance-smart-chain
        # Simple price endpoint for fast responses
        # Market cap and volume data inclusion

    async def fetch_detailed_data(self, address, chain):
        # Comprehensive token information
        # Historical price data
        # Market statistics and metrics

    def handle_rate_limits(self, response):
        # 429 status code handling
        # Retry-After header parsing
        # Exponential backoff implementation
```

### 2. Birdeye API (Solana Specialist)

```python
class BirdeyeAPI:
    """Birdeye API for Solana ecosystem tokens"""

    def __init__(self, api_key):
        self.base_url = 'https://public-api.birdeye.so/defi'
        self.rate_limit = 60  # calls per minute
        self.headers = {'X-API-KEY': api_key}

    async def fetch_solana_token(self, address):
        # Token overview endpoint
        # Real-time price and market cap
        # Liquidity and volume metrics

    async def fetch_token_security(self, address):
        # Security analysis data
        # Mint authority information
        # Freeze authority status

    def validate_solana_address(self, address):
        # Base58 format validation
        # Solana program account checks
        # Token mint validation
```

### 3. Moralis Multi-Chain API

```python
class MoralisAPI:
    """Moralis API for multi-chain token data"""

    def __init__(self, api_key):
        self.base_url = 'https://deep-index.moralis.io/api/v2'
        self.rate_limit = 25  # calls per minute
        self.headers = {'X-API-Key': api_key}

    async def fetch_erc20_price(self, address, chain):
        # ERC20 token price endpoint
        # Multi-chain support (ETH, BSC, Polygon)
        # Token metadata inclusion

    async def fetch_token_metadata(self, address, chain):
        # Token name, symbol, decimals
        # Contract verification status
        # Token supply information

    def map_chain_identifier(self, chain):
        # Chain name to Moralis ID mapping
        # ethereum → eth, bsc → bsc, polygon → polygon
```

### 4. DexScreener Aggregator

```python
class DexScreenerAPI:
    """DexScreener API for DEX aggregated data"""

    def __init__(self):
        self.base_url = 'https://api.dexscreener.com/latest/dex'
        self.rate_limit = 300  # calls per minute (high limit)
        self.timeout = 8

    async def fetch_token_pairs(self, address):
        # All trading pairs for token
        # Liquidity and volume aggregation
        # Price discovery across DEXes

    async def get_best_pair(self, pairs_data):
        # Highest liquidity pair selection
        # Volume-weighted price calculation
        # DEX reliability scoring

    def calculate_aggregated_metrics(self, pairs):
        # Combined liquidity calculation
        # Volume-weighted average price
        # Market cap estimation
```

## Intelligent Failover System

### 1. API Health Monitoring

```python
class APIHealthMonitor:
    """Monitors API performance and reliability"""

    def __init__(self):
        self.health_metrics = {
            'coingecko': {'success_rate': 0.0, 'avg_response_time': 0.0},
            'birdeye': {'success_rate': 0.0, 'avg_response_time': 0.0},
            'moralis': {'success_rate': 0.0, 'avg_response_time': 0.0},
            'dexscreener': {'success_rate': 0.0, 'avg_response_time': 0.0}
        }

    def update_api_health(self, api_name, success, response_time):
        # Rolling average calculation
        # Success rate tracking
        # Response time monitoring

    def get_api_ranking(self, chain):
        # Chain-specific API performance
        # Health-based ranking
        # Availability consideration
```

### 2. Failover Strategy

```python
class FailoverManager:
    """Manages intelligent API selection and failover"""

    def get_api_order(self, chain, token_address):
        # Chain-specific API preferences
        # Health-based reordering
        # Token-specific optimizations

        chain_preferences = {
            'ethereum': ['dexscreener', 'coingecko', 'moralis'],
            'solana': ['birdeye', 'dexscreener', 'coingecko'],
            'bsc': ['dexscreener', 'moralis', 'coingecko']
        }

    async def execute_with_failover(self, apis, fetch_function, *args):
        # Sequential API attempts
        # Error classification and handling
        # Success criteria validation

    def should_retry_api(self, error, api_name):
        # Temporary vs permanent error classification
        # Rate limit vs service error distinction
        # Retry decision logic
```

## Rate Limiting System

### 1. Advanced Rate Limiter

```python
class RateLimiter:
    """Sophisticated rate limiting with burst handling"""

    def __init__(self, calls_per_minute, burst_allowance=5):
        self.calls_per_minute = calls_per_minute
        self.burst_allowance = burst_allowance
        self.call_history = []
        self.burst_used = 0

    async def wait_if_needed(self, api_name):
        # Sliding window rate limiting
        # Burst capacity management
        # Predictive delay calculation

    def calculate_wait_time(self, current_calls):
        # Time until next available slot
        # Burst recovery consideration
        # Minimum delay enforcement

    def reset_burst_allowance(self):
        # Periodic burst capacity reset
        # Usage pattern analysis
        # Adaptive burst sizing
```

### 2. Priority Queue System

```python
class PriorityRequestQueue:
    """Priority-based request queuing for rate limiting"""

    def __init__(self):
        self.high_priority = asyncio.Queue()
        self.normal_priority = asyncio.Queue()
        self.low_priority = asyncio.Queue()

    async def add_request(self, request, priority='normal'):
        # Priority-based queue assignment
        # Request metadata preservation
        # Queue size monitoring

    async def get_next_request(self):
        # Priority-based request selection
        # Fair scheduling algorithm
        # Starvation prevention
```

## Caching Strategy

### 1. Multi-Level Caching

```python
class CacheManager:
    """Multi-level caching for price data optimization"""

    def __init__(self):
        # L1: In-memory cache (TTL: 30 seconds)
        self.memory_cache = TTLCache(maxsize=1000, ttl=30)

        # L2: Redis cache (TTL: 5 minutes)
        self.redis_cache = None  # Optional Redis integration

        # L3: Database cache (TTL: 1 hour)
        self.db_cache = None     # Optional database caching

    async def get_cached_price(self, cache_key):
        # Multi-level cache lookup
        # Cache hit ratio tracking
        # Performance metrics collection

    async def store_price_data(self, cache_key, data, ttl=300):
        # Multi-level cache storage
        # TTL-based expiration
        # Cache size management
```

### 2. Cache Optimization

```python
class CacheOptimizer:
    """Optimizes caching strategy based on usage patterns"""

    def analyze_access_patterns(self):
        # Token access frequency analysis
        # Cache hit/miss ratio tracking
        # Performance impact measurement

    def optimize_ttl_values(self):
        # Dynamic TTL adjustment
        # Token volatility consideration
        # Access pattern adaptation

    def preload_popular_tokens(self):
        # Predictive cache warming
        # Popular token identification
        # Background refresh scheduling
```

## Market Intelligence Integration

### 1. Market Cap Analysis

```python
class MarketCapIntelligence:
    """Advanced market cap analysis and classification"""

    def classify_market_cap_tier(self, market_cap):
        # Micro: < $1M (High risk, high reward)
        # Small: $1M - $100M (Balanced risk/reward)
        # Large: > $100M (Lower risk, established)

    def assess_market_risk(self, market_cap, liquidity, volume):
        # Risk scoring algorithm
        # Liquidity/market cap ratio
        # Volume sustainability analysis

    def calculate_market_score(self, token_data):
        # Comprehensive market scoring
        # Multiple factor integration
        # Confidence level assessment
```

### 2. Price Quality Assessment

```python
class PriceQualityAssessor:
    """Assesses price data quality and reliability"""

    def validate_price_data(self, price_data):
        # Price reasonableness checks
        # Market cap calculation validation
        # Cross-API consistency verification

    def calculate_confidence_score(self, api_responses):
        # Multi-API consensus analysis
        # Price deviation measurement
        # Data completeness scoring

    def detect_price_anomalies(self, current_price, historical_data):
        # Sudden price spike detection
        # Market manipulation indicators
        # Data quality red flags
```

## Performance Optimization

### 1. Concurrent Processing

```python
class ConcurrentPriceFetcher:
    """Optimized concurrent price fetching"""

    async def fetch_multiple_tokens(self, token_list):
        # Batch processing optimization
        # Concurrent API calls with rate limiting
        # Result aggregation and validation

    async def parallel_api_calls(self, apis, token_address):
        # Simultaneous API queries
        # First successful response wins
        # Consensus validation for critical data
```

### 2. Resource Management

```python
class ResourceManager:
    """Manages system resources for optimal performance"""

    def monitor_memory_usage(self):
        # Cache size monitoring
        # Memory leak detection
        # Garbage collection optimization

    def optimize_connection_pools(self):
        # HTTP connection pooling
        # Keep-alive optimization
        # Connection limit management

    def balance_api_load(self):
        # API usage distribution
        # Load balancing across providers
        # Cost optimization strategies
```

## Error Handling & Recovery

### 1. Comprehensive Error Classification

```python
class ErrorClassifier:
    """Classifies and handles different types of API errors"""

    def classify_error(self, error, api_name):
        # Network errors: Retry with backoff
        # Rate limit errors: Wait and retry
        # Authentication errors: Skip API
        # Data errors: Try alternative API
        # Service errors: Temporary skip

    def determine_retry_strategy(self, error_type, attempt_count):
        # Exponential backoff calculation
        # Maximum retry limits
        # Circuit breaker integration
```

### 2. Circuit Breaker Pattern

```python
class APICircuitBreaker:
    """Implements circuit breaker pattern for API reliability"""

    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def record_success(self, api_name):
        # Reset failure count
        # Close circuit if half-open
        # Update health metrics

    def record_failure(self, api_name):
        # Increment failure count
        # Open circuit if threshold exceeded
        # Schedule recovery attempt
```

## Integration Interfaces

### Input Interface

```python
async def fetch_price_data(self, address: str, chain: str) -> PriceData:
    """
    Unified price fetching interface
    Input: Token address and blockchain
    Output: Comprehensive price data with intelligence
    """
```

### Output Format

```python
@dataclass
class PriceData:
    success: bool
    address: str
    chain: str
    name: str
    symbol: str
    price: float
    market_cap: Optional[float]
    liquidity: Optional[float]
    volume_24h: Optional[float]
    price_change_24h: Optional[float]
    source: str
    timestamp: datetime

    # Intelligence fields
    market_cap_tier: Optional[str]
    risk_level: Optional[str]
    confidence: float
```

### Performance Metrics

- **70%+ Success Rate**: Across all API combinations
- **< 5 Second Response Time**: Average API response
- **99%+ Uptime**: System availability target
- **< 2% Error Rate**: Failed price fetches

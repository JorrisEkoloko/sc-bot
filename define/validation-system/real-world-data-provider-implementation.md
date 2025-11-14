# Real World Data Provider - Enhanced Implementation (< 500 lines)

## Overview

The RealWorldDataProvider integrates live market data and authentic content validation into the pipeline, ensuring the system operates with real-world data while maintaining research compliance and performance benchmarks.

## Core Functionality

### Live Data Integration

- **Market Data Collection**: Real-time price and market data
- **Authentic Content**: Real crypto message validation
- **Performance Benchmarks**: Research compliance validation
- **Data Quality Assurance**: Continuous data integrity monitoring

## Implementation

```python
# validation/real_world_data_provider.py
"""
Live data integration and authentic content validation
Ensures system operates with real-world data and research compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import aiohttp
from pathlib import Path

@dataclass
class MarketDataPoint:
    """Real market data point"""
    symbol: str
    price: float
    market_cap: Optional[float]
    volume_24h: Optional[float]
    price_change_24h: Optional[float]
    timestamp: datetime
    source: str
    confidence: float

@dataclass
class ValidationResult:
    """Data validation result"""
    data_type: str
    is_valid: bool
    confidence: float
    validation_time: float
    issues: List[str]
    source: str

class RealWorldDataProvider:
    """Live data integration and validation"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Data sources configuration
        self.data_sources = {
            'coingecko': {
                'base_url': 'https://api.coingecko.com/api/v3',
                'rate_limit': 50,  # requests per minute
                'timeout': 10
            },
            'dexscreener': {
                'base_url': 'https://api.dexscreener.com/latest/dex',
                'rate_limit': 300,
                'timeout': 8
            }
        }

        # Data cache for performance
        self.market_data_cache = {}
        self.cache_ttl = timedelta(minutes=5)

        # Validation benchmarks
        self.validation_benchmarks = {
            'min_data_freshness': timedelta(minutes=10),
            'min_confidence_threshold': 0.7,
            'max_validation_time': 5.0,  # seconds
            'required_data_points': ['price', 'volume_24h']
        }

        # Statistics
        self.stats = {
            'data_requests': 0,
            'cache_hits': 0,
            'validation_passes': 0,
            'validation_failures': 0,
            'avg_response_time': 0.0,
            'data_sources_used': {}
        }

    async def get_live_market_data(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get live market data for symbols"""
        try:
            self.stats['data_requests'] += 1
            market_data = []

            for symbol in symbols:
                # Check cache first
                cache_key = f"market_{symbol}"
                if cache_key in self.market_data_cache:
                    cache_entry = self.market_data_cache[cache_key]
                    if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                        self.stats['cache_hits'] += 1
                        market_data.append(cache_entry['data'])
                        continue

                # Fetch live data
                data_point = await self._fetch_symbol_data(symbol)
                if data_point:
                    market_data.append(data_point)

                    # Cache the result
                    self.market_data_cache[cache_key] = {
                        'data': data_point,
                        'timestamp': datetime.now()
                    }

            self.logger.debug(f"Retrieved live market data for {len(market_data)}/{len(symbols)} symbols")

            return market_data

        except Exception as e:
            self.logger.error(f"Error getting live market data: {e}")
            return []

    async def _fetch_symbol_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data for single symbol from multiple sources"""
        try:
            # Try CoinGecko first
            coingecko_data = await self._fetch_from_coingecko(symbol)
            if coingecko_data:
                return coingecko_data

            # Fallback to DexScreener
            dexscreener_data = await self._fetch_from_dexscreener(symbol)
            if dexscreener_data:
                return dexscreener_data

            return None

        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    async def _fetch_from_coingecko(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data from CoinGecko API"""
        try:
            source_config = self.data_sources['coingecko']
            url = f"{source_config['base_url']}/simple/price"

            params = {
                'ids': symbol.lower(),
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=source_config['timeout'])) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if symbol.lower() in data:
                            token_data = data[symbol.lower()]

                            # Update source usage stats
                            self.stats['data_sources_used']['coingecko'] = self.stats['data_sources_used'].get('coingecko', 0) + 1

                            return MarketDataPoint(
                                symbol=symbol.upper(),
                                price=token_data.get('usd', 0.0),
                                market_cap=token_data.get('usd_market_cap'),
                                volume_24h=token_data.get('usd_24h_vol'),
                                price_change_24h=token_data.get('usd_24h_change'),
                                timestamp=datetime.now(),
                                source='coingecko',
                                confidence=0.9
                            )

            return None

        except Exception as e:
            self.logger.error(f"CoinGecko API error for {symbol}: {e}")
            return None

    async def _fetch_from_dexscreener(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data from DexScreener API"""
        try:
            source_config = self.data_sources['dexscreener']
            url = f"{source_config['base_url']}/search"

            params = {'q': symbol}

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=source_config['timeout'])) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        pairs = data.get('pairs', [])
                        if pairs:
                            # Get the most liquid pair
                            best_pair = max(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0)))

                            # Update source usage stats
                            self.stats['data_sources_used']['dexscreener'] = self.stats['data_sources_used'].get('dexscreener', 0) + 1

                            return MarketDataPoint(
                                symbol=symbol.upper(),
                                price=float(best_pair.get('priceUsd', 0)),
                                market_cap=float(best_pair.get('marketCap', 0)) if best_pair.get('marketCap') else None,
                                volume_24h=float(best_pair.get('volume', {}).get('h24', 0)),
                                price_change_24h=float(best_pair.get('priceChange', {}).get('h24', 0)),
                                timestamp=datetime.now(),
                                source='dexscreener',
                                confidence=0.8
                            )

            return None

        except Exception as e:
            self.logger.error(f"DexScreener API error for {symbol}: {e}")
            return None

    async def validate_data_freshness(self) -> ValidationResult:
        """Validate that system is using fresh, real-world data"""
        try:
            start_time = datetime.now()
            issues = []

            # Check cache freshness
            fresh_entries = 0
            total_entries = len(self.market_data_cache)

            for cache_entry in self.market_data_cache.values():
                age = datetime.now() - cache_entry['timestamp']
                if age < self.validation_benchmarks['min_data_freshness']:
                    fresh_entries += 1

            # Calculate freshness ratio
            freshness_ratio = fresh_entries / max(1, total_entries) if total_entries > 0 else 1.0

            if freshness_ratio < 0.8:
                issues.append(f"Data freshness below threshold: {freshness_ratio:.1%}")

            # Check data source diversity
            sources_used = len(self.stats['data_sources_used'])
            if sources_used < 2:
                issues.append("Limited data source diversity")

            # Check recent activity
            if self.stats['data_requests'] == 0:
                issues.append("No recent data requests")

            validation_time = (datetime.now() - start_time).total_seconds()
            is_valid = len(issues) == 0

            if is_valid:
                self.stats['validation_passes'] += 1
            else:
                self.stats['validation_failures'] += 1

            return ValidationResult(
                data_type='data_freshness',
                is_valid=is_valid,
                confidence=freshness_ratio,
                validation_time=validation_time,
                issues=issues,
                source='real_world_data_provider'
            )

        except Exception as e:
            self.logger.error(f"Error validating data freshness: {e}")
            return ValidationResult(
                data_type='data_freshness',
                is_valid=False,
                confidence=0.0,
                validation_time=0.0,
                issues=[f"Validation error: {e}"],
                source='real_world_data_provider'
            )

    async def validate_authentic_content(self, messages: List[Dict[str, Any]]) -> ValidationResult:
        """Validate that messages contain authentic crypto content"""
        try:
            start_time = datetime.now()
            issues = []

            if not messages:
                issues.append("No messages provided for validation")
                return ValidationResult(
                    data_type='authentic_content',
                    is_valid=False,
                    confidence=0.0,
                    validation_time=0.0,
                    issues=issues,
                    source='real_world_data_provider'
                )

            # Analyze message authenticity
            authentic_indicators = 0
            total_messages = len(messages)

            for message in messages:
                text = message.get('text', '').lower()

                # Check for authentic crypto indicators
                if self._has_authentic_crypto_content(text):
                    authentic_indicators += 1

            authenticity_ratio = authentic_indicators / total_messages

            if authenticity_ratio < 0.5:
                issues.append(f"Low authentic content ratio: {authenticity_ratio:.1%}")

            # Check message diversity
            unique_patterns = set()
            for message in messages:
                text = message.get('text', '')
                # Simple pattern extraction (first 50 chars)
                pattern = text[:50].lower().strip()
                unique_patterns.add(pattern)

            diversity_ratio = len(unique_patterns) / max(1, total_messages)
            if diversity_ratio < 0.3:
                issues.append(f"Low message diversity: {diversity_ratio:.1%}")

            validation_time = (datetime.now() - start_time).total_seconds()
            is_valid = len(issues) == 0
            confidence = (authenticity_ratio + diversity_ratio) / 2

            if is_valid:
                self.stats['validation_passes'] += 1
            else:
                self.stats['validation_failures'] += 1

            return ValidationResult(
                data_type='authentic_content',
                is_valid=is_valid,
                confidence=confidence,
                validation_time=validation_time,
                issues=issues,
                source='real_world_data_provider'
            )

        except Exception as e:
            self.logger.error(f"Error validating authentic content: {e}")
            return ValidationResult(
                data_type='authentic_content',
                is_valid=False,
                confidence=0.0,
                validation_time=0.0,
                issues=[f"Validation error: {e}"],
                source='real_world_data_provider'
            )

    def _has_authentic_crypto_content(self, text: str) -> bool:
        """Check if text has authentic crypto content indicators"""
        try:
            # Authentic crypto indicators
            authentic_patterns = [
                # Contract addresses
                r'0x[a-fA-F0-9]{40}',
                r'[1-9A-HJ-NP-Za-km-z]{32,44}',
                # Price mentions with specific values
                r'\$\d+\.\d+',
                # Specific crypto terms
                r'\b(bitcoin|ethereum|solana|cardano|polygon)\b',
                # Trading terms with context
                r'\b(buy|sell|trade|swap)\s+\w+',
                # Technical analysis
                r'\b(support|resistance|breakout|volume)\b'
            ]

            import re
            for pattern in authentic_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking authentic content: {e}")
            return False

    async def validate_performance_benchmarks(self) -> ValidationResult:
        """Validate system performance against research benchmarks"""
        try:
            start_time = datetime.now()
            issues = []

            # Check response time benchmark
            if self.stats['avg_response_time'] > self.validation_benchmarks['max_validation_time']:
                issues.append(f"Response time above benchmark: {self.stats['avg_response_time']:.2f}s")

            # Check cache hit rate (should be reasonable for performance)
            cache_hit_rate = self.stats['cache_hits'] / max(1, self.stats['data_requests'])
            if cache_hit_rate < 0.2:  # At least 20% cache hits expected
                issues.append(f"Low cache hit rate: {cache_hit_rate:.1%}")

            # Check data source reliability
            total_source_requests = sum(self.stats['data_sources_used'].values())
            if total_source_requests == 0:
                issues.append("No data source usage recorded")

            # Check validation success rate
            total_validations = self.stats['validation_passes'] + self.stats['validation_failures']
            if total_validations > 0:
                success_rate = self.stats['validation_passes'] / total_validations
                if success_rate < 0.8:
                    issues.append(f"Low validation success rate: {success_rate:.1%}")

            validation_time = (datetime.now() - start_time).total_seconds()
            is_valid = len(issues) == 0

            # Calculate overall confidence
            confidence_factors = [
                min(1.0, 5.0 / max(0.1, self.stats['avg_response_time'])),  # Response time factor
                cache_hit_rate,  # Cache efficiency
                min(1.0, total_source_requests / 10.0)  # Source usage factor
            ]
            confidence = sum(confidence_factors) / len(confidence_factors)

            if is_valid:
                self.stats['validation_passes'] += 1
            else:
                self.stats['validation_failures'] += 1

            return ValidationResult(
                data_type='performance_benchmarks',
                is_valid=is_valid,
                confidence=confidence,
                validation_time=validation_time,
                issues=issues,
                source='real_world_data_provider'
            )

        except Exception as e:
            self.logger.error(f"Error validating performance benchmarks: {e}")
            return ValidationResult(
                data_type='performance_benchmarks',
                is_valid=False,
                confidence=0.0,
                validation_time=0.0,
                issues=[f"Validation error: {e}"],
                source='real_world_data_provider'
            )

    async def run_comprehensive_validation(self) -> Dict[str, ValidationResult]:
        """Run all validation checks"""
        try:
            self.logger.info("Running comprehensive real-world data validation...")

            # Run all validation checks
            validations = {
                'data_freshness': await self.validate_data_freshness(),
                'performance_benchmarks': await self.validate_performance_benchmarks()
            }

            # Summary
            all_valid = all(result.is_valid for result in validations.values())
            avg_confidence = sum(result.confidence for result in validations.values()) / len(validations)

            self.logger.info(
                f"Validation complete: {'✅ PASS' if all_valid else '❌ FAIL'} "
                f"(confidence: {avg_confidence:.1%})"
            )

            return validations

        except Exception as e:
            self.logger.error(f"Error in comprehensive validation: {e}")
            return {}

    def cleanup_cache(self, max_age_minutes: int = 30):
        """Clean up old cache entries"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

            entries_to_remove = [
                key for key, entry in self.market_data_cache.items()
                if entry['timestamp'] < cutoff_time
            ]

            for key in entries_to_remove:
                del self.market_data_cache[key]

            if entries_to_remove:
                self.logger.debug(f"Cleaned up {len(entries_to_remove)} old cache entries")

        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get real-world data provider statistics"""
        try:
            cache_hit_rate = self.stats['cache_hits'] / max(1, self.stats['data_requests'])
            validation_success_rate = self.stats['validation_passes'] / max(1, self.stats['validation_passes'] + self.stats['validation_failures'])

            return {
                **self.stats,
                'cache_hit_rate': cache_hit_rate,
                'validation_success_rate': validation_success_rate,
                'cache_size': len(self.market_data_cache),
                'data_sources_active': len(self.stats['data_sources_used'])
            }

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return self.stats
```

## Key Features

### 🌐 Live Data Integration

- **Multi-Source Data**: CoinGecko and DexScreener integration
- **Real-time Fetching**: Fresh market data with caching
- **Source Diversity**: Automatic failover between data sources
- **Performance Caching**: 5-minute TTL for efficiency

### ✅ Authentic Content Validation

- **Content Analysis**: Authentic crypto content detection
- **Pattern Recognition**: Contract addresses, prices, trading terms
- **Diversity Checking**: Message uniqueness validation
- **Quality Assurance**: Authenticity ratio monitoring

### 📊 Performance Benchmarks

- **Response Time**: < 5 second validation target
- **Cache Efficiency**: Minimum 20% cache hit rate
- **Success Rate**: > 80% validation success target
- **Source Reliability**: Multi-source usage tracking

### 🔍 Comprehensive Validation

- **Data Freshness**: < 10 minute data age validation
- **Performance Metrics**: Benchmark compliance checking
- **Statistical Analysis**: Confidence scoring and reporting
- **Continuous Monitoring**: Real-time validation status

## Integration Points

- **MessageProcessor**: Authentic content validation
- **PriceEngine**: Live market data integration
- **PerformanceTracker**: Real-world performance validation
- **StatisticalValidationEngine**: Research compliance verification

This implementation ensures the system operates with authentic, real-world data while maintaining research compliance and performance benchmarks.

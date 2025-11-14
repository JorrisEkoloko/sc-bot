# Intelligence Data Enricher - Enhanced Implementation (< 500 lines)

## Overview

The IntelligenceDataEnricher orchestrates cross-component data sharing and enrichment, creating a unified intelligence layer that enhances data as it flows through the pipeline while maintaining backward compatibility.

## Core Functionality

### Cross-Component Integration

- **Data Enrichment Flow**: Immediate market intelligence integration
- **Component Coordination**: Seamless data sharing between all components
- **Intelligence Context**: Comprehensive context storage for outcome learning
- **Backward Compatibility**: All existing workflows preserved

## Implementation

```python
# intelligence/intelligence_data_enricher.py
"""
Cross-component data sharing and enrichment orchestration
Creates unified intelligence layer while maintaining backward compatibility
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass
class EnrichedAddress:
    """Address enriched with comprehensive intelligence"""
    # Original address data
    address: str
    chain: str
    confidence: float

    # Price data enrichment
    symbol: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    liquidity: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None

    # Intelligence enrichment
    market_cap_tier: Optional[str] = None
    risk_level: Optional[str] = None
    channel_reputation: Optional[float] = None
    historical_performance: Optional[Dict[str, Any]] = None

    # Processing metadata
    price_fetch_success: bool = False
    intelligence_timestamp: datetime = None
    enrichment_source: str = 'unknown'

@dataclass
class IntelligenceContext:
    """Comprehensive intelligence context for tracking"""
    # Core intelligence
    integrated_confidence: float
    hdrb_score: float
    market_cap_tier: str
    channel_reputation: float

    # Market intelligence
    market_analysis: Dict[str, Any]
    risk_assessment: str
    volatility_estimate: str

    # Prediction intelligence
    channel_prediction: Optional[str] = None
    prediction_confidence: Optional[float] = None
    price_target: Optional[float] = None
    timeframe: Optional[str] = None

    # Historical context
    historical_performance: Dict[str, Any] = None
    tier_performance: Dict[str, Any] = None

    # Processing metadata
    enrichment_timestamp: datetime = None
    components_used: List[str] = None

class IntelligenceDataEnricher:
    """Orchestrates data enrichment across all components"""

    def __init__(self, price_fetcher, market_analyzer, channel_reputation_manager, signal_scorer):
        self.logger = logging.getLogger(__name__)

        # Injected components
        self.price_fetcher = price_fetcher
        self.market_analyzer = market_analyzer
        self.channel_reputation_manager = channel_reputation_manager
        self.signal_scorer = signal_scorer

        # Intelligence context storage
        self.intelligence_contexts = {}
        self.context_file = Path('data/intelligence_contexts.json')

        # Enrichment cache for performance
        self.enrichment_cache = {}
        self.cache_ttl = timedelta(minutes=5)

        # Statistics
        self.stats = {
            'addresses_enriched': 0,
            'contexts_stored': 0,
            'cache_hits': 0,
            'enrichment_failures': 0,
            'components_integrated': 0
        }

        # Load existing contexts
        asyncio.create_task(self.load_intelligence_contexts())

    async def enrich_addresses(self, message_text: str, message_data: Dict[str, Any]) -> List[EnrichedAddress]:
        """Enrich extracted addresses with comprehensive market intelligence"""
        try:
            # Step 1: Extract addresses using existing AddressExtractor
            from core.address_extractor import AddressExtractor
            address_extractor = AddressExtractor()
            addresses = address_extractor.extract_addresses(message_text)

            if not addresses:
                return []

            enriched_addresses = []

            # Step 2: Enrich each address with intelligence
            for addr_info in addresses:
                enriched_address = await self._enrich_single_address(
                    addr_info, message_data
                )
                enriched_addresses.append(enriched_address)

            self.stats['addresses_enriched'] += len(enriched_addresses)

            self.logger.debug(f"Enriched {len(enriched_addresses)} addresses with intelligence")

            return enriched_addresses

        except Exception as e:
            self.stats['enrichment_failures'] += 1
            self.logger.error(f"Error enriching addresses: {e}")
            return []

    async def _enrich_single_address(self, addr_info: Dict[str, Any],
                                   message_data: Dict[str, Any]) -> EnrichedAddress:
        """Enrich single address with comprehensive intelligence"""
        try:
            address = addr_info['address']
            chain = addr_info['chain']

            # Check cache first
            cache_key = f"{address}:{chain}"
            if cache_key in self.enrichment_cache:
                cache_entry = self.enrichment_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    self.stats['cache_hits'] += 1
                    return cache_entry['data']

            # Create base enriched address
            enriched = EnrichedAddress(
                address=address,
                chain=chain,
                confidence=addr_info.get('confidence', 0.8),
                intelligence_timestamp=datetime.now(),
                enrichment_source='intelligence_enricher'
            )

            # Step 1: Fetch price data with intelligence
            price_result = await self.price_fetcher.fetch_price_data(address, chain)

            if price_result.success:
                # Add price data
                enriched.symbol = price_result.symbol
                enriched.name = price_result.name
                enriched.price = price_result.price
                enriched.market_cap = price_result.market_cap
                enriched.liquidity = price_result.liquidity
                enriched.volume_24h = price_result.volume_24h
                enriched.price_change_24h = price_result.price_change_24h
                enriched.market_cap_tier = price_result.market_cap_tier
                enriched.risk_level = price_result.risk_level
                enriched.price_fetch_success = True

                # Step 2: Add market intelligence
                if self.market_analyzer:
                    market_analysis = self.market_analyzer.analyze_market_context({
                        'market_cap': price_result.market_cap,
                        'liquidity': price_result.liquidity,
                        'volume_24h': price_result.volume_24h,
                        'price_change_24h': price_result.price_change_24h
                    })

                    enriched.market_cap_tier = market_analysis.tier
                    enriched.risk_level = market_analysis.risk_profile

                # Step 3: Add channel reputation
                if self.channel_reputation_manager:
                    channel = message_data.get('channel', 'unknown')
                    reputation_score = await self.channel_reputation_manager.get_channel_score(
                        channel, enriched.market_cap_tier
                    )
                    enriched.channel_reputation = reputation_score

                # Step 4: Add historical performance
                enriched.historical_performance = await self._get_historical_performance(
                    enriched.market_cap_tier, channel
                )

            # Cache the result
            self.enrichment_cache[cache_key] = {
                'data': enriched,
                'timestamp': datetime.now()
            }

            return enriched

        except Exception as e:
            self.logger.error(f"Error enriching address {addr_info.get('address', 'unknown')}: {e}")
            return EnrichedAddress(
                address=addr_info.get('address', ''),
                chain=addr_info.get('chain', ''),
                confidence=0.1,
                intelligence_timestamp=datetime.now(),
                enrichment_source='error'
            )

    async def create_intelligence_context(self, message_data: Dict[str, Any],
                                        filter_result: Dict[str, Any],
                                        enriched_addresses: List[EnrichedAddress]) -> IntelligenceContext:
        """Create comprehensive intelligence context for tracking"""
        try:
            channel = message_data.get('channel', 'unknown')

            # Get market analysis from enriched addresses
            market_analysis = {}
            if enriched_addresses:
                best_address = max(enriched_addresses, key=lambda a: a.confidence)
                if best_address.market_cap:
                    market_analysis = {
                        'market_cap': best_address.market_cap,
                        'tier': best_address.market_cap_tier,
                        'risk_level': best_address.risk_level,
                        'liquidity': best_address.liquidity
                    }

            # Get channel reputation
            channel_reputation = 0.5
            if self.channel_reputation_manager and enriched_addresses:
                best_address = enriched_addresses[0]
                channel_reputation = await self.channel_reputation_manager.get_channel_score(
                    channel, best_address.market_cap_tier
                )

            # Calculate integrated confidence using signal scorer
            integrated_confidence = filter_result.get('relevance_score', 0.5)
            if self.signal_scorer and market_analysis:
                signal_result = await self.signal_scorer.calculate_confidence(
                    filter_result.get('relevance_score', 0.5),
                    {
                        'market_analysis': market_analysis,
                        'channel_reputation': channel_reputation,
                        'historical_performance': {}
                    }
                )
                integrated_confidence = signal_result.integrated_confidence

            # Get historical performance
            historical_performance = {}
            tier_performance = {}
            if enriched_addresses and self.market_analyzer:
                tier = enriched_addresses[0].market_cap_tier
                if tier:
                    tier_performance = self.market_analyzer.get_tier_performance(tier)

            # Create intelligence context
            context = IntelligenceContext(
                integrated_confidence=integrated_confidence,
                hdrb_score=filter_result.get('relevance_score', 0.5),
                market_cap_tier=market_analysis.get('tier', 'unknown'),
                channel_reputation=channel_reputation,
                market_analysis=market_analysis,
                risk_assessment=market_analysis.get('risk_level', 'unknown'),
                volatility_estimate=self._estimate_volatility(market_analysis),
                historical_performance=historical_performance,
                tier_performance=tier_performance,
                enrichment_timestamp=datetime.now(),
                components_used=['price_fetcher', 'market_analyzer', 'channel_reputation', 'signal_scorer']
            )

            return context

        except Exception as e:
            self.logger.error(f"Error creating intelligence context: {e}")
            return IntelligenceContext(
                integrated_confidence=0.5,
                hdrb_score=0.5,
                market_cap_tier='unknown',
                channel_reputation=0.5,
                market_analysis={},
                risk_assessment='unknown',
                volatility_estimate='unknown',
                enrichment_timestamp=datetime.now(),
                components_used=[]
            )

    async def store_intelligence_context(self, tracking_id: str, context: IntelligenceContext):
        """Store intelligence context for outcome-based learning"""
        try:
            # Convert to serializable format
            context_data = asdict(context)
            context_data['enrichment_timestamp'] = context.enrichment_timestamp.isoformat()

            # Store in memory
            self.intelligence_contexts[tracking_id] = context_data

            # Save to persistence
            await self.save_intelligence_contexts()

            self.stats['contexts_stored'] += 1

            self.logger.debug(f"Stored intelligence context for tracking {tracking_id}")

        except Exception as e:
            self.logger.error(f"Error storing intelligence context: {e}")

    async def get_intelligence_context(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """Get stored intelligence context for tracking"""
        try:
            return self.intelligence_contexts.get(tracking_id)

        except Exception as e:
            self.logger.error(f"Error getting intelligence context: {e}")
            return None

    async def enrich_tracking_completion(self, tracking_id: str,
                                       final_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich tracking completion with learning updates"""
        try:
            # Get stored intelligence context
            intelligence_context = await self.get_intelligence_context(tracking_id)

            if not intelligence_context:
                return final_results

            # Update channel reputation based on outcomes
            channel = final_results.get('channel', 'unknown')
            market_cap_tier = intelligence_context.get('market_cap_tier', 'unknown')

            performance_data = {
                'roi': final_results.get('final_roi', 0.0),
                'market_cap_tier': market_cap_tier,
                'tracking_duration': final_results.get('tracking_duration', 0.0),
                'predicted_confidence': intelligence_context.get('integrated_confidence', 0.5),
                'prediction_accuracy': self._calculate_prediction_accuracy(
                    intelligence_context, final_results
                )
            }

            if self.channel_reputation_manager:
                await self.channel_reputation_manager.update_performance(channel, performance_data)

            # Update market cap tier performance
            if self.market_analyzer:
                await self.market_analyzer.update_tier_performance(
                    market_cap_tier,
                    final_results.get('final_roi', 0.0),
                    final_results.get('tracking_duration', 0.0)
                )

            # Create enriched results
            enriched_results = {
                **final_results,
                'intelligence_context': intelligence_context,
                'learning_updates': {
                    'channel_reputation_updated': True,
                    'market_cap_tier_stats_updated': True,
                    'prediction_accuracy': performance_data['prediction_accuracy'],
                    'enrichment_timestamp': datetime.now().isoformat()
                }
            }

            return enriched_results

        except Exception as e:
            self.logger.error(f"Error enriching tracking completion: {e}")
            return final_results

    async def _get_historical_performance(self, market_cap_tier: str,
                                        channel: str) -> Dict[str, Any]:
        """Get historical performance data for tier and channel"""
        try:
            performance = {}

            # Get tier performance
            if self.market_analyzer:
                tier_performance = self.market_analyzer.get_tier_performance(market_cap_tier)
                performance['tier'] = tier_performance

            # Get channel performance
            if self.channel_reputation_manager:
                channel_performance = await self.channel_reputation_manager.get_channel_score(channel)
                performance['channel'] = channel_performance

            return performance

        except Exception as e:
            self.logger.error(f"Error getting historical performance: {e}")
            return {}

    def _estimate_volatility(self, market_analysis: Dict[str, Any]) -> str:
        """Estimate volatility based on market analysis"""
        try:
            tier = market_analysis.get('tier', 'unknown')

            volatility_map = {
                'micro': 'very_high',
                'small': 'high',
                'large': 'medium'
            }

            return volatility_map.get(tier, 'unknown')

        except Exception as e:
            self.logger.error(f"Error estimating volatility: {e}")
            return 'unknown'

    def _calculate_prediction_accuracy(self, intelligence_context: Dict[str, Any],
                                     final_results: Dict[str, Any]) -> float:
        """Calculate prediction accuracy based on outcomes"""
        try:
            predicted_confidence = intelligence_context.get('integrated_confidence', 0.5)
            actual_roi = final_results.get('final_roi', 0.0)

            # Simple accuracy calculation
            # High confidence should correlate with positive outcomes
            if predicted_confidence > 0.7 and actual_roi > 10:
                return 1.0  # Accurate high confidence prediction
            elif predicted_confidence < 0.4 and actual_roi < 0:
                return 1.0  # Accurate low confidence prediction
            elif 0.4 <= predicted_confidence <= 0.7:
                return 0.7  # Neutral prediction
            else:
                return 0.3  # Inaccurate prediction

        except Exception as e:
            self.logger.error(f"Error calculating prediction accuracy: {e}")
            return 0.5

    async def save_intelligence_contexts(self):
        """Save intelligence contexts to persistence"""
        try:
            self.context_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.context_file, 'w') as f:
                json.dump({
                    'intelligence_contexts': self.intelligence_contexts,
                    'last_updated': datetime.now().isoformat(),
                    'stats': self.stats
                }, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving intelligence contexts: {e}")

    async def load_intelligence_contexts(self):
        """Load intelligence contexts from persistence"""
        try:
            if self.context_file.exists():
                with open(self.context_file, 'r') as f:
                    data = json.load(f)

                self.intelligence_contexts = data.get('intelligence_contexts', {})
                saved_stats = data.get('stats', {})
                self.stats.update(saved_stats)

                self.logger.info(f"Loaded {len(self.intelligence_contexts)} intelligence contexts")

        except Exception as e:
            self.logger.error(f"Error loading intelligence contexts: {e}")

    def cleanup_old_contexts(self, max_age_days: int = 30):
        """Clean up old intelligence contexts"""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            contexts_to_remove = []
            for tracking_id, context in self.intelligence_contexts.items():
                try:
                    timestamp_str = context.get('enrichment_timestamp', '')
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff_date:
                            contexts_to_remove.append(tracking_id)
                except Exception:
                    # Remove contexts with invalid timestamps
                    contexts_to_remove.append(tracking_id)

            for tracking_id in contexts_to_remove:
                del self.intelligence_contexts[tracking_id]

            if contexts_to_remove:
                self.logger.info(f"Cleaned up {len(contexts_to_remove)} old intelligence contexts")

        except Exception as e:
            self.logger.error(f"Error cleaning up old contexts: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get intelligence data enricher statistics"""
        return {
            **self.stats,
            'contexts_stored_count': len(self.intelligence_contexts),
            'cache_size': len(self.enrichment_cache),
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['addresses_enriched']),
            'enrichment_success_rate': (self.stats['addresses_enriched'] - self.stats['enrichment_failures']) / max(1, self.stats['addresses_enriched'])
        }
```

## Key Features

### 🔄 Cross-Component Integration

- **Unified Data Flow**: Seamless data sharing between all components
- **Intelligence Enrichment**: Immediate market context integration
- **Component Coordination**: Orchestrates price, market, reputation, and signal data
- **Backward Compatibility**: All existing workflows preserved

### 🧠 Comprehensive Intelligence Context

- **Market Intelligence**: Cap tier, risk assessment, volatility estimates
- **Channel Intelligence**: Reputation scores, historical performance
- **Signal Intelligence**: Integrated confidence, HDRB scores
- **Prediction Intelligence**: Sentiment, targets, timeframes

### 📊 Outcome-Based Learning

- **Context Storage**: Comprehensive intelligence context preservation
- **Learning Updates**: Channel reputation and tier performance updates
- **Prediction Accuracy**: Correlation between predictions and outcomes
- **Performance Analytics**: Success rate tracking and optimization

### ⚡ Performance Optimization

- **Enrichment Caching**: 5-minute TTL for repeated addresses
- **Efficient Lookup**: Fast component integration
- **Batch Processing**: Multiple addresses in single cycle
- **Memory Management**: Automatic cleanup of old contexts

## Integration Points

- **AddressExtractor**: Receives addresses for enrichment
- **PriceEngine**: Fetches price data with intelligence
- **MarketAnalyzer**: Provides market cap intelligence
- **ChannelReputation**: Supplies reputation scores
- **SignalScorer**: Calculates integrated confidence
- **PerformanceTracker**: Stores and retrieves intelligence contexts

This implementation creates a unified intelligence layer that enhances data throughout the pipeline while maintaining full backward compatibility with existing components.

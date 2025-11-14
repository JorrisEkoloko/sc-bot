# Channel Database Reader - Enhanced Implementation (< 500 lines)

## Overview

The ChannelDatabaseReader integrates with the channel discovery system, reading discovered channels from the database and facilitating their integration into the active monitoring system.

## Core Functionality

### Discovery Integration

- **Database Reading**: Access discovered channels data
- **Quality Filtering**: Score-based channel selection
- **Integration Coordination**: Seamless addition to monitoring
- **Status Management**: Track integration progress

## Implementation

```python
# discovery/channel_database_reader.py
"""
Channel discovery integration and database reading
Facilitates discovered channel integration into monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class DiscoveredChannel:
    """Discovered channel with metadata"""
    username: str
    channel_name: str
    member_count: int
    total_score: float
    crypto_relevance: float
    activity_score: float
    quality_score: float
    discovery_date: datetime
    integration_status: str  # pending, integrated, failed, skipped

@dataclass
class IntegrationResult:
    """Result of channel integration"""
    channel: DiscoveredChannel
    success: bool
    integration_time: float
    error: Optional[str] = None
    messages_found: int = 0

class ChannelDatabaseReader:
    """Channel discovery database integration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Discovery data files
        self.discovered_channels_file = Path("live_data_cache/discovered_channels.json")
        self.integration_status_file = Path("live_data_cache/integration_status.json")

        # Integration settings
        self.min_integration_score = 0.5
        self.max_channels_per_batch = 5
        self.integration_cooldown = timedelta(hours=24)

        # Integration status tracking
        self.integration_status = {}

        # Statistics
        self.stats = {
            'channels_discovered': 0,
            'channels_integrated': 0,
            'integration_attempts': 0,
            'integration_failures': 0,
            'last_integration_time': None
        }

        # Load existing data
        asyncio.create_task(self.load_integration_status())

    async def get_pending_channels_for_integration(self) -> List[DiscoveredChannel]:
        """Get channels ready for integration"""
        try:
            discovered_channels = await self._load_discovered_channels()

            if not discovered_channels:
                return []

            pending_channels = []

            for username, channel_data in discovered_channels.items():
                if self._should_skip_metadata_entry(username):
                    continue

                # Check if already integrated or failed recently
                if await self._is_integration_blocked(username):
                    continue

                # Check quality threshold
                total_score = channel_data.get('total_score', 0)
                if total_score < self.min_integration_score:
                    continue

                # Create discovered channel object
                discovered_channel = DiscoveredChannel(
                    username=username,
                    channel_name=channel_data.get('channel_name', username),
                    member_count=channel_data.get('member_count', 0),
                    total_score=total_score,
                    crypto_relevance=channel_data.get('crypto_relevance', 0),
                    activity_score=channel_data.get('activity_score', 0),
                    quality_score=channel_data.get('quality_score', 0),
                    discovery_date=self._parse_discovery_date(channel_data.get('discovery_date')),
                    integration_status='pending'
                )

                pending_channels.append(discovered_channel)

            # Sort by score (highest first) and limit
            pending_channels.sort(key=lambda c: c.total_score, reverse=True)
            return pending_channels[:self.max_channels_per_batch]

        except Exception as e:
            self.logger.error(f"Error getting pending channels: {e}")
            return []

    async def integrate_discovered_channels(self, telegram_client, active_channels_list) -> List[IntegrationResult]:
        """Integrate discovered channels into active monitoring"""
        try:
            pending_channels = await self.get_pending_channels_for_integration()

            if not pending_channels:
                self.logger.info("No channels pending integration")
                return []

            self.logger.info(f"Integrating {len(pending_channels)} discovered channels...")

            integration_results = []

            for channel in pending_channels:
                try:
                    result = await self._integrate_single_channel(
                        channel, telegram_client, active_channels_list
                    )
                    integration_results.append(result)

                    # Update integration status
                    await self._update_integration_status(channel.username, result)

                except Exception as e:
                    self.logger.error(f"Error integrating {channel.username}: {e}")

                    failed_result = IntegrationResult(
                        channel=channel,
                        success=False,
                        integration_time=0,
                        error=str(e)
                    )
                    integration_results.append(failed_result)
                    await self._update_integration_status(channel.username, failed_result)

            # Update statistics
            successful_integrations = sum(1 for r in integration_results if r.success)
            self.stats['integration_attempts'] += len(integration_results)
            self.stats['channels_integrated'] += successful_integrations
            self.stats['integration_failures'] += len(integration_results) - successful_integrations
            self.stats['last_integration_time'] = datetime.now()

            self.logger.info(
                f"Integration complete: {successful_integrations}/{len(integration_results)} successful"
            )

            return integration_results

        except Exception as e:
            self.logger.error(f"Error in channel integration: {e}")
            return []

    async def _integrate_single_channel(self, channel: DiscoveredChannel,
                                      telegram_client, active_channels_list) -> IntegrationResult:
        """Integrate a single discovered channel"""
        try:
            start_time = datetime.now()

            # Check if channel already in active list
            channel_id = f"@{channel.username}"
            if any(ch.get('id') == channel_id for ch in active_channels_list):
                return IntegrationResult(
                    channel=channel,
                    success=False,
                    integration_time=0,
                    error="Channel already in active monitoring"
                )

            # Test channel access
            try:
                entity = await telegram_client.get_entity(channel_id)

                # Test message access
                message_count = 0
                async for message in telegram_client.iter_messages(entity, limit=3):
                    if message.text:
                        message_count += 1

                # Create channel configuration
                channel_config = {
                    "enabled": True,
                    "channel_id": channel_id,
                    "channel_name": channel.username,
                    "priority": 2,  # Lower priority than manual channels
                    "filters": {
                        "min_views": 10,
                        "keywords": ["crypto", "token", "coin", "signal"],
                        "sentiment_threshold": -0.7
                    },
                    "discovered": True,
                    "discovery_score": channel.total_score,
                    "discovery_date": channel.discovery_date.isoformat(),
                    "integration_date": datetime.now().isoformat()
                }

                # Add to active channels list (this would be done by the calling system)
                active_channels_list.append({
                    "name": channel.username,
                    "id": channel_id,
                    "config": channel_config,
                    "entity": entity,
                    "discovered": True
                })

                integration_time = (datetime.now() - start_time).total_seconds()

                return IntegrationResult(
                    channel=channel,
                    success=True,
                    integration_time=integration_time,
                    messages_found=message_count
                )

            except Exception as access_error:
                return IntegrationResult(
                    channel=channel,
                    success=False,
                    integration_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Channel access failed: {access_error}"
                )

        except Exception as e:
            return IntegrationResult(
                channel=channel,
                success=False,
                integration_time=0,
                error=str(e)
            )

    async def _load_discovered_channels(self) -> Dict[str, Any]:
        """Load discovered channels from database file"""
        try:
            if not self.discovered_channels_file.exists():
                return {}

            with open(self.discovered_channels_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update statistics
            channel_count = len([k for k in data.keys() if not self._should_skip_metadata_entry(k)])
            self.stats['channels_discovered'] = channel_count

            return data

        except Exception as e:
            self.logger.error(f"Error loading discovered channels: {e}")
            return {}

    def _should_skip_metadata_entry(self, key: str) -> bool:
        """Check if key is metadata entry to skip"""
        metadata_keys = ['last_updated', 'discovery_stats', 'total_channels']
        return key.startswith('last_') or key in metadata_keys

    async def _is_integration_blocked(self, username: str) -> bool:
        """Check if integration is blocked for channel"""
        try:
            if username not in self.integration_status:
                return False

            status = self.integration_status[username]

            # Check if already successfully integrated
            if status.get('status') == 'integrated':
                return True

            # Check cooldown for failed integrations
            if status.get('status') == 'failed':
                last_attempt = status.get('last_attempt')
                if last_attempt:
                    last_attempt_time = datetime.fromisoformat(last_attempt)
                    if datetime.now() - last_attempt_time < self.integration_cooldown:
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking integration block: {e}")
            return False

    def _parse_discovery_date(self, date_str: Optional[str]) -> datetime:
        """Parse discovery date string"""
        try:
            if date_str:
                return datetime.fromisoformat(date_str)
            return datetime.now()

        except Exception as e:
            self.logger.error(f"Error parsing discovery date: {e}")
            return datetime.now()

    async def _update_integration_status(self, username: str, result: IntegrationResult):
        """Update integration status for channel"""
        try:
            self.integration_status[username] = {
                'status': 'integrated' if result.success else 'failed',
                'last_attempt': datetime.now().isoformat(),
                'integration_time': result.integration_time,
                'error': result.error,
                'messages_found': result.messages_found,
                'score': result.channel.total_score
            }

            await self.save_integration_status()

        except Exception as e:
            self.logger.error(f"Error updating integration status: {e}")

    async def save_integration_status(self):
        """Save integration status to file"""
        try:
            self.integration_status_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.integration_status_file, 'w') as f:
                json.dump({
                    'integration_status': self.integration_status,
                    'stats': self.stats,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving integration status: {e}")

    async def load_integration_status(self):
        """Load integration status from file"""
        try:
            if self.integration_status_file.exists():
                with open(self.integration_status_file, 'r') as f:
                    data = json.load(f)

                self.integration_status = data.get('integration_status', {})
                saved_stats = data.get('stats', {})
                self.stats.update(saved_stats)

                self.logger.info(f"Loaded integration status for {len(self.integration_status)} channels")

        except Exception as e:
            self.logger.error(f"Error loading integration status: {e}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database and integration statistics"""
        try:
            pending_count = 0
            integrated_count = 0
            failed_count = 0

            for status_data in self.integration_status.values():
                status = status_data.get('status', 'unknown')
                if status == 'integrated':
                    integrated_count += 1
                elif status == 'failed':
                    failed_count += 1
                else:
                    pending_count += 1

            return {
                **self.stats,
                'pending_integration': pending_count,
                'integrated_channels': integrated_count,
                'failed_integrations': failed_count,
                'integration_success_rate': integrated_count / max(1, self.stats['integration_attempts']),
                'database_file_exists': self.discovered_channels_file.exists()
            }

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return self.stats

    async def cleanup_old_integration_data(self, max_age_days: int = 30):
        """Clean up old integration status data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            channels_to_remove = []
            for username, status_data in self.integration_status.items():
                try:
                    last_attempt = status_data.get('last_attempt')
                    if last_attempt:
                        last_attempt_time = datetime.fromisoformat(last_attempt)
                        if last_attempt_time < cutoff_date and status_data.get('status') == 'failed':
                            channels_to_remove.append(username)
                except Exception:
                    # Remove entries with invalid timestamps
                    channels_to_remove.append(username)

            for username in channels_to_remove:
                del self.integration_status[username]

            if channels_to_remove:
                await self.save_integration_status()
                self.logger.info(f"Cleaned up {len(channels_to_remove)} old integration records")

        except Exception as e:
            self.logger.error(f"Error cleaning up integration data: {e}")

    def get_integration_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for channel integration"""
        try:
            recommendations = []

            # Analyze integration patterns
            successful_integrations = [
                status for status in self.integration_status.values()
                if status.get('status') == 'integrated'
            ]

            if successful_integrations:
                avg_score = sum(s.get('score', 0) for s in successful_integrations) / len(successful_integrations)
                avg_messages = sum(s.get('messages_found', 0) for s in successful_integrations) / len(successful_integrations)

                recommendations.append({
                    'type': 'score_threshold',
                    'recommendation': f"Channels with score > {avg_score:.2f} have higher success rate",
                    'data': {'avg_successful_score': avg_score}
                })

                recommendations.append({
                    'type': 'activity_indicator',
                    'recommendation': f"Successful channels average {avg_messages:.1f} recent messages",
                    'data': {'avg_messages': avg_messages}
                })

            # Integration timing recommendations
            if self.stats['integration_failures'] > 0:
                failure_rate = self.stats['integration_failures'] / self.stats['integration_attempts']
                if failure_rate > 0.3:
                    recommendations.append({
                        'type': 'integration_timing',
                        'recommendation': f"High failure rate ({failure_rate:.1%}) - consider increasing score threshold",
                        'data': {'failure_rate': failure_rate}
                    })

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
```

## Key Features

### 🔍 Discovery Database Integration

- **Channel Reading**: Access discovered channels from JSON database
- **Quality Filtering**: Score-based channel selection (>0.5 threshold)
- **Batch Processing**: Maximum 5 channels per integration batch
- **Status Tracking**: Comprehensive integration status management

### 🎯 Smart Integration Logic

- **Duplicate Prevention**: Avoid re-integrating existing channels
- **Access Validation**: Test channel accessibility before integration
- **Cooldown Management**: 24-hour cooldown for failed integrations
- **Configuration Generation**: Automatic channel config creation

### 📊 Integration Analytics

- **Success Tracking**: Integration success/failure rates
- **Performance Metrics**: Integration time and message counts
- **Recommendations**: Data-driven integration suggestions
- **Statistics**: Comprehensive integration analytics

### ⚡ Performance Optimization

- **Metadata Filtering**: Skip non-channel entries efficiently
- **Batch Limiting**: Prevent system overload
- **Status Caching**: Fast integration status lookup
- **Cleanup Management**: Automatic old data cleanup

## Integration Points

- **TelegramMonitor**: Provides Telegram client for channel testing
- **ActiveCoinsCollector**: Historical scanning for integrated channels
- **ChannelReputation**: Initial reputation setup for new channels
- **Main Application**: Channel configuration and monitoring integration

This implementation provides seamless integration of discovered channels into the active monitoring system while maintaining quality control and performance optimization.

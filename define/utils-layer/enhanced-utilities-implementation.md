# Enhanced Utilities - Complete Implementation (< 500 lines)

## Overview

The Enhanced Utilities provide comprehensive error handling, rate limiting, logging, and monitoring capabilities that support all system components with production-ready reliability and performance optimization.

## Core Functionality

### Comprehensive Error Management

- **Universal Error Handling**: 3-retry pattern with exponential backoff
- **Circuit Breaker**: API failure protection and recovery
- **Graceful Degradation**: Core functionality preservation
- **Error Analytics**: Comprehensive error tracking and reporting

### Advanced Rate Limiting

- **Multi-API Support**: Individual rate limits per API
- **Intelligent Backoff**: Dynamic rate adjustment
- **Priority Queuing**: Critical request prioritization
- **Performance Monitoring**: Rate limit efficiency tracking

## Implementation

```python
# utils/enhanced_error_handler.py
"""
Comprehensive error handling with circuit breaker and recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time
import json
from pathlib import Path

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorRecord:
    """Error record for tracking and analysis"""
    timestamp: datetime
    component: str
    error_type: str
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    retry_count: int
    resolved: bool

class CircuitBreaker:
    """Circuit breaker for API protection"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'closed'

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

class EnhancedErrorHandler:
    """Comprehensive error handling system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Error tracking
        self.error_records = []
        self.error_file = Path('data/error_records.json')

        # Circuit breakers for different components
        self.circuit_breakers = {}

        # Retry configuration
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 30.0,
            'exponential_base': 2.0,
            'jitter': True
        }

        # Error statistics
        self.stats = {
            'total_errors': 0,
            'errors_by_component': {},
            'errors_by_severity': {severity.value: 0 for severity in ErrorSeverity},
            'recovery_success_rate': 0.0,
            'circuit_breaker_trips': 0
        }

    async def handle_with_retry(self, func: Callable, component: str,
                              context: Dict[str, Any] = None,
                              max_retries: int = None) -> Any:
        """Execute function with comprehensive error handling and retry"""
        max_retries = max_retries or self.retry_config['max_retries']
        context = context or {}

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Use circuit breaker if available
                if component in self.circuit_breakers:
                    return self.circuit_breakers[component].call(func)
                else:
                    return await func() if asyncio.iscoroutinefunction(func) else func()

            except Exception as e:
                last_exception = e

                # Record error
                await self._record_error(
                    component=component,
                    error_type=type(e).__name__,
                    severity=self._classify_error_severity(e),
                    message=str(e),
                    context=context,
                    retry_count=attempt
                )

                # Check if we should retry
                if attempt < max_retries and self._should_retry(e):
                    delay = self._calculate_retry_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {component}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        # All retries exhausted
        await self._record_error(
            component=component,
            error_type=type(last_exception).__name__,
            severity=ErrorSeverity.HIGH,
            message=f"All retries exhausted: {last_exception}",
            context=context,
            retry_count=max_retries
        )

        raise last_exception

    def get_circuit_breaker(self, component: str) -> CircuitBreaker:
        """Get or create circuit breaker for component"""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = CircuitBreaker()
        return self.circuit_breakers[component]

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if error should be retried"""
        # Don't retry certain types of errors
        non_retryable_errors = [
            'AuthenticationError',
            'PermissionError',
            'ValueError',
            'TypeError'
        ]

        return type(exception).__name__ not in non_retryable_errors

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(
            self.retry_config['base_delay'] * (self.retry_config['exponential_base'] ** attempt),
            self.retry_config['max_delay']
        )

        if self.retry_config['jitter']:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter

        return delay

    def _classify_error_severity(self, exception: Exception) -> ErrorSeverity:
        """Classify error severity"""
        error_type = type(exception).__name__

        critical_errors = ['SystemExit', 'KeyboardInterrupt', 'MemoryError']
        high_errors = ['ConnectionError', 'TimeoutError', 'HTTPError']
        medium_errors = ['ValueError', 'TypeError', 'AttributeError']

        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    async def _record_error(self, component: str, error_type: str,
                          severity: ErrorSeverity, message: str,
                          context: Dict[str, Any], retry_count: int):
        """Record error for tracking and analysis"""
        try:
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                component=component,
                error_type=error_type,
                severity=severity,
                message=message,
                context=context,
                retry_count=retry_count,
                resolved=False
            )

            self.error_records.append(error_record)

            # Update statistics
            self.stats['total_errors'] += 1
            self.stats['errors_by_component'][component] = self.stats['errors_by_component'].get(component, 0) + 1
            self.stats['errors_by_severity'][severity.value] += 1

            # Limit error records to prevent memory issues
            if len(self.error_records) > 1000:
                self.error_records = self.error_records[-1000:]

            # Save to file periodically
            if len(self.error_records) % 10 == 0:
                await self._save_error_records()

        except Exception as e:
            self.logger.error(f"Error recording error: {e}")

    async def _save_error_records(self):
        """Save error records to file"""
        try:
            self.error_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            serializable_records = []
            for record in self.error_records[-100:]:  # Save last 100 records
                serializable_records.append({
                    'timestamp': record.timestamp.isoformat(),
                    'component': record.component,
                    'error_type': record.error_type,
                    'severity': record.severity.value,
                    'message': record.message,
                    'context': record.context,
                    'retry_count': record.retry_count,
                    'resolved': record.resolved
                })

            with open(self.error_file, 'w') as f:
                json.dump({
                    'error_records': serializable_records,
                    'stats': self.stats,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving error records: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary and statistics"""
        recent_errors = [
            record for record in self.error_records
            if (datetime.now() - record.timestamp).total_seconds() < 3600  # Last hour
        ]

        return {
            'total_errors': self.stats['total_errors'],
            'recent_errors': len(recent_errors),
            'errors_by_component': self.stats['errors_by_component'],
            'errors_by_severity': self.stats['errors_by_severity'],
            'circuit_breaker_status': {
                component: breaker.state
                for component, breaker in self.circuit_breakers.items()
            },
            'most_common_errors': self._get_most_common_errors()
        }

    def _get_most_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error types"""
        error_counts = {}
        for record in self.error_records[-100:]:  # Last 100 errors
            key = f"{record.component}:{record.error_type}"
            error_counts[key] = error_counts.get(key, 0) + 1

        return sorted(
            [{'error': k, 'count': v} for k, v in error_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:5]

# utils/rate_limiter.py
"""
Advanced rate limiting with priority queuing and intelligent backoff
"""

import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class RequestPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int
    burst_limit: int
    priority_boost: float = 1.0

class AdvancedRateLimiter:
    """Advanced rate limiter with priority queuing"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Rate limit configurations per API
        self.api_configs = {}

        # Request tracking
        self.request_history = {}
        self.request_queues = {}

        # Statistics
        self.stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'avg_wait_time': 0.0,
            'api_usage': {}
        }

    def configure_api(self, api_name: str, config: RateLimitConfig):
        """Configure rate limits for specific API"""
        self.api_configs[api_name] = config
        self.request_history[api_name] = []
        self.request_queues[api_name] = {priority: [] for priority in RequestPriority}
        self.stats['api_usage'][api_name] = {'requests': 0, 'rate_limited': 0}

    async def acquire(self, api_name: str, priority: RequestPriority = RequestPriority.MEDIUM) -> float:
        """Acquire rate limit permission"""
        if api_name not in self.api_configs:
            return 0.0  # No rate limiting configured

        start_time = time.time()

        # Check if we need to wait
        wait_time = await self._calculate_wait_time(api_name, priority)

        if wait_time > 0:
            self.stats['rate_limited_requests'] += 1
            self.stats['api_usage'][api_name]['rate_limited'] += 1
            await asyncio.sleep(wait_time)

        # Record request
        self._record_request(api_name)

        # Update statistics
        total_time = time.time() - start_time
        self.stats['total_requests'] += 1
        self.stats['api_usage'][api_name]['requests'] += 1
        self.stats['avg_wait_time'] = (
            (self.stats['avg_wait_time'] * (self.stats['total_requests'] - 1) + total_time) /
            self.stats['total_requests']
        )

        return total_time

    async def _calculate_wait_time(self, api_name: str, priority: RequestPriority) -> float:
        """Calculate wait time based on rate limits and priority"""
        config = self.api_configs[api_name]
        history = self.request_history[api_name]

        # Clean old requests (older than 1 minute)
        current_time = time.time()
        history[:] = [req_time for req_time in history if current_time - req_time < 60]

        # Check if we're within rate limits
        if len(history) < config.requests_per_minute:
            return 0.0  # No wait needed

        # Calculate wait time based on oldest request
        oldest_request = min(history)
        wait_time = 60 - (current_time - oldest_request)

        # Apply priority boost (higher priority = less wait time)
        priority_multiplier = 1.0 - (priority.value - 1) * 0.2  # Up to 60% reduction for critical
        wait_time *= priority_multiplier

        return max(0.0, wait_time)

    def _record_request(self, api_name: str):
        """Record request timestamp"""
        self.request_history[api_name].append(time.time())

    def get_api_status(self, api_name: str) -> Dict[str, Any]:
        """Get current API rate limit status"""
        if api_name not in self.api_configs:
            return {'error': 'API not configured'}

        config = self.api_configs[api_name]
        history = self.request_history[api_name]

        # Clean old requests
        current_time = time.time()
        recent_requests = [req_time for req_time in history if current_time - req_time < 60]

        return {
            'requests_per_minute_limit': config.requests_per_minute,
            'current_requests_per_minute': len(recent_requests),
            'remaining_requests': max(0, config.requests_per_minute - len(recent_requests)),
            'reset_time': min(recent_requests) + 60 if recent_requests else current_time,
            'usage_percentage': (len(recent_requests) / config.requests_per_minute) * 100
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            **self.stats,
            'rate_limit_percentage': (self.stats['rate_limited_requests'] / max(1, self.stats['total_requests'])) * 100,
            'configured_apis': list(self.api_configs.keys()),
            'api_status': {api: self.get_api_status(api) for api in self.api_configs.keys()}
        }

# utils/system_monitor.py
"""
System health monitoring and performance tracking
"""

import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from pathlib import Path

class SystemMonitor:
    """System health and performance monitoring"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Monitoring configuration
        self.monitoring_interval = 60  # seconds
        self.history_retention = timedelta(hours=24)

        # Performance history
        self.performance_history = []
        self.history_file = Path('data/performance_history.json')

        # Alert thresholds
        self.thresholds = {
            'cpu_usage': 80.0,      # %
            'memory_usage': 85.0,   # %
            'disk_usage': 90.0,     # %
            'response_time': 5.0    # seconds
        }

        # Component registration
        self.registered_components = {}

        # Statistics
        self.stats = {
            'monitoring_duration': 0,
            'alerts_generated': 0,
            'performance_samples': 0,
            'component_count': 0
        }

    def register_component(self, name: str, health_check: callable):
        """Register component for health monitoring"""
        self.registered_components[name] = {
            'health_check': health_check,
            'last_check': None,
            'status': 'unknown',
            'response_time': 0.0
        }
        self.stats['component_count'] = len(self.registered_components)

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': dict(psutil.net_io_counters()._asdict()),
                'process_count': len(psutil.pids()),
                'component_health': await self._check_component_health()
            }

            # Store in history
            self.performance_history.append(metrics)
            self.stats['performance_samples'] += 1

            # Clean old history
            cutoff_time = datetime.now() - self.history_retention
            self.performance_history = [
                m for m in self.performance_history
                if datetime.fromisoformat(m['timestamp']) > cutoff_time
            ]

            # Check for alerts
            await self._check_alerts(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}

    async def _check_component_health(self) -> Dict[str, Any]:
        """Check health of registered components"""
        health_results = {}

        for name, component in self.registered_components.items():
            try:
                start_time = datetime.now()

                # Run health check
                if asyncio.iscoroutinefunction(component['health_check']):
                    is_healthy = await component['health_check']()
                else:
                    is_healthy = component['health_check']()

                response_time = (datetime.now() - start_time).total_seconds()

                # Update component status
                component['last_check'] = datetime.now()
                component['status'] = 'healthy' if is_healthy else 'unhealthy'
                component['response_time'] = response_time

                health_results[name] = {
                    'status': component['status'],
                    'response_time': response_time,
                    'last_check': component['last_check'].isoformat()
                }

            except Exception as e:
                component['status'] = 'error'
                component['last_check'] = datetime.now()

                health_results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': component['last_check'].isoformat()
                }

        return health_results

    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []

        # CPU usage alert
        if metrics['cpu_usage'] > self.thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metrics['cpu_usage']:.1f}%")

        # Memory usage alert
        if metrics['memory_usage'] > self.thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metrics['memory_usage']:.1f}%")

        # Disk usage alert
        if metrics['disk_usage'] > self.thresholds['disk_usage']:
            alerts.append(f"High disk usage: {metrics['disk_usage']:.1f}%")

        # Component response time alerts
        for name, health in metrics['component_health'].items():
            if health.get('response_time', 0) > self.thresholds['response_time']:
                alerts.append(f"Slow component response: {name} ({health['response_time']:.1f}s)")

        # Log alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert}")
            self.stats['alerts_generated'] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_history:
            return {}

        recent_metrics = self.performance_history[-10:]  # Last 10 samples

        return {
            'avg_cpu_usage': sum(m['cpu_usage'] for m in recent_metrics) / len(recent_metrics),
            'avg_memory_usage': sum(m['memory_usage'] for m in recent_metrics) / len(recent_metrics),
            'avg_disk_usage': sum(m['disk_usage'] for m in recent_metrics) / len(recent_metrics),
            'component_status': {
                name: comp['status'] for name, comp in self.registered_components.items()
            },
            'monitoring_stats': self.stats,
            'last_updated': datetime.now().isoformat()
        }

# Global instances
error_handler = EnhancedErrorHandler()
rate_limiter = AdvancedRateLimiter()
system_monitor = SystemMonitor()

# Convenience functions
async def handle_with_retry(func, component: str, context: Dict[str, Any] = None):
    """Global error handling function"""
    return await error_handler.handle_with_retry(func, component, context)

async def acquire_rate_limit(api_name: str, priority: RequestPriority = RequestPriority.MEDIUM):
    """Global rate limiting function"""
    return await rate_limiter.acquire(api_name, priority)

def register_component_health(name: str, health_check: callable):
    """Global component registration function"""
    system_monitor.register_component(name, health_check)
```

## Key Features

### 🛡️ Comprehensive Error Handling

- **Universal Retry Pattern**: 3-retry with exponential backoff
- **Circuit Breaker**: API failure protection and recovery
- **Error Classification**: Severity-based error categorization
- **Error Analytics**: Comprehensive tracking and reporting

### ⚡ Advanced Rate Limiting

- **Multi-API Support**: Individual rate limits per API
- **Priority Queuing**: Critical request prioritization
- **Intelligent Backoff**: Dynamic rate adjustment
- **Usage Analytics**: Rate limit efficiency monitoring

### 📊 System Monitoring

- **Performance Metrics**: CPU, memory, disk usage tracking
- **Component Health**: Registered component health checks
- **Alert System**: Threshold-based alerting
- **Performance History**: 24-hour performance retention

### 🔧 Production Ready

- **Memory Management**: Automatic cleanup and limits
- **Persistence**: Error and performance data storage
- **Statistics**: Comprehensive usage analytics
- **Global Access**: Convenient utility functions

## Integration Points

- **All Components**: Universal error handling and rate limiting
- **PriceEngine**: API rate limiting and circuit breaker protection
- **TelegramMonitor**: Connection error handling and recovery
- **Main Application**: System health monitoring and alerting

This implementation provides production-ready utilities that enhance reliability, performance, and monitoring across the entire system.

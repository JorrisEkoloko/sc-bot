# Main System Orchestration - Deep Implementation Guide

## Overview

Clean, efficient system orchestration that coordinates all components in a production-ready crypto intelligence system with comprehensive monitoring and error handling.

## Architecture Design

### Core Responsibilities

- Component lifecycle management and coordination
- Async task orchestration and monitoring
- System health monitoring and alerting
- Graceful startup and shutdown procedures
- Resource management and optimization

### Component Structure

```
SystemOrchestration/
├── system_coordinator.py    # Main system coordination
├── task_manager.py         # Async task management
├── health_monitor.py       # System health monitoring
├── resource_manager.py     # Resource optimization
└── lifecycle_manager.py    # Startup/shutdown management
```

## Main System Coordinator

### 1. Core System Class

```python
class CryptoIntelligenceSystem:
    """Clean orchestration of all crypto intelligence components"""

    def __init__(self, config_path='config/settings.json'):
        # System identification
        self.system_id = str(uuid.uuid4())[:8]
        self.startup_time = datetime.now()

        # Configuration management
        self.config = Config.load(config_path)
        self.logger = setup_logger('crypto_intelligence', self.config.logging)

        # System state management
        self.running = False
        self.initialization_complete = False
        self.shutdown_initiated = False

        # Component initialization
        self._initialize_core_components()
        self._initialize_intelligence_components()
        self._initialize_system_services()

        # Task management
        self.task_manager = TaskManager(self.logger)
        self.health_monitor = HealthMonitor(self.logger)
        self.resource_manager = ResourceManager(self.config.resources)

        # Performance tracking
        self.system_stats = SystemStats()
        self.performance_metrics = PerformanceMetrics()

        # Signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _initialize_core_components(self):
        """Initialize all core system components"""
        try:
            # Core pipeline components
            self.telegram_monitor = TelegramMonitor(self.config.telegram)
            self.message_processor = MessageProcessor(self.config.processing)
            self.address_extractor = AddressExtractor()
            self.price_engine = PriceEngine(self.config.apis)
            self.performance_tracker = PerformanceTracker(self.config.tracking)
            self.data_output = DataOutput(self.config.output)

            self.logger.info("✅ Core components initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize core components: {e}")
            raise

    def _initialize_intelligence_components(self):
        """Initialize intelligence layer components"""
        try:
            # Intelligence components
            self.market_analyzer = MarketAnalyzer()
            self.channel_reputation = ChannelReputation()
            self.signal_scorer = SignalScorer(self.config.intelligence)

            # Connect intelligence components
            self.message_processor.set_intelligence_components(
                self.market_analyzer, self.channel_reputation, self.signal_scorer
            )

            self.performance_tracker.set_components(
                self.price_engine, self.channel_reputation
            )

            self.logger.info("✅ Intelligence components initialized and connected")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize intelligence components: {e}")
            raise

    def _initialize_system_services(self):
        """Initialize system-level services"""
        try:
            # Error handling and recovery
            self.error_handler = ErrorHandler(self.config.error_handling)

            # Monitoring and alerting
            self.alert_manager = AlertManager(self.config.alerts)

            # Data backup and recovery
            self.backup_manager = BackupManager(self.config.backup)

            self.logger.info("✅ System services initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize system services: {e}")
            raise
```

### 2. System Lifecycle Management

```python
class LifecycleManager:
    """Manages system startup and shutdown procedures"""

    async def startup_sequence(self, system):
        """Execute comprehensive startup sequence"""
        try:
            self.logger.info("🚀 Starting Crypto Intelligence System...")

            # Phase 1: Component initialization
            await self._initialize_components(system)

            # Phase 2: Connection establishment
            await self._establish_connections(system)

            # Phase 3: Data recovery and validation
            await self._recover_system_state(system)

            # Phase 4: Health checks
            await self._perform_startup_health_checks(system)

            # Phase 5: Background task startup
            await self._start_background_tasks(system)

            system.initialization_complete = True
            system.running = True

            self.logger.info("✅ System startup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ System startup failed: {e}")
            await self._cleanup_partial_startup(system)
            return False

    async def _initialize_components(self, system):
        """Initialize all system components"""
        # Telegram monitor initialization
        if not await system.telegram_monitor.initialize():
            raise Exception("Telegram monitor initialization failed")

        # Price engine initialization
        await system.price_engine.initialize_apis()

        # Performance tracker data loading
        await system.performance_tracker.load_tracking_data()

        # Data output initialization
        await system.data_output.initialize_outputs()

    async def _establish_connections(self, system):
        """Establish external connections"""
        # Telegram connection
        if not await system.telegram_monitor.connect():
            raise Exception("Telegram connection failed")

        # Google Sheets connection (if configured)
        await system.data_output.test_connections()

        # API health checks
        await system.price_engine.validate_api_connections()

    async def _recover_system_state(self, system):
        """Recover system state from previous session"""
        # Load tracking data
        await system.performance_tracker.load_tracking_data()

        # Load channel reputation data
        await system.channel_reputation.load_performance_data()

        # Load market analysis history
        await system.market_analyzer.load_performance_data()

    async def shutdown_sequence(self, system):
        """Execute graceful shutdown sequence"""
        try:
            self.logger.info("🛑 Initiating graceful system shutdown...")
            system.shutdown_initiated = True

            # Phase 1: Stop accepting new work
            system.running = False

            # Phase 2: Complete current operations
            await self._complete_pending_operations(system)

            # Phase 3: Save system state
            await self._save_system_state(system)

            # Phase 4: Close connections
            await self._close_connections(system)

            # Phase 5: Cleanup resources
            await self._cleanup_resources(system)

            self.logger.info("✅ System shutdown completed successfully")

        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")
```

## Task Management System

### 1. Async Task Manager

```python
class TaskManager:
    """Manages all background tasks with monitoring and recovery"""

    def __init__(self, logger):
        self.logger = logger
        self.tasks = {}
        self.task_stats = {}
        self.restart_policies = {}

    async def start_all_tasks(self, system):
        """Start all background tasks with monitoring"""
        try:
            # Core processing tasks
            self.tasks['telegram_monitoring'] = asyncio.create_task(
                self._run_telegram_monitoring_loop(system)
            )

            self.tasks['message_processing'] = asyncio.create_task(
                self._run_message_processing_loop(system)
            )

            self.tasks['price_updates'] = asyncio.create_task(
                self._run_price_update_loop(system)
            )

            self.tasks['data_output'] = asyncio.create_task(
                self._run_data_output_loop(system)
            )

            # System maintenance tasks
            self.tasks['health_monitoring'] = asyncio.create_task(
                self._run_health_monitoring_loop(system)
            )

            self.tasks['resource_management'] = asyncio.create_task(
                self._run_resource_management_loop(system)
            )

            self.tasks['backup_management'] = asyncio.create_task(
                self._run_backup_loop(system)
            )

            # Set up task monitoring
            for task_name, task in self.tasks.items():
                task.add_done_callback(
                    lambda t, name=task_name: self._handle_task_completion(name, t)
                )

            self.logger.info(f"✅ Started {len(self.tasks)} background tasks")

        except Exception as e:
            self.logger.error(f"❌ Failed to start background tasks: {e}")
            raise

    async def _run_telegram_monitoring_loop(self, system):
        """Telegram monitoring task with error recovery"""
        task_name = 'telegram_monitoring'

        while system.running:
            try:
                await system.telegram_monitor.start_monitoring()

            except Exception as e:
                self.logger.error(f"❌ Telegram monitoring error: {e}")
                await self._handle_task_error(task_name, e, system)

                if system.running:
                    await asyncio.sleep(30)  # Wait before restart

    async def _run_message_processing_loop(self, system):
        """Message processing task with performance monitoring"""
        task_name = 'message_processing'

        while system.running:
            try:
                # Get next message from queue
                message_data = await system.telegram_monitor.get_next_message()

                if message_data:
                    # Process message through pipeline
                    start_time = time.time()
                    await system.process_crypto_signal(message_data)

                    # Update performance metrics
                    processing_time = time.time() - start_time
                    system.performance_metrics.update_processing_time(processing_time)
                    system.system_stats.messages_processed += 1

            except Exception as e:
                self.logger.error(f"❌ Message processing error: {e}")
                system.system_stats.errors += 1
                await asyncio.sleep(1)

    async def _handle_task_error(self, task_name, error, system):
        """Handle task errors with restart policies"""
        self.task_stats[task_name] = self.task_stats.get(task_name, {
            'errors': 0,
            'restarts': 0,
            'last_error': None
        })

        self.task_stats[task_name]['errors'] += 1
        self.task_stats[task_name]['last_error'] = str(error)

        # Apply restart policy
        restart_policy = self.restart_policies.get(task_name, {
            'max_restarts': 5,
            'restart_delay': 30,
            'exponential_backoff': True
        })

        if self.task_stats[task_name]['restarts'] < restart_policy['max_restarts']:
            self.task_stats[task_name]['restarts'] += 1

            delay = restart_policy['restart_delay']
            if restart_policy['exponential_backoff']:
                delay *= (2 ** (self.task_stats[task_name]['restarts'] - 1))

            self.logger.warning(
                f"⚠️ Restarting {task_name} in {delay} seconds "
                f"(attempt {self.task_stats[task_name]['restarts']})"
            )

            await asyncio.sleep(delay)
        else:
            self.logger.error(f"❌ {task_name} exceeded maximum restart attempts")
            system.running = False
```

### 2. Health Monitoring System

```python
class HealthMonitor:
    """Comprehensive system health monitoring"""

    def __init__(self, logger):
        self.logger = logger
        self.health_metrics = {}
        self.alert_thresholds = {}
        self.last_health_check = None

    async def run_health_monitoring_loop(self, system):
        """Continuous health monitoring with alerting"""
        while system.running:
            try:
                # Collect health metrics
                health_status = await self._collect_health_metrics(system)

                # Evaluate health status
                alerts = self._evaluate_health_status(health_status)

                # Generate alerts if needed
                if alerts:
                    await self._generate_health_alerts(alerts, system)

                # Update health history
                self._update_health_history(health_status)

                # Log periodic health summary
                if self._should_log_health_summary():
                    await self._log_health_summary(health_status, system)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_health_metrics(self, system):
        """Collect comprehensive health metrics"""
        health_metrics = {
            'timestamp': datetime.now(),
            'system_uptime': (datetime.now() - system.startup_time).total_seconds(),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage(),
            'queue_sizes': await self._get_queue_sizes(system),
            'component_health': await self._check_component_health(system),
            'performance_metrics': self._get_performance_metrics(system),
            'error_rates': self._calculate_error_rates(system)
        }

        return health_metrics

    async def _check_component_health(self, system):
        """Check health of individual components"""
        component_health = {}

        # Telegram monitor health
        component_health['telegram_monitor'] = {
            'connected': system.telegram_monitor.is_connected,
            'queue_size': system.telegram_monitor.get_queue_size(),
            'last_message': system.telegram_monitor.stats.get('last_message_time')
        }

        # Price engine health
        component_health['price_engine'] = {
            'api_health': system.price_engine.get_api_health_status(),
            'cache_hit_rate': system.price_engine.get_cache_hit_rate(),
            'avg_response_time': system.price_engine.get_avg_response_time()
        }

        # Performance tracker health
        component_health['performance_tracker'] = {
            'active_tracking': len(system.performance_tracker.get_active_tracking()),
            'update_success_rate': system.performance_tracker.get_update_success_rate(),
            'memory_usage': system.performance_tracker.get_memory_usage()
        }

        # Data output health
        component_health['data_output'] = {
            'csv_success_rate': system.data_output.get_csv_success_rate(),
            'sheets_success_rate': system.data_output.get_sheets_success_rate(),
            'pending_writes': system.data_output.get_pending_write_count()
        }

        return component_health
```

## Resource Management

### 1. Resource Optimizer

```python
class ResourceManager:
    """Manages system resources and optimization"""

    def __init__(self, config):
        self.config = config
        self.resource_limits = config.limits
        self.optimization_enabled = config.optimization_enabled

    async def run_resource_management_loop(self, system):
        """Continuous resource monitoring and optimization"""
        while system.running:
            try:
                # Monitor resource usage
                resource_status = await self._monitor_resources(system)

                # Apply optimizations if needed
                if self.optimization_enabled:
                    await self._apply_optimizations(resource_status, system)

                # Check resource limits
                await self._enforce_resource_limits(resource_status, system)

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"❌ Resource management error: {e}")
                await asyncio.sleep(300)

    async def _monitor_resources(self, system):
        """Monitor system resource usage"""
        return {
            'memory': {
                'used': psutil.virtual_memory().used,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'disk': {
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            }
        }

    async def _apply_optimizations(self, resource_status, system):
        """Apply resource optimizations"""
        # Memory optimization
        if resource_status['memory']['percent'] > 80:
            await self._optimize_memory_usage(system)

        # Cache optimization
        if resource_status['memory']['percent'] > 70:
            await self._optimize_caches(system)

        # Cleanup optimization
        if resource_status['disk']['percent'] > 85:
            await self._cleanup_old_data(system)

    async def _optimize_memory_usage(self, system):
        """Optimize memory usage across components"""
        # Cleanup tracking data
        await system.performance_tracker.cleanup_old_tracking()

        # Optimize price engine caches
        await system.price_engine.optimize_caches()

        # Cleanup message processor caches
        system.message_processor.cleanup_caches()

        # Force garbage collection
        import gc
        gc.collect()
```

## Performance Monitoring

### 1. Performance Metrics Collector

```python
class PerformanceMetrics:
    """Collects and analyzes system performance metrics"""

    def __init__(self):
        self.metrics_history = []
        self.current_metrics = {}
        self.performance_targets = {
            'message_processing_time': 60.0,  # seconds
            'price_fetch_success_rate': 0.70,
            'tracking_completion_rate': 0.95,
            'data_output_success_rate': 0.99
        }

    def update_processing_time(self, processing_time):
        """Update message processing time metrics"""
        if 'processing_times' not in self.current_metrics:
            self.current_metrics['processing_times'] = []

        self.current_metrics['processing_times'].append(processing_time)

        # Keep only last 1000 measurements
        if len(self.current_metrics['processing_times']) > 1000:
            self.current_metrics['processing_times'] = \
                self.current_metrics['processing_times'][-1000:]

    def calculate_performance_summary(self):
        """Calculate comprehensive performance summary"""
        if not self.current_metrics:
            return {}

        processing_times = self.current_metrics.get('processing_times', [])

        summary = {
            'avg_processing_time': np.mean(processing_times) if processing_times else 0,
            'max_processing_time': np.max(processing_times) if processing_times else 0,
            'p95_processing_time': np.percentile(processing_times, 95) if processing_times else 0,
            'processing_time_target_met': (
                np.mean(processing_times) < self.performance_targets['message_processing_time']
                if processing_times else False
            )
        }

        return summary

    def check_performance_targets(self):
        """Check if performance targets are being met"""
        summary = self.calculate_performance_summary()
        target_status = {}

        for target_name, target_value in self.performance_targets.items():
            if target_name in summary:
                target_status[target_name] = {
                    'target': target_value,
                    'actual': summary[target_name],
                    'met': summary[target_name] <= target_value
                }

        return target_status
```

### 2. System Statistics Tracker

```python
class SystemStats:
    """Tracks comprehensive system statistics"""

    def __init__(self):
        self.start_time = datetime.now()
        self.messages_processed = 0
        self.signals_detected = 0
        self.tokens_tracked = 0
        self.data_written = 0
        self.errors = 0

        # Component-specific stats
        self.component_stats = {}

        # Performance history
        self.hourly_stats = []
        self.daily_stats = []

    def get_current_stats(self):
        """Get current system statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'messages_processed': self.messages_processed,
            'signals_detected': self.signals_detected,
            'tokens_tracked': self.tokens_tracked,
            'data_written': self.data_written,
            'errors': self.errors,
            'messages_per_hour': (self.messages_processed / (uptime / 3600)) if uptime > 0 else 0,
            'error_rate': (self.errors / max(1, self.messages_processed)),
            'signal_detection_rate': (self.signals_detected / max(1, self.messages_processed))
        }

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        current_stats = self.get_current_stats()

        report = {
            'system_overview': current_stats,
            'component_performance': self.component_stats,
            'performance_trends': self._calculate_trends(),
            'recommendations': self._generate_recommendations(current_stats)
        }

        return report

    def _generate_recommendations(self, stats):
        """Generate performance optimization recommendations"""
        recommendations = []

        if stats['error_rate'] > 0.05:  # > 5% error rate
            recommendations.append("High error rate detected - investigate error patterns")

        if stats['messages_per_hour'] < 10:  # Low message volume
            recommendations.append("Low message volume - check Telegram connections")

        if stats['signal_detection_rate'] < 0.1:  # < 10% signal detection
            recommendations.append("Low signal detection - review filtering thresholds")

        return recommendations
```

## Integration Interfaces

### System Control Interface

```python
async def start(self) -> bool:
    """
    Start the complete crypto intelligence system
    Output: Success status
    """
```

### Health Check Interface

```python
async def get_system_health(self) -> Dict[str, Any]:
    """
    Get comprehensive system health status
    Output: Health metrics and status
    """
```

### Performance Interface

```python
async def get_performance_metrics(self) -> Dict[str, Any]:
    """
    Get system performance metrics
    Output: Performance statistics and trends
    """
```

## Configuration Management

### System Configuration

```json
{
  "system": {
    "max_memory_usage": "2GB",
    "max_cpu_usage": 80,
    "health_check_interval": 60,
    "performance_monitoring": true
  },
  "tasks": {
    "restart_policies": {
      "telegram_monitoring": {
        "max_restarts": 5,
        "restart_delay": 30,
        "exponential_backoff": true
      }
    }
  },
  "alerts": {
    "error_rate_threshold": 0.05,
    "memory_usage_threshold": 0.85,
    "response_time_threshold": 60
  }
}
```

## Performance Targets

### System Performance

- **< 500 Lines Main.py**: Clean orchestration code
- **99%+ Uptime**: System availability target
- **< 60 Second Processing**: End-to-end message processing
- **< 2GB Memory Usage**: Total system memory footprint

### Reliability Metrics

- **< 5% Error Rate**: System-wide error tolerance
- **95%+ Task Completion**: Background task success rate
- **< 5 Second Recovery**: Error recovery time
- **100% Data Integrity**: No data loss during operations

"""Shutdown coordinator - handles graceful system shutdown.

FIXED: Issue #5 - Resource Lifecycle Conflict
Uses CleanupCoordinator for guaranteed resource cleanup.

Based on RAII pattern and resource pool management.
"""
from typing import Set, List, Tuple, Callable, Dict, Any
from utils.logger import get_logger
from infrastructure.lifecycle.cleanup_coordinator import CleanupCoordinator


class ShutdownCoordinator:
    """
    Coordinates graceful shutdown of all system components.
    
    FIXED: Issue #5 - Uses CleanupCoordinator for guaranteed cleanup
    
    Ensures:
    - All components are cleaned up properly
    - No double-cleanup occurs
    - Failures in one component don't prevent others from cleaning up
    - Proper logging of cleanup status
    """
    
    def __init__(self, logger=None):
        """Initialize shutdown coordinator."""
        self.logger = logger or get_logger('ShutdownCoordinator')
        self.cleanup_coordinator = CleanupCoordinator('SystemShutdown')
    
    async def shutdown_all(self, components: dict):
        """
        Shutdown all system components gracefully.
        
        FIXED: Issue #5 - Uses CleanupCoordinator for guaranteed cleanup
        
        Args:
            components: Dictionary of component_name -> component_instance
        """
        self.logger.info("Shutting down system...")
        
        # Register all components with cleanup coordinator
        self._register_components(components)
        
        # Execute coordinated cleanup with timeout
        try:
            await self.cleanup_coordinator.cleanup_all(timeout=30.0)
            self.logger.info("✅ Shutdown complete")
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
            # Get status to see what failed
            status = self.cleanup_coordinator.get_status()
            failed = [name for name, state in status.items() if state == 'error']
            if failed:
                self.logger.error(f"Failed to cleanup: {', '.join(failed)}")
            raise
    
    def _register_components(self, components: dict):
        """
        Register all components with cleanup coordinator.
        
        FIXED: Issue #5 - Centralized component registration
        
        Args:
            components: Dictionary of component_name -> component_instance
        """
        # Priority queue
        if components.get('priority_queue'):
            self.cleanup_coordinator.register_component(
                'priority_queue',
                components['priority_queue'],
                cleanup_method='stop_consumer',
                is_async=True
            )
        
        # Telegram monitor
        if components.get('telegram_monitor'):
            self.cleanup_coordinator.register_component(
                'telegram_monitor',
                components['telegram_monitor'],
                cleanup_method='disconnect',
                is_async=True
            )
        
        # Pair resolver
        if components.get('pair_resolver'):
            self.cleanup_coordinator.register_component(
                'pair_resolver',
                components['pair_resolver'],
                cleanup_method='close',
                is_async=True
            )
        
        # Price engine
        if components.get('price_engine'):
            self.cleanup_coordinator.register_component(
                'price_engine',
                components['price_engine'],
                cleanup_method='close',
                is_async=True
            )
        
        # Historical price retriever
        if components.get('historical_price_retriever'):
            self.cleanup_coordinator.register_component(
                'historical_price_retriever',
                components['historical_price_retriever'],
                cleanup_method='close',
                is_async=True
            )
        
        # Dead token detector
        if components.get('dead_token_detector'):
            self.cleanup_coordinator.register_component(
                'dead_token_detector',
                components['dead_token_detector'],
                cleanup_method='close',
                is_async=True
            )
        
        # Reputation scheduler
        if components.get('reputation_scheduler'):
            self.cleanup_coordinator.register_component(
                'reputation_scheduler',
                components['reputation_scheduler'],
                cleanup_method='stop',
                is_async=True
            )
        
        # Performance tracker (sync save)
        if components.get('performance_tracker'):
            self.cleanup_coordinator.register_component(
                'performance_tracker',
                components['performance_tracker'],
                cleanup_method='save_to_disk',
                is_async=False
            )
        
        # Outcome tracker (sync save)
        if components.get('outcome_tracker'):
            def save_outcomes(tracker):
                tracker.repository.save(tracker.outcomes)
            
            self.cleanup_coordinator.register_component(
                'outcome_tracker',
                components['outcome_tracker'],
                cleanup_method='save_outcomes',
                is_async=False
            )
        
        # Reputation engine (sync save)
        if components.get('reputation_engine'):
            self.cleanup_coordinator.register_component(
                'reputation_engine',
                components['reputation_engine'],
                cleanup_method='save_reputations',
                is_async=False
            )
        
        # Historical bootstrap (sync save)
        if components.get('historical_bootstrap'):
            self.cleanup_coordinator.register_component(
                'historical_bootstrap',
                components['historical_bootstrap'],
                cleanup_method='save_all',
                is_async=False
            )
    
    def _build_async_cleanup_tasks(self, components: dict) -> List[Tuple[str, Callable]]:
        """Build list of async cleanup tasks."""
        tasks = []
        
        # Priority queue cleanup
        if self._should_cleanup('priority_queue', components):
            priority_queue = components.get('priority_queue')
            if priority_queue and hasattr(priority_queue, 'is_running') and priority_queue.is_running():
                async def cleanup_priority_queue():
                    await priority_queue.stop_consumer(timeout=30.0)
                    stats = priority_queue.get_stats()
                    if self.logger:
                        self.logger.info(
                            f"Priority queue final stats: "
                            f"enqueued={stats['total_enqueued']}, "
                            f"processed={stats['total_processed']}, "
                            f"dropped={stats['total_dropped']}"
                        )
                    self._cleanup_completed.add('priority_queue')
                
                tasks.append(('priority_queue', cleanup_priority_queue()))
        
        # Telegram monitor cleanup
        if self._should_cleanup('telegram_monitor', components):
            telegram_monitor = components.get('telegram_monitor')
            if telegram_monitor:
                async def cleanup_telegram():
                    await telegram_monitor.disconnect()
                    self._cleanup_completed.add('telegram_monitor')
                
                tasks.append(('telegram_monitor', cleanup_telegram()))
        
        # Pair resolver cleanup
        if self._should_cleanup('pair_resolver', components):
            pair_resolver = components.get('pair_resolver')
            if pair_resolver:
                async def cleanup_pair_resolver():
                    await pair_resolver.close()
                    self._cleanup_completed.add('pair_resolver')
                
                tasks.append(('pair_resolver', cleanup_pair_resolver()))
        
        # Price engine cleanup
        if self._should_cleanup('price_engine', components):
            price_engine = components.get('price_engine')
            if price_engine:
                async def cleanup_price_engine():
                    await price_engine.close()
                    self._cleanup_completed.add('price_engine')
                
                tasks.append(('price_engine', cleanup_price_engine()))
        
        # Historical price retriever cleanup
        if self._should_cleanup('historical_price_retriever', components):
            historical_price_retriever = components.get('historical_price_retriever')
            if historical_price_retriever:
                async def cleanup_historical_price():
                    await historical_price_retriever.close()
                    self._cleanup_completed.add('historical_price_retriever')
                
                tasks.append(('historical_price_retriever', cleanup_historical_price()))
        
        # Dead token detector cleanup
        if self._should_cleanup('dead_token_detector', components):
            dead_token_detector = components.get('dead_token_detector')
            if dead_token_detector:
                async def cleanup_dead_token():
                    await dead_token_detector.close()
                    self._cleanup_completed.add('dead_token_detector')
                
                tasks.append(('dead_token_detector', cleanup_dead_token()))
        
        # Reputation scheduler cleanup
        if self._should_cleanup('reputation_scheduler', components):
            reputation_scheduler = components.get('reputation_scheduler')
            if reputation_scheduler and hasattr(reputation_scheduler, 'is_running') and reputation_scheduler.is_running():
                async def cleanup_reputation_scheduler():
                    await reputation_scheduler.stop()
                    self._cleanup_completed.add('reputation_scheduler')
                
                tasks.append(('reputation_scheduler', cleanup_reputation_scheduler()))
        
        return tasks
    
    def _build_sync_cleanup_tasks(self, components: dict) -> List[Tuple[str, Callable]]:
        """Build list of sync cleanup tasks."""
        tasks = []
        
        # Performance tracker cleanup
        if self._should_cleanup('performance_tracker', components):
            performance_tracker = components.get('performance_tracker')
            if performance_tracker:
                def cleanup_perf():
                    performance_tracker.save_to_disk()
                    self._cleanup_completed.add('performance_tracker')
                
                tasks.append(('performance_tracker', cleanup_perf))
        
        # Outcome tracker cleanup
        if self._should_cleanup('outcome_tracker', components):
            outcome_tracker = components.get('outcome_tracker')
            if outcome_tracker:
                def cleanup_outcome():
                    outcome_tracker.repository.save(outcome_tracker.outcomes)
                    self._cleanup_completed.add('outcome_tracker')
                
                tasks.append(('outcome_tracker', cleanup_outcome))
        
        # Reputation engine cleanup
        if self._should_cleanup('reputation_engine', components):
            reputation_engine = components.get('reputation_engine')
            if reputation_engine:
                def cleanup_reputation():
                    reputation_engine.save_reputations()
                    self._cleanup_completed.add('reputation_engine')
                
                tasks.append(('reputation_engine', cleanup_reputation))
        
        # Historical bootstrap cleanup
        if self._should_cleanup('historical_bootstrap', components):
            historical_bootstrap = components.get('historical_bootstrap')
            if historical_bootstrap:
                def cleanup_bootstrap():
                    historical_bootstrap.save_all()
                    self._cleanup_completed.add('historical_bootstrap')
                
                tasks.append(('historical_bootstrap', cleanup_bootstrap))
        
        return tasks
    
    async def _execute_async_cleanups(self, tasks: List[Tuple[str, Callable]]):
        """Execute all async cleanup tasks."""
        for name, task in tasks:
            try:
                await task
                self.logger.debug(f"Successfully cleaned up {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {name}: {e}")
                # Continue to next cleanup
    
    def _execute_sync_cleanups(self, tasks: List[Tuple[str, Callable]]):
        """Execute all sync cleanup tasks."""
        for name, cleanup_func in tasks:
            try:
                cleanup_func()
                self.logger.debug(f"Successfully cleaned up {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {name}: {e}")
                # Continue to next cleanup
    
    def get_status(self) -> Dict[str, str]:
        """
        Get cleanup status of all components.
        
        Returns:
            Dictionary of component_name -> state
        """
        return self.cleanup_coordinator.get_status()
    
    def reset(self):
        """Reset cleanup tracking (for testing or restart scenarios)."""
        self.cleanup_coordinator.reset()

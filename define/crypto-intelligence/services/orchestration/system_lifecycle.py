"""System lifecycle manager - handles system state and transitions."""
import asyncio
from enum import Enum
from typing import Optional
from utils.logger import get_logger


class SystemState(Enum):
    """System states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    RESTARTING = "restarting"


class SystemLifecycle:
    """
    Manages system lifecycle and state transitions.
    
    Ensures thread-safe state management with atomic transitions.
    """
    
    def __init__(self, logger=None):
        """Initialize system lifecycle manager."""
        self.logger = logger or get_logger('SystemLifecycle')
        self._state = SystemState.STOPPED
        self._shutdown_lock: Optional[asyncio.Lock] = None
        self._global_init_lock: Optional[asyncio.Lock] = None
    
    async def ensure_locks_initialized(self):
        """Initialize async locks safely (thread-safe)."""
        if self._shutdown_lock is not None:
            return
        
        # Use module-level lock for initialization
        if self._global_init_lock is None:
            self._global_init_lock = asyncio.Lock()
        
        async with self._global_init_lock:
            # Double-check after acquiring lock
            if self._shutdown_lock is not None:
                return
            
            # Create lock directly in async context
            self._shutdown_lock = asyncio.Lock()
    
    async def transition_state(
        self,
        from_states: list[SystemState],
        to_state: SystemState
    ) -> bool:
        """
        Atomically transition state with validation.
        
        Args:
            from_states: List of valid source states
            to_state: Target state
            
        Returns:
            True if transition succeeded, False otherwise
        """
        await self.ensure_locks_initialized()
        
        async with self._shutdown_lock:
            if self._state not in from_states:
                self.logger.warning(
                    f"Cannot transition from {self._state.value} to {to_state.value}. "
                    f"Valid sources: {[s.value for s in from_states]}"
                )
                return False
            
            old_state = self._state
            self._state = to_state
            self.logger.debug(f"State transition: {old_state.value} → {to_state.value}")
            return True
    
    async def get_state(self) -> SystemState:
        """Get current state atomically."""
        await self.ensure_locks_initialized()
        
        async with self._shutdown_lock:
            return self._state
    
    async def can_start(self) -> tuple[bool, Optional[str]]:
        """
        Check if system can start.
        
        Returns:
            Tuple of (can_start, reason_if_not)
        """
        state = await self.get_state()
        
        if state == SystemState.RUNNING:
            return False, "already_running"
        elif state == SystemState.STOPPING:
            return False, "currently_stopping"
        elif state == SystemState.STARTING:
            return False, "already_starting"
        elif state == SystemState.RESTARTING:
            return False, "currently_restarting"
        
        return True, None
    
    async def can_stop(self) -> tuple[bool, Optional[str]]:
        """
        Check if system can stop.
        
        Returns:
            Tuple of (can_stop, reason_if_not)
        """
        state = await self.get_state()
        
        if state == SystemState.STOPPED:
            return False, "already_stopped"
        elif state == SystemState.STOPPING:
            return False, "already_stopping"
        
        return True, None
    
    async def request_start(self) -> bool:
        """
        Request system start with state validation.
        
        Returns:
            True if start request accepted
        """
        can_start, reason = await self.can_start()
        
        if not can_start:
            if reason == "already_running":
                self.logger.info("System already running")
            else:
                self.logger.warning(f"Cannot start: {reason}")
            return False
        
        # Transition to starting
        success = await self.transition_state(
            [SystemState.STOPPED],
            SystemState.STARTING
        )
        
        return success
    
    async def request_stop(self) -> bool:
        """
        Request system stop with state validation.
        
        Returns:
            True if stop request accepted
        """
        can_stop, reason = await self.can_stop()
        
        if not can_stop:
            if reason == "already_stopped":
                self.logger.debug("System already stopped")
            else:
                self.logger.warning(f"Cannot stop: {reason}")
            return False
        
        # Transition to stopping
        state = await self.get_state()
        success = await self.transition_state(
            [SystemState.RUNNING, SystemState.STARTING, SystemState.RESTARTING],
            SystemState.STOPPING
        )
        
        return success
    
    async def mark_running(self) -> bool:
        """Mark system as running after successful start."""
        return await self.transition_state(
            [SystemState.STARTING],
            SystemState.RUNNING
        )
    
    async def mark_stopped(self) -> bool:
        """Mark system as stopped after successful shutdown."""
        state = await self.get_state()
        return await self.transition_state(
            [SystemState.STOPPING, SystemState.STARTING, SystemState.RESTARTING],
            SystemState.STOPPED
        )
    
    async def request_restart(self) -> bool:
        """Request system restart."""
        state = await self.get_state()
        
        if state == SystemState.RUNNING:
            return await self.transition_state(
                [SystemState.RUNNING],
                SystemState.RESTARTING
            )
        
        return False
    
    def is_running(self) -> bool:
        """Check if system is in running state (non-async check)."""
        return self._state == SystemState.RUNNING
    
    def is_stopped(self) -> bool:
        """Check if system is in stopped state (non-async check)."""
        return self._state == SystemState.STOPPED

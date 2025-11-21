"""System state manager with validated transitions.

Integrates state machine validation with system lifecycle management.
"""
import asyncio
from typing import Optional
from utils.state_machine import SystemStateMachine, SystemState
from utils.logger import get_logger


class StateManager:
    """
    Manages system state with validated transitions.
    
    Provides high-level interface for system lifecycle management
    with automatic validation and error handling.
    """
    
    def __init__(self, name: str = "CryptoIntelligence"):
        """
        Initialize state manager.
        
        Args:
            name: System name
        """
        self.name = name
        self.state_machine = SystemStateMachine(name)
        self.logger = get_logger(f'StateManager.{name}')
    
    async def request_start(self) -> bool:
        """
        Request system start with validation.
        
        Returns:
            True if start request accepted
        """
        current = await self.state_machine.get_state()
        
        if current == SystemState.RUNNING:
            self.logger.info("System already running")
            return True
        
        if current == SystemState.STOPPING:
            raise RuntimeError(
                "Cannot start while stopping - wait for shutdown to complete"
            )
        
        if current == SystemState.STARTING:
            raise RuntimeError("Already starting")
        
        success = await self.state_machine.start()
        if not success:
            raise RuntimeError(f"Cannot start from state: {current.value}")
        
        return True
    
    async def mark_running(self) -> bool:
        """
        Mark system as running after successful startup.
        
        Returns:
            True if transition succeeded
            
        Raises:
            RuntimeError: If transition fails
        """
        success = await self.state_machine.mark_running()
        if not success:
            raise RuntimeError("Failed to transition to running state")
        return True
    
    async def request_stop(self) -> bool:
        """
        Request system stop with validation.
        
        Returns:
            True if stop request accepted
        """
        current = await self.state_machine.get_state()
        
        if current == SystemState.STOPPED:
            self.logger.debug("System already stopped")
            return True
        
        success = await self.state_machine.stop()
        if not success:
            self.logger.warning(f"Stop request rejected from state {current.value}")
            return False
        
        return True
    
    async def mark_stopped(self) -> bool:
        """
        Mark system as stopped after successful shutdown.
        
        Returns:
            True if transition succeeded
        """
        return await self.state_machine.mark_stopped()
    
    async def mark_error(self, error: Exception) -> bool:
        """
        Mark system as in error state.
        
        Args:
            error: Exception that caused error state
            
        Returns:
            True if transition succeeded
        """
        return await self.state_machine.mark_error(error)
    
    async def get_state(self) -> SystemState:
        """Get current system state."""
        return await self.state_machine.get_state()
    
    def get_state_sync(self) -> SystemState:
        """Get current system state (non-thread-safe)."""
        return self.state_machine.get_state_sync()
    
    def is_running(self) -> bool:
        """Check if system is running (quick check)."""
        return self.state_machine.get_state_sync() == SystemState.RUNNING
    
    def is_stopped(self) -> bool:
        """Check if system is stopped (quick check)."""
        return self.state_machine.get_state_sync() == SystemState.STOPPED
    
    def get_history_summary(self) -> str:
        """Get state transition history summary."""
        return self.state_machine.get_history_summary()

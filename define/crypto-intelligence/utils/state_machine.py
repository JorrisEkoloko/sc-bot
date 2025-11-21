"""State machine validation with finite state machine theory.

Based on:
- Finite State Machine theory (automata theory)
- State pattern (Gang of Four design patterns)
- Wikipedia: Finite-state machine

This module provides validated state transitions to prevent invalid
state changes and ensure system consistency.
"""
import asyncio
from typing import Dict, Set, Optional, Callable, Any
from enum import Enum
from datetime import datetime
from utils.logger import get_logger


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateMachine:
    """
    Generic state machine with validated transitions.
    
    Based on finite state machine theory:
    - States: Finite set of possible states
    - Transitions: Valid state changes
    - Guards: Conditions for transitions
    - Actions: Side effects on transitions
    
    Reference: https://en.wikipedia.org/wiki/Finite-state_machine
    """
    
    def __init__(
        self,
        name: str,
        initial_state: Enum,
        transitions: Dict[Enum, Set[Enum]],
        guards: Optional[Dict[tuple, Callable]] = None,
        actions: Optional[Dict[tuple, Callable]] = None
    ):
        """
        Initialize state machine.
        
        Args:
            name: State machine name
            initial_state: Initial state
            transitions: Dictionary of state -> set of valid next states
            guards: Optional guard functions for transitions
            actions: Optional action functions on transitions
        """
        self.name = name
        self._current_state = initial_state
        self.transitions = transitions
        self.guards = guards or {}
        self.actions = actions or {}
        self.logger = get_logger(f'StateMachine.{name}')
        self._lock: Optional[asyncio.Lock] = None
        self._history: list = [(datetime.now(), initial_state, None)]
    
    async def _ensure_lock(self):
        """Ensure lock is initialized."""
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def transition(
        self,
        to_state: Enum,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempt state transition with validation.
        
        Args:
            to_state: Target state
            context: Optional context for guards/actions
            
        Returns:
            True if transition succeeded
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        await self._ensure_lock()
        
        async with self._lock:
            from_state = self._current_state
            
            # Validate transition
            if not self._is_valid_transition(from_state, to_state):
                raise StateTransitionError(
                    f"Invalid transition: {from_state.value} -> {to_state.value}. "
                    f"Valid transitions from {from_state.value}: "
                    f"{[s.value for s in self.transitions.get(from_state, set())]}"
                )
            
            # Check guard condition
            if not await self._check_guard(from_state, to_state, context):
                self.logger.warning(
                    f"Guard failed for transition: {from_state.value} -> {to_state.value}"
                )
                return False
            
            # Execute action
            try:
                await self._execute_action(from_state, to_state, context)
            except Exception as e:
                self.logger.error(
                    f"Action failed for transition {from_state.value} -> {to_state.value}: {e}"
                )
                raise
            
            # Perform transition
            self._current_state = to_state
            self._history.append((datetime.now(), to_state, from_state))
            
            self.logger.info(
                f"State transition: {from_state.value} -> {to_state.value}"
            )
            
            return True
    
    def _is_valid_transition(self, from_state: Enum, to_state: Enum) -> bool:
        """Check if transition is valid."""
        valid_next_states = self.transitions.get(from_state, set())
        return to_state in valid_next_states
    
    async def _check_guard(
        self,
        from_state: Enum,
        to_state: Enum,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check guard condition for transition."""
        guard_key = (from_state, to_state)
        guard_func = self.guards.get(guard_key)
        
        if guard_func is None:
            return True  # No guard, allow transition
        
        try:
            if asyncio.iscoroutinefunction(guard_func):
                return await guard_func(context)
            else:
                return guard_func(context)
        except Exception as e:
            self.logger.error(f"Guard function error: {e}")
            return False
    
    async def _execute_action(
        self,
        from_state: Enum,
        to_state: Enum,
        context: Optional[Dict[str, Any]]
    ):
        """Execute action on transition."""
        action_key = (from_state, to_state)
        action_func = self.actions.get(action_key)
        
        if action_func is None:
            return  # No action
        
        if asyncio.iscoroutinefunction(action_func):
            await action_func(context)
        else:
            action_func(context)
    
    async def get_state(self) -> Enum:
        """Get current state (thread-safe)."""
        await self._ensure_lock()
        
        async with self._lock:
            return self._current_state
    
    def get_state_sync(self) -> Enum:
        """Get current state (non-thread-safe, for quick checks)."""
        return self._current_state
    
    async def can_transition_to(self, to_state: Enum) -> bool:
        """Check if transition to state is possible."""
        await self._ensure_lock()
        
        async with self._lock:
            return self._is_valid_transition(self._current_state, to_state)
    
    def get_valid_transitions(self) -> Set[Enum]:
        """Get valid transitions from current state."""
        return self.transitions.get(self._current_state, set())
    
    def get_history(self) -> list:
        """Get state transition history."""
        return self._history.copy()
    
    def get_history_summary(self) -> str:
        """Get human-readable history summary."""
        lines = [f"State machine: {self.name}"]
        lines.append(f"Current state: {self._current_state.value}")
        lines.append(f"History ({len(self._history)} transitions):")
        
        for timestamp, state, from_state in self._history[-10:]:  # Last 10
            if from_state:
                lines.append(
                    f"  {timestamp.strftime('%H:%M:%S')} - "
                    f"{from_state.value} -> {state.value}"
                )
            else:
                lines.append(
                    f"  {timestamp.strftime('%H:%M:%S')} - "
                    f"Initial: {state.value}"
                )
        
        return "\n".join(lines)


class SystemState(Enum):
    """System lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    RESTARTING = "restarting"
    ERROR = "error"


class SystemStateMachine(StateMachine):
    """
    State machine for system lifecycle management.
    
    Enforces valid system state transitions and prevents invalid operations.
    """
    
    # Define valid transitions
    TRANSITIONS = {
        SystemState.STOPPED: {
            SystemState.STARTING,
            SystemState.ERROR
        },
        SystemState.STARTING: {
            SystemState.RUNNING,
            SystemState.STOPPING,
            SystemState.ERROR
        },
        SystemState.RUNNING: {
            SystemState.STOPPING,
            SystemState.RESTARTING,
            SystemState.ERROR
        },
        SystemState.STOPPING: {
            SystemState.STOPPED,
            SystemState.ERROR
        },
        SystemState.RESTARTING: {
            SystemState.STARTING,
            SystemState.STOPPING,
            SystemState.ERROR
        },
        SystemState.ERROR: {
            SystemState.STOPPED,
            SystemState.STARTING
        }
    }
    
    def __init__(self, name: str = "System"):
        """Initialize system state machine."""
        super().__init__(
            name=name,
            initial_state=SystemState.STOPPED,
            transitions=self.TRANSITIONS
        )
    
    async def start(self) -> bool:
        """Request system start."""
        current = await self.get_state()
        
        if current == SystemState.RUNNING:
            self.logger.info("System already running")
            return True
        
        if current not in [SystemState.STOPPED, SystemState.ERROR]:
            self.logger.warning(
                f"Cannot start from state {current.value}"
            )
            return False
        
        try:
            await self.transition(SystemState.STARTING)
            return True
        except StateTransitionError as e:
            self.logger.error(f"Start failed: {e}")
            return False
    
    async def mark_running(self) -> bool:
        """Mark system as running after successful start."""
        try:
            await self.transition(SystemState.RUNNING)
            return True
        except StateTransitionError as e:
            self.logger.error(f"Failed to mark as running: {e}")
            return False
    
    async def stop(self) -> bool:
        """Request system stop."""
        current = await self.get_state()
        
        if current == SystemState.STOPPED:
            self.logger.debug("System already stopped")
            return True
        
        if current == SystemState.STOPPING:
            self.logger.warning("System already stopping")
            return False
        
        try:
            await self.transition(SystemState.STOPPING)
            return True
        except StateTransitionError as e:
            self.logger.error(f"Stop failed: {e}")
            return False
    
    async def mark_stopped(self) -> bool:
        """Mark system as stopped after successful shutdown."""
        try:
            await self.transition(SystemState.STOPPED)
            return True
        except StateTransitionError as e:
            self.logger.error(f"Failed to mark as stopped: {e}")
            return False
    
    async def mark_error(self, error: Exception) -> bool:
        """Mark system as in error state."""
        self.logger.error(f"System error: {error}")
        try:
            await self.transition(SystemState.ERROR, context={'error': error})
            return True
        except StateTransitionError:
            # Already in error state or transition not allowed
            return False
    
    async def restart(self) -> bool:
        """Request system restart."""
        current = await self.get_state()
        
        if current != SystemState.RUNNING:
            self.logger.warning(
                f"Cannot restart from state {current.value}"
            )
            return False
        
        try:
            await self.transition(SystemState.RESTARTING)
            return True
        except StateTransitionError as e:
            self.logger.error(f"Restart failed: {e}")
            return False

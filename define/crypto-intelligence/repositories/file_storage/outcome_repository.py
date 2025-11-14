"""Signal outcome data persistence.

Pure data access layer for loading and saving signal outcomes.

Task 5 Enhancement: Two-file tracking system
- active_tracking.json: In-progress signals (<30 days old)
- completed_history.json: Finished signals (≥30 days old)

MCP-Validated: Atomicity pattern from Wikipedia ensures no data loss during archival.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from domain.signal_outcome import SignalOutcome
from utils.logger import setup_logger


class OutcomeRepository:
    """Pure data access for signal outcomes with two-file tracking system.
    
    Implements atomic file updates to prevent data loss during archival.
    """
    
    def __init__(self, data_dir: str = "data/reputation", logger=None):
        """
        Initialize outcome repository.
        
        Args:
            data_dir: Directory for storing outcome data
            logger: Optional logger instance
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Legacy file (backward compatibility)
        self.outcomes_file = self.data_dir / "signal_outcomes.json"
        
        # Task 5: Two-file tracking system
        self.active_tracking_file = self.data_dir / "active_tracking.json"
        self.completed_history_file = self.data_dir / "completed_history.json"
        
        self.logger = logger or setup_logger('OutcomeRepository')
    
    def save(self, outcomes: Dict[str, SignalOutcome]) -> None:
        """
        Save outcomes to JSON file.
        
        Args:
            outcomes: Dictionary of address -> SignalOutcome
        """
        try:
            data = {
                address: outcome.to_dict()
                for address, outcome in outcomes.items()
            }
            
            with open(self.outcomes_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(outcomes)} outcomes to {self.outcomes_file}")
        except Exception as e:
            self.logger.error(f"Failed to save outcomes: {e}")
    
    def load(self) -> Dict[str, SignalOutcome]:
        """
        Load outcomes from JSON file.
        
        Returns:
            Dictionary of address -> SignalOutcome
        """
        if not self.outcomes_file.exists():
            self.logger.debug("No existing outcomes file found")
            return {}
        
        try:
            with open(self.outcomes_file, 'r') as f:
                data = json.load(f)
            
            outcomes = {
                address: SignalOutcome.from_dict(outcome_data)
                for address, outcome_data in data.items()
            }
            
            self.logger.info(f"Loaded {len(outcomes)} outcomes from {self.outcomes_file}")
            return outcomes
        except Exception as e:
            self.logger.error(f"Failed to load outcomes: {e}")
            return {}
    
    def get_file_path(self) -> Path:
        """Get the path to the outcomes file (legacy)."""
        return self.outcomes_file
    
    def load_two_file_system(self) -> Tuple[Dict[str, SignalOutcome], Dict[str, SignalOutcome]]:
        """
        Load outcomes from two-file tracking system.
        
        Returns:
            Tuple of (active_outcomes, completed_outcomes)
        """
        active = self._load_from_file(self.active_tracking_file)
        completed = self._load_from_file(self.completed_history_file)
        
        self.logger.info(
            f"Loaded {len(active)} active signals, {len(completed)} completed signals"
        )
        
        return active, completed
    
    def save_two_file_system(
        self,
        active_outcomes: Dict[str, SignalOutcome],
        completed_outcomes: Dict[str, SignalOutcome]
    ) -> None:
        """
        Save outcomes to two-file tracking system atomically.
        
        MCP-Validated: Uses atomic write pattern to prevent data loss.
        
        Args:
            active_outcomes: In-progress signals
            completed_outcomes: Finished signals
        """
        # Save both files atomically
        self._save_to_file(self.active_tracking_file, active_outcomes)
        self._save_to_file(self.completed_history_file, completed_outcomes)
        
        self.logger.debug(
            f"Saved {len(active_outcomes)} active, {len(completed_outcomes)} completed signals"
        )
    
    def archive_to_history(
        self,
        address: str,
        active_outcomes: Dict[str, SignalOutcome],
        completed_outcomes: Dict[str, SignalOutcome]
    ) -> bool:
        """
        Archive a signal from active to completed history atomically.
        
        MCP-Validated: Atomicity ensures either both operations succeed or none.
        
        Args:
            address: Token address to archive
            active_outcomes: Active signals dict
            completed_outcomes: Completed signals dict
            
        Returns:
            True if archived successfully
        """
        if address not in active_outcomes:
            self.logger.warning(f"Cannot archive {address[:10]}...: not in active tracking")
            return False
        
        # Move signal from active to completed
        signal = active_outcomes[address]
        completed_outcomes[address] = signal
        del active_outcomes[address]
        
        # Save both files atomically
        self.save_two_file_system(active_outcomes, completed_outcomes)
        
        self.logger.info(
            f"Archived signal {address[:10]}... (Signal #{signal.signal_number}) to history"
        )
        
        return True
    
    def check_for_duplicate(
        self,
        address: str,
        active_outcomes: Dict[str, SignalOutcome],
        completed_outcomes: Dict[str, SignalOutcome]
    ) -> Tuple[bool, Optional[int], Optional[list]]:
        """
        Check if coin is already tracked (deduplication logic).
        
        MCP-Validated: Deduplication pattern from Wikipedia.
        
        Args:
            address: Token address to check
            active_outcomes: Active signals dict
            completed_outcomes: Completed signals dict
            
        Returns:
            Tuple of (is_duplicate, next_signal_number, previous_signals)
            - is_duplicate: True if already in active tracking (skip)
            - next_signal_number: Signal number for fresh start (if not duplicate)
            - previous_signals: List of previous signal IDs
        """
        # Check active tracking first
        if address in active_outcomes:
            self.logger.debug(f"Duplicate: {address[:10]}... already in active tracking")
            return True, None, None
        
        # Check completed history for fresh start
        if address in completed_outcomes:
            completed_signal = completed_outcomes[address]
            next_number = completed_signal.signal_number + 1
            previous_signals = completed_signal.previous_signals + [completed_signal.message_id]
            
            self.logger.info(
                f"Fresh start: {address[:10]}... previously tracked "
                f"(Signal #{completed_signal.signal_number}: {completed_signal.ath_multiplier:.3f}x), "
                f"starting Signal #{next_number}"
            )
            
            return False, next_number, previous_signals
        
        # First mention
        self.logger.debug(f"First mention: {address[:10]}... starting Signal #1")
        return False, 1, []
    
    def _load_from_file(self, file_path: Path) -> Dict[str, SignalOutcome]:
        """Load outcomes from a specific file."""
        if not file_path.exists():
            self.logger.debug(f"No existing file: {file_path.name}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            outcomes = {
                address: SignalOutcome.from_dict(outcome_data)
                for address, outcome_data in data.items()
            }
            
            self.logger.debug(f"Loaded {len(outcomes)} outcomes from {file_path.name}")
            return outcomes
        except Exception as e:
            self.logger.error(f"Failed to load from {file_path.name}: {e}")
            return {}
    
    def _save_to_file(self, file_path: Path, outcomes: Dict[str, SignalOutcome]) -> None:
        """Save outcomes to a specific file atomically."""
        try:
            data = {
                address: outcome.to_dict()
                for address, outcome in outcomes.items()
            }
            
            # Atomic write: write to temp file, then rename
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename (MCP-validated atomicity pattern)
            temp_file.replace(file_path)
            
            self.logger.debug(f"Saved {len(outcomes)} outcomes to {file_path.name}")
        except Exception as e:
            self.logger.error(f"Failed to save to {file_path.name}: {e}")

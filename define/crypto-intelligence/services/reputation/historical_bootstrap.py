"""Historical bootstrap service for channel reputation initialization.

Task 5: Refactor and enhance historical bootstrap with smart checkpoint handling.

Key Features:
1. Two-file tracking system (active vs completed)
2. Deduplication logic (prevents duplicate tracking)
3. Fresh start re-monitoring (Signal #1, #2, #3...)
4. Progress persistence (resumability after crash)
5. Smart checkpoint handling (leverages Task 4)

MCP-Validated:
- Checkpoint/restart pattern from Wikipedia
- Deduplication pattern from Wikipedia
- Atomicity pattern from Wikipedia
- ROI formula from Investopedia
- TD learning from Wikipedia (alpha=0.1)
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from domain.signal_outcome import SignalOutcome
from domain.bootstrap_status import BootstrapStatus
from repositories.file_storage.outcome_repository import OutcomeRepository
from services.pricing.historical_price_service import HistoricalPriceService
from utils.logger import setup_logger


class HistoricalBootstrap:
    """Historical bootstrap service with two-file tracking and progress persistence.
    
    Extracts bootstrap logic from historical_scraper.py into dedicated service.
    """
    
    def __init__(
        self,
        data_dir: str = "data/reputation",
        historical_price_service: Optional[HistoricalPriceService] = None,
        logger=None
    ):
        """
        Initialize historical bootstrap service.
        
        Args:
            data_dir: Directory for reputation data
            historical_price_service: HistoricalPriceService instance (Task 4)
            logger: Logger instance
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger or setup_logger('HistoricalBootstrap')
        
        # Initialize repositories
        self.outcome_repository = OutcomeRepository(data_dir, self.logger)
        
        # Task 4 integration: Historical price service
        self.historical_price_service = historical_price_service
        
        # Two-file tracking system
        self.active_outcomes: Dict[str, SignalOutcome] = {}
        self.completed_outcomes: Dict[str, SignalOutcome] = {}
        
        # Progress tracking
        self.status_file = self.data_dir / "bootstrap_status.json"
        self.bootstrap_status: Optional[BootstrapStatus] = None
        
        # Checkpoint interval (save every N messages)
        self.checkpoint_interval = 100
        
        self.logger.info("HistoricalBootstrap initialized")
    
    def load_existing_data(self) -> None:
        """Load existing outcomes from two-file system."""
        self.active_outcomes, self.completed_outcomes = (
            self.outcome_repository.load_two_file_system()
        )
        
        self.logger.info(
            f"Loaded {len(self.active_outcomes)} active signals, "
            f"{len(self.completed_outcomes)} completed signals"
        )
    
    def load_progress(self) -> Optional[BootstrapStatus]:
        """
        Load bootstrap progress from checkpoint file.
        
        Returns:
            BootstrapStatus if exists, None otherwise
        """
        if not self.status_file.exists():
            self.logger.debug("No existing bootstrap progress found")
            return None
        
        try:
            with open(self.status_file, 'r') as f:
                data = json.load(f)
            
            status = BootstrapStatus.from_dict(data)
            self.logger.info(
                f"Loaded bootstrap progress: {status.processed_messages}/{status.total_messages} messages processed"
            )
            
            if status.last_processed_message_id:
                self.logger.info(f"Resuming from message ID: {status.last_processed_message_id}")
            
            return status
        except Exception as e:
            self.logger.error(f"Failed to load bootstrap progress: {e}")
            return None
    
    def save_progress(self, status: BootstrapStatus) -> None:
        """
        Save bootstrap progress to checkpoint file.
        
        MCP-Validated: Checkpoint pattern for fault tolerance.
        
        Args:
            status: Current bootstrap status
        """
        try:
            status.last_updated = datetime.now()
            status.last_checkpoint_time = datetime.now()
            
            # Atomic write
            temp_file = self.status_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(status.to_dict(), f, indent=2)
            
            temp_file.replace(self.status_file)
            
            self.logger.debug(
                f"Checkpoint saved: {status.processed_messages} messages, "
                f"{status.processed_tokens} tokens"
            )
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")
    
    def clear_progress(self) -> None:
        """Clear bootstrap progress file on successful completion."""
        try:
            if self.status_file.exists():
                self.status_file.unlink()
                self.logger.info("Bootstrap complete: Clearing progress file")
        except Exception as e:
            self.logger.error(f"Failed to clear progress file: {e}")
    
    def check_for_duplicate(
        self,
        address: str
    ) -> Tuple[bool, Optional[int], Optional[list]]:
        """
        Check if coin is already tracked (deduplication logic).
        
        MCP-Validated: Deduplication pattern from Wikipedia.
        
        Args:
            address: Token address to check
            
        Returns:
            Tuple of (is_duplicate, next_signal_number, previous_signals)
        """
        return self.outcome_repository.check_for_duplicate(
            address,
            self.active_outcomes,
            self.completed_outcomes
        )
    
    def archive_to_history(self, address: str) -> bool:
        """
        Archive a completed signal from active to history.
        
        MCP-Validated: Atomicity ensures no data loss.
        
        Args:
            address: Token address to archive
            
        Returns:
            True if archived successfully
        """
        return self.outcome_repository.archive_to_history(
            address,
            self.active_outcomes,
            self.completed_outcomes
        )
    
    def add_signal(
        self,
        address: str,
        signal: SignalOutcome
    ) -> None:
        """
        Add a new signal to active tracking.
        
        Args:
            address: Token address
            signal: SignalOutcome instance
        """
        self.active_outcomes[address] = signal
        
        self.logger.debug(
            f"Added signal {address[:10]}... (Signal #{signal.signal_number}) to active tracking"
        )
    
    def save_all(self) -> None:
        """Save both active and completed outcomes."""
        self.outcome_repository.save_two_file_system(
            self.active_outcomes,
            self.completed_outcomes
        )
    
    def get_active_count(self) -> int:
        """Get count of active signals."""
        return len(self.active_outcomes)
    
    def get_completed_count(self) -> int:
        """Get count of completed signals."""
        return len(self.completed_outcomes)
    
    def get_channel_outcomes(
        self,
        channel_name: str,
        completed_only: bool = True
    ) -> List[SignalOutcome]:
        """
        Get all outcomes for a specific channel.
        
        Args:
            channel_name: Channel name
            completed_only: If True, only return completed signals
            
        Returns:
            List of SignalOutcome instances
        """
        outcomes = []
        
        if completed_only:
            outcomes = [
                outcome for outcome in self.completed_outcomes.values()
                if outcome.channel_name == channel_name
            ]
        else:
            # Include both active and completed
            outcomes = [
                outcome for outcome in list(self.active_outcomes.values()) + list(self.completed_outcomes.values())
                if outcome.channel_name == channel_name
            ]
        
        return outcomes
    
    def calculate_smart_checkpoints(
        self,
        message_date: datetime,
        current_date: Optional[datetime] = None
    ) -> List[Tuple[str, any]]:
        """
        Calculate which checkpoints have been reached (Task 4 integration).
        
        Args:
            message_date: Date of the original message
            current_date: Current date (default: now)
            
        Returns:
            List of (checkpoint_name, timedelta) for reached checkpoints
        """
        if self.historical_price_service:
            return self.historical_price_service.calculate_smart_checkpoints(
                message_date,
                current_date
            )
        else:
            # Fallback if no historical price service
            from datetime import timedelta, timezone
            
            # Ensure both datetimes are timezone-aware
            now = current_date or datetime.now(timezone.utc)
            msg_date = message_date if message_date.tzinfo else message_date.replace(tzinfo=timezone.utc)
            
            elapsed = now - msg_date
            
            all_checkpoints = [
                ('1h', timedelta(hours=1)),
                ('4h', timedelta(hours=4)),
                ('24h', timedelta(hours=24)),
                ('3d', timedelta(days=3)),
                ('7d', timedelta(days=7)),
                ('30d', timedelta(days=30))
            ]
            
            return [(name, delta) for name, delta in all_checkpoints if elapsed >= delta]
    
    def determine_signal_status(
        self,
        message_date: datetime,
        current_date: Optional[datetime] = None
    ) -> str:
        """
        Determine if signal is completed or in_progress based on elapsed time.
        
        Args:
            message_date: Date of the original message
            current_date: Current date (default: now)
            
        Returns:
            "completed" if ≥30 days old, "in_progress" otherwise
        """
        from datetime import timedelta, timezone
        
        # Ensure both datetimes are timezone-aware
        now = current_date or datetime.now(timezone.utc)
        msg_date = message_date if message_date.tzinfo else message_date.replace(tzinfo=timezone.utc)
        
        elapsed = now - msg_date
        
        if elapsed >= timedelta(days=30):
            return "completed"
        else:
            return "in_progress"
    
    def get_statistics(self) -> Dict:
        """
        Get bootstrap statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            'active_signals': len(self.active_outcomes),
            'completed_signals': len(self.completed_outcomes),
            'total_signals': len(self.active_outcomes) + len(self.completed_outcomes),
            'channels': len(set(
                outcome.channel_name 
                for outcome in list(self.active_outcomes.values()) + list(self.completed_outcomes.values())
            ))
        }


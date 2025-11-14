"""Signal outcome data persistence.

Pure data access layer for loading and saving signal outcomes.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from intelligence.signal_outcome import SignalOutcome
from utils.logger import setup_logger


class OutcomeRepository:
    """Pure data access for signal outcomes - no business logic."""
    
    def __init__(self, data_dir: str = "data/reputation", logger=None):
        """
        Initialize outcome repository.
        
        Args:
            data_dir: Directory for storing outcome data
            logger: Optional logger instance
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.outcomes_file = self.data_dir / "signal_outcomes.json"
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
        """Get the path to the outcomes file."""
        return self.outcomes_file

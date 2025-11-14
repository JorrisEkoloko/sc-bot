"""Channel reputation data persistence.

Pure data access layer for loading and saving channel reputations.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from domain.channel_reputation import ChannelReputation
from utils.logger import setup_logger


class ReputationRepository:
    """Pure data access for channel reputations - no business logic."""
    
    def __init__(self, data_dir: str = "data/reputation", logger=None):
        """
        Initialize reputation repository.
        
        Args:
            data_dir: Directory for storing reputation data
            logger: Optional logger instance
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.reputations_file = self.data_dir / "channels.json"
        self.logger = logger or setup_logger('ReputationRepository')
    
    def save(self, reputations: Dict[str, ChannelReputation]) -> None:
        """
        Save reputations to JSON file.
        
        Args:
            reputations: Dictionary of channel_name -> ChannelReputation
        """
        try:
            data = {
                channel: reputation.to_dict()
                for channel, reputation in reputations.items()
            }
            
            with open(self.reputations_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(reputations)} channel reputations")
        except Exception as e:
            self.logger.error(f"Failed to save reputations: {e}")
            raise
    
    def load(self) -> Dict[str, ChannelReputation]:
        """
        Load reputations from JSON file.
        
        Returns:
            Dictionary of channel_name -> ChannelReputation
        """
        if not self.reputations_file.exists():
            self.logger.debug("No reputation file found, starting fresh")
            return {}
        
        try:
            with open(self.reputations_file, 'r') as f:
                data = json.load(f)
            
            reputations = {
                channel: ChannelReputation.from_dict(rep_data)
                for channel, rep_data in data.items()
            }
            
            self.logger.debug(f"Loaded {len(reputations)} channel reputations")
            return reputations
        except Exception as e:
            self.logger.error(f"Failed to load reputations: {e}")
            return {}
    
    def get_file_path(self) -> Path:
        """Get the path to the reputations file."""
        return self.reputations_file

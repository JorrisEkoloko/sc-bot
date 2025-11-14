"""Performance tracking configuration."""
from dataclasses import dataclass


@dataclass
class PerformanceConfig:
    """Performance tracking configuration."""
    tracking_days: int = 7  # Number of days to track
    data_dir: str = "data/performance"  # Directory for tracking data
    update_interval: int = 7200  # Update interval in seconds (2 hours)
    
    @classmethod
    def load_from_env(cls) -> 'PerformanceConfig':
        """Load performance configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        # Load .env file
        load_dotenv()
        
        return cls(
            tracking_days=int(os.getenv('PERFORMANCE_TRACKING_DAYS', '7')),
            data_dir=os.getenv('PERFORMANCE_DATA_DIR', 'data/performance'),
            update_interval=int(os.getenv('PERFORMANCE_UPDATE_INTERVAL', '7200'))
        )


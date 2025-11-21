"""Performance data domain model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PerformanceData:
    """7-day ATH performance metrics with time-based classification."""
    address: str
    chain: str
    symbol: Optional[str] = None  # Token symbol
    first_message_id: str = ""
    start_price: float = 0.0
    start_time: str = ""  # ISO format string
    ath_since_mention: float = 0.0
    ath_time: str = ""  # ISO format string
    ath_multiplier: float = 1.0
    current_multiplier: float = 1.0
    days_tracked: int = 0
    current_price: float = 0.0
    time_to_ath: Optional[str] = None  # ISO duration or None
    is_at_ath: bool = False
    # Time-based performance fields (Task 4: Dual-metric classification)
    days_to_ath: float = 0.0
    peak_timing: str = ""
    day_7_price: float = 0.0
    day_7_multiplier: float = 0.0
    day_7_classification: str = ""
    day_30_price: float = 0.0
    day_30_multiplier: float = 0.0
    day_30_classification: str = ""
    trajectory: str = ""

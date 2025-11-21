"""Performance tracking for 7-day ATH monitoring.

Tracks price performance over 7 days with disk persistence.
Business logic layer - delegates persistence to TrackingRepository.

Based on verified documentation:
- JSON: https://docs.python.org/3/library/json.html
- pathlib: https://docs.python.org/3/library/pathlib.html
- datetime: https://docs.python.org/3/library/datetime.html
- dataclasses: https://docs.python.org/3/library/dataclasses.html
"""
from datetime import datetime, timedelta
from typing import Optional

from utils.logger import setup_logger
from repositories.writers.csv_writer import CSVTableWriter
from repositories.file_storage.tracking_repository import TrackingRepository
from domain.performance_data import PerformanceData


class PerformanceTracker:
    """Track 7-day ATH performance for addresses.
    
    Business logic layer - calculates ATH and performance metrics.
    Delegates persistence to TrackingRepository.
    Writes to PERFORMANCE CSV table on every update.
    """
    
    # PERFORMANCE table columns (19 columns with time-based fields)
    PERFORMANCE_COLUMNS = [
        'address', 'chain', 'first_message_id', 'start_price', 'start_time',
        'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked',
        # Time-based performance columns (Task 4: Dual-metric classification)
        'days_to_ath', 'peak_timing', 'day_7_price', 'day_7_multiplier', 'day_7_classification',
        'day_30_price', 'day_30_multiplier', 'day_30_classification', 'trajectory'
    ]
    
    def __init__(self, data_dir: str = "data/performance", tracking_days: int = 7, 
                 csv_output_dir: str = "output", enable_csv: bool = True, logger=None):
        """
        Initialize performance tracker.
        
        Args:
            data_dir: Directory for tracking data storage
            tracking_days: Number of days to track (default: 7)
            csv_output_dir: Directory for CSV output
            enable_csv: Enable CSV table writing
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('PerformanceTracker')
        self.tracking_days = tracking_days
        self.tracking_data = {}
        self.enable_csv = enable_csv
        
        # Use repository for persistence (separation of concerns)
        self.repository = TrackingRepository(data_dir, self.logger)
        
        # Initialize CSV writer if enabled
        self.csv_writer = None
        if enable_csv:
            try:
                self.csv_writer = CSVTableWriter(
                    table_name='performance',
                    columns=self.PERFORMANCE_COLUMNS,
                    output_dir=csv_output_dir,
                    logger=self.logger
                )
                self.logger.debug("CSV writer initialized for PERFORMANCE table")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CSV writer: {e}")
                self.csv_writer = None
        
        # Load existing data from repository
        self.tracking_data = self.repository.load()
        
        self.logger.info(f"Performance tracker initialized (tracking {tracking_days} days, CSV: {enable_csv})")
    
    async def start_tracking(self, address: str, chain: str, initial_price: float, message_id: str = "unknown",
                           known_ath: Optional[float] = None, symbol: Optional[str] = None):
        """
        Start tracking a new address.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            initial_price: Starting price in USD
            message_id: ID of first message mentioning this address
            known_ath: Optional known ATH from APIs (coin's real all-time high)
            symbol: Optional token symbol
        """
        if address in self.tracking_data:
            self.logger.debug(f"Address {address[:10]}... already tracked")
            return
        
        now = datetime.now()
        self.tracking_data[address] = {
            'address': address,
            'chain': chain,
            'symbol': symbol,
            'first_message_id': message_id,
            'start_price': initial_price,
            'start_time': now.isoformat(),
            'ath_since_mention': initial_price,
            'ath_time': now.isoformat(),
            'current_price': initial_price,
            'last_update': now.isoformat(),
            'known_ath': known_ath,  # Coin's real ATH from APIs (or OHLC ATH after 7 days)
            'ohlc_fetched': False  # Flag to track if 7-day OHLC has been fetched
        }
        
        if known_ath:
            self.logger.info(
                f"Started tracking {address[:10]}... at ${initial_price:.6f} "
                f"(known ATH: ${known_ath:.6f})"
            )
        else:
            self.logger.info(f"Started tracking {address[:10]}... at ${initial_price:.6f}")
        
        await self.save_to_disk_async()
        
        # Write to CSV table
        self._write_to_csv(address)
    
    async def update_price(self, address: str, current_price: float):
        """
        Update current price and ATH if needed.
        
        Args:
            address: Token contract address
            current_price: Current price in USD
        """
        if address not in self.tracking_data:
            self.logger.warning(f"Address {address[:10]}... not tracked, cannot update")
            return
        
        entry = self.tracking_data[address]
        old_price = entry['current_price']
        entry['current_price'] = current_price
        entry['last_update'] = datetime.now().isoformat()
        
        # Update ATH if current price is higher
        if current_price > entry['ath_since_mention']:
            old_ath = entry['ath_since_mention']
            entry['ath_since_mention'] = current_price
            entry['ath_time'] = datetime.now().isoformat()
            
            multiplier = current_price / entry['start_price']
            self.logger.info(
                f"New ATH for {address[:10]}...: ${current_price:.6f} "
                f"(was ${old_ath:.6f}, {multiplier:.2f}x from start)"
            )
        else:
            self.logger.debug(
                f"Updated price for {address[:10]}...: ${current_price:.6f} "
                f"(was ${old_price:.6f})"
            )
        
        # Use async save for thread safety
        await self.save_to_disk_async()
        
        # Write to CSV table
        self._write_to_csv(address)
    
    def get_performance(self, address: str) -> Optional[PerformanceData]:
        """
        Get performance metrics for address.
        
        Args:
            address: Token contract address
            
        Returns:
            PerformanceData object or None if not tracked
        """
        if address not in self.tracking_data:
            return None
        
        entry = self.tracking_data[address]
        start_time = datetime.fromisoformat(entry['start_time'])
        ath_time = datetime.fromisoformat(entry['ath_time'])
        days_tracked = (datetime.now() - start_time).days
        
        # Calculate multipliers
        ath_multiplier = entry['ath_since_mention'] / entry['start_price']
        current_multiplier = entry['current_price'] / entry['start_price']
        
        # Check if at ATH (within 1% tolerance)
        is_at_ath = abs(entry['current_price'] - entry['ath_since_mention']) / entry['ath_since_mention'] < 0.01
        
        # Calculate time to ATH
        time_to_ath = None
        if not is_at_ath:
            delta = ath_time - start_time
            time_to_ath = str(delta)  # String representation of timedelta
        
        # Calculate days_to_ath from ath_time
        days_to_ath_value = (ath_time - start_time).total_seconds() / 86400
        
        return PerformanceData(
            address=address,
            chain=entry['chain'],
            symbol=entry.get('symbol'),
            first_message_id=entry.get('first_message_id', 'unknown'),
            start_price=entry['start_price'],
            start_time=entry['start_time'],
            ath_since_mention=entry['ath_since_mention'],
            ath_time=entry['ath_time'],
            ath_multiplier=ath_multiplier,
            current_multiplier=current_multiplier,
            days_tracked=days_tracked,
            current_price=entry['current_price'],
            time_to_ath=time_to_ath,
            is_at_ath=is_at_ath,
            # Time-based performance fields (Task 4: Dual-metric classification)
            # These come from SignalOutcome via outcome_tracker, stored in tracking_data
            days_to_ath=days_to_ath_value,
            peak_timing=entry.get('peak_timing', ''),
            day_7_price=entry.get('day_7_price', 0.0),
            day_7_multiplier=entry.get('day_7_multiplier', 0.0),
            day_7_classification=entry.get('day_7_classification', ''),
            day_30_price=entry.get('day_30_price', 0.0),
            day_30_multiplier=entry.get('day_30_multiplier', 0.0),
            day_30_classification=entry.get('day_30_classification', ''),
            trajectory=entry.get('trajectory', '')
        )
    
    def cleanup_old_entries(self):
        """Remove entries older than configured tracking days (atomic operation)."""
        now = datetime.now()
        
        # Build new dict with only valid, recent entries (atomic operation)
        new_tracking_data = {}
        removed_count = 0
        
        for address, entry in self.tracking_data.items():
            try:
                start_time = datetime.fromisoformat(entry['start_time'])
                age_days = (now - start_time).days
                
                if age_days <= self.tracking_days:
                    new_tracking_data[address] = entry
                else:
                    removed_count += 1
                    self.logger.info(f"Removed old tracking entry: {address[:10]}... (>{self.tracking_days} days)")
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Invalid entry for {address[:10]}...: {e}, removing")
                removed_count += 1
        
        # Atomic replacement
        self.tracking_data = new_tracking_data
        
        if removed_count > 0:
            self.save_to_disk()
            self.logger.info(f"Cleanup complete: removed {removed_count} entries")
    
    async def save_to_disk_async(self):
        """Persist tracking data using repository (async, thread-safe)."""
        await self.repository.save_async(self.tracking_data)
    
    def save_to_disk(self):
        """Persist tracking data using repository (synchronous)."""
        self.repository.save(self.tracking_data)
    
    def get_tracking_summary(self) -> dict:
        """
        Get summary statistics of tracked addresses.
        
        Returns:
            Dictionary with tracking statistics
        """
        if not self.tracking_data:
            return {
                'total_tracked': 0,
                'by_chain': {},
                'avg_multiplier': 0.0,
                'best_performer': None
            }
        
        # Count by chain
        by_chain = {}
        multipliers = []
        best_performer = None
        best_multiplier = 0.0
        
        for address, entry in self.tracking_data.items():
            chain = entry.get('chain', 'unknown')
            by_chain[chain] = by_chain.get(chain, 0) + 1
            
            # Calculate multiplier
            multiplier = entry['ath_since_mention'] / entry['start_price']
            multipliers.append(multiplier)
            
            if multiplier > best_multiplier:
                best_multiplier = multiplier
                best_performer = {
                    'address': address[:10] + '...',
                    'chain': chain,
                    'multiplier': multiplier,
                    'start_price': entry['start_price'],
                    'ath_price': entry['ath_since_mention']
                }
        
        avg_multiplier = sum(multipliers) / len(multipliers) if multipliers else 0.0
        
        return {
            'total_tracked': len(self.tracking_data),
            'by_chain': by_chain,
            'avg_multiplier': avg_multiplier,
            'best_performer': best_performer
        }
    
    def to_table_row(self, address: str) -> Optional[list]:
        """
        Convert tracking data to PERFORMANCE table format (10 columns).
        
        Args:
            address: Token contract address
            
        Returns:
            List of values for CSV row or None if address not tracked
        """
        if address not in self.tracking_data:
            return None
        
        entry = self.tracking_data[address]
        start_time = datetime.fromisoformat(entry['start_time'])
        days_tracked = (datetime.now() - start_time).days
        
        # Calculate multipliers
        ath_multiplier = entry['ath_since_mention'] / entry['start_price']
        current_multiplier = entry['current_price'] / entry['start_price']
        
        return [
            entry['address'],
            entry['chain'],
            entry.get('first_message_id', 'unknown'),
            entry['start_price'],
            entry['start_time'],
            entry['ath_since_mention'],
            entry['ath_time'],
            round(ath_multiplier, 4),
            round(current_multiplier, 4),
            days_tracked
        ]
    
    def _write_to_csv(self, address: str):
        """
        Write tracking data to CSV table.
        
        Args:
            address: Token contract address
        """
        if not self.csv_writer:
            return
        
        try:
            row = self.to_table_row(address)
            if row:
                self.csv_writer.update_or_insert(address, row)
                self.logger.debug(f"Wrote performance data to CSV for {address[:10]}...")
        except Exception as e:
            self.logger.error(f"Failed to write to CSV for {address[:10]}...: {e}")


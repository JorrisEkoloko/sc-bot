"""Performance tracking for 7-day ATH monitoring.

Tracks price performance over 7 days with disk persistence.
Based on verified documentation:
- JSON: https://docs.python.org/3/library/json.html
- pathlib: https://docs.python.org/3/library/pathlib.html
- datetime: https://docs.python.org/3/library/datetime.html
- dataclasses: https://docs.python.org/3/library/dataclasses.html
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from utils.logger import setup_logger
from core.csv_table_writer import CSVTableWriter


@dataclass
class PerformanceData:
    """7-day ATH performance metrics."""
    address: str
    chain: str
    first_message_id: str
    start_price: float
    start_time: str  # ISO format string
    ath_since_mention: float
    ath_time: str  # ISO format string
    ath_multiplier: float
    current_multiplier: float
    days_tracked: int
    current_price: float = 0.0
    time_to_ath: Optional[str] = None  # ISO duration or None
    is_at_ath: bool = False


class PerformanceTracker:
    """Track 7-day ATH performance for addresses.
    
    Maintains internal JSON for fast lookups and recovery across restarts.
    Writes to PERFORMANCE CSV table on every update.
    """
    
    # PERFORMANCE table columns (10 columns)
    PERFORMANCE_COLUMNS = [
        'address', 'chain', 'first_message_id', 'start_price', 'start_time',
        'ath_since_mention', 'ath_time', 'ath_multiplier', 'current_multiplier', 'days_tracked'
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
        self.data_dir = Path(data_dir)
        self.data_file = self.data_dir / 'tracking.json'
        self.tracking_days = tracking_days
        self.tracking_data = {}
        self.enable_csv = enable_csv
        self._save_lock = None  # Will be initialized in async context
        
        # Initialize threading lock for sync save operations
        import threading
        self._sync_save_lock = threading.Lock()
        
        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Performance data directory: {self.data_dir}")
        
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
        
        # Load existing data
        self.load_from_disk()
        
        self.logger.info(f"Performance tracker initialized (tracking {tracking_days} days, CSV: {enable_csv})")
    
    def start_tracking(self, address: str, chain: str, initial_price: float, message_id: str = "unknown"):
        """
        Start tracking a new address.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            initial_price: Starting price in USD
            message_id: ID of first message mentioning this address
        """
        if address in self.tracking_data:
            self.logger.debug(f"Address {address[:10]}... already tracked")
            return
        
        now = datetime.now()
        self.tracking_data[address] = {
            'address': address,
            'chain': chain,
            'first_message_id': message_id,
            'start_price': initial_price,
            'start_time': now.isoformat(),
            'ath_since_mention': initial_price,
            'ath_time': now.isoformat(),
            'current_price': initial_price,
            'last_update': now.isoformat()
        }
        
        self.logger.info(f"Started tracking {address[:10]}... at ${initial_price:.6f}")
        self.save_to_disk()
        
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
        
        return PerformanceData(
            address=address,
            chain=entry['chain'],
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
            is_at_ath=is_at_ath
        )
    
    def cleanup_old_entries(self):
        """Remove entries older than configured tracking days."""
        now = datetime.now()
        to_remove = []
        
        for address, entry in self.tracking_data.items():
            try:
                start_time = datetime.fromisoformat(entry['start_time'])
                age_days = (now - start_time).days
                
                if age_days > self.tracking_days:
                    to_remove.append(address)
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Invalid entry for {address[:10]}...: {e}")
                to_remove.append(address)
        
        for address in to_remove:
            del self.tracking_data[address]
            self.logger.info(f"Removed old tracking entry: {address[:10]}... (>{self.tracking_days} days)")
        
        if to_remove:
            self.save_to_disk()
            self.logger.info(f"Cleanup complete: removed {len(to_remove)} entries")
    
    async def _ensure_save_lock(self):
        """Ensure save lock is initialized in async context."""
        if self._save_lock is None:
            import asyncio
            self._save_lock = asyncio.Lock()
    
    async def save_to_disk_async(self):
        """Persist tracking data to JSON file (async, thread-safe)."""
        import os
        await self._ensure_save_lock()
        
        async with self._save_lock:
            try:
                # Write to temporary file first for atomic operation
                temp_file = self.data_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                temp_file.replace(self.data_file)
                self.logger.debug(f"Saved tracking data to {self.data_file}")
            except (IOError, OSError) as e:
                self.logger.error(f"Failed to save tracking data (I/O error): {e}")
            except json.JSONEncodeError as e:
                self.logger.error(f"Failed to encode tracking data to JSON: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error saving tracking data: {e}")
    
    def save_to_disk(self):
        """Persist tracking data to JSON file (synchronous fallback)."""
        import os
        
        # Check if we're in an async context
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            # We're in async context - warn and schedule async version
            self.logger.warning("save_to_disk() called in async context, scheduling save_to_disk_async() instead")
            asyncio.create_task(self.save_to_disk_async())
            return
        except RuntimeError:
            # No running loop - safe to proceed with sync save
            pass
        
        # Use threading lock for sync context
        with self._sync_save_lock:
            try:
                # Write to temporary file first for atomic operation
                temp_file = self.data_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                temp_file.replace(self.data_file)
                self.logger.debug(f"Saved tracking data to {self.data_file}")
            except (IOError, OSError) as e:
                self.logger.error(f"Failed to save tracking data (I/O error): {e}")
            except json.JSONEncodeError as e:
                self.logger.error(f"Failed to encode tracking data to JSON: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error saving tracking data: {e}")
    
    def load_from_disk(self):
        """Load tracking data from JSON file."""
        if not self.data_file.exists():
            self.logger.info("No existing tracking data found, starting fresh")
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.tracking_data = json.load(f)
            self.logger.info(f"Loaded {len(self.tracking_data)} tracking entries from disk")
            
            # Cleanup old entries on load
            self.cleanup_old_entries()
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Corrupted tracking data file: {e}. Starting fresh.")
            self.tracking_data = {}
        except Exception as e:
            self.logger.error(f"Failed to load tracking data: {e}. Starting fresh.")
            self.tracking_data = {}
    
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


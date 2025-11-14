"""Persistent cache for historical price data."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from domain.historical_price import HistoricalPriceData, OHLCCandle
from utils.logger import setup_logger


class HistoricalPriceCache:
    """Manages persistent caching of historical price data."""
    
    def __init__(self, cache_dir: str = "data/cache", save_interval: int = 10, logger=None):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory for cache storage
            save_interval: Save cache after N new entries (default: 10, 0=save immediately)
            logger: Logger instance
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "historical_prices.json"
        self.save_interval = save_interval
        self._dirty_count = 0  # Track unsaved cache entries
        self.logger = logger or setup_logger('HistoricalPriceCache')
        
        # In-memory cache
        self.memory_cache: Dict[str, HistoricalPriceData] = {}
        
        # Load from disk
        self._load_cache()
    
    def get_cache_key(self, symbol: str, timestamp: datetime, window_days: int) -> str:
        """Generate cache key."""
        date_str = timestamp.strftime('%Y-%m-%d')
        return f"{symbol}_{date_str}_{window_days}d"
    
    def get(self, cache_key: str) -> Optional[HistoricalPriceData]:
        """Get cached data."""
        data = self.memory_cache.get(cache_key)
        if data:
            data.cached = True
        return data
    
    def set(self, cache_key: str, data: HistoricalPriceData) -> None:
        """Store data in cache."""
        self.memory_cache[cache_key] = data
        self._dirty_count += 1
        self._save_cache()  # Will only save if interval reached
    
    def _load_cache(self):
        """Load persistent cache from disk."""
        if not self.cache_file.exists():
            self.logger.debug("No cache file found, starting fresh")
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
                # Convert to HistoricalPriceData objects
                for key, data in cache_data.items():
                    candles = [OHLCCandle.from_dict(c) for c in data['candles']]
                    self.memory_cache[key] = HistoricalPriceData(
                        symbol=data['symbol'],
                        price_at_timestamp=data['price_at_timestamp'],
                        ath_in_window=data['ath_in_window'],
                        ath_timestamp=datetime.fromisoformat(data['ath_timestamp']),
                        days_to_ath=data['days_to_ath'],
                        candles=candles,
                        source=data['source']
                    )
                
                self.logger.info(f"Loaded {len(self.memory_cache)} cached historical prices")
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self, force: bool = False):
        """
        Save persistent cache to disk with batching.
        
        Args:
            force: Force save regardless of dirty count
        """
        # Skip if no changes and not forced
        if not force and self._dirty_count == 0:
            return
        
        # Skip if interval not reached and not forced
        if not force and self.save_interval > 0 and self._dirty_count < self.save_interval:
            return
        
        try:
            # Convert memory cache to serializable format
            cache_data = {}
            for key, data in self.memory_cache.items():
                cache_data[key] = {
                    'symbol': data.symbol,
                    'price_at_timestamp': data.price_at_timestamp,
                    'ath_in_window': data.ath_in_window,
                    'ath_timestamp': data.ath_timestamp.isoformat(),
                    'days_to_ath': data.days_to_ath,
                    'candles': [c.to_dict() for c in data.candles],
                    'source': data.source
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            self.logger.debug(f"Saved {len(cache_data)} entries to cache")
            self._dirty_count = 0  # Reset counter
        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")

    def flush(self):
        """Force save any pending cache entries."""
        self._save_cache(force=True)

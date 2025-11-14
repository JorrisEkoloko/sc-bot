"""Repository for coin cross-channel performance data.

Manages persistence of coin performance across multiple channels.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from domain.coin_cross_channel import CoinCrossChannel, ChannelCoinPerformance
from utils.logger import setup_logger


class CoinCrossChannelRepository:
    """Repository for coin cross-channel data."""
    
    def __init__(self, data_dir: str = "data/reputation", logger=None):
        """
        Initialize repository.
        
        Args:
            data_dir: Directory for data storage
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('CoinCrossChannelRepository')
        self.data_dir = Path(data_dir)
        self.data_file = self.data_dir / 'coins_cross_channel.json'
        self.coins: Dict[str, CoinCrossChannel] = {}
        
        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.load()
        
        self.logger.info(f"Coin cross-channel repository initialized with {len(self.coins)} coins")
    
    def get_coin(self, address: str) -> Optional[CoinCrossChannel]:
        """
        Get coin cross-channel data by address.
        
        Args:
            address: Token contract address
            
        Returns:
            CoinCrossChannel object or None if not found
        """
        return self.coins.get(address)
    
    def get_or_create_coin(self, address: str, symbol: str) -> CoinCrossChannel:
        """
        Get existing coin or create new one.
        
        Args:
            address: Token contract address
            symbol: Token symbol
            
        Returns:
            CoinCrossChannel object
        """
        if address not in self.coins:
            self.coins[address] = CoinCrossChannel(
                symbol=symbol,
                address=address,
                first_mentioned=datetime.now(),
                last_updated=datetime.now()
            )
            self.logger.info(f"Created new cross-channel tracking for {symbol} ({address[:10]}...)")
        
        return self.coins[address]
    
    def update_coin_performance(
        self,
        address: str,
        symbol: str,
        channel_name: str,
        signal_id: str,
        roi: float
    ):
        """
        Update coin performance for a specific channel.
        
        Args:
            address: Token contract address
            symbol: Token symbol
            channel_name: Channel name
            signal_id: Signal ID
            roi: ROI multiplier
        """
        coin = self.get_or_create_coin(address, symbol)
        
        # Update or create channel performance
        if channel_name not in coin.channel_performance:
            coin.channel_performance[channel_name] = ChannelCoinPerformance(
                channel_name=channel_name
            )
        
        channel_perf = coin.channel_performance[channel_name]
        
        # Update channel-specific metrics
        # Only increment mentions if this is a new signal (avoid counting same message multiple times)
        if signal_id not in channel_perf.signals:
            channel_perf.signals.append(signal_id)
            channel_perf.total_mentions += 1
        else:
            # Signal already tracked, just update the ROI
            self.logger.debug(f"Signal {signal_id} already tracked for {channel_name}, updating ROI only")
        
        # Recalculate channel average ROI
        if channel_perf.total_mentions == 1:
            channel_perf.average_roi = roi
            channel_perf.best_roi = roi
            channel_perf.worst_roi = roi
        else:
            # Update average using incremental formula
            old_avg = channel_perf.average_roi
            n = channel_perf.total_mentions
            channel_perf.average_roi = old_avg + (roi - old_avg) / n
            
            # Update best/worst
            channel_perf.best_roi = max(channel_perf.best_roi, roi)
            channel_perf.worst_roi = min(channel_perf.worst_roi, roi)
        
        channel_perf.last_mentioned = datetime.now()
        
        # Update coin-level aggregates
        self._recalculate_coin_aggregates(coin)
        
        coin.last_mentioned = datetime.now()
        coin.last_updated = datetime.now()
        
        self.logger.debug(
            f"Updated {symbol} performance for {channel_name}: "
            f"{roi:.3f}x (channel avg: {channel_perf.average_roi:.3f}x)"
        )
    
    def _recalculate_coin_aggregates(self, coin: CoinCrossChannel):
        """
        Recalculate coin-level aggregate metrics.
        
        Args:
            coin: CoinCrossChannel object to update
        """
        if not coin.channel_performance:
            return
        
        # Count channels and mentions
        coin.total_channels = len(coin.channel_performance)
        coin.total_mentions = sum(
            perf.total_mentions 
            for perf in coin.channel_performance.values()
        )
        
        # Calculate overall average ROI (weighted by mentions)
        total_weighted_roi = sum(
            perf.average_roi * perf.total_mentions
            for perf in coin.channel_performance.values()
        )
        coin.average_roi_all_channels = total_weighted_roi / coin.total_mentions if coin.total_mentions > 0 else 0.0
        
        # Find best and worst channels
        best_channel = None
        best_roi = 0.0
        worst_channel = None
        worst_roi = float('inf')
        
        for channel_name, perf in coin.channel_performance.items():
            if perf.average_roi > best_roi:
                best_roi = perf.average_roi
                best_channel = channel_name
            if perf.average_roi < worst_roi:
                worst_roi = perf.average_roi
                worst_channel = channel_name
        
        coin.best_channel = best_channel
        coin.worst_channel = worst_channel
        coin.best_channel_roi = best_roi
        coin.worst_channel_roi = worst_roi
        
        # Calculate consensus strength (inverse of coefficient of variation)
        if len(coin.channel_performance) > 1:
            rois = [perf.average_roi for perf in coin.channel_performance.values()]
            mean_roi = sum(rois) / len(rois)
            variance = sum((roi - mean_roi) ** 2 for roi in rois) / len(rois)
            std_dev = variance ** 0.5
            
            # Consensus strength: 1.0 = perfect agreement, 0.0 = high disagreement
            if mean_roi > 0:
                cv = std_dev / mean_roi  # Coefficient of variation
                coin.consensus_strength = max(0.0, 1.0 - cv)
            else:
                coin.consensus_strength = 0.0
        else:
            coin.consensus_strength = 1.0  # Only one channel, perfect "consensus"
        
        # Generate recommendation
        if coin.best_channel and coin.total_channels > 1:
            coin.recommendation = f"Follow {coin.best_channel} for {coin.symbol} calls ({best_roi:.2f}x avg)"
        elif coin.best_channel:
            coin.recommendation = f"Only {coin.best_channel} has called {coin.symbol} ({best_roi:.2f}x)"
        else:
            coin.recommendation = "Insufficient data"
        
        # Update cross-channel expected ROI (simple average for now, can enhance with TD learning)
        coin.expected_roi_cross_channel = coin.average_roi_all_channels
    
    def get_all_coins(self) -> Dict[str, CoinCrossChannel]:
        """
        Get all coins.
        
        Returns:
            Dictionary of address -> CoinCrossChannel
        """
        return self.coins
    
    def save(self):
        """Save coins to JSON file."""
        try:
            data = {
                address: coin.to_dict()
                for address, coin in self.coins.items()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved {len(self.coins)} coins to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Failed to save coins: {e}")
    
    def load(self):
        """Load coins from JSON file."""
        if not self.data_file.exists():
            self.logger.info("No existing coin cross-channel data found")
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.coins = {
                address: CoinCrossChannel.from_dict(coin_data)
                for address, coin_data in data.items()
            }
            
            self.logger.info(f"Loaded {len(self.coins)} coins from {self.data_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Corrupted coin data file: {e}. Starting fresh.")
            self.coins = {}
        except Exception as e:
            self.logger.error(f"Failed to load coins: {e}. Starting fresh.")
            self.coins = {}

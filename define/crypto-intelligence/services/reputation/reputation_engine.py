"""Channel reputation engine.

Manages channel reputations based on signal outcomes with ROI tracking.

Enhanced with multi-dimensional TD learning (Task 3):
- Level 1: Overall channel TD learning
- Level 2: Coin-specific TD learning  
- Level 3: Cross-channel coin tracking

Based on verified TD learning concepts:
- TD Learning: https://en.wikipedia.org/wiki/Temporal_difference_learning
- Formula: new_value = old_value + alpha * (actual - old_value)
- Learning rate alpha = 0.1 for gradual adaptation
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from utils.logger import setup_logger
from domain.signal_outcome import SignalOutcome
from domain.channel_reputation import (
    ChannelReputation, 
    TierPerformance,
    PredictionError,
    CoinSpecificPerformance
)
from domain.coin_cross_channel import CoinCrossChannel
from services.reputation.reputation_calculator import ReputationCalculator
from services.reputation.td_learning_service import TDLearningService
from repositories.file_storage.reputation_repository import ReputationRepository
from repositories.file_storage.coin_cross_channel_repository import CoinCrossChannelRepository


class ReputationEngine:
    """Manages channel reputations based on ROI outcomes."""
    
    def __init__(self, data_dir: str = "data/reputation", logger=None):
        """
        Initialize reputation engine.
        
        Args:
            data_dir: Directory for storing reputation data
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('ReputationEngine')
        self.repository = ReputationRepository(data_dir, self.logger)
        self.coin_cross_channel_repo = CoinCrossChannelRepository(data_dir, self.logger)
        self.reputations: Dict[str, ChannelReputation] = {}
        
        # Delegate TD learning to separate service (separation of concerns)
        self.td_learning_service = TDLearningService(self.logger)
        
        # Load existing reputations
        self.load_reputations()
        
        self.logger.info(f"Reputation engine initialized with {len(self.reputations)} channels")
    
    def update_reputation(self, channel_name: str, outcomes: List[SignalOutcome]) -> ChannelReputation:
        """
        Update or create reputation for a channel based on outcomes.
        
        Args:
            channel_name: Channel name
            outcomes: List of completed signal outcomes
            
        Returns:
            Updated ChannelReputation
        """
        # Get or create reputation
        if channel_name not in self.reputations:
            reputation = ChannelReputation(channel_name=channel_name)
            self.reputations[channel_name] = reputation
        else:
            reputation = self.reputations[channel_name]
        
        # Filter to completed outcomes only
        completed = [o for o in outcomes if o.is_complete]
        
        if not completed:
            self.logger.debug(f"No completed outcomes for {channel_name}")
            return reputation
        
        # Update basic counts
        reputation.total_signals = len(completed)
        
        # Calculate win rate
        winners, losers, neutral, win_rate = ReputationCalculator.calculate_win_rate(completed)
        reputation.winning_signals = winners
        reputation.losing_signals = losers
        reputation.neutral_signals = neutral
        reputation.win_rate = win_rate
        
        # Calculate ROI metrics
        avg_roi, median_roi, best_roi, worst_roi = ReputationCalculator.calculate_average_roi(completed)
        reputation.average_roi = avg_roi
        reputation.median_roi = median_roi
        reputation.best_roi = best_roi
        reputation.worst_roi = worst_roi
        
        # Calculate Sharpe ratio
        sharpe_ratio, std_dev = ReputationCalculator.calculate_sharpe_ratio(completed)
        reputation.sharpe_ratio = sharpe_ratio
        reputation.roi_std_dev = std_dev
        
        # Calculate speed metrics
        avg_time_to_ath, avg_time_to_2x, speed_score = ReputationCalculator.calculate_speed_score(completed)
        reputation.avg_time_to_ath = avg_time_to_ath
        reputation.avg_time_to_2x = avg_time_to_2x
        reputation.speed_score = speed_score
        
        # Calculate confidence metrics
        avg_confidence, avg_hdrb_score = ReputationCalculator.calculate_confidence_metrics(completed)
        reputation.avg_confidence = avg_confidence
        reputation.avg_hdrb_score = avg_hdrb_score
        
        # Calculate tier-specific performance
        for tier in ['micro', 'small', 'mid', 'large']:
            tier_metrics = ReputationCalculator.calculate_tier_performance(completed, tier)
            reputation.tier_performance[tier] = TierPerformance(
                total_calls=tier_metrics['total_calls'],
                winning_calls=tier_metrics['winning_calls'],
                win_rate=tier_metrics['win_rate'],
                avg_roi=tier_metrics['avg_roi'],
                sharpe_ratio=tier_metrics['sharpe_ratio']
            )
        
        # Calculate composite reputation score
        reputation.reputation_score = ReputationCalculator.calculate_composite_score(reputation)
        
        # Determine reputation tier
        reputation.reputation_tier = ReputationCalculator.determine_tier(
            reputation.reputation_score,
            reputation.total_signals
        )
        
        # Initialize expected ROI if not set (for TD learning - Task 3)
        if reputation.expected_roi == 1.0 and reputation.average_roi > 0:
            reputation.expected_roi = reputation.average_roi
        
        # Update metadata
        if completed:
            dates = [o.entry_timestamp for o in completed if o.entry_timestamp]
            if dates:
                reputation.first_signal_date = min(dates)
                reputation.last_signal_date = max(dates)
        reputation.last_updated = datetime.now()
        
        # Save to disk
        self.save_reputations()
        
        self.logger.info(
            f"Updated reputation for {channel_name}: "
            f"Score={reputation.reputation_score:.1f}, "
            f"Tier={reputation.reputation_tier}, "
            f"Win Rate={reputation.win_rate:.1f}%, "
            f"Avg ROI={reputation.average_roi:.3f}x"
        )
        
        return reputation
    
    def get_reputation(self, channel_name: str) -> Optional[ChannelReputation]:
        """
        Get reputation for a channel.
        
        Args:
            channel_name: Channel name
            
        Returns:
            ChannelReputation or None if not found
        """
        return self.reputations.get(channel_name)
    
    def get_all_reputations(self) -> List[ChannelReputation]:
        """
        Get all channel reputations sorted by score.
        
        Returns:
            List of ChannelReputation objects sorted by score (descending)
        """
        return sorted(
            self.reputations.values(),
            key=lambda r: r.reputation_score,
            reverse=True
        )
    
    def save_reputations(self) -> None:
        """Save reputations using repository."""
        self.repository.save(self.reputations)
    
    def load_reputations(self) -> None:
        """Load reputations using repository."""
        self.reputations = self.repository.load()

    
    # ========================================================================
    # PART 8 TASK 3: Multi-Dimensional TD Learning (Delegated to TDLearningService)
    # ========================================================================
    
    def apply_td_learning(
        self,
        channel_name: str,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 1: Overall Channel TD Learning (delegates to service).
        
        Args:
            channel_name: Channel name
            outcome: Completed signal outcome with actual ROI
        """
        reputation = self.reputations.get(channel_name)
        if not reputation:
            self.logger.warning(f"No reputation found for {channel_name}")
            return
        
        # Delegate to TD learning service
        self.td_learning_service.apply_overall_td_learning(reputation, outcome)
    
    def apply_coin_specific_td_learning(
        self,
        channel_name: str,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 2: Coin-Specific TD Learning (delegates to service).
        
        Args:
            channel_name: Channel name
            outcome: Completed signal outcome
        """
        reputation = self.reputations.get(channel_name)
        if not reputation:
            return
        
        # Delegate to TD learning service
        self.td_learning_service.apply_coin_specific_td_learning(reputation, outcome)
    
    def update_cross_channel_coin_performance(
        self,
        channel_name: str,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 3: Cross-Channel Coin Tracking (delegates to service).
        
        Args:
            channel_name: Channel name
            outcome: Completed signal outcome
        """
        # Delegate to TD learning service
        self.td_learning_service.update_cross_channel_performance(
            self.coin_cross_channel_repo,
            channel_name,
            outcome
        )
    
    def get_multi_dimensional_prediction(
        self,
        channel_name: str,
        coin_address: str,
        coin_symbol: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Get multi-dimensional ROI prediction (delegates to service).
        
        Args:
            channel_name: Channel name
            coin_address: Token address
            coin_symbol: Token symbol
            
        Returns:
            Tuple of (weighted_prediction, breakdown_dict)
        """
        reputation = self.reputations.get(channel_name)
        if not reputation:
            return 1.5, {}  # Default neutral prediction
        
        # Delegate to TD learning service
        return self.td_learning_service.get_multi_dimensional_prediction(
            reputation,
            self.coin_cross_channel_repo,
            coin_address,
            coin_symbol
        )
    
    def save_reputations(self) -> None:
        """Save reputations using repository."""
        self.repository.save(self.reputations)
    
    def load_reputations(self) -> None:
        """Load reputations using repository."""
        self.reputations = self.repository.load()

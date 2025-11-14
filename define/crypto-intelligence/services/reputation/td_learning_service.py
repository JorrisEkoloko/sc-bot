"""Temporal Difference Learning service for reputation prediction.

Handles multi-dimensional TD learning:
- Level 1: Overall channel TD learning
- Level 2: Coin-specific TD learning
- Level 3: Cross-channel coin tracking

Based on verified TD learning concepts:
- TD Learning: https://en.wikipedia.org/wiki/Temporal_difference_learning
- Formula: new_value = old_value + alpha * (actual - old_value)
"""
from datetime import datetime
from typing import Dict, Tuple

from utils.logger import setup_logger
from domain.signal_outcome import SignalOutcome
from domain.channel_reputation import (
    ChannelReputation,
    PredictionError,
    CoinSpecificPerformance
)
from repositories.file_storage.coin_cross_channel_repository import CoinCrossChannelRepository


class TDLearningService:
    """Handles multi-dimensional TD learning for reputation prediction."""
    
    def __init__(self, logger=None):
        """
        Initialize TD learning service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('TDLearningService')
        self.alpha = 0.1  # Learning rate for gradual adaptation
        self.recency_lambda = 0.01  # Decay factor for recency weighting
    
    def apply_overall_td_learning(
        self,
        reputation: ChannelReputation,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 1: Overall Channel TD Learning.
        
        Updates the channel's expected ROI using temporal difference learning:
        new_expected_roi = old_expected_roi + alpha * (actual_roi - old_expected_roi)
        
        Args:
            reputation: Channel reputation to update
            outcome: Completed signal outcome with actual ROI
        """
        predicted_roi = reputation.expected_roi
        actual_roi = outcome.ath_multiplier
        error = actual_roi - predicted_roi
        error_percentage = (error / predicted_roi) * 100 if predicted_roi > 0 else 0.0
        
        # Apply TD learning formula
        new_expected_roi = predicted_roi + (self.alpha * error)
        
        # Create detailed error record
        prediction_error = self._create_prediction_error(
            outcome, predicted_roi, actual_roi, error, error_percentage
        )
        
        # Store error (no limit - track ALL errors)
        reputation.prediction_error_history.append(prediction_error)
        
        # Update statistics
        reputation.total_predictions += 1
        
        # Check if prediction was accurate (within 10%)
        if abs(error_percentage) <= 10.0:
            reputation.correct_predictions += 1
        
        # Track over/underestimations
        if error > 0:
            reputation.underestimations += 1
        elif error < 0:
            reputation.overestimations += 1
        
        # Calculate MAE and MSE
        self._update_error_statistics(reputation)
        
        # Update expected ROI
        old_expected = reputation.expected_roi
        reputation.expected_roi = new_expected_roi
        
        # Calculate accuracy percentage
        accuracy = (reputation.correct_predictions / reputation.total_predictions * 100) if reputation.total_predictions > 0 else 0.0
        
        self.logger.info(
            f"TD Learning (Overall): Expected ROI {old_expected:.3f}x → {new_expected_roi:.3f}x "
            f"(error: {error:+.3f}x, {error_percentage:+.1f}%)"
        )
        self.logger.info(
            f"Total Predictions: {reputation.total_predictions}, "
            f"Accuracy: {accuracy:.1f}%, "
            f"MAE: {reputation.mean_absolute_error:.3f}x"
        )
    
    def apply_coin_specific_td_learning(
        self,
        reputation: ChannelReputation,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 2: Coin-Specific TD Learning.
        
        Updates the channel's expected ROI for this specific coin.
        First mention initializes with actual outcome.
        Subsequent mentions update using TD learning.
        
        Args:
            reputation: Channel reputation to update
            outcome: Completed signal outcome
        """
        address = outcome.address
        symbol = outcome.symbol
        actual_roi = outcome.ath_multiplier
        
        # Get or create coin-specific performance
        if address not in reputation.coin_specific_performance:
            # First mention: Initialize with actual outcome
            self._initialize_coin_performance(reputation, address, symbol, actual_roi, outcome)
        else:
            # Subsequent mention: Apply TD learning
            self._update_coin_performance(reputation, address, symbol, actual_roi, outcome)
    
    def _initialize_coin_performance(
        self,
        reputation: ChannelReputation,
        address: str,
        symbol: str,
        actual_roi: float,
        outcome: SignalOutcome
    ) -> None:
        """Initialize coin-specific performance on first mention."""
        coin_perf = CoinSpecificPerformance(
            symbol=symbol,
            address=address,
            total_mentions=1,
            signals=[str(outcome.message_id)],
            average_roi=actual_roi,
            expected_roi=actual_roi,  # Initialize with first outcome
            best_roi=actual_roi,
            worst_roi=actual_roi,
            last_mentioned=datetime.now()
        )
        reputation.coin_specific_performance[address] = coin_perf
        
        self.logger.info(
            f"TD Learning (Coin-Specific): {symbol} "
            f"First signal: Initialize expected ROI = {actual_roi:.3f}x"
        )
    
    def _update_coin_performance(
        self,
        reputation: ChannelReputation,
        address: str,
        symbol: str,
        actual_roi: float,
        outcome: SignalOutcome
    ) -> None:
        """Update coin-specific performance on subsequent mentions."""
        coin_perf = reputation.coin_specific_performance[address]
        
        predicted_roi = coin_perf.expected_roi
        error = actual_roi - predicted_roi
        error_percentage = (error / predicted_roi) * 100 if predicted_roi > 0 else 0.0
        
        # Apply TD learning
        new_expected_roi = predicted_roi + (self.alpha * error)
        
        # Create error record
        prediction_error = self._create_prediction_error(
            outcome, predicted_roi, actual_roi, error, error_percentage
        )
        
        # Update coin-specific tracking
        coin_perf.prediction_error_history.append(prediction_error)
        coin_perf.total_predictions += 1
        
        if abs(error_percentage) <= 10.0:
            coin_perf.correct_predictions += 1
        
        if error > 0:
            coin_perf.underestimations += 1
        elif error < 0:
            coin_perf.overestimations += 1
        
        # Calculate MAE
        all_errors = [abs(err.error) for err in coin_perf.prediction_error_history]
        coin_perf.mean_absolute_error = sum(all_errors) / len(all_errors) if all_errors else 0.0
        
        # Update expected ROI
        coin_perf.expected_roi = new_expected_roi
        
        # Update other metrics
        coin_perf.total_mentions += 1
        if str(outcome.message_id) not in coin_perf.signals:
            coin_perf.signals.append(str(outcome.message_id))
        
        # Update average ROI (incremental)
        n = coin_perf.total_mentions
        coin_perf.average_roi = coin_perf.average_roi + (actual_roi - coin_perf.average_roi) / n
        
        coin_perf.best_roi = max(coin_perf.best_roi, actual_roi)
        coin_perf.worst_roi = min(coin_perf.worst_roi, actual_roi)
        coin_perf.last_mentioned = datetime.now()
        
        # Calculate accuracy
        accuracy = (coin_perf.correct_predictions / coin_perf.total_predictions * 100) if coin_perf.total_predictions > 0 else 0.0
        
        self.logger.info(
            f"TD Learning (Coin-Specific): {symbol} "
            f"Expected ROI {predicted_roi:.3f}x → {new_expected_roi:.3f}x "
            f"(error: {error:+.3f}x)"
        )
        self.logger.info(
            f"Coin Predictions: {coin_perf.total_predictions}, "
            f"Coin Accuracy: {accuracy:.1f}%, "
            f"Coin MAE: {coin_perf.mean_absolute_error:.3f}x"
        )
    
    def update_cross_channel_performance(
        self,
        coin_repo: CoinCrossChannelRepository,
        channel_name: str,
        outcome: SignalOutcome
    ) -> None:
        """
        Apply Level 3: Cross-Channel Coin Tracking.
        
        Updates how this coin performs across all channels.
        Identifies best/worst channels for this coin.
        
        Args:
            coin_repo: Cross-channel repository
            channel_name: Channel name
            outcome: Completed signal outcome
        """
        address = outcome.address
        symbol = outcome.symbol
        actual_roi = outcome.ath_multiplier
        signal_id = str(outcome.message_id)
        
        # Update coin cross-channel performance
        coin_repo.update_coin_performance(
            address=address,
            symbol=symbol,
            channel_name=channel_name,
            signal_id=signal_id,
            roi=actual_roi
        )
        
        # Get updated coin data
        coin = coin_repo.get_coin(address)
        if coin:
            self.logger.info(
                f"Cross-Channel Update: {symbol} - "
                f"Best: {coin.best_channel} ({coin.best_channel_roi:.3f}x), "
                f"Overall: {coin.average_roi_all_channels:.3f}x across {coin.total_channels} channels"
            )
            
            if coin.recommendation:
                self.logger.info(f"Recommendation: {coin.recommendation}")
        
        # Save cross-channel data
        coin_repo.save()
    
    def get_multi_dimensional_prediction(
        self,
        reputation: ChannelReputation,
        coin_repo: CoinCrossChannelRepository,
        coin_address: str,
        coin_symbol: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Get multi-dimensional ROI prediction combining all 3 levels.
        
        Weighted prediction:
        - Overall channel: 40% weight
        - Coin-specific: 50% weight (most important!)
        - Cross-channel: 10% weight
        
        Args:
            reputation: Channel reputation
            coin_repo: Cross-channel repository
            coin_address: Token address
            coin_symbol: Token symbol
            
        Returns:
            Tuple of (weighted_prediction, breakdown_dict)
        """
        # Level 1: Overall channel prediction
        overall_prediction = reputation.expected_roi
        overall_weight = 0.40
        
        # Level 2: Coin-specific prediction
        coin_specific_prediction = overall_prediction  # Default to overall
        coin_specific_weight = 0.50
        
        if coin_address in reputation.coin_specific_performance:
            coin_perf = reputation.coin_specific_performance[coin_address]
            coin_specific_prediction = coin_perf.expected_roi
        
        # Level 3: Cross-channel prediction
        cross_channel_prediction = overall_prediction  # Default to overall
        cross_channel_weight = 0.10
        
        coin = coin_repo.get_coin(coin_address)
        if coin:
            cross_channel_prediction = coin.expected_roi_cross_channel
        
        # Calculate weighted prediction
        weighted_prediction = (
            (overall_prediction * overall_weight) +
            (coin_specific_prediction * coin_specific_weight) +
            (cross_channel_prediction * cross_channel_weight)
        )
        
        breakdown = {
            'overall': overall_prediction,
            'coin_specific': coin_specific_prediction,
            'cross_channel': cross_channel_prediction,
            'weighted': weighted_prediction,
            'overall_weight': overall_weight,
            'coin_specific_weight': coin_specific_weight,
            'cross_channel_weight': cross_channel_weight
        }
        
        self.logger.info(
            f"Prediction: Overall {overall_prediction:.3f}x (40%), "
            f"Coin-Specific {coin_specific_prediction:.3f}x (50%), "
            f"Cross-Channel {cross_channel_prediction:.3f}x (10%) = {weighted_prediction:.3f}x"
        )
        
        return weighted_prediction, breakdown
    
    def _create_prediction_error(
        self,
        outcome: SignalOutcome,
        predicted: float,
        actual: float,
        error: float,
        error_percentage: float
    ) -> PredictionError:
        """Create prediction error record."""
        return PredictionError(
            timestamp=datetime.now().isoformat(),
            signal_id=str(outcome.message_id),
            coin_symbol=outcome.symbol,
            coin_address=outcome.address,
            predicted_roi=predicted,
            actual_roi=actual,
            error=error,
            error_percentage=error_percentage,
            entry_price=outcome.entry_price,
            ath_price=outcome.ath_price,
            days_to_ath=outcome.days_to_ath,
            outcome_category=outcome.outcome_category
        )
    
    def _update_error_statistics(self, reputation: ChannelReputation) -> None:
        """Update MAE and MSE statistics."""
        all_errors = [abs(err.error) for err in reputation.prediction_error_history]
        reputation.mean_absolute_error = sum(all_errors) / len(all_errors) if all_errors else 0.0
        
        squared_errors = [err.error ** 2 for err in reputation.prediction_error_history]
        reputation.mean_squared_error = sum(squared_errors) / len(squared_errors) if squared_errors else 0.0

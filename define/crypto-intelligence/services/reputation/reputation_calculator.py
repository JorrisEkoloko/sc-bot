"""Reputation calculation utilities.

Calculate channel reputation metrics from ROI outcomes.
"""
import statistics
from typing import List

from domain.signal_outcome import SignalOutcome
from domain.channel_reputation import ChannelReputation, REPUTATION_TIERS


class ReputationCalculator:
    """Calculate reputation metrics from signal outcomes."""
    
    @staticmethod
    def calculate_win_rate(outcomes: List[SignalOutcome]) -> tuple[int, int, int, float]:
        """
        Calculate win rate from signal outcomes.
        
        Winner classification is market-tier aware:
        - Large-cap: ROI ≥ 1.2x (20% gain)
        - Mid-cap: ROI ≥ 1.5x (50% gain)
        - Small/Micro-cap: ROI ≥ 2.0x (100% gain)
        
        Args:
            outcomes: List of completed signal outcomes
            
        Returns:
            tuple[int, int, int, float]: (winners, losers, neutral, win_rate)
        """
        if not outcomes:
            return (0, 0, 0, 0.0)
        
        # Use the is_winner field which is already market-tier aware
        winners = sum(1 for o in outcomes if o.is_winner)
        losers = sum(1 for o in outcomes if o.ath_multiplier < 1.0)
        neutral = len(outcomes) - winners - losers
        win_rate = (winners / len(outcomes)) * 100
        
        return (winners, losers, neutral, win_rate)
    
    @staticmethod
    def calculate_average_roi(outcomes: List[SignalOutcome]) -> tuple[float, float, float, float]:
        """
        Calculate ROI statistics from signal outcomes.
        
        Args:
            outcomes: List of completed signal outcomes
            
        Returns:
            tuple[float, float, float, float]: (average, median, best, worst)
        """
        if not outcomes:
            return (0.0, 0.0, 0.0, 0.0)
        
        roi_values = [o.ath_multiplier for o in outcomes]
        
        average = statistics.mean(roi_values)
        median = statistics.median(roi_values)
        best = max(roi_values)
        worst = min(roi_values)
        
        return (average, median, best, worst)
    
    @staticmethod
    def calculate_sharpe_ratio(outcomes: List[SignalOutcome]) -> tuple[float, float]:
        """
        Calculate Sharpe ratio (risk-adjusted returns).
        
        Formula (validated by Investopedia):
        Sharpe = (avg_roi - 1.0) / std_dev(roi)
        
        Args:
            outcomes: List of completed signal outcomes
            
        Returns:
            tuple[float, float]: (sharpe_ratio, std_dev)
        """
        if len(outcomes) < 2:
            return (0.0, 0.0)
        
        roi_values = [o.ath_multiplier for o in outcomes]
        
        avg_roi = statistics.mean(roi_values)
        std_dev = statistics.stdev(roi_values)
        
        if std_dev == 0:
            return (0.0, 0.0)
        
        sharpe_ratio = (avg_roi - 1.0) / std_dev
        
        return (sharpe_ratio, std_dev)
    
    @staticmethod
    def calculate_speed_score(outcomes: List[SignalOutcome]) -> tuple[float, float, float]:
        """
        Calculate speed metrics (time to ATH).
        
        Args:
            outcomes: List of completed signal outcomes
            
        Returns:
            tuple[float, float, float]: (avg_time_to_ath, avg_time_to_2x, speed_score)
        """
        if not outcomes:
            return (0.0, 0.0, 0.0)
        
        # Average time to ATH (all signals)
        ath_times = [o.days_to_ath for o in outcomes if o.days_to_ath > 0]
        avg_time_to_ath = statistics.mean(ath_times) if ath_times else 0.0
        
        # Average time to 2x (winners only)
        winner_times = [o.days_to_ath for o in outcomes if o.is_winner and o.days_to_ath > 0]
        avg_time_to_2x = statistics.mean(winner_times) if winner_times else 0.0
        
        # Speed score: 0-100 (faster = higher)
        # 1 day = 100, 7 days = 50, 30 days = 0
        if avg_time_to_ath > 0:
            speed_score = max(0, min(100, 100 - (avg_time_to_ath - 1) * 3.33))
        else:
            speed_score = 0.0
        
        return (avg_time_to_ath, avg_time_to_2x, speed_score)
    
    @staticmethod
    def calculate_confidence_metrics(outcomes: List[SignalOutcome]) -> tuple[float, float]:
        """
        Calculate average confidence metrics.
        
        Args:
            outcomes: List of completed signal outcomes
            
        Returns:
            tuple[float, float]: (avg_confidence, avg_hdrb_score)
        """
        if not outcomes:
            return (0.0, 0.0)
        
        confidences = [o.entry_confidence for o in outcomes if o.entry_confidence > 0]
        hdrb_scores = [o.hdrb_score for o in outcomes if o.hdrb_score > 0]
        
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        avg_hdrb_score = statistics.mean(hdrb_scores) if hdrb_scores else 0.0
        
        return (avg_confidence, avg_hdrb_score)
    
    @staticmethod
    def calculate_composite_score(reputation: ChannelReputation) -> float:
        """
        Calculate composite reputation score (0-100).
        
        Weighted formula:
        - Win Rate × 30% (most important psychologically)
        - Avg ROI × 25% (financial outcome)
        - Sharpe Ratio × 20% (risk-adjusted)
        - Speed × 15% (meme coins move fast)
        - Confidence × 10% (signal quality)
        
        Args:
            reputation: Channel reputation with calculated metrics
            
        Returns:
            float: Composite score (0-100)
        """
        # Normalize components to 0-100 scale
        win_rate_score = reputation.win_rate  # Already 0-100
        
        # ROI score: normalize to 0-100 (2x = 50, 5x = 100)
        roi_score = min(100, (reputation.average_roi - 1.0) * 50)
        
        # Sharpe score: normalize to 0-100 (sharpe of 2 = 100)
        sharpe_score = min(100, reputation.sharpe_ratio * 50)
        
        # Speed score: already 0-100
        speed_score = reputation.speed_score
        
        # Confidence score: convert to 0-100
        confidence_score = reputation.avg_confidence * 100
        
        # Weighted composite
        score = (
            win_rate_score * 0.30 +
            roi_score * 0.25 +
            sharpe_score * 0.20 +
            speed_score * 0.15 +
            confidence_score * 0.10
        )
        
        return min(100, max(0, score))
    
    @staticmethod
    def determine_tier(score: float, total_signals: int) -> str:
        """
        Determine reputation tier based on score and signal count.
        
        Args:
            score: Reputation score (0-100)
            total_signals: Total number of signals
            
        Returns:
            str: Reputation tier name
        """
        # Require minimum 10 signals for tier classification
        if total_signals < 10:
            return "Unproven"
        
        # Find matching tier
        for tier_name, tier_range in REPUTATION_TIERS.items():
            if tier_range is None:  # Unproven
                continue
            min_score, max_score = tier_range
            if min_score <= score < max_score:
                return tier_name
        
        # Default to Unreliable if score is very low
        return "Unreliable"
    
    @staticmethod
    def calculate_tier_performance(outcomes: List[SignalOutcome], tier: str) -> dict:
        """
        Calculate performance metrics for a specific market cap tier.
        
        Args:
            outcomes: List of completed signal outcomes
            tier: Market cap tier (micro/small/mid/large)
            
        Returns:
            dict: Tier performance metrics
        """
        tier_outcomes = [o for o in outcomes if o.market_tier == tier]
        
        if not tier_outcomes:
            return {
                'total_calls': 0,
                'winning_calls': 0,
                'win_rate': 0.0,
                'avg_roi': 0.0,
                'sharpe_ratio': 0.0
            }
        
        winners, _, _, win_rate = ReputationCalculator.calculate_win_rate(tier_outcomes)
        avg_roi, _, _, _ = ReputationCalculator.calculate_average_roi(tier_outcomes)
        sharpe_ratio, _ = ReputationCalculator.calculate_sharpe_ratio(tier_outcomes)
        
        return {
            'total_calls': len(tier_outcomes),
            'winning_calls': winners,
            'win_rate': win_rate,
            'avg_roi': avg_roi,
            'sharpe_ratio': sharpe_ratio
        }

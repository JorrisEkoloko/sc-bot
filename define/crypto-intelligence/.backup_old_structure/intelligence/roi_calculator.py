"""ROI calculation utilities.

Core ROI calculation formulas validated by Investopedia.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from intelligence.signal_outcome import SignalOutcome, CheckpointData, CHECKPOINTS


class ROICalculator:
    """Calculate ROI (Return on Investment) for crypto signals."""
    
    @staticmethod
    def calculate_roi(entry_price: float, current_price: float) -> tuple[float, float]:
        """
        Calculate ROI percentage and multiplier.
        
        Formula (validated by Investopedia):
        - ROI Percentage = ((current_price - entry_price) / entry_price) * 100
        - ROI Multiplier = current_price / entry_price
        
        Examples:
        - Entry $1.00, Current $2.00 → ROI = 100%, Multiplier = 2.0x
        - Entry $1.47, Current $4.78 → ROI = 225.2%, Multiplier = 3.252x
        - Entry $14.96, Current $13.94 → ROI = -6.8%, Multiplier = 0.932x
        
        Args:
            entry_price: Price at entry
            current_price: Current price
            
        Returns:
            tuple[float, float]: (roi_percentage, roi_multiplier)
        """
        if entry_price <= 0:
            return (0.0, 0.0)
        
        roi_percentage = ((current_price - entry_price) / entry_price) * 100
        roi_multiplier = current_price / entry_price
        
        return (roi_percentage, roi_multiplier)
    
    @staticmethod
    def update_ath(outcome: SignalOutcome, current_price: float) -> bool:
        """
        Update ATH (All-Time High) if current price is higher.
        
        Args:
            outcome: Signal outcome to update
            current_price: Current price
            
        Returns:
            bool: True if ATH was updated
        """
        if current_price > outcome.ath_price:
            outcome.ath_price = current_price
            _, roi_multiplier = ROICalculator.calculate_roi(outcome.entry_price, current_price)
            outcome.ath_multiplier = roi_multiplier
            outcome.ath_timestamp = datetime.now(timezone.utc)
            
            if outcome.entry_timestamp:
                outcome.days_to_ath = (datetime.now(timezone.utc) - outcome.entry_timestamp).total_seconds() / 86400
            
            return True
        return False
    
    @staticmethod
    def check_checkpoints(outcome: SignalOutcome, current_price: float) -> List[str]:
        """
        Check which checkpoints have been reached and update them.
        
        Args:
            outcome: Signal outcome to check
            current_price: Current price
            
        Returns:
            List of checkpoint names that were just reached
        """
        if not outcome.entry_timestamp:
            return []
        
        elapsed = datetime.now(timezone.utc) - outcome.entry_timestamp
        reached = []
        
        for name, interval in CHECKPOINTS.items():
            checkpoint = outcome.checkpoints[name]
            
            # Skip if already reached
            if checkpoint.reached:
                continue
            
            # Check if enough time has elapsed
            if elapsed >= interval:
                roi_percentage, roi_multiplier = ROICalculator.calculate_roi(
                    outcome.entry_price, current_price
                )
                
                # Calculate checkpoint timestamp from entry time + interval
                checkpoint.timestamp = outcome.entry_timestamp + interval
                checkpoint.price = current_price
                checkpoint.roi_percentage = roi_percentage
                checkpoint.roi_multiplier = roi_multiplier
                checkpoint.reached = True
                
                reached.append(name)
        
        return reached
    
    @staticmethod
    def categorize_outcome(ath_multiplier: float) -> tuple[bool, str]:
        """
        Categorize outcome based on ATH ROI multiplier.
        
        Categories:
        - moon: 5x+ (400%+ gain)
        - great: 3-5x (200-400% gain)
        - good: 2-3x (100-200% gain)
        - break_even: 1-2x (0-100% gain)
        - loss: <1x (negative ROI)
        
        Args:
            ath_multiplier: ATH ROI multiplier
            
        Returns:
            tuple[bool, str]: (is_winner, outcome_category)
        """
        is_winner = ath_multiplier >= 2.0
        
        if ath_multiplier >= 5.0:
            category = "moon"
        elif ath_multiplier >= 3.0:
            category = "great"
        elif ath_multiplier >= 2.0:
            category = "good"
        elif ath_multiplier >= 1.0:
            category = "break_even"
        else:
            category = "loss"
        
        return (is_winner, category)
    
    @staticmethod
    def check_stop_conditions(outcome: SignalOutcome) -> tuple[bool, str]:
        """
        Check if tracking should stop based on conditions.
        
        Stop conditions:
        - 30 days elapsed
        - 90% loss from ATH
        - Zero volume (not implemented here, requires external data)
        
        Args:
            outcome: Signal outcome to check
            
        Returns:
            tuple[bool, str]: (should_stop, reason)
        """
        if not outcome.entry_timestamp:
            return (False, "")
        
        elapsed = datetime.now(timezone.utc) - outcome.entry_timestamp
        
        # Check 30-day limit
        if elapsed >= timedelta(days=30):
            return (True, "30d_elapsed")
        
        # Check 90% loss from ATH
        if outcome.ath_price > 0:
            loss_from_ath = (outcome.ath_price - outcome.current_price) / outcome.ath_price
            if loss_from_ath >= 0.90:
                return (True, "90%_loss")
        
        return (False, "")

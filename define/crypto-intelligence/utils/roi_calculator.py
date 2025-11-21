"""ROI calculation utilities.

Pure mathematical functions for calculating Return on Investment (ROI).
Formula validated by Investopedia: https://www.investopedia.com/terms/r/returnoninvestment.asp

ROI Formula:
    ROI% = ((Current Value - Cost) / Cost) × 100
    ROI Multiplier = Current Value / Cost

Examples:
    Entry $1.00 → Current $2.00 = 100% ROI (2.0x multiplier)
    Entry $1.47 → Current $4.78 = 225.2% ROI (3.252x multiplier)
    Entry $14.96 → Current $13.94 = -6.8% ROI (0.932x multiplier)
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from domain.signal_outcome import SignalOutcome, CHECKPOINTS


class ROICalculator:
    """Pure utility functions for ROI calculations."""
    
    @staticmethod
    def calculate_roi(entry_price: float, current_price: float) -> Tuple[float, float]:
        """
        Calculate ROI percentage and multiplier.
        
        Args:
            entry_price: Price at entry
            current_price: Current price
            
        Returns:
            Tuple[float, float]: (roi_percentage, roi_multiplier)
            
        Examples:
            >>> ROICalculator.calculate_roi(1.00, 2.00)
            (100.0, 2.0)
            >>> ROICalculator.calculate_roi(1.47, 4.78)
            (225.17, 3.252)
        """
        # Handle edge cases to prevent division by zero
        if entry_price <= 0 or current_price <= 0:
            return (0.0, 1.0)  # No movement if prices are invalid
        
        roi_percentage = ((current_price - entry_price) / entry_price) * 100
        roi_multiplier = current_price / entry_price
        
        return (roi_percentage, roi_multiplier)
    
    @staticmethod
    def update_ath(outcome: SignalOutcome, current_price: float) -> bool:
        """
        Update ATH (All-Time High) if current price is higher.
        
        Args:
            outcome: Signal outcome to update (mutated in place)
            current_price: Current price
            
        Returns:
            bool: True if ATH was updated, False otherwise
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
        
        Checkpoints: 1h, 4h, 24h, 3d, 7d, 30d
        
        Args:
            outcome: Signal outcome to check (mutated in place)
            current_price: Current price
            
        Returns:
            List[str]: Names of checkpoints that were just reached
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
    def categorize_outcome(ath_multiplier: float) -> Tuple[bool, str]:
        """
        Categorize outcome based on ATH ROI multiplier.
        
        Categories:
            - moon: 5x+ (400%+ gain)
            - great: 3-5x (200-400% gain)
            - good: 2-3x (100-200% gain)
            - moderate: 1.5-2x (50-100% gain)
            - break_even: 1-1.5x (0-50% gain)
            - loss: <1x (negative ROI)
        
        Args:
            ath_multiplier: ATH ROI multiplier
            
        Returns:
            Tuple[bool, str]: (is_winner, outcome_category)
        """
        is_winner = ath_multiplier >= 1.5  # 50%+ gain threshold
        
        if ath_multiplier >= 5.0:
            category = "moon"
        elif ath_multiplier >= 3.0:
            category = "great"
        elif ath_multiplier >= 2.0:
            category = "good"
        elif ath_multiplier >= 1.5:
            category = "moderate"
        elif ath_multiplier >= 1.0:
            category = "break_even"
        else:
            category = "loss"
        
        return (is_winner, category)
    
    @staticmethod
    def check_stop_conditions(outcome: SignalOutcome) -> Tuple[bool, str]:
        """
        Check if tracking should stop based on conditions.
        
        Stop conditions:
            - 30 days elapsed
            - 90% loss from ATH
        
        Args:
            outcome: Signal outcome to check
            
        Returns:
            Tuple[bool, str]: (should_stop, reason)
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
    
    @staticmethod
    def analyze_trajectory(day_7_multiplier: float, day_30_multiplier: float, ath_multiplier: float = None) -> Tuple[str, float]:
        """
        Analyze performance trajectory from day 7 to day 30, considering ATH.
        
        Determines if performance improved or crashed after day 7, and calculates
        crash severity if applicable. When ATH is provided, considers whether
        the signal crashed from its peak even if day 30 > day 7.
        
        Args:
            day_7_multiplier: ROI multiplier at day 7
            day_30_multiplier: ROI multiplier at day 30
            ath_multiplier: Optional ATH multiplier (0-30 days)
            
        Returns:
            Tuple[str, float]: (trajectory, crash_severity_percentage)
            - trajectory: "crashed" if significantly down from peak or day 7, "improved" otherwise
            - crash_severity: percentage drop from peak or day 7 (0.0 if improved)
            
        Examples:
            >>> ROICalculator.analyze_trajectory(2.0, 1.0)
            ("crashed", 50.0)
            >>> ROICalculator.analyze_trajectory(2.0, 3.0)
            ("improved", 0.0)
            >>> ROICalculator.analyze_trajectory(0.93, 1.00, 1.04)
            ("crashed", 3.8)  # Crashed from 1.04x ATH to 1.00x
        """
        # If ATH is provided, check if we crashed from the peak
        if ath_multiplier and ath_multiplier > day_30_multiplier:
            # Calculate drop from ATH to day 30
            drop_from_ath = ((ath_multiplier - day_30_multiplier) / ath_multiplier) * 100
            
            # Consider it a crash if dropped more than 2% from ATH
            # (even small drops from peak indicate failure to hold gains)
            if drop_from_ath > 2.0:
                return ("crashed", drop_from_ath)
        
        # Otherwise, compare day 7 to day 30
        if day_30_multiplier < day_7_multiplier:
            # Calculate crash severity as percentage drop
            crash_severity = ((day_7_multiplier - day_30_multiplier) / day_7_multiplier) * 100
            return ("crashed", crash_severity)
        else:
            # Performance improved or stayed the same
            return ("improved", 0.0)
    
    @staticmethod
    def determine_peak_timing(days_to_ath: float) -> str:
        """
        Determine if peak came early or late.
        
        Classification:
            - early_peaker: ATH within first 7 days
            - late_peaker: ATH after day 7
        
        Args:
            days_to_ath: Days from entry to ATH
            
        Returns:
            str: "early_peaker" or "late_peaker"
            
        Examples:
            >>> ROICalculator.determine_peak_timing(5.0)
            "early_peaker"
            >>> ROICalculator.determine_peak_timing(15.0)
            "late_peaker"
            >>> ROICalculator.determine_peak_timing(7.0)
            "early_peaker"
        """
        if days_to_ath <= 7:
            return "early_peaker"
        else:
            return "late_peaker"
    
    @staticmethod
    def calculate_optimal_exit_window(days_to_ath: float) -> Tuple[int, int]:
        """
        Calculate optimal exit window around ATH.
        
        The optimal exit window is ±2 days around the ATH, providing traders
        with a target timeframe for taking profits.
        
        Args:
            days_to_ath: Days from entry to ATH
            
        Returns:
            Tuple[int, int]: (start_day, end_day) for optimal exit window
            
        Examples:
            >>> ROICalculator.calculate_optimal_exit_window(15.0)
            (13, 17)
            >>> ROICalculator.calculate_optimal_exit_window(1.0)
            (0, 3)
            >>> ROICalculator.calculate_optimal_exit_window(30.0)
            (28, 32)
        """
        start_day = max(0, int(days_to_ath) - 2)
        end_day = int(days_to_ath) + 2
        return (start_day, end_day)

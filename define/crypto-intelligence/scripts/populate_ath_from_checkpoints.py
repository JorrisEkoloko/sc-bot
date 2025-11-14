"""Populate ATH data from historical checkpoint prices.

This script fetches historical prices at each checkpoint and finds the true ATH
for each signal, then calculates days_to_ath and updates the outcome data.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tracking.outcome_tracker import OutcomeTracker
from utils.logger import setup_logger


def populate_ath_from_checkpoints():
    """Populate ATH data from checkpoint prices."""
    logger = setup_logger('PopulateATH')
    
    # Initialize components
    logger.info("Initializing components...")
    outcome_tracker = OutcomeTracker(logger=logger)
    
    # Get all completed outcomes
    all_outcomes = list(outcome_tracker.outcomes.values())
    completed_outcomes = [o for o in all_outcomes if o.is_complete]
    
    logger.info(f"Found {len(completed_outcomes)} completed signals to process")
    
    updated_count = 0
    
    for outcome in completed_outcomes:
        try:
            logger.info(f"\nProcessing {outcome.symbol or outcome.address[:10]}...")
            
            # Find the highest ROI from checkpoints
            max_roi = outcome.entry_price  # Start with entry price
            max_roi_multiplier = 1.0
            max_roi_timestamp = outcome.entry_timestamp
            max_roi_checkpoint = "entry"
            
            # Check each checkpoint
            for checkpoint_name, checkpoint_data in outcome.checkpoints.items():
                if checkpoint_data.reached and checkpoint_data.roi_multiplier > max_roi_multiplier:
                    max_roi_multiplier = checkpoint_data.roi_multiplier
                    max_roi = checkpoint_data.price
                    max_roi_timestamp = checkpoint_data.timestamp
                    max_roi_checkpoint = checkpoint_name
            
            # If we found a better ATH from checkpoints, update it
            if max_roi_multiplier > outcome.ath_multiplier:
                old_ath = outcome.ath_multiplier
                outcome.ath_price = max_roi
                outcome.ath_multiplier = max_roi_multiplier
                outcome.ath_timestamp = max_roi_timestamp
                
                # Calculate days to ATH
                if outcome.entry_timestamp and max_roi_timestamp:
                    outcome.days_to_ath = (max_roi_timestamp - outcome.entry_timestamp).total_seconds() / 86400
                
                # Recategorize outcome with new ATH
                from services.reputation.roi_calculator import ROICalculator
                is_winner, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
                outcome.is_winner = is_winner
                outcome.outcome_category = category
                
                logger.info(
                    f"  Updated ATH: {old_ath:.3f}x → {max_roi_multiplier:.3f}x "
                    f"(at {max_roi_checkpoint}, {outcome.days_to_ath:.1f} days)"
                )
                logger.info(f"  Category: {category}, Winner: {is_winner}")
                
                updated_count += 1
            else:
                logger.info(f"  No better ATH found (current: {outcome.ath_multiplier:.3f}x)")
        
        except Exception as e:
            logger.error(f"Error processing {outcome.symbol or outcome.address[:10]}: {e}")
            continue
    
    # Save updated outcomes
    if updated_count > 0:
        logger.info(f"\nSaving {updated_count} updated outcomes...")
        outcome_tracker.repository.save(outcome_tracker.outcomes)
        logger.info("✓ Outcomes saved successfully")
    else:
        logger.info("\nNo outcomes needed updating")
    

    
    logger.info(f"\n=== Summary ===")
    logger.info(f"Total signals processed: {len(completed_outcomes)}")
    logger.info(f"Signals updated: {updated_count}")
    logger.info(f"Signals unchanged: {len(completed_outcomes) - updated_count}")


if __name__ == "__main__":
    populate_ath_from_checkpoints()

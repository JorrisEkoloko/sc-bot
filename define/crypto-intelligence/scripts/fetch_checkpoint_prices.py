"""
Fetch historical prices at checkpoint timepoints for completed signals.

This script reads signal outcomes and fetches historical price data at each
checkpoint (1h, 4h, 24h, 3d, 7d, 30d) to calculate actual ROI.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tracking.outcome_tracker import OutcomeTracker
from domain.signal_outcome import CHECKPOINTS
from services.pricing.price_engine import PriceEngine
from config.price_config import PriceConfig
from utils.logger import setup_logger


async def fetch_checkpoint_prices():
    """Fetch historical prices at checkpoints for all signals."""
    logger = setup_logger('CheckpointPriceFetcher')
    
    # Initialize components
    logger.info("Initializing components...")
    outcome_tracker = OutcomeTracker()
    price_config = PriceConfig.load_from_env()
    price_engine = PriceEngine(price_config)
    
    # Get all signals
    signals = list(outcome_tracker.outcomes.values())
    logger.info(f"Found {len(signals)} signals to process")
    
    updated_count = 0
    
    for signal in signals:
        logger.info(f"\nProcessing signal: {signal.symbol or signal.address[:10]}")
        logger.info(f"  Entry: {signal.entry_timestamp} at ${signal.entry_price:.6f}")
        
        if not signal.entry_timestamp:
            logger.warning(f"  Skipping - no entry timestamp")
            continue
        
        # Determine chain from address
        if len(signal.address) == 44 or len(signal.address) == 43:
            chain = "solana"
        else:
            chain = "evm"
        
        # Fetch historical prices at each checkpoint
        for checkpoint_name, interval in CHECKPOINTS.items():
            checkpoint = signal.checkpoints[checkpoint_name]
            
            # Calculate the target time for this checkpoint
            target_time = signal.entry_timestamp + interval
            
            # Skip if checkpoint is in the future
            if target_time > datetime.now(signal.entry_timestamp.tzinfo):
                logger.info(f"  {checkpoint_name}: Skipping (in future)")
                continue
            
            logger.info(f"  {checkpoint_name}: Fetching price at {target_time}")
            
            # Try to fetch historical price using CryptoCompare if we have a symbol
            price = None
            if signal.symbol and len(signal.symbol) <= 10:  # Valid symbol
                try:
                    timestamp = int(target_time.timestamp())
                    price = await price_engine.cryptocompare.get_price_at_timestamp(
                        signal.symbol, timestamp
                    )
                    if price:
                        logger.info(f"    Historical price from CryptoCompare: ${price:.6f}")
                except Exception as e:
                    logger.debug(f"    CryptoCompare failed: {e}")
            
            # Fallback to current price if historical not available
            if not price:
                try:
                    price_data = await price_engine.get_price(signal.address, chain)
                    if price_data:
                        price = price_data.price_usd
                        logger.info(f"    Using current price (historical not available): ${price:.6f}")
                except Exception as e:
                    logger.error(f"    Error fetching price: {e}")
            
            if price:
                # Calculate ROI
                roi_percentage = ((price - signal.entry_price) / signal.entry_price) * 100
                roi_multiplier = price / signal.entry_price
                
                # Update checkpoint
                checkpoint.timestamp = target_time
                checkpoint.price = price
                checkpoint.roi_percentage = roi_percentage
                checkpoint.roi_multiplier = roi_multiplier
                checkpoint.reached = True
                
                logger.info(f"    ROI: {roi_multiplier:.3f}x ({roi_percentage:+.1f}%)")
                
                # Update ATH if this is higher
                if price > signal.ath_price:
                    signal.ath_price = price
                    signal.ath_multiplier = roi_multiplier
                    signal.ath_timestamp = target_time
                    days_to_ath = (target_time - signal.entry_timestamp).total_seconds() / 86400
                    signal.days_to_ath = days_to_ath
                    logger.info(f"    New ATH: {roi_multiplier:.3f}x at {checkpoint_name}")
            else:
                logger.warning(f"    No price data available")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        # Update current price and multiplier
        signal.current_price = signal.ath_price if signal.ath_price > 0 else signal.entry_price
        signal.current_multiplier = signal.ath_multiplier if signal.ath_multiplier > 0 else 1.0
        
        # Reclassify outcome based on actual ROI
        if signal.ath_multiplier >= 2.0:
            signal.is_winner = True
            if signal.ath_multiplier >= 5.0:
                signal.outcome_category = "moon"
            elif signal.ath_multiplier >= 3.0:
                signal.outcome_category = "great"
            else:
                signal.outcome_category = "good"
        else:
            signal.is_winner = False
            if signal.ath_multiplier >= 1.0:
                signal.outcome_category = "break_even"
            else:
                signal.outcome_category = "loss"
        
        logger.info(f"  Final: {signal.outcome_category.upper()} - ATH {signal.ath_multiplier:.3f}x")
        updated_count += 1
    
    # Save updated outcomes
    logger.info(f"\nSaving {updated_count} updated signals...")
    outcome_tracker.save_outcomes()
    
    # Close price engine
    await price_engine.close()
    
    logger.info("Done!")
    
    # Print summary
    print("\n" + "="*80)
    print("CHECKPOINT PRICE FETCH SUMMARY")
    print("="*80)
    print(f"Total signals processed: {len(signals)}")
    print(f"Signals updated: {updated_count}")
    
    winners = [s for s in signals if s.is_winner]
    losers = [s for s in signals if not s.is_winner and s.is_complete]
    
    print(f"\nWinners (ROI >= 2.0x): {len(winners)}")
    for signal in winners:
        print(f"  {signal.symbol or signal.address[:10]}: {signal.ath_multiplier:.3f}x ({signal.outcome_category})")
    
    print(f"\nLosers (ROI < 2.0x): {len(losers)}")
    for signal in losers:
        print(f"  {signal.symbol or signal.address[:10]}: {signal.ath_multiplier:.3f}x ({signal.outcome_category})")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(fetch_checkpoint_prices())

"""Reputation scheduler - handles background reputation updates."""
import asyncio
from typing import Optional
from utils.logger import get_logger


class ReputationScheduler:
    """
    Manages periodic reputation updates and table refreshes.
    
    Runs background tasks for:
    - Channel reputation updates (every 30 minutes)
    - Reputation table refreshes
    - Outcome tracker event flushing
    """
    
    def __init__(
        self,
        reputation_engine,
        outcome_tracker,
        data_output,
        update_interval: int = 1800,  # 30 minutes
        logger=None
    ):
        """
        Initialize reputation scheduler.
        
        Args:
            reputation_engine: ReputationEngine instance
            outcome_tracker: OutcomeTracker instance
            data_output: DataOutput instance
            update_interval: Update interval in seconds (default: 1800 = 30 min)
            logger: Optional logger instance
        """
        self.reputation_engine = reputation_engine
        self.outcome_tracker = outcome_tracker
        self.data_output = data_output
        self.update_interval = update_interval
        self.logger = logger or get_logger('ReputationScheduler')
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the reputation update loop."""
        if self._running:
            self.logger.warning("Reputation scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        self.logger.info(f"🏆 Reputation scheduler started (interval: {self.update_interval}s)")
    
    async def stop(self):
        """Stop the reputation update loop."""
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        self.logger.info("🏆 Reputation scheduler stopped")
    
    async def _update_loop(self):
        """Periodically update channel reputations and refresh all reputation tables."""
        self.logger.info(f"🏆 Starting reputation update loop (every {self.update_interval // 60} minutes)")
        
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                
                if not self._running:
                    break
                
                await self.update_all_reputation_tables()
                
                # Flush pending events from outcome tracker
                if self.outcome_tracker:
                    await self.outcome_tracker.flush_pending_events()
                    
            except asyncio.CancelledError:
                self.logger.info("🏆 Reputation update loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in reputation update loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def update_channel_reputations(self):
        """
        Update channel reputations based on completed signals.
        
        This should be called periodically or after processing messages
        to keep reputation tables up to date.
        """
        if not self.reputation_engine or not self.outcome_tracker:
            return
        
        self.logger.info("Updating channel reputations from completed signals...")
        
        # Get all channels that have completed outcomes
        all_outcomes = self.outcome_tracker.outcomes
        channels_with_outcomes = set(
            outcome.channel_name 
            for outcome in all_outcomes.values() 
            if outcome.is_complete
        )
        
        reputations_updated = 0
        for channel_name in channels_with_outcomes:
            # Get completed outcomes for this channel
            channel_outcomes = self.outcome_tracker.get_channel_outcomes(
                channel_name, 
                completed_only=True
            )
            
            if channel_outcomes:
                reputation = self.reputation_engine.update_reputation(
                    channel_name, 
                    channel_outcomes
                )
                reputations_updated += 1
                self.logger.info(
                    f"Updated reputation for {channel_name}: "
                    f"Score={reputation.reputation_score:.1f}/100, "
                    f"Tier={reputation.reputation_tier}, "
                    f"Win Rate={reputation.win_rate:.1f}%, "
                    f"Avg ROI={reputation.average_roi:.3f}x"
                )
        
        if reputations_updated > 0:
            # Save updated reputations
            self.reputation_engine.save_reputations()
            self.logger.info(f"✅ Updated {reputations_updated} channel reputation(s)")
        else:
            self.logger.debug("No completed signals found for reputation updates")
    
    async def update_all_reputation_tables(self):
        """Update all reputation tables with latest data."""
        if not self.reputation_engine or not self.data_output:
            return
        
        self.logger.info("🏆 Updating all reputation tables...")
        
        try:
            # Get all reputations sorted by score
            reputations = self.reputation_engine.get_all_reputations()
            
            if not reputations:
                self.logger.debug("No reputations to update")
                return
            
            # Update all 4 reputation tables
            await self.data_output.write_channel_rankings(reputations)
            await self.data_output.write_channel_coin_performance(reputations)
            await self.data_output.write_coin_cross_channel(
                self.reputation_engine.coin_cross_channel_repo
            )
            await self.data_output.write_prediction_accuracy(reputations)
            
            self.logger.info(
                f"🏆 Updated all reputation tables with {len(reputations)} channels"
            )
                
        except Exception as e:
            self.logger.error(f"❌ Error updating reputation tables: {e}")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

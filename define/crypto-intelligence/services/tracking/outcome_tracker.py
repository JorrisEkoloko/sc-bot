"""Signal outcome tracker with ROI calculation at checkpoints.

Tracks signal outcomes from entry to completion, calculating ROI at multiple
time intervals (1h, 4h, 24h, 3d, 7d, 30d) to measure channel performance.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, List

from utils.logger import setup_logger
from utils.roi_calculator import ROICalculator
from domain.signal_outcome import SignalOutcome
from repositories.file_storage.outcome_repository import OutcomeRepository
# Task 6: Event-driven architecture
from domain.events import SignalStartedEvent, SignalCompletedEvent, CheckpointUpdatedEvent


class OutcomeTracker:
    """Tracks signal outcomes with ROI calculation at checkpoints."""
    
    def __init__(self, data_dir: str = "data/reputation", logger=None, event_bus=None):
        """
        Initialize outcome tracker.
        
        Args:
            data_dir: Directory for storing outcome data
            logger: Optional logger instance
            event_bus: Optional EventBus for publishing events (Task 6)
        """
        self.logger = logger or setup_logger('OutcomeTracker')
        self.repository = OutcomeRepository(data_dir, self.logger)
        self.outcomes: Dict[str, SignalOutcome] = {}
        self.event_bus = event_bus  # Task 6: Event bus for publishing events
        
        # Load existing outcomes
        self.outcomes = self.repository.load()
        
        self.logger.info(f"Outcome tracker initialized with {len(self.outcomes)} tracked signals")
    
    def track_signal(self, message_id: int, channel_name: str, address: str,
                    entry_price: float, entry_confidence: float = 0.0,
                    entry_source: str = "current_price", symbol: Optional[str] = None,
                    sentiment: str = "neutral", sentiment_score: float = 0.0,
                    hdrb_score: float = 0.0, confidence: float = 0.0,
                    market_tier: str = "", risk_level: str = "", risk_score: float = 0.0,
                    entry_timestamp: Optional[datetime] = None) -> SignalOutcome:
        """
        Start tracking a new signal.
        
        Args:
            message_id: Message ID from Telegram
            channel_name: Channel that mentioned the token
            address: Token contract address
            entry_price: Price when first mentioned
            entry_confidence: Confidence in entry price (0.0-1.0)
            entry_source: Source of entry price
            symbol: Token symbol
            sentiment: Message sentiment
            sentiment_score: Sentiment score
            hdrb_score: HDRB engagement score
            confidence: Overall signal confidence
            market_tier: Market cap tier
            risk_level: Risk level
            risk_score: Risk score
            entry_timestamp: Optional timestamp for historical signals (defaults to now)
            
        Returns:
            SignalOutcome object
        """
        # Ensure we use timezone-aware datetime for consistency
        now = datetime.now(timezone.utc)
        entry_ts = entry_timestamp or now
        
        # If entry_timestamp is naive, make it aware (assume UTC)
        if entry_ts.tzinfo is None:
            entry_ts = entry_ts.replace(tzinfo=timezone.utc)
        
        outcome = SignalOutcome(
            message_id=message_id,
            channel_name=channel_name,
            address=address,
            symbol=symbol,
            entry_price=entry_price,
            entry_timestamp=entry_ts,
            entry_confidence=entry_confidence,
            entry_source=entry_source,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            hdrb_score=hdrb_score,
            confidence=confidence,
            market_tier=market_tier,
            risk_level=risk_level,
            risk_score=risk_score,
            current_price=entry_price,
            current_multiplier=1.0,
            ath_price=entry_price,
            ath_multiplier=1.0,
            ath_timestamp=entry_ts
        )
        
        self.outcomes[address] = outcome
        
        # For historical signals, immediately check which checkpoints should already be reached
        # We use the entry price as the "current" price since we don't have historical price data
        # This will mark checkpoints as reached based on time elapsed, with ROI = 0% (no price change)
        if entry_ts < now:
            elapsed = now - entry_ts
            # Check which checkpoints should already be reached based on time elapsed
            reached_checkpoints = ROICalculator.check_checkpoints(outcome, entry_price)
            if reached_checkpoints:
                self.logger.info(f"Historical signal: {len(reached_checkpoints)} checkpoints already reached: {', '.join(reached_checkpoints)}")
            
            # Check if signal should be completed (30 days elapsed)
            should_stop, reason = ROICalculator.check_stop_conditions(outcome)
            if should_stop:
                self.complete_signal(address, reason)
                self.logger.info(f"Historical signal completed: {symbol or address[:10]} - {reason}")
        
        self.repository.save(self.outcomes)
        
        self.logger.info(f"Started tracking signal: {symbol or address[:10]} at ${entry_price:.6f} from {channel_name}")
        
        # Task 6: Publish SignalStartedEvent
        if self.event_bus:
            event = SignalStartedEvent(
                signal_id=str(message_id),
                address=address,
                chain="ethereum",  # TODO: Get from address extractor
                symbol=symbol or address[:10],
                entry_price=entry_price,
                entry_timestamp=entry_ts,
                channel_name=channel_name,
                message_id=message_id,
                signal_number=1,  # TODO: Get from HistoricalBootstrap deduplication
                previous_signals=[],
                metadata={
                    'sentiment': sentiment,
                    'hdrb_score': hdrb_score,
                    'confidence': confidence
                }
            )
            self._publish_event_safe(event)
        
        return outcome
    
    def calculate_roi(self, entry_price: float, current_price: float) -> tuple[float, float]:
        """Calculate ROI using ROICalculator."""
        return ROICalculator.calculate_roi(entry_price, current_price)
    
    def update_price(self, address: str, current_price: float) -> Optional[SignalOutcome]:
        """
        Update price and check checkpoints for a tracked signal.
        
        Args:
            address: Token contract address
            current_price: Current token price
            
        Returns:
            Updated SignalOutcome or None if not tracked
        """
        outcome = self.outcomes.get(address)
        if not outcome or outcome.is_complete:
            return None
        
        # Update current price and ROI
        outcome.current_price = current_price
        _, roi_multiplier = ROICalculator.calculate_roi(outcome.entry_price, current_price)
        outcome.current_multiplier = roi_multiplier
        
        # Update ATH if current price is higher
        ath_updated = ROICalculator.update_ath(outcome, current_price)
        if ath_updated:
            self.logger.debug(f"New ATH for {outcome.symbol or address[:10]}: ${current_price:.6f} ({outcome.ath_multiplier:.3f}x)")
        
        # Check and update checkpoints
        reached_checkpoints = ROICalculator.check_checkpoints(outcome, current_price)
        if reached_checkpoints:
            self.logger.info(f"Checkpoints reached for {outcome.symbol or address[:10]}: {', '.join(reached_checkpoints)}")
            
            # Process day 7 checkpoint (time-based classification)
            if "7d" in reached_checkpoints:
                self._process_day_7_checkpoint(outcome)
            
            # Process day 30 checkpoint (time-based classification)
            if "30d" in reached_checkpoints:
                self._process_day_30_checkpoint(outcome)
            
            # Task 6: Publish CheckpointUpdatedEvent for each reached checkpoint
            if self.event_bus:
                for checkpoint_name in reached_checkpoints:
                    roi_pct, roi_mult = ROICalculator.calculate_roi(outcome.entry_price, current_price)
                    event = CheckpointUpdatedEvent(
                        signal_id=str(outcome.message_id),
                        address=address,
                        checkpoint_name=checkpoint_name,
                        current_price=current_price,
                        roi_percentage=roi_pct,
                        roi_multiplier=roi_mult,
                        timestamp=datetime.now(timezone.utc)
                    )
                    self._publish_event_safe(event)
        
        # Check stop conditions
        should_stop, reason = ROICalculator.check_stop_conditions(outcome)
        if should_stop:
            self.complete_signal(address, reason)
        else:
            self.repository.save(self.outcomes)
        
        return outcome
    
    def complete_signal(self, address: str, reason: str) -> Optional[SignalOutcome]:
        """
        Mark signal as complete and categorize outcome.
        
        Args:
            address: Token contract address
            reason: Completion reason
            
        Returns:
            Completed SignalOutcome or None if not tracked
        """
        outcome = self.outcomes.get(address)
        if not outcome:
            return None
        
        # Check if already completed
        if outcome.is_complete:
            self.logger.warning(f"Signal {outcome.symbol or address[:10]} already completed")
            return outcome
        
        # Validate ATH data exists
        if outcome.ath_multiplier == 0.0:
            self.logger.warning(
                f"Signal {outcome.symbol or address[:10]} has no ATH data, using entry price as ATH"
            )
            outcome.ath_multiplier = 1.0
            outcome.ath_price = outcome.entry_price
        
        outcome.is_complete = True
        outcome.completion_reason = reason
        outcome.status = "completed"
        
        # Categorize outcome using ROICalculator
        is_winner, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
        outcome.is_winner = is_winner
        outcome.outcome_category = category
        
        self.repository.save(self.outcomes)
        
        self.logger.info(
            f"Signal completed: {outcome.symbol or address[:10]} - "
            f"ATH: {outcome.ath_multiplier:.3f}x, "
            f"Category: {outcome.outcome_category}, "
            f"Winner: {outcome.is_winner}, "
            f"Reason: {reason}"
        )
        
        # Task 6: Publish SignalCompletedEvent
        if self.event_bus:
            event = SignalCompletedEvent(
                signal_id=str(outcome.message_id),
                address=address,
                channel_name=outcome.channel_name,
                symbol=outcome.symbol or address[:10],
                entry_price=outcome.entry_price,
                ath_price=outcome.ath_price,
                ath_multiplier=outcome.ath_multiplier,
                days_to_ath=outcome.days_to_ath,
                is_winner=outcome.is_winner,
                outcome_category=outcome.outcome_category,
                signal_number=1,  # TODO: Get from signal_outcome
                entry_timestamp=outcome.entry_timestamp,
                completion_timestamp=datetime.now(timezone.utc),
                market_tier=outcome.market_tier,
                all_checkpoints={},  # TODO: Extract from outcome
                metadata={'completion_reason': reason}
            )
            self._publish_event_safe(event)
        
        return outcome
    
    def get_outcome(self, address: str) -> Optional[SignalOutcome]:
        """Get outcome for an address."""
        return self.outcomes.get(address)
    
    def get_channel_outcomes(self, channel_name: str, completed_only: bool = False) -> List[SignalOutcome]:
        """
        Get all outcomes for a channel.
        
        Args:
            channel_name: Channel name
            completed_only: Only return completed outcomes
            
        Returns:
            List of SignalOutcome objects
        """
        outcomes = [
            outcome for outcome in self.outcomes.values()
            if outcome.channel_name == channel_name
        ]
        
        if completed_only:
            outcomes = [o for o in outcomes if o.is_complete]
        
        return outcomes
    
    def _process_day_7_checkpoint(self, outcome: SignalOutcome) -> None:
        """
        Process day 7 checkpoint for time-based classification.
        
        Captures performance at day 7 and classifies based on current ATH.
        
        Args:
            outcome: Signal outcome to process
        """
        # Extract day 7 data from existing checkpoint
        day_7_checkpoint = outcome.checkpoints.get("7d")
        if not day_7_checkpoint or not day_7_checkpoint.reached:
            self.logger.warning(f"Day 7 checkpoint not reached for {outcome.symbol or outcome.address[:10]}")
            return
        
        # Populate day 7 fields
        outcome.day_7_price = day_7_checkpoint.price
        outcome.day_7_multiplier = day_7_checkpoint.roi_multiplier
        
        # Classify based on current ATH (not day 7 price)
        _, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
        outcome.day_7_classification = category
        
        self.logger.info(
            f"Day 7 checkpoint: {outcome.symbol or outcome.address[:10]} - "
            f"ATH {outcome.ath_multiplier:.2f}x, "
            f"Current {outcome.day_7_multiplier:.2f}x, "
            f"Classification: {category}"
        )
        
        # Save outcome with day 7 data
        self.repository.save(self.outcomes)
    
    def _process_day_30_checkpoint(self, outcome: SignalOutcome) -> None:
        """
        Process day 30 checkpoint for time-based classification.
        
        Captures final performance at day 30, classifies based on final ATH,
        calculates trajectory, and determines peak timing.
        
        Args:
            outcome: Signal outcome to process
        """
        # Extract day 30 data from existing checkpoint
        day_30_checkpoint = outcome.checkpoints.get("30d")
        if not day_30_checkpoint or not day_30_checkpoint.reached:
            self.logger.warning(f"Day 30 checkpoint not reached for {outcome.symbol or outcome.address[:10]}")
            return
        
        # Populate day 30 fields
        outcome.day_30_price = day_30_checkpoint.price
        outcome.day_30_multiplier = day_30_checkpoint.roi_multiplier
        
        # Classify based on final ATH
        _, category = ROICalculator.categorize_outcome(outcome.ath_multiplier)
        outcome.day_30_classification = category
        
        # Calculate trajectory (improved or crashed from day 7 to day 30, considering ATH)
        if outcome.day_7_multiplier > 0:
            trajectory, crash_severity = ROICalculator.analyze_trajectory(
                outcome.day_7_multiplier,
                outcome.day_30_multiplier,
                outcome.ath_multiplier  # Pass ATH to detect crashes from peak
            )
            outcome.trajectory = trajectory
            
            # Log severe crashes
            if trajectory == "crashed" and crash_severity > 50:
                self.logger.warning(
                    f"Severe crash: {outcome.symbol or outcome.address[:10]} "
                    f"dropped {crash_severity:.1f}% from day 7 to day 30"
                )
        else:
            outcome.trajectory = "unknown"
        
        # Determine peak timing (early or late peaker)
        if outcome.days_to_ath >= 0:
            outcome.peak_timing = ROICalculator.determine_peak_timing(outcome.days_to_ath)
        else:
            outcome.peak_timing = "unknown"
        
        self.logger.info(
            f"Day 30 final: {outcome.symbol or outcome.address[:10]} - "
            f"ATH {outcome.ath_multiplier:.2f}x (day {outcome.days_to_ath:.0f}), "
            f"Final {outcome.day_30_multiplier:.2f}x, "
            f"Trajectory: {outcome.trajectory}"
        )
        
        # Mark as complete (30 days elapsed)
        outcome.is_complete = True
        outcome.status = "completed"
        outcome.completion_reason = "30d_elapsed"
        
        # Save outcome with day 30 data
        self.repository.save(self.outcomes)
    
    def _publish_event_safe(self, event):
        """
        Publish event safely from any context (sync or async).
        
        Args:
            event: Event to publish
        """
        if not self.event_bus:
            return
        
        try:
            import asyncio
            # Try to get running loop
            loop = asyncio.get_running_loop()
            # We're in async context - schedule task
            asyncio.create_task(self.event_bus.publish(event))
        except RuntimeError:
            # No event loop running - log warning
            self.logger.warning(
                f"Cannot publish {type(event).__name__} - no event loop running. "
                f"Event will be skipped."
            )

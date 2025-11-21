"""Signal tracking service - handles performance and outcome tracking."""
import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from domain.message_event import MessageEvent
from services.message_processing.processed_message import ProcessedMessage
from utils.logger import get_logger


class SignalTrackingService:
    """Handles signal performance and outcome tracking."""
    
    def __init__(
        self,
        performance_tracker,
        outcome_tracker,
        dead_token_detector,
        historical_bootstrap,
        logger=None
    ):
        """Initialize signal tracking service."""
        self.performance_tracker = performance_tracker
        self.outcome_tracker = outcome_tracker
        self.dead_token_detector = dead_token_detector
        self.historical_bootstrap = historical_bootstrap
        self.logger = logger or get_logger('SignalTrackingService')
    
    async def check_dead_token(self, address: str, chain: str) -> tuple[bool, Optional[str]]:
        """
        Check if token is dead/blacklisted.
        
        Args:
            address: Token address
            chain: Blockchain name
            
        Returns:
            Tuple of (is_dead, reason)
        """
        if self.dead_token_detector.is_blacklisted(address):
            reason = self.dead_token_detector.get_blacklist_reason(address)
            self.logger.info(f"[DEAD TOKEN] {address[:10]}... is blacklisted: {reason}")
            return True, reason
        
        # Check if dead (adds to blacklist if dead)
        stats = await self.dead_token_detector.check_and_blacklist_if_dead(address, chain)
        if stats.is_dead:
            self.logger.warning(f"[DEAD TOKEN] Detected {address[:10]}...: {stats.reason}")
            return True, stats.reason
        
        return False, None
    
    def calculate_message_age(self, timestamp: datetime) -> tuple[float, float]:
        """
        Calculate message age in hours and days.
        
        Args:
            timestamp: Message timestamp
            
        Returns:
            Tuple of (hours, days)
        """
        now_utc = datetime.now(timezone.utc)
        msg_date = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        hours = (now_utc - msg_date).total_seconds() / 3600
        days = hours / 24
        return hours, days
    
    def is_signal_complete(self, message_age_days: float) -> bool:
        """Check if signal is complete (≥30 days old)."""
        return message_age_days >= 30
    
    async def track_ongoing_signal(
        self,
        address: str,
        chain: str,
        current_price: float,
        message_id: str,
        known_ath: Optional[float],
        symbol: str
    ):
        """
        Start or update performance tracking for ongoing signal.
        
        Args:
            address: Token address
            chain: Blockchain name
            current_price: Current token price
            message_id: Message ID
            known_ath: Known ATH from API
            symbol: Token symbol
        """
        if address not in self.performance_tracker.tracking_data:
            await self.performance_tracker.start_tracking(
                address=address,
                chain=chain,
                initial_price=current_price,
                message_id=str(message_id),
                known_ath=known_ath,
                symbol=symbol
            )
        else:
            await self.performance_tracker.update_price(
                address=address,
                current_price=current_price
            )
    
    def create_or_get_outcome(
        self,
        event: MessageEvent,
        processed: ProcessedMessage,
        address: str,
        entry_price: float,
        price_data,
        symbol: str
    ):
        """
        Create or retrieve outcome for signal.
        
        Args:
            event: Message event
            processed: Processed message
            address: Token address
            entry_price: Entry price
            price_data: Price data object
            symbol: Token symbol
            
        Returns:
            SignalOutcome object
        """
        outcome = self.outcome_tracker.outcomes.get(address)
        
        if not outcome:
            outcome = self.outcome_tracker.track_signal(
                message_id=event.message_id,
                channel_name=event.channel_name,
                address=address,
                entry_price=entry_price,
                entry_confidence=1.0,
                entry_source=price_data.source,
                symbol=symbol,
                sentiment=processed.sentiment,
                sentiment_score=processed.sentiment_score,
                hdrb_score=processed.hdrb_score,
                confidence=processed.confidence,
                market_tier=getattr(price_data, 'market_tier', ""),
                risk_level=getattr(price_data, 'risk_level', ""),
                risk_score=getattr(price_data, 'risk_score', 0.0),
                entry_timestamp=event.timestamp
            )
        
        return outcome
    
    async def populate_checkpoints_from_ohlc(
        self,
        outcome,
        entry_price: float,
        entry_timestamp: datetime,
        symbol: str,
        address: str,
        chain: str,
        window_days: int,
        ohlc_result: dict
    ):
        """
        Populate checkpoint prices from OHLC data.
        
        Args:
            outcome: SignalOutcome object
            entry_price: Entry price
            entry_timestamp: Entry timestamp
            symbol: Token symbol
            address: Token address
            chain: Blockchain name
            window_days: Window in days
            ohlc_result: OHLC data result
        """
        try:
            # Extract OHLC data from result
            ohlc_data = ohlc_result.get('ohlc_data', [])
            
            if not ohlc_data:
                self.logger.debug(f"No OHLC data to populate checkpoints for {symbol}")
                return
            
            # Calculate checkpoint timestamps (1h, 6h, 24h, 7d, 14d, 30d)
            from datetime import timedelta
            checkpoints = {
                '1h': entry_timestamp + timedelta(hours=1),
                '6h': entry_timestamp + timedelta(hours=6),
                '24h': entry_timestamp + timedelta(hours=24),
                '7d': entry_timestamp + timedelta(days=7),
                '14d': entry_timestamp + timedelta(days=14),
                '30d': entry_timestamp + timedelta(days=30)
            }
            
            # Find closest OHLC candle for each checkpoint
            for checkpoint_name, checkpoint_time in checkpoints.items():
                closest_candle = self._find_closest_candle(ohlc_data, checkpoint_time)
                
                if closest_candle:
                    price = closest_candle.get('close', entry_price)
                    multiplier = price / entry_price if entry_price > 0 else 1.0
                    
                    # Set checkpoint on outcome
                    setattr(outcome, f'price_{checkpoint_name}', price)
                    setattr(outcome, f'multiplier_{checkpoint_name}', multiplier)
                    
                    self.logger.debug(
                        f"Checkpoint {checkpoint_name}: ${price:.6f} ({multiplier:.3f}x)"
                    )
            
            # Save outcome
            self.outcome_tracker.repository.save(self.outcome_tracker.outcomes)
            
        except Exception as e:
            self.logger.error(f"Error populating checkpoints: {e}")
    
    def _find_closest_candle(self, ohlc_data: list, target_time: datetime) -> Optional[dict]:
        """Find OHLC candle closest to target time."""
        if not ohlc_data:
            return None
        
        closest = None
        min_diff = float('inf')
        
        for candle in ohlc_data:
            candle_time = candle.get('timestamp')
            if not candle_time:
                continue
            
            # Convert to datetime if needed
            if isinstance(candle_time, (int, float)):
                from datetime import datetime, timezone
                candle_time = datetime.fromtimestamp(candle_time, tz=timezone.utc)
            
            diff = abs((candle_time - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = candle
        
        return closest
    
    def classify_outcome(self, outcome, market_tier: str) -> str:
        """
        Classify outcome as winner/loser/break_even.
        
        Args:
            outcome: SignalOutcome object
            market_tier: Market tier (micro/small/large)
            
        Returns:
            Outcome category string
        """
        winner_threshold = self._get_winner_threshold(market_tier)
        
        if outcome.ath_multiplier >= winner_threshold:
            outcome.is_winner = True
            return "winner"
        elif outcome.ath_multiplier < 1.0:
            outcome.is_winner = False
            return "loser"
        else:
            outcome.is_winner = False
            return "break_even"
    
    def _get_winner_threshold(self, market_tier: str) -> float:
        """Get winner threshold based on market tier."""
        thresholds = {
            'micro': 2.0,   # 2x for micro-cap
            'small': 1.5,   # 1.5x for small-cap
            'large': 1.2    # 1.2x for large-cap
        }
        return thresholds.get(market_tier, 1.5)  # Default 1.5x
    
    def get_performance_data(self, address: str) -> Optional[Dict[str, Any]]:
        """Get performance tracking data for address."""
        if address not in self.performance_tracker.tracking_data:
            return None
        
        perf_data = self.performance_tracker.tracking_data[address]
        return {
            'ath_multiplier': perf_data.ath_multiplier,
            'days_tracked': perf_data.days_tracked,
            'current_price': perf_data.current_price
        }

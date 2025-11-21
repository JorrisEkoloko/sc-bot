"""Message handler - coordinates message processing pipeline."""
from typing import Optional

from domain.message_event import MessageEvent
from utils.logger import get_logger


class MessageHandler:
    """Handles incoming message events through the complete pipeline."""
    
    def __init__(
        self,
        message_processor,
        signal_processing_service,  # Can be old SignalProcessingService or new SignalCoordinator
        data_output,
        logger=None
    ):
        """Initialize message handler with dependencies."""
        self.message_processor = message_processor
        self.signal_processing_service = signal_processing_service  # Works with both old and new
        self.data_output = data_output
        self.logger = logger or get_logger('MessageHandler')
    
    async def handle_message(self, event: MessageEvent):
        """
        Handle received message through complete pipeline.
        
        Args:
            event: Message event data
        """
        if not self.message_processor:
            self.logger.warning("Message processor not initialized, skipping message")
            return
        
        try:
            import time
            start_time = time.time()
            
            # Process the message (HDRB, crypto detection, sentiment)
            processed = await self.message_processor.process_message(
                channel_name=event.channel_name,
                message_text=event.message_text,
                timestamp=event.timestamp,
                message_id=event.message_id,
                message_obj=event.message_obj,
                channel_id=event.channel_id
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Message processing took {processing_time:.0f}ms")
            
            # Process addresses if crypto relevant
            addresses_data = []
            
            if processed.is_crypto_relevant and processed.crypto_mentions:
                signal_start = time.time()
                
                # Write message to MESSAGES table
                await self.data_output.write_message({
                    'message_id': str(event.message_id),
                    'timestamp': event.timestamp.isoformat(),
                    'channel_name': event.channel_name,
                    'message_text': event.message_text,
                    'hdrb_score': processed.hdrb_score,
                    'crypto_mentions': processed.crypto_mentions,
                    'sentiment': processed.sentiment,
                    'confidence': processed.confidence,
                    'forwards': processed.forwards,
                    'reactions': processed.reactions,
                    'replies': processed.replies,
                    'views': processed.views,
                    'channel_reputation_score': processed.channel_reputation_score,
                    'channel_reputation_tier': processed.channel_reputation_tier,
                    'channel_expected_roi': processed.channel_expected_roi,
                    'prediction_source': processed.prediction_source
                })
                
                # Process addresses through signal processing service
                # Works with both old SignalProcessingService.process_addresses() 
                # and new SignalCoordinator.process_signal()
                if hasattr(self.signal_processing_service, 'process_signal'):
                    # New SignalCoordinator
                    addresses_data = await self.signal_processing_service.process_signal(event, processed)
                else:
                    # Old SignalProcessingService
                    addresses_data = await self.signal_processing_service.process_addresses(event, processed)
                
                signal_time = (time.time() - signal_start) * 1000
                self.logger.debug(f"Signal processing took {signal_time:.0f}ms")
            
            # Display results
            self._display_processed_message(processed, addresses_data)
            
            # Log processing results
            self.logger.info(
                f"Message processed: ID={processed.message_id}, "
                f"HDRB={processed.hdrb_score:.2f}, "
                f"crypto_relevant={processed.is_crypto_relevant}, "
                f"sentiment={processed.sentiment}, "
                f"confidence={processed.confidence:.2f}, "
                f"mentions={len(processed.crypto_mentions)}, "
                f"addresses={len(addresses_data)}, "
                f"time={processed.processing_time_ms:.2f}ms"
            )
            
            if processed.crypto_mentions:
                self.logger.info(f"Crypto mentions detected: {', '.join(processed.crypto_mentions)}")
            
            if processed.error:
                self.logger.error(f"Processing error: {processed.error}")
            
        except Exception as e:
            self.logger.error(f"Error handling message {event.message_id}: {e}", exc_info=True)

    def _display_processed_message(self, processed, addresses_data=None):
        """Display processed message with enhanced console output."""
        formatted_time = processed.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        print("\n" + "="*80)
        print(f"[{formatted_time}] [{processed.channel_name}] (ID: {processed.message_id})")
        print("="*80)
        
        print(f"📊 HDRB Score: {processed.hdrb_score:.1f}/100 (IC: {processed.hdrb_raw:.1f})")
        print(f"   Engagement: {processed.forwards} forwards, {processed.reactions} reactions, {processed.replies} replies")
        
        if processed.is_crypto_relevant and processed.crypto_mentions:
            mentions_str = ', '.join(processed.crypto_mentions)
            print(f"💰 Crypto Mentions: {mentions_str}")
        else:
            print(f"💰 Crypto Mentions: None")
        
        if addresses_data:
            print(f"\n💎 Addresses:")
            for addr_data in addresses_data:
                short_addr = addr_data['address'][:10] + '...'
                print(f"   • {short_addr} ({addr_data['chain']}) - ${addr_data['price']:.6f}")
                if addr_data['ath_multiplier'] > 1.0:
                    print(f"     📊 Performance: {addr_data['ath_multiplier']:.2f}x ATH (tracked {addr_data['days_tracked']} days)")
        
        sentiment_emoji = {
            'positive': '📈',
            'negative': '📉',
            'neutral': '➡️'
        }
        emoji = sentiment_emoji.get(processed.sentiment, '➡️')
        print(f"\n{emoji} Sentiment: {processed.sentiment.capitalize()} ({processed.sentiment_score:+.2f})")
        
        conf_indicator = "🟢 HIGH" if processed.is_high_confidence else "🟡 LOW"
        print(f"🎯 Confidence: {conf_indicator} ({processed.confidence:.2f})")
        
        print(f"\n{processed.message_text}")
        print(f"\n⏱️  Processed in {processed.processing_time_ms:.2f}ms")
        
        if processed.error:
            print(f"⚠️  Error: {processed.error}")
        
        print("="*80 + "\n")

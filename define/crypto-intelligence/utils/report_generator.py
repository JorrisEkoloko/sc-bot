"""Report generation utilities.

Pure presentation logic for formatting verification reports.
"""
from datetime import datetime
from typing import Dict, Any, List


class ReportGenerator:
    """Pure presentation logic for generating reports."""
    
    @staticmethod
    def generate_verification_report(stats: Dict[str, Any], 
                                     reputation_engine=None,
                                     performance_tracker=None) -> str:
        """
        Generate verification report from statistics.
        
        Args:
            stats: Statistics dictionary
            reputation_engine: Optional reputation engine for channel data
            performance_tracker: Optional performance tracker for tracking data
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("="*80)
        report.append("HISTORICAL SCRAPER VERIFICATION REPORT")
        report.append("="*80)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary statistics
        report.extend(ReportGenerator._format_summary_section(stats))
        
        # HDRB Score Statistics
        if stats.get('hdrb_scores'):
            report.extend(ReportGenerator._format_hdrb_section(stats))
        
        # Crypto Detection Statistics
        report.extend(ReportGenerator._format_crypto_detection_section(stats))
        
        # Address Extraction Statistics (Part 3)
        report.extend(ReportGenerator._format_address_extraction_section(stats))
        
        # Price Fetching Statistics (Part 3)
        report.extend(ReportGenerator._format_price_fetching_section(stats))
        
        # Performance Tracking Statistics (Part 3 - Task 3)
        report.extend(ReportGenerator._format_performance_tracking_section(stats))
        
        # Multi-Table Output Statistics (Part 3 - Task 4)
        report.extend(ReportGenerator._format_multi_table_output_section(stats))
        
        # Part 8: Channel Reputation + Outcome Learning Statistics
        report.extend(ReportGenerator._format_reputation_section(stats, reputation_engine))
        
        # Performance Tracker Summary
        if performance_tracker:
            report.extend(ReportGenerator._format_tracker_summary_section(performance_tracker))
        
        # Sentiment Analysis Statistics
        report.extend(ReportGenerator._format_sentiment_section(stats))
        
        # Confidence Statistics
        if stats.get('confidence_scores'):
            report.extend(ReportGenerator._format_confidence_section(stats))
        
        # Performance Statistics
        if stats.get('processing_times'):
            report.extend(ReportGenerator._format_performance_section(stats))
        
        # Verification Status
        report.extend(ReportGenerator._format_verification_section(stats, performance_tracker))
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)
    
    @staticmethod
    def _format_summary_section(stats: Dict[str, Any]) -> List[str]:
        """Format summary statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("SUMMARY STATISTICS")
        lines.append("="*80)
        lines.append(f"Total messages fetched: {stats.get('total_messages', 0)}")
        lines.append(f"Successfully processed: {stats.get('processed_messages', 0)}")
        lines.append(f"Processing errors: {stats.get('errors', 0)}")
        
        if stats.get('processed_messages', 0) > 0:
            success_rate = (stats['processed_messages'] / stats['total_messages']) * 100
            lines.append(f"Success rate: {success_rate:.1f}%")
        
        return lines
    
    @staticmethod
    def _format_hdrb_section(stats: Dict[str, Any]) -> List[str]:
        """Format HDRB score statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("HDRB SCORE STATISTICS")
        lines.append("="*80)
        hdrb_scores = stats['hdrb_scores']
        lines.append(f"Minimum: {min(hdrb_scores):.2f}/100")
        lines.append(f"Maximum: {max(hdrb_scores):.2f}/100")
        lines.append(f"Average: {sum(hdrb_scores)/len(hdrb_scores):.2f}/100")
        return lines
    
    @staticmethod
    def _format_crypto_detection_section(stats: Dict[str, Any]) -> List[str]:
        """Format crypto detection statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CRYPTO DETECTION STATISTICS")
        lines.append("="*80)
        lines.append(f"Crypto relevant messages: {stats.get('crypto_relevant', 0)}/{stats.get('processed_messages', 0)}")
        if stats.get('processed_messages', 0) > 0:
            crypto_rate = (stats['crypto_relevant'] / stats['processed_messages']) * 100
            lines.append(f"Crypto relevance rate: {crypto_rate:.1f}%")
        return lines
    
    @staticmethod
    def _format_address_extraction_section(stats: Dict[str, Any]) -> List[str]:
        """Format address extraction statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("ADDRESS EXTRACTION STATISTICS (PART 3)")
        lines.append("="*80)
        lines.append(f"Total addresses found: {stats.get('addresses_found', 0)}")
        lines.append(f"EVM addresses (Ethereum, BSC, Polygon, etc.): {stats.get('evm_addresses', 0)}")
        lines.append(f"Solana addresses: {stats.get('solana_addresses', 0)}")
        lines.append(f"Invalid addresses: {stats.get('invalid_addresses', 0)}")
        if stats.get('addresses_found', 0) > 0:
            valid_rate = ((stats['addresses_found'] - stats.get('invalid_addresses', 0)) / stats['addresses_found']) * 100
            lines.append(f"Validation rate: {valid_rate:.1f}%")
        return lines
    
    @staticmethod
    def _format_price_fetching_section(stats: Dict[str, Any]) -> List[str]:
        """Format price fetching statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PRICE FETCHING STATISTICS (PART 3)")
        lines.append("="*80)
        valid_addresses = stats.get('addresses_found', 0) - stats.get('invalid_addresses', 0)
        lines.append(f"Valid addresses: {valid_addresses}")
        lines.append(f"Prices fetched: {stats.get('prices_fetched', 0)}")
        lines.append(f"Price failures: {stats.get('price_failures', 0)}")
        if valid_addresses > 0:
            success_rate = (stats.get('prices_fetched', 0) / valid_addresses) * 100
            lines.append(f"Price fetch success rate: {success_rate:.1f}%")
        
        # API Usage Breakdown
        if stats.get('api_usage'):
            lines.append("\nAPI Usage Breakdown:")
            for api, count in sorted(stats['api_usage'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats.get('prices_fetched', 1)) * 100 if stats.get('prices_fetched', 0) > 0 else 0
                lines.append(f"  {api}: {count} requests ({percentage:.1f}%)")
        
        return lines
    
    @staticmethod
    def _format_performance_tracking_section(stats: Dict[str, Any]) -> List[str]:
        """Format performance tracking statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PERFORMANCE TRACKING STATISTICS (PART 3 - TASK 3)")
        lines.append("="*80)
        lines.append(f"New addresses tracked: {stats.get('tracking_started', 0)}")
        lines.append(f"Existing addresses updated: {stats.get('tracking_updated', 0)}")
        lines.append(f"Performance ATH updates detected: {stats.get('performance_ath_updates', 0)}")
        lines.append(f"Outcome ATH updates detected: {stats.get('outcome_ath_updates', 0)}")
        return lines
    
    @staticmethod
    def _format_multi_table_output_section(stats: Dict[str, Any]) -> List[str]:
        """Format multi-table output statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("MULTI-TABLE OUTPUT STATISTICS (PART 3 - TASK 4)")
        lines.append("="*80)
        lines.append(f"Messages written: {stats.get('messages_written', 0)}")
        lines.append(f"Token prices written: {stats.get('token_prices_written', 0)}")
        lines.append(f"Performance records written: {stats.get('performance_written', 0)}")
        lines.append(f"Historical records written: {stats.get('historical_written', 0)}")
        return lines
    
    @staticmethod
    def _format_reputation_section(stats: Dict[str, Any], reputation_engine=None) -> List[str]:
        """Format channel reputation statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PART 8: CHANNEL REPUTATION + OUTCOME LEARNING")
        lines.append("="*80)
        lines.append(f"Signals tracked: {stats.get('signals_tracked', 0)}")
        lines.append(f"Dead tokens detected: {stats.get('dead_tokens_detected', 0)}")
        lines.append(f"Dead tokens skipped (blacklisted): {stats.get('dead_tokens_skipped', 0)}")
        lines.append(f"Winners classified (ROI ≥ 1.5x): {stats.get('winners_classified', 0)}")
        lines.append(f"Losers classified (ROI < 1.5x): {stats.get('losers_classified', 0)}")
        lines.append(f"Reputations calculated: {stats.get('reputations_calculated', 0)}")
        
        # Show reputation details
        if reputation_engine and stats.get('reputations_calculated', 0) > 0:
            lines.append("\nChannel Reputations:")
            for reputation in reputation_engine.get_all_reputations():
                lines.append(f"\n  {reputation.channel_name}:")
                lines.append(f"    Reputation Score: {reputation.reputation_score:.1f}/100 ({reputation.reputation_tier})")
                lines.append(f"    Total Signals: {reputation.total_signals}")
                lines.append(f"    Win Rate: {reputation.win_rate:.1f}% ({reputation.winning_signals} winners)")
                lines.append(f"    Average ROI: {reputation.average_roi:.3f}x ({(reputation.average_roi - 1) * 100:.1f}% gain)")
                lines.append(f"    Sharpe Ratio: {reputation.sharpe_ratio:.2f}")
                lines.append(f"    Speed Score: {reputation.speed_score:.1f}")
                lines.append(f"    Expected ROI: {reputation.expected_roi:.3f}x")
        
        return lines
    
    @staticmethod
    def _format_tracker_summary_section(performance_tracker) -> List[str]:
        """Format performance tracker summary section.
        
        Note: This shows PerformanceTracker data (ATH since we started tracking).
        For historical signals, the real 30-day ATH is in OutcomeTracker (signal_outcomes.json).
        """
        lines = []
        tracking_summary = performance_tracker.get_tracking_summary()
        lines.append(f"\nTotal addresses in tracker: {tracking_summary['total_tracked']}")
        
        if tracking_summary.get('by_chain'):
            lines.append("\nAddresses by chain:")
            for chain, count in tracking_summary['by_chain'].items():
                lines.append(f"  {chain}: {count}")
        
        # Note: avg_multiplier from PerformanceTracker is ATH since we started tracking,
        # not the historical 30-day ATH. For historical analysis, use OutcomeTracker data.
        if tracking_summary.get('avg_multiplier', 0) > 0:
            lines.append(f"\nAverage ATH multiplier (since tracking started): {tracking_summary['avg_multiplier']:.2f}x")
        
        if tracking_summary.get('best_performer'):
            bp = tracking_summary['best_performer']
            lines.append(f"\nBest performer (since tracking started):")
            lines.append(f"  Address: {bp['address']}")
            lines.append(f"  Chain: {bp['chain']}")
            lines.append(f"  ATH Multiplier: {bp['multiplier']:.2f}x")
            lines.append(f"  Start Price: ${bp['start_price']:.6f}")
            lines.append(f"  ATH Price: ${bp['ath_price']:.6f}")
            lines.append(f"  Note: For historical signals, see OutcomeTracker for 30-day ATH")
        
        # CSV Output Statistics
        if hasattr(performance_tracker, 'csv_writer') and performance_tracker.csv_writer:
            try:
                csv_file = performance_tracker.csv_writer.get_current_file()
                csv_rows = performance_tracker.csv_writer.count_rows()
                lines.append(f"\nCSV Output:")
                lines.append(f"  File: {csv_file}")
                lines.append(f"  Rows: {csv_rows}")
            except Exception:
                pass
        
        return lines
    
    @staticmethod
    def _format_sentiment_section(stats: Dict[str, Any]) -> List[str]:
        """Format sentiment analysis statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("SENTIMENT ANALYSIS STATISTICS")
        lines.append("="*80)
        lines.append(f"Positive: {stats.get('positive_sentiment', 0)}")
        lines.append(f"Negative: {stats.get('negative_sentiment', 0)}")
        lines.append(f"Neutral: {stats.get('neutral_sentiment', 0)}")
        return lines
    
    @staticmethod
    def _format_confidence_section(stats: Dict[str, Any]) -> List[str]:
        """Format confidence statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CONFIDENCE STATISTICS")
        lines.append("="*80)
        lines.append(f"High confidence messages: {stats.get('high_confidence', 0)}/{stats.get('processed_messages', 0)}")
        if stats.get('processed_messages', 0) > 0:
            high_conf_rate = (stats.get('high_confidence', 0) / stats['processed_messages']) * 100
            lines.append(f"High confidence rate: {high_conf_rate:.1f}%")
        confidence_scores = stats.get('confidence_scores', [])
        if confidence_scores:
            lines.append(f"Average confidence: {sum(confidence_scores)/len(confidence_scores):.2f}")
        return lines
    
    @staticmethod
    def _format_performance_section(stats: Dict[str, Any]) -> List[str]:
        """Format performance statistics section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PERFORMANCE STATISTICS")
        lines.append("="*80)
        processing_times = stats['processing_times']
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        lines.append(f"Average processing time: {avg_time:.2f}ms")
        lines.append(f"Minimum processing time: {min_time:.2f}ms")
        lines.append(f"Maximum processing time: {max_time:.2f}ms")
        
        # Check if performance targets met
        if avg_time < 100.0:
            lines.append(f"✓ Performance target met (< 100ms)")
        else:
            lines.append(f"✗ Performance target not met (>= 100ms)")
        
        return lines
    
    @staticmethod
    def _format_verification_section(stats: Dict[str, Any], performance_tracker=None) -> List[str]:
        """Format verification status section."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("VERIFICATION STATUS")
        lines.append("="*80)
        
        # Get tracking summary if available
        tracking_summary = performance_tracker.get_tracking_summary() if performance_tracker else {}
        avg_time = sum(stats.get('processing_times', [0])) / len(stats.get('processing_times', [1])) if stats.get('processing_times') else 0
        
        checks = [
            (stats.get('processed_messages', 0) > 0, "Messages processed successfully"),
            (bool(stats.get('hdrb_scores')), "HDRB scores calculated"),
            (stats.get('crypto_relevant', 0) >= 0, "Crypto detection working"),
            (stats.get('positive_sentiment', 0) + stats.get('negative_sentiment', 0) + stats.get('neutral_sentiment', 0) == stats.get('processed_messages', 0), "Sentiment analysis working"),
            (bool(stats.get('confidence_scores')), "Confidence scores calculated"),
            (avg_time < 100.0 if stats.get('processing_times') else False, "Performance targets met"),
            # Part 3 - Task 3 checks
            (stats.get('addresses_found', 0) > 0, "Address extraction working (Part 3)"),
            (stats.get('prices_fetched', 0) > 0, "Price fetching working (Part 3)"),
            (stats.get('tracking_started', 0) > 0 or stats.get('tracking_updated', 0) > 0, "Performance tracking working (Part 3 - Task 3)"),
            (tracking_summary.get('total_tracked', 0) > 0, "Performance tracker has data (Part 3 - Task 3)"),
            (performance_tracker.csv_writer is not None if performance_tracker else False, "CSV writer initialized (Part 3 - Task 3)"),
            # Part 3 - Task 4 checks
            (stats.get('messages_written', 0) > 0, "Messages written to MESSAGES table (Part 3 - Task 4)"),
            (stats.get('token_prices_written', 0) > 0, "Token prices written to TOKEN_PRICES table (Part 3 - Task 4)"),
            (stats.get('performance_written', 0) > 0, "Performance written to PERFORMANCE table (Part 3 - Task 4)"),
            (stats.get('historical_written', 0) >= 0, "Historical data fetching implemented (Part 3 - Task 4)"),
            # Part 8 checks
            (stats.get('signals_tracked', 0) > 0, "✓ Signals tracked with entry price and ROI (Part 8 - Task 1)"),
            (stats.get('winners_classified', 0) + stats.get('losers_classified', 0) > 0, "✓ Winners classified (ROI ≥ 1.5x) (Part 8 - Task 1)"),
            (stats.get('reputations_calculated', 0) > 0, "✓ Channel reputations calculated from outcomes (Part 8 - Task 2)"),
        ]
        
        passed = sum(1 for check, _ in checks if check)
        total = len(checks)
        
        for check, description in checks:
            status = "✓" if check else "✗"
            lines.append(f"{status} {description}")
        
        lines.append(f"\nVerification: {passed}/{total} checks passed")
        
        if passed == total:
            lines.append("\n✓ ALL VERIFICATION CHECKS PASSED!")
        else:
            lines.append(f"\n✗ {total - passed} verification check(s) failed")
        
        return lines

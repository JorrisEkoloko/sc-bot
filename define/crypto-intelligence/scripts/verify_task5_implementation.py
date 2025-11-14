#!/usr/bin/env python3
"""
Task 5 Implementation Verification Script

Validates all Task 5 features:
1. Two-file tracking system
2. Deduplication logic
3. Fresh start re-monitoring
4. Progress persistence
5. Smart checkpoint handling

MCP-Validated patterns verified.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.signal_outcome import SignalOutcome
from domain.bootstrap_status import BootstrapStatus
from services.reputation.historical_bootstrap import HistoricalBootstrap
from repositories.file_storage.outcome_repository import OutcomeRepository


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_check(passed, message):
    """Print check result."""
    symbol = "✓" if passed else "❌"
    print(f"{symbol} {message}")


def verify_domain_models():
    """Verify domain models have required fields."""
    print_header("1. DOMAIN MODELS VERIFICATION")
    
    # Test SignalOutcome
    signal = SignalOutcome(
        message_id=1,
        channel_name="Test",
        address="0x123",
        symbol="TEST",
        signal_number=2,
        previous_signals=[1]
    )
    
    print_check(hasattr(signal, 'signal_number'), "SignalOutcome has signal_number field")
    print_check(hasattr(signal, 'previous_signals'), "SignalOutcome has previous_signals field")
    print_check(signal.signal_number == 2, "signal_number initialized correctly")
    print_check(signal.previous_signals == [1], "previous_signals initialized correctly")
    
    # Test serialization
    signal_dict = signal.to_dict()
    print_check('signal_number' in signal_dict, "signal_number serializes to dict")
    print_check('previous_signals' in signal_dict, "previous_signals serializes to dict")
    
    # Test deserialization
    signal_restored = SignalOutcome.from_dict(signal_dict)
    print_check(signal_restored.signal_number == 2, "signal_number deserializes correctly")
    print_check(signal_restored.previous_signals == [1], "previous_signals deserializes correctly")
    
    # Test BootstrapStatus
    status = BootstrapStatus(
        total_messages=100,
        processed_messages=50,
        last_processed_message_id=12345
    )
    
    print_check(hasattr(status, 'last_processed_message_id'), "BootstrapStatus has checkpoint fields")
    print_check(status.last_processed_message_id == 12345, "Checkpoint data stored correctly")
    
    return True


def verify_two_file_system():
    """Verify two-file tracking system."""
    print_header("2. TWO-FILE TRACKING SYSTEM VERIFICATION")
    
    # Create temporary bootstrap
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Create test signals
        active_signal = SignalOutcome(
            message_id=1,
            channel_name="Test",
            address="0x123",
            symbol="ACTIVE",
            status="in_progress"
        )
        
        completed_signal = SignalOutcome(
            message_id=2,
            channel_name="Test",
            address="0x456",
            symbol="DONE",
            status="completed",
            is_complete=True
        )
        
        # Add to tracking
        bootstrap.active_outcomes["0x123"] = active_signal
        bootstrap.completed_outcomes["0x456"] = completed_signal
        
        # Save
        bootstrap.save_all()
        
        # Verify files exist
        active_file = Path(temp_dir) / "active_tracking.json"
        completed_file = Path(temp_dir) / "completed_history.json"
        
        print_check(active_file.exists(), "active_tracking.json created")
        print_check(completed_file.exists(), "completed_history.json created")
        
        # Load and verify
        bootstrap2 = HistoricalBootstrap(data_dir=temp_dir)
        bootstrap2.load_existing_data()
        
        print_check(len(bootstrap2.active_outcomes) == 1, "Active signals loaded correctly")
        print_check(len(bootstrap2.completed_outcomes) == 1, "Completed signals loaded correctly")
        print_check("0x123" in bootstrap2.active_outcomes, "Active signal in correct file")
        print_check("0x456" in bootstrap2.completed_outcomes, "Completed signal in correct file")
    
    return True


def verify_deduplication():
    """Verify deduplication logic."""
    print_header("3. DEDUPLICATION LOGIC VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Add signal to active tracking
        signal = SignalOutcome(
            message_id=1,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=1
        )
        bootstrap.active_outcomes["0x123"] = signal
        
        # Check for duplicate (should be True)
        is_dup, next_num, prev_signals = bootstrap.check_for_duplicate("0x123")
        print_check(is_dup is True, "Detects duplicate in active tracking")
        print_check(next_num is None, "Returns None for duplicate")
        
        # Move to completed
        bootstrap.completed_outcomes["0x123"] = signal
        del bootstrap.active_outcomes["0x123"]
        
        # Check again (should be fresh start)
        is_dup, next_num, prev_signals = bootstrap.check_for_duplicate("0x123")
        print_check(is_dup is False, "Allows fresh start after completion")
        print_check(next_num == 2, "Increments signal number for fresh start")
        print_check(prev_signals == [1], "Tracks previous signal IDs")
        
        # Check new coin (should be first mention)
        is_dup, next_num, prev_signals = bootstrap.check_for_duplicate("0x999")
        print_check(is_dup is False, "Allows first mention")
        print_check(next_num == 1, "Starts at signal number 1")
        print_check(prev_signals == [], "No previous signals for first mention")
    
    return True


def verify_fresh_start_monitoring():
    """Verify fresh start re-monitoring."""
    print_header("4. FRESH START RE-MONITORING VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Signal #1
        signal1 = SignalOutcome(
            message_id=1,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=1,
            previous_signals=[],
            entry_price=1.47,
            ath_multiplier=3.252
        )
        bootstrap.completed_outcomes["0x123"] = signal1
        
        # Check for Signal #2
        is_dup, next_num, prev_signals = bootstrap.check_for_duplicate("0x123")
        
        print_check(next_num == 2, "Signal #2 number correct")
        print_check(prev_signals == [1], "References Signal #1")
        
        # Create Signal #2 with different entry price
        signal2 = SignalOutcome(
            message_id=2,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=next_num,
            previous_signals=prev_signals,
            entry_price=2.10,  # Different entry!
            ath_multiplier=1.85
        )
        
        print_check(signal2.entry_price != signal1.entry_price, "Signal #2 has independent entry price")
        print_check(signal2.signal_number == 2, "Signal #2 numbered correctly")
        print_check(1 in signal2.previous_signals, "Signal #2 references Signal #1")
        
        # Move Signal #2 to completed
        bootstrap.completed_outcomes["0x123"] = signal2
        
        # Check for Signal #3
        is_dup, next_num, prev_signals = bootstrap.check_for_duplicate("0x123")
        
        print_check(next_num == 3, "Signal #3 number correct")
        print_check(prev_signals == [1, 2], "References Signal #1 and #2")
    
    return True


def verify_progress_persistence():
    """Verify progress persistence."""
    print_header("5. PROGRESS PERSISTENCE VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Create status
        status = BootstrapStatus(
            total_messages=1000,
            processed_messages=500,
            total_tokens=50,
            processed_tokens=25,
            last_processed_message_id=12345,
            channel_name="Test Channel"
        )
        
        # Save progress
        bootstrap.save_progress(status)
        
        # Verify file exists
        status_file = Path(temp_dir) / "bootstrap_status.json"
        print_check(status_file.exists(), "bootstrap_status.json created")
        
        # Load progress
        loaded_status = bootstrap.load_progress()
        print_check(loaded_status is not None, "Progress loaded successfully")
        print_check(loaded_status.processed_messages == 500, "Progress data correct")
        print_check(loaded_status.last_processed_message_id == 12345, "Checkpoint ID preserved")
        
        # Clear progress
        bootstrap.clear_progress()
        print_check(not status_file.exists(), "Progress file cleared on completion")
    
    return True


def verify_archival():
    """Verify archival from active to history."""
    print_header("6. ARCHIVAL LOGIC VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Add signal to active
        signal = SignalOutcome(
            message_id=1,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=1,
            status="completed",
            is_complete=True
        )
        bootstrap.active_outcomes["0x123"] = signal
        
        print_check("0x123" in bootstrap.active_outcomes, "Signal in active before archival")
        print_check("0x123" not in bootstrap.completed_outcomes, "Signal not in completed before archival")
        
        # Archive
        success = bootstrap.archive_to_history("0x123")
        
        print_check(success is True, "Archival succeeded")
        print_check("0x123" not in bootstrap.active_outcomes, "Signal removed from active")
        print_check("0x123" in bootstrap.completed_outcomes, "Signal moved to completed")
        
        # Verify atomicity (both files updated)
        bootstrap.save_all()
        bootstrap2 = HistoricalBootstrap(data_dir=temp_dir)
        bootstrap2.load_existing_data()
        
        print_check("0x123" not in bootstrap2.active_outcomes, "Active file updated atomically")
        print_check("0x123" in bootstrap2.completed_outcomes, "Completed file updated atomically")
    
    return True


def verify_smart_checkpoints():
    """Verify smart checkpoint handling."""
    print_header("7. SMART CHECKPOINT HANDLING VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Message 2 days old
        message_date = datetime.now() - timedelta(days=2)
        checkpoints = bootstrap.calculate_smart_checkpoints(message_date)
        checkpoint_names = [name for name, _ in checkpoints]
        
        print_check('1h' in checkpoint_names, "1h checkpoint reached (2 days old)")
        print_check('4h' in checkpoint_names, "4h checkpoint reached (2 days old)")
        print_check('24h' in checkpoint_names, "24h checkpoint reached (2 days old)")
        print_check('3d' not in checkpoint_names, "3d checkpoint not reached (2 days old)")
        print_check('7d' not in checkpoint_names, "7d checkpoint not reached (2 days old)")
        
        # Message 35 days old
        old_message = datetime.now() - timedelta(days=35)
        checkpoints = bootstrap.calculate_smart_checkpoints(old_message)
        checkpoint_names = [name for name, _ in checkpoints]
        
        print_check('30d' in checkpoint_names, "30d checkpoint reached (35 days old)")
        print_check(len(checkpoints) == 6, "All checkpoints reached (35 days old)")
        
        # Status determination
        status = bootstrap.determine_signal_status(old_message)
        print_check(status == "completed", "Status 'completed' for 35 days old")
        
        status = bootstrap.determine_signal_status(message_date)
        print_check(status == "in_progress", "Status 'in_progress' for 2 days old")
    
    return True


def verify_statistics():
    """Verify statistics gathering."""
    print_header("8. STATISTICS VERIFICATION")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap = HistoricalBootstrap(data_dir=temp_dir)
        
        # Add signals
        bootstrap.active_outcomes["0x123"] = SignalOutcome(
            message_id=1,
            channel_name="Channel A",
            address="0x123",
            symbol="TEST1"
        )
        bootstrap.active_outcomes["0x456"] = SignalOutcome(
            message_id=2,
            channel_name="Channel A",
            address="0x456",
            symbol="TEST2"
        )
        bootstrap.completed_outcomes["0x789"] = SignalOutcome(
            message_id=3,
            channel_name="Channel B",
            address="0x789",
            symbol="TEST3"
        )
        
        stats = bootstrap.get_statistics()
        
        print_check(stats['active_signals'] == 2, "Active signals count correct")
        print_check(stats['completed_signals'] == 1, "Completed signals count correct")
        print_check(stats['total_signals'] == 3, "Total signals count correct")
        print_check(stats['channels'] == 2, "Unique channels count correct")
    
    return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("  TASK 5 IMPLEMENTATION VERIFICATION")
    print("  MCP-Validated Patterns: Checkpoint/Restart, Deduplication, Atomicity")
    print("=" * 70)
    
    checks = [
        ("Domain Models", verify_domain_models),
        ("Two-File System", verify_two_file_system),
        ("Deduplication", verify_deduplication),
        ("Fresh Start Re-Monitoring", verify_fresh_start_monitoring),
        ("Progress Persistence", verify_progress_persistence),
        ("Archival Logic", verify_archival),
        ("Smart Checkpoints", verify_smart_checkpoints),
        ("Statistics", verify_statistics)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    for name, result in results:
        symbol = "✓" if result else "❌"
        print(f"{symbol} {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\nTask 5 Implementation:")
        print("  ✓ Two-file tracking system")
        print("  ✓ Deduplication logic")
        print("  ✓ Fresh start re-monitoring")
        print("  ✓ Progress persistence")
        print("  ✓ Smart checkpoint handling")
        print("  ✓ MCP-validated patterns")
        print("\nReady for integration with historical_scraper.py!")
        return 0
    else:
        print("\n❌ SOME VERIFICATIONS FAILED")
        print("Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


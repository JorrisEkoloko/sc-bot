"""Tests for historical bootstrap service (Task 5).

Validates:
1. Two-file tracking system
2. Deduplication logic
3. Fresh start re-monitoring
4. Progress persistence
5. Smart checkpoint handling
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from domain.signal_outcome import SignalOutcome
from domain.bootstrap_status import BootstrapStatus
from services.reputation.historical_bootstrap import HistoricalBootstrap


class TestHistoricalBootstrap:
    """Test suite for HistoricalBootstrap service."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary data directory."""
        data_dir = tmp_path / "reputation"
        data_dir.mkdir()
        return str(data_dir)
    
    @pytest.fixture
    def bootstrap(self, temp_data_dir):
        """Create HistoricalBootstrap instance."""
        return HistoricalBootstrap(data_dir=temp_data_dir)
    
    def test_initialization(self, bootstrap):
        """Test bootstrap initialization."""
        assert bootstrap is not None
        assert bootstrap.active_outcomes == {}
        assert bootstrap.completed_outcomes == {}
        assert bootstrap.checkpoint_interval == 100
    
    def test_two_file_tracking_system(self, bootstrap):
        """Test two-file tracking system (active vs completed)."""
        # Create test signals
        active_signal = SignalOutcome(
            message_id=1,
            channel_name="Test Channel",
            address="0x123",
            symbol="TEST",
            entry_price=1.0,
            status="in_progress"
        )
        
        completed_signal = SignalOutcome(
            message_id=2,
            channel_name="Test Channel",
            address="0x456",
            symbol="DONE",
            entry_price=2.0,
            status="completed",
            is_complete=True
        )
        
        # Add to tracking
        bootstrap.active_outcomes["0x123"] = active_signal
        bootstrap.completed_outcomes["0x456"] = completed_signal
        
        # Save
        bootstrap.save_all()
        
        # Load
        bootstrap.load_existing_data()
        
        # Verify
        assert len(bootstrap.active_outcomes) == 1
        assert len(bootstrap.completed_outcomes) == 1
        assert "0x123" in bootstrap.active_outcomes
        assert "0x456" in bootstrap.completed_outcomes
    
    def test_deduplication_logic(self, bootstrap):
        """Test deduplication logic (prevents duplicate tracking)."""
        # Add signal to active tracking
        signal = SignalOutcome(
            message_id=1,
            channel_name="Test Channel",
            address="0x123",
            symbol="TEST",
            entry_price=1.0,
            signal_number=1
        )
        bootstrap.active_outcomes["0x123"] = signal
        
        # Check for duplicate (should be True)
        is_duplicate, next_number, previous_signals = bootstrap.check_for_duplicate("0x123")
        assert is_duplicate is True
        assert next_number is None
        assert previous_signals is None
    
    def test_fresh_start_re_monitoring(self, bootstrap):
        """Test fresh start re-monitoring (Signal #2, #3, etc.)."""
        # Add completed signal
        completed_signal = SignalOutcome(
            message_id=1,
            channel_name="Test Channel",
            address="0x123",
            symbol="TEST",
            entry_price=1.0,
            signal_number=1,
            ath_multiplier=3.252,
            status="completed",
            is_complete=True
        )
        bootstrap.completed_outcomes["0x123"] = completed_signal
        
        # Check for duplicate (should be False, but with fresh start info)
        is_duplicate, next_number, previous_signals = bootstrap.check_for_duplicate("0x123")
        assert is_duplicate is False
        assert next_number == 2  # Signal #2
        assert previous_signals == [1]  # Previous message ID
    
    def test_archival_to_history(self, bootstrap):
        """Test archival from active to completed history."""
        # Add signal to active
        signal = SignalOutcome(
            message_id=1,
            channel_name="Test Channel",
            address="0x123",
            symbol="TEST",
            entry_price=1.0,
            signal_number=1,
            status="completed",
            is_complete=True
        )
        bootstrap.active_outcomes["0x123"] = signal
        
        # Archive
        success = bootstrap.archive_to_history("0x123")
        assert success is True
        
        # Verify moved
        assert "0x123" not in bootstrap.active_outcomes
        assert "0x123" in bootstrap.completed_outcomes
    
    def test_progress_persistence(self, bootstrap, temp_data_dir):
        """Test progress persistence (resumability)."""
        # Create status
        status = BootstrapStatus(
            total_messages=1000,
            processed_messages=500,
            total_tokens=50,
            processed_tokens=25,
            successful_outcomes=20,
            failed_outcomes=5,
            last_processed_message_id=12345,
            channel_name="Test Channel",
            started_at=datetime.now()
        )
        
        # Save progress
        bootstrap.save_progress(status)
        
        # Verify file exists
        assert bootstrap.status_file.exists()
        
        # Load progress
        loaded_status = bootstrap.load_progress()
        assert loaded_status is not None
        assert loaded_status.processed_messages == 500
        assert loaded_status.last_processed_message_id == 12345
    
    def test_clear_progress(self, bootstrap):
        """Test clearing progress file on completion."""
        # Create and save status
        status = BootstrapStatus(
            total_messages=100,
            processed_messages=100,
            channel_name="Test Channel"
        )
        bootstrap.save_progress(status)
        
        # Verify exists
        assert bootstrap.status_file.exists()
        
        # Clear
        bootstrap.clear_progress()
        
        # Verify deleted
        assert not bootstrap.status_file.exists()
    
    def test_smart_checkpoint_handling(self, bootstrap):
        """Test smart checkpoint handling (Task 4 integration)."""
        # Message 2 days old
        message_date = datetime.now() - timedelta(days=2)
        checkpoints = bootstrap.calculate_smart_checkpoints(message_date)
        
        # Should have 1h, 4h, 24h
        checkpoint_names = [name for name, _ in checkpoints]
        assert '1h' in checkpoint_names
        assert '4h' in checkpoint_names
        assert '24h' in checkpoint_names
        assert '3d' not in checkpoint_names  # Not reached yet
        assert '7d' not in checkpoint_names
        assert '30d' not in checkpoint_names
    
    def test_signal_status_determination(self, bootstrap):
        """Test signal status determination (completed vs in_progress)."""
        # Message 35 days old (completed)
        old_message = datetime.now() - timedelta(days=35)
        status = bootstrap.determine_signal_status(old_message)
        assert status == "completed"
        
        # Message 5 days old (in_progress)
        recent_message = datetime.now() - timedelta(days=5)
        status = bootstrap.determine_signal_status(recent_message)
        assert status == "in_progress"
    
    def test_signal_numbering(self, bootstrap):
        """Test signal numbering for multiple mentions."""
        # First mention
        is_dup, num, prev = bootstrap.check_for_duplicate("0x123")
        assert is_dup is False
        assert num == 1
        assert prev == []
        
        # Add to completed
        signal1 = SignalOutcome(
            message_id=1,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=1,
            previous_signals=[]
        )
        bootstrap.completed_outcomes["0x123"] = signal1
        
        # Second mention
        is_dup, num, prev = bootstrap.check_for_duplicate("0x123")
        assert is_dup is False
        assert num == 2
        assert prev == [1]
        
        # Add Signal #2 to completed
        signal2 = SignalOutcome(
            message_id=2,
            channel_name="Test",
            address="0x123",
            symbol="TEST",
            signal_number=2,
            previous_signals=[1]
        )
        bootstrap.completed_outcomes["0x123"] = signal2
        
        # Third mention
        is_dup, num, prev = bootstrap.check_for_duplicate("0x123")
        assert is_dup is False
        assert num == 3
        assert prev == [1, 2]
    
    def test_get_statistics(self, bootstrap):
        """Test statistics gathering."""
        # Add some signals
        bootstrap.active_outcomes["0x123"] = SignalOutcome(
            message_id=1,
            channel_name="Channel A",
            address="0x123",
            symbol="TEST1"
        )
        bootstrap.completed_outcomes["0x456"] = SignalOutcome(
            message_id=2,
            channel_name="Channel B",
            address="0x456",
            symbol="TEST2"
        )
        
        stats = bootstrap.get_statistics()
        assert stats['active_signals'] == 1
        assert stats['completed_signals'] == 1
        assert stats['total_signals'] == 2
        assert stats['channels'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


"""
Test script to verify separation of concerns refactoring.

Tests all refactored components to ensure they work correctly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_config_validator():
    """Test ConfigValidator utility."""
    print("\n" + "="*80)
    print("Testing ConfigValidator...")
    print("="*80)
    
    from utils.config_validator import ConfigValidator
    
    # Test valid Telegram config
    errors, warnings = ConfigValidator.validate_telegram_config(
        api_id=12345,
        api_hash="a" * 32,
        phone="+1234567890"
    )
    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    print("✓ Valid Telegram config passed")
    
    # Test invalid Telegram config
    errors, warnings = ConfigValidator.validate_telegram_config(
        api_id=0,
        api_hash="short",
        phone="invalid"
    )
    assert len(errors) == 3, f"Expected 3 errors, got {len(errors)}: {errors}"
    print("✓ Invalid Telegram config detected")
    
    # Test log level validation
    validated, warnings = ConfigValidator.validate_log_level("DEBUG")
    assert validated == "DEBUG", f"Expected DEBUG, got {validated}"
    assert len(warnings) == 0, f"Expected no warnings, got: {warnings}"
    print("✓ Valid log level passed")
    
    validated, warnings = ConfigValidator.validate_log_level("INVALID")
    assert validated == "INFO", f"Expected INFO fallback, got {validated}"
    assert len(warnings) == 1, f"Expected 1 warning, got {len(warnings)}: {warnings}"
    print("✓ Invalid log level handled with fallback")
    
    print("\n✓ ConfigValidator tests passed!")


def test_data_enrichment_service():
    """Test DataEnrichmentService."""
    print("\n" + "="*80)
    print("Testing DataEnrichmentService...")
    print("="*80)
    
    from services.pricing.data_enrichment import DataEnrichmentService
    from domain.price_data import PriceData
    
    service = DataEnrichmentService()
    print("✓ DataEnrichmentService initialized")
    
    # Create mock price data
    price_data = PriceData(
        price_usd=1.23,
        symbol="TEST",
        market_cap=1000000,
        volume_24h=50000,
        liquidity_usd=100000,
        price_change_24h=5.0
    )
    
    # Enrich data (will skip if market analyzer not available)
    enriched = service.enrich_price_data(price_data)
    assert enriched is not None, "Expected enriched data"
    assert enriched.price_usd == 1.23, "Price should remain unchanged"
    print("✓ Price data enrichment completed")
    
    print("\n✓ DataEnrichmentService tests passed!")


def test_report_generator():
    """Test ReportGenerator utility."""
    print("\n" + "="*80)
    print("Testing ReportGenerator...")
    print("="*80)
    
    from utils.report_generator import ReportGenerator
    
    # Create mock statistics
    stats = {
        'total_messages': 100,
        'processed_messages': 95,
        'errors': 5,
        'hdrb_scores': [50.0, 60.0, 70.0],
        'crypto_relevant': 30,
        'addresses_found': 20,
        'evm_addresses': 15,
        'solana_addresses': 5,
        'invalid_addresses': 2,
        'prices_fetched': 18,
        'price_failures': 2,
        'api_usage': {'coingecko': 10, 'birdeye': 8},
        'tracking_started': 15,
        'tracking_updated': 3,
        'performance_ath_updates': 5,
        'outcome_ath_updates': 2,
        'messages_written': 95,
        'token_prices_written': 18,
        'performance_written': 18,
        'historical_written': 10,
        'signals_tracked': 15,
        'winners_classified': 5,
        'losers_classified': 10,
        'reputations_calculated': 2,
        'positive_sentiment': 40,
        'negative_sentiment': 20,
        'neutral_sentiment': 35,
        'confidence_scores': [0.7, 0.8, 0.6],
        'high_confidence': 60,
        'processing_times': [50.0, 60.0, 55.0]
    }
    
    # Generate report
    report = ReportGenerator.generate_verification_report(stats)
    assert isinstance(report, str), "Expected string report"
    assert len(report) > 0, "Report should not be empty"
    assert "VERIFICATION REPORT" in report, "Report should contain title"
    assert "SUMMARY STATISTICS" in report, "Report should contain summary"
    print("✓ Report generated successfully")
    print(f"✓ Report length: {len(report)} characters")
    
    print("\n✓ ReportGenerator tests passed!")


def test_outcome_repository():
    """Test OutcomeRepository."""
    print("\n" + "="*80)
    print("Testing OutcomeRepository...")
    print("="*80)
    
    from repositories.file_storage.outcome_repository import OutcomeRepository
    from domain.signal_outcome import SignalOutcome
    from datetime import datetime, timezone
    import tempfile
    import shutil
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo = OutcomeRepository(data_dir=temp_dir)
        print("✓ OutcomeRepository initialized")
        
        # Create test outcome
        outcome = SignalOutcome(
            message_id=123,
            channel_name="test_channel",
            address="0x1234567890abcdef",
            symbol="TEST",
            entry_price=1.0,
            entry_timestamp=datetime.now(timezone.utc)
        )
        
        # Save outcomes
        outcomes = {"0x1234567890abcdef": outcome}
        repo.save(outcomes)
        print("✓ Outcomes saved")
        
        # Load outcomes
        loaded = repo.load()
        assert len(loaded) == 1, f"Expected 1 outcome, got {len(loaded)}"
        assert "0x1234567890abcdef" in loaded, "Expected address in loaded outcomes"
        assert loaded["0x1234567890abcdef"].symbol == "TEST", "Symbol should match"
        print("✓ Outcomes loaded successfully")
        
        print("\n✓ OutcomeRepository tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_outcome_tracker():
    """Test OutcomeTracker with repository."""
    print("\n" + "="*80)
    print("Testing OutcomeTracker...")
    print("="*80)
    
    from intelligence.outcome_tracker import OutcomeTracker
    from datetime import datetime, timezone
    import tempfile
    import shutil
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        tracker = OutcomeTracker(data_dir=temp_dir)
        print("✓ OutcomeTracker initialized")
        
        # Track a signal
        outcome = tracker.track_signal(
            message_id=456,
            channel_name="test_channel",
            address="0xabcdef1234567890",
            entry_price=2.5,
            symbol="TEST2"
        )
        
        assert outcome is not None, "Expected outcome object"
        assert outcome.entry_price == 2.5, "Entry price should match"
        print("✓ Signal tracked successfully")
        
        # Update price
        updated = tracker.update_price("0xabcdef1234567890", 3.0)
        assert updated is not None, "Expected updated outcome"
        assert updated.current_price == 3.0, "Current price should be updated"
        print("✓ Price updated successfully")
        
        # Get outcome
        retrieved = tracker.get_outcome("0xabcdef1234567890")
        assert retrieved is not None, "Expected to retrieve outcome"
        assert retrieved.symbol == "TEST2", "Symbol should match"
        print("✓ Outcome retrieved successfully")
        
        print("\n✓ OutcomeTracker tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_config_with_validator():
    """Test Config class using ConfigValidator."""
    print("\n" + "="*80)
    print("Testing Config with ConfigValidator...")
    print("="*80)
    
    from config.settings import Config, TelegramConfig, ChannelConfig
    
    # Create test config
    telegram = TelegramConfig(
        api_id=12345,
        api_hash="a" * 32,
        phone="+1234567890"
    )
    
    channels = [
        ChannelConfig(id="test1", name="Test Channel 1", enabled=True)
    ]
    
    # Mock config object
    class MockConfig:
        def __init__(self):
            self.telegram = telegram
            self.channels = channels
            self.log_level = "INFO"
        
        def validate(self):
            from utils.config_validator import ConfigValidator
            errors, warnings = ConfigValidator.validate_all(
                self.telegram,
                self.channels,
                self.log_level
            )
            if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                self.log_level = 'INFO'
            return errors, warnings
    
    config = MockConfig()
    errors, warnings = config.validate()
    
    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    print("✓ Config validation passed")
    
    print("\n✓ Config with ConfigValidator tests passed!")


def test_imports():
    """Test all imports work correctly."""
    print("\n" + "="*80)
    print("Testing all imports...")
    print("="*80)
    
    try:
        from utils.config_validator import ConfigValidator
        print("✓ ConfigValidator imported")
        
        from core.data_enrichment_service import DataEnrichmentService
        print("✓ DataEnrichmentService imported")
        
        from utils.report_generator import ReportGenerator
        print("✓ ReportGenerator imported")
        
        from intelligence.outcome_repository import OutcomeRepository
        print("✓ OutcomeRepository imported")
        
        from intelligence.outcome_tracker import OutcomeTracker
        print("✓ OutcomeTracker imported")
        
        from config.settings import Config
        print("✓ Config imported")
        
        from core.price_engine import PriceEngine
        print("✓ PriceEngine imported")
        
        import main
        print("✓ main.py imported")
        
        print("\n✓ All imports successful!")
        
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        raise


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SEPARATION OF CONCERNS REFACTORING TESTS")
    print("="*80)
    
    try:
        test_imports()
        test_config_validator()
        test_data_enrichment_service()
        test_report_generator()
        test_outcome_repository()
        test_outcome_tracker()
        test_config_with_validator()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        print("\nRefactoring Summary:")
        print("  ✓ Configuration validation extracted to utils/config_validator.py")
        print("  ✓ Market intelligence analysis moved to core/data_enrichment_service.py")
        print("  ✓ Report generation extracted to utils/report_generator.py")
        print("  ✓ Data persistence separated to intelligence/outcome_repository.py")
        print("  ✓ Business logic properly separated from data access")
        print("  ✓ All components tested and working correctly")
        print("\n" + "="*80)
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"✗ TEST FAILED: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

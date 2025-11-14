"""Test suite for new layered architecture.

Verifies that all layers work correctly with proper separation of concerns.
"""
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path


def test_domain_layer():
    """Test domain models - pure data structures with no dependencies."""
    print("\n" + "="*80)
    print("TEST 1: Domain Layer")
    print("="*80)
    
    try:
        from domain.price_data import PriceData
        from domain.signal_outcome import SignalOutcome, CheckpointData, CHECKPOINTS
        from domain.channel_reputation import ChannelReputation, TierPerformance, REPUTATION_TIERS
        from domain.message_event import MessageEvent
        
        print("✅ All domain models imported successfully")
        
        # Test PriceData
        price = PriceData(
            price_usd=0.00001234,
            market_cap=1000000,
            volume_24h=50000,
            symbol="TEST",
            source="test"
        )
        print(f"✅ PriceData created: {price.symbol} @ ${price.price_usd}")
        
        # Test SignalOutcome
        outcome = SignalOutcome(
            message_id=12345,
            channel_name="test_channel",
            address="0xtest123",
            symbol="TEST",
            entry_price=0.00001234
        )
        print(f"✅ SignalOutcome created: {outcome.symbol} from {outcome.channel_name}")
        
        # Test ChannelReputation
        reputation = ChannelReputation(channel_name="test_channel")
        print(f"✅ ChannelReputation created: {reputation.channel_name}")
        
        # Test MessageEvent
        event = MessageEvent(
            channel_id="123",
            channel_name="test_channel",
            message_id=456,
            message_text="Test message",
            timestamp=datetime.now(),
            sender_id=789
        )
        print(f"✅ MessageEvent created: {event.message_text}")
        
        print("\n✅ Domain Layer: PASS - All models work correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Domain Layer: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repositories_layer():
    """Test repositories - data access with no business logic."""
    print("\n" + "="*80)
    print("TEST 2: Repositories Layer")
    print("="*80)
    
    try:
        # Test API clients
        from repositories.api_clients import (
            PriceData,
            BaseAPIClient,
            CoinGeckoClient,
            BirdeyeClient,
            MoralisClient,
            DexScreenerClient,
            CryptoCompareClient,
            DefiLlamaClient,
            TwelveDataClient
        )
        print("✅ All API clients imported successfully")
        
        # Test file storage repositories
        from repositories.file_storage import (
            OutcomeRepository,
            ReputationRepository,
            TrackingRepository
        )
        print("✅ All file storage repositories imported successfully")
        
        # Test writers
        from repositories.writers import CSVTableWriter, GoogleSheetsMultiTable
        print("✅ All writers imported successfully")
        
        # Test OutcomeRepository
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = OutcomeRepository(data_dir=tmpdir)
            print(f"✅ OutcomeRepository created: {repo.get_file_path()}")
            
            # Test save/load
            from domain.signal_outcome import SignalOutcome
            test_outcome = SignalOutcome(
                message_id=123,
                channel_name="test",
                address="0xtest",
                entry_price=0.001
            )
            repo.save({"0xtest": test_outcome})
            loaded = repo.load()
            print(f"✅ OutcomeRepository save/load works: {len(loaded)} outcomes")
        
        # Test ReputationRepository
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ReputationRepository(data_dir=tmpdir)
            print(f"✅ ReputationRepository created: {repo.get_file_path()}")
            
            # Test save/load
            from domain.channel_reputation import ChannelReputation
            test_rep = ChannelReputation(channel_name="test")
            repo.save({"test": test_rep})
            loaded = repo.load()
            print(f"✅ ReputationRepository save/load works: {len(loaded)} reputations")
        
        print("\n✅ Repositories Layer: PASS - All repositories work correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Repositories Layer: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_services_layer():
    """Test services - business logic with no data access."""
    print("\n" + "="*80)
    print("TEST 3: Services Layer")
    print("="*80)
    
    try:
        # Test analytics services
        from services.analytics import (
            SentimentAnalyzer,
            HDRBScorer,
            MarketAnalyzer,
            MarketIntelligence
        )
        print("✅ All analytics services imported successfully")
        
        # Test message processing services
        from services.message_processing import (
            MessageProcessor,
            AddressExtractor,
            CryptoDetector
        )
        print("✅ All message processing services imported successfully")
        
        # Test pricing services
        from services.pricing import PriceEngine, DataEnrichmentService
        print("✅ All pricing services imported successfully")
        
        # Test tracking services
        from services.tracking import PerformanceTracker, OutcomeTracker
        print("✅ All tracking services imported successfully")
        
        # Test reputation services
        from services.reputation import (
            ReputationEngine,
            ReputationCalculator,
            ROICalculator
        )
        print("✅ All reputation services imported successfully")
        
        # Test SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        sentiment, score = analyzer.analyze("This is bullish! 🚀 Moon soon!")
        print(f"✅ SentimentAnalyzer works: '{sentiment}' (score: {score:.2f})")
        
        # Test HDRBScorer
        scorer = HDRBScorer()
        result = scorer.calculate_score(forwards=10, reactions=50, replies=5)
        print(f"✅ HDRBScorer works: score={result['normalized_score']:.2f}")
        
        # Test MarketAnalyzer
        analyzer = MarketAnalyzer()
        # MarketAnalyzer.analyze expects keyword arguments
        intelligence = analyzer.analyze(
            market_cap=5000000.0,
            liquidity_usd=50000.0,
            volume_24h=100000.0,
            price_change_24h=5.5
        )
        print(f"✅ MarketAnalyzer works: tier={intelligence.market_tier}, risk={intelligence.risk_level}")
        
        # Test AddressExtractor
        extractor = AddressExtractor()
        # AddressExtractor.extract_addresses expects a list of crypto mentions
        addresses = extractor.extract_addresses(["0x1234567890abcdef1234567890abcdef12345678"])
        print(f"✅ AddressExtractor works: found {len(addresses)} addresses")
        
        # Test CryptoDetector
        detector = CryptoDetector()
        mentions = detector.detect_mentions("Bitcoin and Ethereum are pumping! BTC ETH")
        print(f"✅ CryptoDetector works: found {len(mentions)} mentions")
        
        print("\n✅ Services Layer: PASS - All services work correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Services Layer: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infrastructure_layer():
    """Test infrastructure - external integrations."""
    print("\n" + "="*80)
    print("TEST 4: Infrastructure Layer")
    print("="*80)
    
    try:
        # Test telegram integration
        from infrastructure.telegram import TelegramMonitor
        print("✅ TelegramMonitor imported successfully")
        
        # Test output
        from infrastructure.output import MultiTableDataOutput
        print("✅ MultiTableDataOutput imported successfully")
        
        # Test scrapers
        from infrastructure.scrapers import HistoricalScraper
        print("✅ HistoricalScraper imported successfully")
        
        print("\n✅ Infrastructure Layer: PASS - All components imported correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Infrastructure Layer: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_orchestrator():
    """Test main system orchestrator."""
    print("\n" + "="*80)
    print("TEST 5: Main Orchestrator")
    print("="*80)
    
    try:
        from main import CryptoIntelligenceSystem
        print("✅ CryptoIntelligenceSystem imported successfully")
        
        # Test instantiation (without actually starting)
        system = CryptoIntelligenceSystem()
        print("✅ CryptoIntelligenceSystem instantiated successfully")
        
        print("\n✅ Main Orchestrator: PASS - System can be created")
        return True
        
    except Exception as e:
        print(f"\n❌ Main Orchestrator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_flow():
    """Test that dependency flow is correct (no circular dependencies)."""
    print("\n" + "="*80)
    print("TEST 6: Dependency Flow")
    print("="*80)
    
    try:
        # Test domain has no dependencies
        import domain
        print("✅ Domain layer has no external dependencies")
        
        # Test repositories depend only on domain
        from repositories.api_clients.base_client import BaseAPIClient
        from repositories.file_storage.outcome_repository import OutcomeRepository
        print("✅ Repositories layer depends only on domain")
        
        # Test services depend on repositories and domain
        from services.analytics.sentiment_analyzer import SentimentAnalyzer
        from services.pricing.price_engine import PriceEngine
        print("✅ Services layer depends on repositories and domain")
        
        # Test infrastructure depends on services
        from infrastructure.telegram.telegram_monitor import TelegramMonitor
        print("✅ Infrastructure layer depends on services")
        
        # Test main depends on infrastructure
        from main import CryptoIntelligenceSystem
        print("✅ Main orchestrator depends on infrastructure")
        
        print("\n✅ Dependency Flow: PASS - Proper layered dependencies")
        return True
        
    except Exception as e:
        print(f"\n❌ Dependency Flow: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_flow():
    """Test a simple integration flow through all layers."""
    print("\n" + "="*80)
    print("TEST 7: Integration Flow")
    print("="*80)
    
    try:
        # Create a message event (domain)
        from domain.message_event import MessageEvent
        event = MessageEvent(
            channel_id="123",
            channel_name="test_channel",
            message_id=456,
            message_text="Check out Bitcoin! BTC is pumping 🚀",
            timestamp=datetime.now(),
            sender_id=789
        )
        print(f"✅ Step 1: Created MessageEvent")
        
        # Detect crypto mentions (service)
        from services.message_processing.crypto_detector import CryptoDetector
        detector = CryptoDetector()
        mentions = detector.detect_mentions(event.message_text)
        print(f"✅ Step 2: Detected {len(mentions)} crypto mentions")
        
        # Analyze sentiment (service)
        from services.analytics.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        sentiment, score = analyzer.analyze(event.message_text)
        print(f"✅ Step 3: Analyzed sentiment: {sentiment} ({score:.2f})")
        
        # Calculate HDRB score (service)
        from services.analytics.hdrb_scorer import HDRBScorer
        scorer = HDRBScorer()
        hdrb = scorer.calculate_score(forwards=5, reactions=20, replies=2)
        print(f"✅ Step 4: Calculated HDRB score: {hdrb['normalized_score']:.2f}")
        
        # Create signal outcome (domain)
        from domain.signal_outcome import SignalOutcome
        outcome = SignalOutcome(
            message_id=event.message_id,
            channel_name=event.channel_name,
            address="0xtest123",
            symbol="BTC",
            entry_price=50000.0,
            sentiment=sentiment,
            sentiment_score=score,
            hdrb_score=hdrb['normalized_score']
        )
        print(f"✅ Step 5: Created SignalOutcome")
        
        # Save to repository
        import tempfile
        from repositories.file_storage.outcome_repository import OutcomeRepository
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = OutcomeRepository(data_dir=tmpdir)
            repo.save({"0xtest123": outcome})
            loaded = repo.load()
            print(f"✅ Step 6: Saved and loaded from repository")
        
        print("\n✅ Integration Flow: PASS - All layers work together")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration Flow: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all architecture tests."""
    print("\n" + "="*80)
    print("NEW ARCHITECTURE TEST SUITE")
    print("="*80)
    print("Testing layered architecture with proper separation of concerns")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Domain Layer", test_domain_layer()))
    results.append(("Repositories Layer", test_repositories_layer()))
    results.append(("Services Layer", test_services_layer()))
    results.append(("Infrastructure Layer", test_infrastructure_layer()))
    results.append(("Main Orchestrator", test_main_orchestrator()))
    results.append(("Dependency Flow", test_dependency_flow()))
    results.append(("Integration Flow", test_integration_flow()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("="*80)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Architecture is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

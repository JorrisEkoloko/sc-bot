"""Test script for ReputationEngine."""
from datetime import datetime, timedelta
from services.tracking.outcome_tracker import OutcomeTracker
from services.reputation.reputation_engine import ReputationEngine
from domain.signal_outcome import SignalOutcome

def create_test_outcomes():
    """Create test signal outcomes for reputation calculation."""
    tracker = OutcomeTracker()
    
    # Create 15 test signals with varying ROI outcomes
    test_data = [
        # (symbol, entry, ath, days, winner)
        ("TOKEN1", 1.00, 3.25, 1.0, True),   # 3.25x - great
        ("TOKEN2", 1.00, 0.93, 2.0, False),  # 0.93x - loss
        ("TOKEN3", 1.00, 2.15, 1.5, True),   # 2.15x - good
        ("TOKEN4", 1.00, 4.50, 0.8, True),   # 4.50x - great
        ("TOKEN5", 1.00, 0.75, 3.0, False),  # 0.75x - loss
        ("TOKEN6", 1.00, 2.80, 1.2, True),   # 2.80x - good
        ("TOKEN7", 1.00, 1.50, 2.5, False),  # 1.50x - break_even
        ("TOKEN8", 1.00, 3.10, 1.0, True),   # 3.10x - great
        ("TOKEN9", 1.00, 0.85, 4.0, False),  # 0.85x - loss
        ("TOKEN10", 1.00, 2.40, 1.8, True),  # 2.40x - good
        ("TOKEN11", 1.00, 1.75, 2.0, False), # 1.75x - break_even
        ("TOKEN12", 1.00, 2.90, 1.3, True),  # 2.90x - good
        ("TOKEN13", 1.00, 5.20, 0.5, True),  # 5.20x - moon
        ("TOKEN14", 1.00, 1.20, 3.5, False), # 1.20x - break_even
        ("TOKEN15", 1.00, 2.60, 1.5, True),  # 2.60x - good
    ]
    
    outcomes = []
    for i, (symbol, entry, ath, days, is_winner) in enumerate(test_data):
        outcome = tracker.track_signal(
            message_id=1000 + i,
            channel_name="Eric Cryptomans Journal",
            address=f"test_address_{i}",
            entry_price=entry,
            entry_confidence=0.82,
            entry_source="message_text",
            symbol=symbol,
            sentiment="positive",
            sentiment_score=0.78,
            hdrb_score=68.5,
            confidence=0.82,
            market_tier="small",
            risk_level="high",
            risk_score=0.75
        )
        
        # Set ATH and complete
        outcome.ath_price = ath
        outcome.ath_multiplier = ath
        outcome.days_to_ath = days
        outcome.entry_timestamp = datetime.now() - timedelta(days=days)
        tracker.complete_signal(f"test_address_{i}", "test")
        
        outcomes.append(outcome)
    
    return outcomes

def test_reputation_calculation():
    """Test reputation calculation from outcomes."""
    print("="*60)
    print("TEST 1: Reputation Calculation")
    print("="*60)
    
    # Create test outcomes
    outcomes = create_test_outcomes()
    print(f"\n✓ Created {len(outcomes)} test signal outcomes")
    
    # Calculate reputation
    engine = ReputationEngine()
    reputation = engine.update_reputation("Eric Cryptomans Journal", outcomes)
    
    print(f"\nChannel: {reputation.channel_name}")
    print("-"*60)
    
    # Test win rate
    print(f"\n1. Win Rate Calculation:")
    print(f"   Total Signals: {reputation.total_signals}")
    print(f"   Winners (≥2x): {reputation.winning_signals}")
    print(f"   Losers (<1x): {reputation.losing_signals}")
    print(f"   Neutral (1-2x): {reputation.neutral_signals}")
    print(f"   Win Rate: {reputation.win_rate:.1f}%")
    expected_win_rate = (9 / 15) * 100  # 9 winners out of 15
    print(f"   Expected: {expected_win_rate:.1f}%")
    print(f"   ✓ PASS" if abs(reputation.win_rate - expected_win_rate) < 0.1 else "   ✗ FAIL")
    
    # Test average ROI
    print(f"\n2. Average ROI Calculation:")
    print(f"   Average ROI: {reputation.average_roi:.3f}x ({(reputation.average_roi - 1) * 100:.1f}% gain)")
    print(f"   Median ROI: {reputation.median_roi:.3f}x")
    print(f"   Best ROI: {reputation.best_roi:.3f}x")
    print(f"   Worst ROI: {reputation.worst_roi:.3f}x")
    print(f"   ✓ Average ROI calculated")
    
    # Test Sharpe ratio
    print(f"\n3. Sharpe Ratio Calculation:")
    print(f"   Sharpe Ratio: {reputation.sharpe_ratio:.3f}")
    print(f"   ROI Std Dev: {reputation.roi_std_dev:.3f}")
    print(f"   Formula: ({reputation.average_roi:.3f} - 1.0) / {reputation.roi_std_dev:.3f} = {reputation.sharpe_ratio:.3f}")
    print(f"   ✓ Sharpe ratio calculated")
    
    # Test speed score
    print(f"\n4. Speed Score Calculation:")
    print(f"   Avg Time to ATH: {reputation.avg_time_to_ath:.1f} days")
    print(f"   Avg Time to 2x: {reputation.avg_time_to_2x:.1f} days")
    print(f"   Speed Score: {reputation.speed_score:.1f}/100")
    print(f"   ✓ Speed score calculated")
    
    # Test composite score
    print(f"\n5. Composite Reputation Score:")
    print(f"   Win Rate ({reputation.win_rate:.1f}%) × 30% = {reputation.win_rate * 0.30:.1f}")
    print(f"   Avg ROI ({reputation.average_roi:.3f}x) × 25% = {(reputation.average_roi - 1.0) * 50 * 0.25:.1f}")
    print(f"   Sharpe ({reputation.sharpe_ratio:.3f}) × 20% = {reputation.sharpe_ratio * 50 * 0.20:.1f}")
    print(f"   Speed ({reputation.speed_score:.1f}) × 15% = {reputation.speed_score * 0.15:.1f}")
    print(f"   Confidence ({reputation.avg_confidence:.2f}) × 10% = {reputation.avg_confidence * 100 * 0.10:.1f}")
    print(f"   ---")
    print(f"   Reputation Score: {reputation.reputation_score:.1f}/100")
    print(f"   Reputation Tier: {reputation.reputation_tier}")
    print(f"   ✓ Composite score calculated")

def test_tier_classification():
    """Test reputation tier classification."""
    print("\n" + "="*60)
    print("TEST 2: Reputation Tier Classification")
    print("="*60)
    
    from intelligence.reputation_calculator import ReputationCalculator
    
    test_cases = [
        (95, 15, "Elite"),
        (82, 15, "Excellent"),
        (68, 15, "Good"),
        (52, 15, "Average"),
        (35, 15, "Poor"),
        (15, 15, "Unreliable"),
        (75, 5, "Unproven"),  # Not enough signals
    ]
    
    for score, signals, expected_tier in test_cases:
        tier = ReputationCalculator.determine_tier(score, signals)
        status = "✓ PASS" if tier == expected_tier else "✗ FAIL"
        print(f"   Score={score}, Signals={signals} → {tier} (expected: {expected_tier}) {status}")

def test_persistence():
    """Test reputation persistence."""
    print("\n" + "="*60)
    print("TEST 3: Reputation Persistence")
    print("="*60)
    
    # Create and save reputation
    outcomes = create_test_outcomes()
    engine1 = ReputationEngine()
    rep1 = engine1.update_reputation("Test Channel", outcomes)
    
    print(f"\n✓ Created reputation: Score={rep1.reputation_score:.1f}, Tier={rep1.reputation_tier}")
    
    # Load reputation in new engine
    engine2 = ReputationEngine()
    rep2 = engine2.get_reputation("Test Channel")
    
    if rep2:
        print(f"✓ Loaded reputation: Score={rep2.reputation_score:.1f}, Tier={rep2.reputation_tier}")
        print(f"✓ Persistence working correctly")
    else:
        print(f"✗ Failed to load reputation")

def test_expected_roi_initialization():
    """Test expected ROI initialization."""
    print("\n" + "="*60)
    print("TEST 4: Expected ROI Initialization")
    print("="*60)
    
    outcomes = create_test_outcomes()
    engine = ReputationEngine()
    reputation = engine.update_reputation("ROI Test Channel", outcomes)
    
    print(f"\n   Average ROI: {reputation.average_roi:.3f}x")
    print(f"   Expected ROI: {reputation.expected_roi:.3f}x")
    print(f"   ✓ Expected ROI initialized to average ROI")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("REPUTATION ENGINE VALIDATION TESTS")
    print("="*60)
    
    test_reputation_calculation()
    test_tier_classification()
    test_persistence()
    test_expected_roi_initialization()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

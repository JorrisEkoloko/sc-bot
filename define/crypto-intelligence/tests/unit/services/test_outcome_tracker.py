"""Test script for OutcomeTracker ROI calculations."""
import asyncio
from datetime import datetime, timedelta
from services.tracking.outcome_tracker import OutcomeTracker
from utils.roi_calculator import ROICalculator
from domain.signal_outcome import CHECKPOINTS

def test_roi_calculation():
    """Test ROI calculation formula."""
    print("="*60)
    print("TEST 1: ROI Calculation Formula")
    print("="*60)
    
    # Test case 1: Entry $1.47, Current $4.78 (AVICI example)
    roi_pct, roi_mult = ROICalculator.calculate_roi(1.47, 4.78)
    print(f"\nTest Case 1: Entry $1.47 → Current $4.78")
    print(f"  ROI Percentage: {roi_pct:.1f}%")
    print(f"  ROI Multiplier: {roi_mult:.3f}x")
    print(f"  Expected: 225.2%, 3.252x")
    print(f"  ✓ PASS" if abs(roi_pct - 225.2) < 0.1 and abs(roi_mult - 3.252) < 0.001 else "  ✗ FAIL")
    
    # Test case 2: Entry $14.96, Current $13.94 (NKP example)
    roi_pct, roi_mult = ROICalculator.calculate_roi(14.96, 13.94)
    print(f"\nTest Case 2: Entry $14.96 → Current $13.94")
    print(f"  ROI Percentage: {roi_pct:.1f}%")
    print(f"  ROI Multiplier: {roi_mult:.3f}x")
    print(f"  Expected: -6.8%, 0.932x")
    print(f"  ✓ PASS" if abs(roi_pct - (-6.8)) < 0.1 and abs(roi_mult - 0.932) < 0.001 else "  ✗ FAIL")
    
    # Test case 3: Entry $1.00, Current $2.00 (2x winner)
    roi_pct, roi_mult = ROICalculator.calculate_roi(1.00, 2.00)
    print(f"\nTest Case 3: Entry $1.00 → Current $2.00")
    print(f"  ROI Percentage: {roi_pct:.1f}%")
    print(f"  ROI Multiplier: {roi_mult:.3f}x")
    print(f"  Expected: 100.0%, 2.000x")
    print(f"  ✓ PASS" if abs(roi_pct - 100.0) < 0.1 and abs(roi_mult - 2.0) < 0.001 else "  ✗ FAIL")

def test_signal_tracking():
    """Test signal tracking with checkpoints."""
    tracker = OutcomeTracker()
    
    print("\n" + "="*60)
    print("TEST 2: Signal Tracking with Checkpoints")
    print("="*60)
    
    # Track a new signal
    outcome = tracker.track_signal(
        message_id=12345,
        channel_name="Eric Cryptomans Journal",
        address="5gb4npgfb3mhfhsekn4sbay6t9mb8ikce9hyikyid4td",
        entry_price=1.47,
        entry_confidence=0.85,
        entry_source="message_text",
        symbol="AVICI",
        sentiment="positive",
        sentiment_score=0.78,
        hdrb_score=68.5,
        confidence=0.82,
        market_tier="small",
        risk_level="high",
        risk_score=0.75
    )
    
    print(f"\n✓ Signal tracked: {outcome.symbol} at ${outcome.entry_price:.2f}")
    print(f"  Channel: {outcome.channel_name}")
    print(f"  Entry Confidence: {outcome.entry_confidence:.2f}")
    print(f"  Entry Source: {outcome.entry_source}")
    
    # Simulate price updates at different checkpoints
    print("\n" + "-"*60)
    print("Simulating price updates at checkpoints:")
    print("-"*60)
    
    # Manually set entry timestamp to past for testing
    outcome.entry_timestamp = datetime.now() - timedelta(days=2)
    
    # Update 1: After 1 hour - small gain
    print("\n1h checkpoint: $1.52 (+3.4%)")
    tracker.update_price(outcome.address, 1.52)
    cp_1h = outcome.checkpoints["1h"]
    print(f"  Reached: {cp_1h.reached}")
    print(f"  ROI: {cp_1h.roi_percentage:.1f}% ({cp_1h.roi_multiplier:.3f}x)")
    
    # Update 2: After 4 hours - moderate gain
    print("\n4h checkpoint: $1.89 (+28.6%)")
    tracker.update_price(outcome.address, 1.89)
    cp_4h = outcome.checkpoints["4h"]
    print(f"  Reached: {cp_4h.reached}")
    print(f"  ROI: {cp_4h.roi_percentage:.1f}% ({cp_4h.roi_multiplier:.3f}x)")
    
    # Update 3: After 24 hours - big gain (ATH)
    print("\n24h checkpoint: $4.78 (+225.2%) ← ATH")
    tracker.update_price(outcome.address, 4.78)
    cp_24h = outcome.checkpoints["24h"]
    print(f"  Reached: {cp_24h.reached}")
    print(f"  ROI: {cp_24h.roi_percentage:.1f}% ({cp_24h.roi_multiplier:.3f}x)")
    print(f"  ATH: ${outcome.ath_price:.2f} ({outcome.ath_multiplier:.3f}x)")
    print(f"  Days to ATH: {outcome.days_to_ath:.1f}")
    
    # Update 4: After 3 days - slight pullback
    print("\n3d checkpoint: $4.29 (+191.8%)")
    tracker.update_price(outcome.address, 4.29)
    cp_3d = outcome.checkpoints["3d"]
    print(f"  Reached: {cp_3d.reached}")
    print(f"  ROI: {cp_3d.roi_percentage:.1f}% ({cp_3d.roi_multiplier:.3f}x)")
    print(f"  Current vs ATH: ${outcome.current_price:.2f} vs ${outcome.ath_price:.2f}")
    
    # Check winner status
    print("\n" + "-"*60)
    print("Outcome Analysis:")
    print("-"*60)
    print(f"  ATH Multiplier: {outcome.ath_multiplier:.3f}x")
    print(f"  Is Winner (≥2x): {outcome.ath_multiplier >= 2.0}")
    print(f"  Status: {outcome.status}")
    
    if outcome.ath_multiplier >= 2.0:
        print(f"  ✓ WINNER - Achieved {outcome.ath_multiplier:.3f}x (>{outcome.ath_multiplier - 1:.1%} gain)")
    else:
        print(f"  ✗ Not a winner - Only achieved {outcome.ath_multiplier:.3f}x")

def test_outcome_categorization():
    """Test outcome categorization."""
    tracker = OutcomeTracker()
    
    print("\n" + "="*60)
    print("TEST 3: Outcome Categorization")
    print("="*60)
    
    test_cases = [
        (12.5, "moon", "5x+ = 400%+ gain"),
        (4.2, "great", "3-5x = 200-400% gain"),
        (2.5, "good", "2-3x = 100-200% gain"),
        (1.5, "break_even", "1-2x = 0-100% gain"),
        (0.5, "loss", "<1x = negative ROI")
    ]
    
    for ath_mult, expected_category, description in test_cases:
        # Create and complete a signal
        address = f"test_{ath_mult}"
        outcome = tracker.track_signal(
            message_id=int(ath_mult * 1000),
            channel_name="Test Channel",
            address=address,
            entry_price=1.0,
            symbol=f"TEST{int(ath_mult)}"
        )
        
        outcome.ath_price = ath_mult
        outcome.ath_multiplier = ath_mult
        tracker.complete_signal(address, "test")
        
        print(f"\n  ATH: {ath_mult:.1f}x → Category: {outcome.outcome_category}")
        print(f"    Expected: {expected_category} ({description})")
        print(f"    Winner: {outcome.is_winner}")
        print(f"    ✓ PASS" if outcome.outcome_category == expected_category else "    ✗ FAIL")

def test_checkpoint_timing():
    """Test checkpoint timing."""
    print("\n" + "="*60)
    print("TEST 4: Checkpoint Timing")
    print("="*60)
    
    print("\nCheckpoint intervals:")
    for name, interval in CHECKPOINTS.items():
        total_seconds = interval.total_seconds()
        if total_seconds < 3600:
            print(f"  {name}: {total_seconds/60:.0f} minutes")
        elif total_seconds < 86400:
            print(f"  {name}: {total_seconds/3600:.0f} hours")
        else:
            print(f"  {name}: {total_seconds/86400:.0f} days")
    
    print("\n✓ Checkpoints align with pump-and-dump lifecycle:")
    print("  1h-4h: Initial pump phase")
    print("  24h: Peak or dump begins")
    print("  3d-7d: Post-dump stabilization")
    print("  30d: Long-term survivors")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("OUTCOME TRACKER VALIDATION TESTS")
    print("="*60)
    
    test_roi_calculation()
    test_signal_tracking()
    test_outcome_categorization()
    test_checkpoint_timing()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

#!/usr/bin/env python3
"""
External MCP-style verification script for channel reputation system.
Validates data integrity, calculations, and system state.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_json(filepath):
    """Load JSON file safely."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def verify_signal_outcomes(data):
    """Verify signal outcomes data structure and calculations."""
    print("\n=== SIGNAL OUTCOMES VERIFICATION ===")
    
    if not data:
        print("❌ No signal outcomes data found")
        return False
    
    total = len(data)
    print(f"✓ Total signals: {total}")
    
    # Check completion status
    completed = [s for s in data.values() if s.get('is_complete', False)]
    print(f"✓ Completed signals: {len(completed)}/{total}")
    
    # Check winner classification
    winners = [s for s in completed if s.get('is_winner', False)]
    losers = [s for s in completed if not s.get('is_winner', False) and s.get('ath_multiplier', 1.0) < 1.0]
    neutral = [s for s in completed if not s.get('is_winner', False) and s.get('ath_multiplier', 1.0) >= 1.0]
    
    print(f"✓ Winners (>2x): {len(winners)}")
    print(f"✓ Losers (<1x): {len(losers)}")
    print(f"✓ Neutral/Break-even: {len(neutral)}")
    
    # Verify ROI calculations
    print("\n--- ROI Analysis ---")
    for addr, signal in list(data.items())[:3]:  # Sample first 3
        ath_mult = signal.get('ath_multiplier', 1.0)
        is_winner = signal.get('is_winner', False)
        outcome = signal.get('outcome_category', 'unknown')
        
        print(f"  {signal.get('symbol', 'N/A')}: {ath_mult}x → {outcome} (winner={is_winner})")
        
        # Validate winner classification
        if ath_mult >= 2.0 and not is_winner:
            print(f"    ⚠️  Should be winner but marked as {is_winner}")
        if ath_mult < 2.0 and is_winner:
            print(f"    ⚠️  Marked as winner but only {ath_mult}x")
    
    # Check for data issues
    issues = []
    all_same_roi = len(set(s.get('ath_multiplier', 1.0) for s in data.values())) == 1
    if all_same_roi:
        issues.append("All signals have identical ROI (likely data issue)")
    
    if issues:
        print("\n⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

def verify_channel_reputation(data):
    """Verify channel reputation calculations."""
    print("\n=== CHANNEL REPUTATION VERIFICATION ===")
    
    if not data:
        print("❌ No channel reputation data found")
        return False
    
    for channel_name, stats in data.items():
        print(f"\n--- {channel_name} ---")
        print(f"  Total signals: {stats.get('total_signals', 0)}")
        print(f"  Win rate: {stats.get('win_rate', 0)*100:.1f}%")
        print(f"  Average ROI: {stats.get('average_roi', 0):.3f}x")
        print(f"  Reputation score: {stats.get('reputation_score', 0):.1f}/100")
        print(f"  Tier: {stats.get('reputation_tier', 'Unknown')}")
        
        # Verify calculations
        total = stats.get('total_signals', 0)
        winners = stats.get('winning_signals', 0)
        calculated_win_rate = winners / total if total > 0 else 0
        reported_win_rate = stats.get('win_rate', 0)
        
        if abs(calculated_win_rate - reported_win_rate) > 0.01:
            print(f"  ⚠️  Win rate mismatch: calculated {calculated_win_rate:.2%} vs reported {reported_win_rate:.2%}")
        
        # Check reputation score logic
        rep_score = stats.get('reputation_score', 0)
        if total < 5 and rep_score > 30:
            print(f"  ⚠️  Reputation score seems high for only {total} signals")
        
        if stats.get('win_rate', 0) == 0 and stats.get('average_roi', 0) == 1.0:
            print(f"  ⚠️  No wins and 1.0x ROI suggests incomplete data")
    
    return True

def verify_data_consistency(outcomes_data, channels_data):
    """Cross-verify data consistency between files."""
    print("\n=== DATA CONSISTENCY VERIFICATION ===")
    
    # Count signals per channel in outcomes
    channel_signal_counts = {}
    for signal in outcomes_data.values():
        channel = signal.get('channel_name', 'Unknown')
        channel_signal_counts[channel] = channel_signal_counts.get(channel, 0) + 1
    
    # Compare with channel reputation data
    for channel, count in channel_signal_counts.items():
        if channel in channels_data:
            reported_count = channels_data[channel].get('total_signals', 0)
            if count != reported_count:
                print(f"⚠️  {channel}: {count} signals in outcomes vs {reported_count} in reputation")
            else:
                print(f"✓ {channel}: {count} signals match")
        else:
            print(f"⚠️  {channel}: Found in outcomes but not in reputation data")
    
    return True

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("CHANNEL REPUTATION SYSTEM VERIFICATION")
    print("=" * 60)
    
    # Load data files
    base_path = Path(__file__).parent.parent / "data" / "reputation"
    
    outcomes_data = load_json(base_path / "signal_outcomes.json")
    channels_data = load_json(base_path / "channels.json")
    
    if not outcomes_data or not channels_data:
        print("\n❌ VERIFICATION FAILED: Missing data files")
        sys.exit(1)
    
    # Run verification checks
    checks = [
        verify_signal_outcomes(outcomes_data),
        verify_channel_reputation(channels_data),
        verify_data_consistency(outcomes_data, channels_data)
    ]
    
    # Summary
    print("\n" + "=" * 60)
    if all(checks):
        print("✓ VERIFICATION PASSED")
        print("\nRECOMMENDATION: System structure is correct but data appears")
        print("to be test/placeholder data. Consider cleaning database.")
    else:
        print("❌ VERIFICATION FAILED")
        print("\nISSUES FOUND: Review warnings above")
    print("=" * 60)
    
    return 0 if all(checks) else 1

if __name__ == "__main__":
    sys.exit(main())

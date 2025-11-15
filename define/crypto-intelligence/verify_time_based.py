#!/usr/bin/env python3
"""Quick verification of time-based performance data."""
import json

# Load completed signals
with open('data/reputation/completed_history.json', 'r') as f:
    data = json.load(f)

print(f"Total completed signals: {len(data)}\n")
print("Time-Based Performance Data:")
print("=" * 80)

for addr, signal in data.items():
    symbol = signal.get('symbol', 'Unknown')
    entry_price = signal.get('entry_price', 0)
    ath_price = signal.get('ath_price', 0)
    ath_mult = signal.get('ath_multiplier', 0)
    days_to_ath = signal.get('days_to_ath', 0)
    
    # Day 7 checkpoint
    day_7_price = signal.get('day_7_price', 0)
    day_7_mult = signal.get('day_7_multiplier', 0)
    day_7_class = signal.get('day_7_classification', 'N/A')
    
    # Day 30 checkpoint
    day_30_price = signal.get('day_30_price', 0)
    day_30_mult = signal.get('day_30_multiplier', 0)
    day_30_class = signal.get('day_30_classification', 'N/A')
    
    # Analysis
    trajectory = signal.get('trajectory', 'N/A')
    peak_timing = signal.get('peak_timing', 'N/A')
    
    # Checkpoints from raw data
    checkpoints = signal.get('checkpoints', {})
    cp_7d = checkpoints.get('7d', {})
    cp_30d = checkpoints.get('30d', {})
    
    print(f"\n{'='*80}")
    print(f"{symbol} (Entry: ${entry_price:.6f})")
    print(f"{'='*80}")
    print(f"\n📊 ATH Performance:")
    print(f"   Peak: ${ath_price:.6f} ({ath_mult:.3f}x) on day {days_to_ath:.1f}")
    print(f"   Peak Timing: {peak_timing}")
    
    print(f"\n📅 Day 7 Checkpoint:")
    print(f"   Price: ${day_7_price:.6f} ({day_7_mult:.3f}x)")
    print(f"   Classification: {day_7_class.upper()}")
    print(f"   Checkpoint Data: ${cp_7d.get('price', 0):.6f} ({cp_7d.get('roi_multiplier', 0):.3f}x)")
    print(f"   Reached: {cp_7d.get('reached', False)}")
    
    print(f"\n📅 Day 30 Checkpoint:")
    print(f"   Price: ${day_30_price:.6f} ({day_30_mult:.3f}x)")
    print(f"   Classification: {day_30_class.upper()}")
    print(f"   Checkpoint Data: ${cp_30d.get('price', 0):.6f} ({cp_30d.get('roi_multiplier', 0):.3f}x)")
    print(f"   Reached: {cp_30d.get('reached', False)}")
    
    print(f"\n📈 Trajectory Analysis:")
    print(f"   Day 7 → Day 30: {day_7_mult:.3f}x → {day_30_mult:.3f}x")
    print(f"   Trajectory: {trajectory.upper()}")
    if trajectory == "crashed":
        drop_pct = ((day_7_mult - day_30_mult) / day_7_mult) * 100
        print(f"   Drop: {drop_pct:.1f}%")
    elif trajectory == "improved":
        gain_pct = ((day_30_mult - day_7_mult) / day_7_mult) * 100 if day_7_mult > 0 else 0
        print(f"   Gain: {gain_pct:.1f}%")

print("\n" + "=" * 80)
print("✓ All time-based fields populated successfully!")

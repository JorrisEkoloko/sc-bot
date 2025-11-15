"""Show peak timing analysis for all completed signals."""
import json
from datetime import datetime

# Load completed signals
with open('data/reputation/completed_history.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("PEAK TIMING ANALYSIS")
print("=" * 80)
print()

for address, signal in data.items():
    symbol = signal.get('symbol', address[:10])
    entry_date = signal['entry_timestamp'][:10]
    ath_date = signal['ath_timestamp'][:10] if signal.get('ath_timestamp') else 'N/A'
    days_to_ath = signal.get('days_to_ath', 0)
    peak_timing = signal.get('peak_timing', 'unknown')
    ath_mult = signal.get('ath_multiplier', 0)
    day_7_mult = signal.get('day_7_multiplier', 0)
    day_30_mult = signal.get('day_30_multiplier', 0)
    trajectory = signal.get('trajectory', 'unknown')
    
    print(f"{symbol:10} | Entry: {entry_date} | ATH: {ath_date} (day {days_to_ath:.1f})")
    print(f"           | Peak: {peak_timing:12} | ATH: {ath_mult:.2f}x")
    print(f"           | Day 7: {day_7_mult:.2f}x | Day 30: {day_30_mult:.2f}x | Trajectory: {trajectory}")
    print()

print("=" * 80)

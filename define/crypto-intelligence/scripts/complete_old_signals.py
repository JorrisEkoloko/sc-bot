"""
Complete old signals that have passed their 30-day tracking period.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

# Load signal outcomes
outcomes_file = Path("data/reputation/signal_outcomes.json")
with open(outcomes_file, 'r') as f:
    outcomes = json.load(f)

print(f"Loaded {len(outcomes)} signals")
print()

# Check each signal
completed_count = 0
for address, signal in outcomes.items():
    if signal['is_complete']:
        continue
    
    # Parse entry timestamp
    entry_time = datetime.fromisoformat(signal['entry_timestamp'])
    days_since_entry = (datetime.now(entry_time.tzinfo) - entry_time).days
    
    print(f"{signal['symbol']} ({address[:10]}...)")
    print(f"  Entry: {signal['entry_timestamp'][:10]}")
    print(f"  Days since entry: {days_since_entry}")
    
    # If more than 30 days have passed, mark as complete
    if days_since_entry >= 30:
        signal['is_complete'] = True
        signal['status'] = 'completed'
        signal['completion_reason'] = '30_days_elapsed'
        
        # Determine if winner or loser based on ATH
        if signal['ath_multiplier'] >= 2.0:
            signal['is_winner'] = True
            signal['outcome_category'] = 'winner'
        else:
            signal['is_winner'] = False
            signal['outcome_category'] = 'loser'
        
        completed_count += 1
        print(f"  ✓ Marked as complete: {signal['outcome_category']} (ATH: {signal['ath_multiplier']:.2f}x)")
    else:
        print(f"  Still in progress (need {30 - days_since_entry} more days)")
    
    print()

# Save updated outcomes
if completed_count > 0:
    with open(outcomes_file, 'w') as f:
        json.dump(outcomes, f, indent=2)
    print(f"✓ Completed {completed_count} signals and saved to {outcomes_file}")
else:
    print("No signals to complete")

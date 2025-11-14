"""Verify the current state of the reputation system."""
import json
from pathlib import Path

# Load data
signals_file = Path("data/reputation/signal_outcomes.json")
channels_file = Path("data/reputation/channels.json")

with open(signals_file) as f:
    signals = json.load(f)

with open(channels_file) as f:
    channels = json.load(f)

print("=== REPUTATION SYSTEM STATE ===\n")

# Analyze signals
print(f"Total signals tracked: {len(signals)}")
completed = [s for s in signals.values() if s['is_complete']]
print(f"Completed signals: {len(completed)}")
winners = [s for s in completed if s['is_winner']]
print(f"Winners: {len(winners)}")

print("\n=== SIGNAL DETAILS ===")
for addr, signal in signals.items():
    print(f"\n{signal['symbol']} ({addr[:8]}...)")
    print(f"  Entry: ${signal['entry_price']:.8f}")
    print(f"  ATH: ${signal['ath_price']:.8f} ({signal['ath_multiplier']:.2f}x)")
    print(f"  Days to ATH: {signal['days_to_ath']:.2f}")
    print(f"  Status: {signal['status']}")
    print(f"  Winner: {signal['is_winner']}")
    print(f"  Category: {signal['outcome_category']}")

print("\n=== CHANNEL REPUTATION ===")
for channel_name, channel in channels.items():
    print(f"\n{channel_name}:")
    print(f"  Reputation Score: {channel['reputation_score']}/100")
    print(f"  Tier: {channel['reputation_tier']}")
    print(f"  Win Rate: {channel['win_rate']*100:.1f}%")
    print(f"  Average ROI: {channel['average_roi']:.3f}x")
    print(f"  Sharpe Ratio: {channel['sharpe_ratio']:.2f}")
    print(f"  Speed Score: {channel['speed_score']}")

print("\n=== DIAGNOSIS ===")
print("Problem: All signals show 1.0x ROI (break even)")
print("Likely cause: Historical scraper used same price for entry and ATH")
print("Solution: Need real historical price data or clean database")

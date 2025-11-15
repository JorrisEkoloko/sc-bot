"""Display detailed PERFORMANCE data with prices and classifications."""
import json
from pathlib import Path

def show_detailed_performance():
    """Display detailed performance data for each signal."""
    
    # Load completed signals
    data_file = Path("data/reputation/completed_history.json")
    if not data_file.exists():
        print("No completed signals found")
        return
    
    with open(data_file) as f:
        signals = json.load(f)
    
    print("\n" + "="*100)
    print("DETAILED PERFORMANCE OUTPUT - Time-Based Classification")
    print("="*100)
    
    for idx, (address, signal) in enumerate(list(signals.items())[:5], 1):  # Show first 5
        symbol = signal.get('symbol', 'UNKNOWN')
        entry_price = signal.get('entry_price', 0)
        
        print(f"\n{idx}. {symbol} ({address[:10]}...)")
        print("-" * 100)
        
        # Entry
        print(f"   Entry: ${entry_price:.6f}")
        
        # ATH
        ath_price = signal.get('ath_price', 0)
        ath_mult = signal.get('ath_multiplier', 0)
        days_to_ath = signal.get('days_to_ath', 0)
        peak_timing = signal.get('peak_timing', 'unknown')
        print(f"   ATH:   ${ath_price:.6f} ({ath_mult:.2f}x) on day {days_to_ath:.1f} [{peak_timing}]")
        
        # Day 7
        day_7_price = signal.get('day_7_price', 0)
        day_7_mult = signal.get('day_7_multiplier', 0)
        day_7_class = signal.get('day_7_classification', 'N/A')
        print(f"   Day 7: ${day_7_price:.6f} ({day_7_mult:.2f}x) - Classification: {day_7_class.upper()}")
        
        # Day 30
        day_30_price = signal.get('day_30_price', 0)
        day_30_mult = signal.get('day_30_multiplier', 0)
        day_30_class = signal.get('day_30_classification', 'N/A')
        trajectory = signal.get('trajectory', 'N/A')
        print(f"   Day 30: ${day_30_price:.6f} ({day_30_mult:.2f}x) - Classification: {day_30_class.upper()}")
        
        # Trajectory
        if trajectory == 'crashed':
            # Calculate drop percentage
            if ath_mult > day_30_mult:
                drop_pct = ((ath_mult - day_30_mult) / ath_mult) * 100
                print(f"   Trajectory: 🔴 CRASHED ({drop_pct:.1f}% drop from ATH)")
            else:
                print(f"   Trajectory: 🔴 CRASHED")
        else:
            print(f"   Trajectory: 🟢 IMPROVED")
        
        # Trading insight
        print(f"\n   💡 Insight:")
        if peak_timing == 'early_peaker':
            print(f"      - Peaked early (day {days_to_ath:.1f})")
            if trajectory == 'crashed':
                print(f"      - Should have exited at day 7 ({day_7_mult:.2f}x) instead of holding to day 30 ({day_30_mult:.2f}x)")
        else:
            print(f"      - Peaked late (day {days_to_ath:.1f})")
            if trajectory == 'crashed':
                print(f"      - Holding past day 7 was correct, but crashed after peak")
    
    print("\n" + "="*100)
    
    # Channel insights
    print("\n📊 Channel Pattern Analysis:")
    early_peakers = sum(1 for s in signals.values() if s.get('peak_timing') == 'early_peaker')
    late_peakers = sum(1 for s in signals.values() if s.get('peak_timing') == 'late_peaker')
    crashed = sum(1 for s in signals.values() if s.get('trajectory') == 'crashed')
    
    print(f"   - {early_peakers}/{len(signals)} signals peak within 7 days ({early_peakers/len(signals)*100:.1f}%)")
    print(f"   - {late_peakers}/{len(signals)} signals peak after day 7 ({late_peakers/len(signals)*100:.1f}%)")
    print(f"   - {crashed}/{len(signals)} signals crashed from peak ({crashed/len(signals)*100:.1f}%)")
    
    if early_peakers > late_peakers:
        print(f"\n   ⚠️  Recommendation: EXIT EARLY (1-7 days) for this channel")
        print(f"      Most signals peak within the first week, then crash.")
    else:
        print(f"\n   ✅ Recommendation: HOLD LONGER (7-30 days) for this channel")
        print(f"      Signals tend to peak after day 7.")
    
    print()

if __name__ == "__main__":
    show_detailed_performance()

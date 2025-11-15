"""Display PERFORMANCE table output with time-based columns."""
import json
from pathlib import Path

def show_performance_output():
    """Display completed signals with time-based performance data."""
    
    # Load completed signals
    data_file = Path("data/reputation/completed_history.json")
    if not data_file.exists():
        print("No completed signals found")
        return
    
    with open(data_file) as f:
        signals = json.load(f)
    
    print("\n" + "="*120)
    print("PERFORMANCE TABLE OUTPUT - Time-Based Classification")
    print("="*120)
    print(f"\nTotal Signals: {len(signals)}\n")
    
    # Table header
    header = f"{'Symbol':<10} {'ATH':<8} {'Days':<6} {'Peak':<12} {'Day 7':<8} {'D7 Class':<12} {'Day 30':<8} {'D30 Class':<12} {'Trajectory':<10}"
    print(header)
    print("-" * 120)
    
    # Display each signal
    for address, signal in list(signals.items())[:10]:  # Show first 10
        symbol = signal.get('symbol', 'UNKNOWN')[:10]
        ath = f"{signal.get('ath_multiplier', 0):.2f}x"
        days_to_ath = f"{signal.get('days_to_ath', 0):.1f}"
        peak_timing = signal.get('peak_timing', 'unknown')[:12]
        day_7_mult = f"{signal.get('day_7_multiplier', 0):.2f}x"
        day_7_class = signal.get('day_7_classification', 'N/A')[:12]
        day_30_mult = f"{signal.get('day_30_multiplier', 0):.2f}x"
        day_30_class = signal.get('day_30_classification', 'N/A')[:12]
        trajectory = signal.get('trajectory', 'N/A')[:10]
        
        row = f"{symbol:<10} {ath:<8} {days_to_ath:<6} {peak_timing:<12} {day_7_mult:<8} {day_7_class:<12} {day_30_mult:<8} {day_30_class:<12} {trajectory:<10}"
        print(row)
    
    print("\n" + "="*120)
    print("\nColumn Descriptions:")
    print("  ATH: All-time high multiplier (0-30 days)")
    print("  Days: Days from entry to ATH")
    print("  Peak: early_peaker (≤7 days) or late_peaker (>7 days)")
    print("  Day 7: ROI multiplier at day 7 checkpoint")
    print("  D7 Class: Classification based on ATH at day 7")
    print("  Day 30: ROI multiplier at day 30 checkpoint")
    print("  D30 Class: Final classification based on ATH")
    print("  Trajectory: improved (day 30 > day 7) or crashed (day 30 < day 7 or < ATH)")
    print("\n" + "="*120)
    
    # Summary statistics
    print("\nSummary Statistics:")
    early_peakers = sum(1 for s in signals.values() if s.get('peak_timing') == 'early_peaker')
    late_peakers = sum(1 for s in signals.values() if s.get('peak_timing') == 'late_peaker')
    crashed = sum(1 for s in signals.values() if s.get('trajectory') == 'crashed')
    improved = sum(1 for s in signals.values() if s.get('trajectory') == 'improved')
    
    print(f"  Early Peakers: {early_peakers}/{len(signals)} ({early_peakers/len(signals)*100:.1f}%)")
    print(f"  Late Peakers: {late_peakers}/{len(signals)} ({late_peakers/len(signals)*100:.1f}%)")
    print(f"  Crashed: {crashed}/{len(signals)} ({crashed/len(signals)*100:.1f}%)")
    print(f"  Improved: {improved}/{len(signals)} ({improved/len(signals)*100:.1f}%)")
    print()

if __name__ == "__main__":
    show_performance_output()

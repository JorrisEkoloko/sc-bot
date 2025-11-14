"""
Visual comparison showing the improvement from the ambiguous ticker fix.
"""

from services.message_processing.crypto_detector import CryptoDetector


def show_comparison():
    """Show before/after comparison for problematic messages."""
    detector = CryptoDetector()
    
    print("\n" + "="*80)
    print("BEFORE vs AFTER: Ambiguous Ticker Detection Fix")
    print("="*80)
    
    test_messages = [
        {
            "id": "3349",
            "text": "the $METIS token is going crazy. It's very likely one of the best places to make money",
            "before": ["METIS", "ONE"],
            "after": ["METIS"]
        },
        {
            "id": "3344",
            "text": "This is one of the most undervalued Alts imo. Potential 100x.",
            "before": ["ONE"],
            "after": []
        },
        {
            "id": "3325",
            "text": "$ROSE as one of his top 3 picks. In the mid term I see this out performing $ETH and $SOL",
            "before": ["ROSE", "ONE", "ETH", "SOL"],
            "after": ["ROSE", "ETH", "SOL"]
        },
        {
            "id": "3314",
            "text": "Once the Bitcoin one is inevitably approved, the ETH pumps will be outrageous",
            "before": ["ONE", "ETH"],
            "after": ["ETH"]
        },
        {
            "id": "NEW",
            "text": "Check out this link for more info on $LINK and $NEAR protocol",
            "before": ["LINK", "NEAR"],
            "after": ["LINK", "NEAR"]
        }
    ]
    
    for msg in test_messages:
        print(f"\n{'-'*80}")
        print(f"Message ID: {msg['id']}")
        print(f"Text: {msg['text'][:70]}...")
        print()
        
        actual = detector.detect_mentions(msg['text'])
        
        # Show before (simulated)
        print(f"❌ BEFORE (with false positives):")
        print(f"   Detected: {msg['before']}")
        
        # Show after (actual)
        print(f"✅ AFTER (fixed):")
        print(f"   Detected: {actual}")
        
        # Validation
        if actual == msg['after']:
            print(f"   Status: ✓ CORRECT")
        else:
            print(f"   Status: ✗ MISMATCH (expected {msg['after']})")
        
        # Highlight improvements
        false_positives_removed = [t for t in msg['before'] if t not in msg['after']]
        if false_positives_removed:
            print(f"   Improvement: Removed false positives: {false_positives_removed}")
    
    print(f"\n{'='*80}")
    print("Summary:")
    print("- Common English words (one, link, near, etc.) no longer cause false positives")
    print("- Ambiguous tickers require $ or # prefix for detection")
    print("- Non-ambiguous tickers (BTC, ETH, SOL) work with or without prefix")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    show_comparison()

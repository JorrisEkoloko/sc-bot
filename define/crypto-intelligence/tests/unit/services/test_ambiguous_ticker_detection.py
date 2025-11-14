"""
Test ambiguous ticker detection with prefix requirement.

Tests that common English words like "ONE" are not detected as tickers
unless they have a $ or # prefix.
"""

from services.message_processing.crypto_detector import CryptoDetector


def test_ambiguous_ticker_detection():
    """Test that ambiguous tickers require prefix."""
    detector = CryptoDetector()
    
    print("\n" + "="*80)
    print("AMBIGUOUS TICKER DETECTION TEST")
    print("="*80)
    
    # Test cases
    test_cases = [
        {
            "text": "Incase you've been living under a rock the $METIS token & ecosystem is going crazy and I have strong reason to believe it's just getting started. If you have small capital (sub 10k) it's very likely one of the best places to make money on",
            "expected": ["METIS"],
            "should_not_contain": ["ONE"],
            "description": "Message with 'one of the best' - should NOT detect ONE"
        },
        {
            "text": "$ONE is pumping hard today! Harmony network is on fire.",
            "expected": ["ONE"],
            "should_not_contain": [],
            "description": "Message with $ONE prefix - SHOULD detect ONE"
        },
        {
            "text": "#ONE to the moon! 🚀",
            "expected": ["ONE"],
            "should_not_contain": [],
            "description": "Message with #ONE hashtag - SHOULD detect ONE"
        },
        {
            "text": "This one looks promising. Near future we'll see gains.",
            "expected": [],
            "should_not_contain": ["ONE", "NEAR"],
            "description": "Common English usage - should NOT detect ONE or NEAR"
        },
        {
            "text": "$NEAR Protocol is one of the best L1 chains",
            "expected": ["NEAR"],
            "should_not_contain": ["ONE"],
            "description": "Mixed: $NEAR should be detected, 'one of' should not"
        },
        {
            "text": "BTC ETH SOL are the top 3",
            "expected": ["BTC", "ETH", "SOL"],
            "should_not_contain": [],
            "description": "Non-ambiguous tickers without prefix - should detect all"
        },
        {
            "text": "Check out this link for more info",
            "expected": [],
            "should_not_contain": ["LINK"],
            "description": "Word 'link' in sentence - should NOT detect LINK"
        },
        {
            "text": "$LINK is breaking out! Chainlink oracles are essential.",
            "expected": ["LINK"],
            "should_not_contain": [],
            "description": "$LINK with prefix - SHOULD detect LINK"
        },
        {
            "text": "I bought some cake at the store",
            "expected": [],
            "should_not_contain": ["CAKE"],
            "description": "Word 'cake' in sentence - should NOT detect CAKE"
        },
        {
            "text": "$CAKE farming on PancakeSwap is profitable",
            "expected": ["CAKE"],
            "should_not_contain": [],
            "description": "$CAKE with prefix - SHOULD detect CAKE"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*80}")
        print(f"Test {i}: {test['description']}")
        print(f"Text: {test['text'][:100]}...")
        
        mentions = detector.detect_mentions(test['text'])
        
        print(f"Detected: {mentions}")
        print(f"Expected: {test['expected']}")
        
        # Check expected mentions are present
        expected_found = all(exp in mentions for exp in test['expected'])
        
        # Check unwanted mentions are NOT present
        unwanted_not_found = all(unwanted not in mentions for unwanted in test['should_not_contain'])
        
        if expected_found and unwanted_not_found:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            if not expected_found:
                missing = [exp for exp in test['expected'] if exp not in mentions]
                print(f"  Missing expected: {missing}")
            if not unwanted_not_found:
                unwanted = [u for u in test['should_not_contain'] if u in mentions]
                print(f"  Incorrectly detected: {unwanted}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'='*80}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = test_ambiguous_ticker_detection()
    exit(0 if success else 1)

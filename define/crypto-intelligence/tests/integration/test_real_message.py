"""
Test with the actual message from the CSV that had the false positive.
"""

from services.message_processing.crypto_detector import CryptoDetector


def test_real_message():
    """Test with the actual problematic message."""
    detector = CryptoDetector()
    
    # The actual message from message ID 3349
    message_text = """Incase you've been living under a rock  the $METIS token & ecosystem is going crazy and I have strong reason to believe it's just getting started.

If you have small capital (sub 10k) it's very likely one of the best places to make money on, the fees are non existent and the chain is genuinely one of the smoothest to use and there isn't much saturation (currently like 10 worthwhile projects, many more in the pipeline)

I wanted to write a long paragraph/thread on my thesis prior to things going """
    
    print("\n" + "="*80)
    print("REAL MESSAGE TEST - Message ID 3349")
    print("="*80)
    print(f"\nMessage text:\n{message_text[:200]}...\n")
    
    mentions = detector.detect_mentions(message_text)
    
    print(f"Detected mentions: {mentions}")
    print(f"\nExpected: ['METIS']")
    print(f"Should NOT contain: ['ONE']")
    
    if mentions == ['METIS']:
        print("\n✓ SUCCESS: Correctly detected only METIS, ignored 'one of the best'")
        return True
    else:
        print(f"\n✗ FAILED: Got {mentions} instead of ['METIS']")
        return False


if __name__ == "__main__":
    success = test_real_message()
    exit(0 if success else 1)

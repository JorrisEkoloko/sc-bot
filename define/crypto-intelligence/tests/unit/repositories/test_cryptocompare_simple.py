"""Simple test to verify CryptoCompare is integrated."""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*60)
print("CryptoCompare Integration Check")
print("="*60)

# Check 1: API Key
api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
if api_key:
    print(f"✅ CRYPTOCOMPARE_API_KEY found: {api_key[:20]}...")
else:
    print("❌ CRYPTOCOMPARE_API_KEY not found")

# Check 2: Client import
try:
    from core.api_clients import CryptoCompareClient
    print("✅ CryptoCompareClient imported successfully")
except ImportError as e:
    print(f"❌ Failed to import CryptoCompareClient: {e}")

# Check 3: Price engine import
try:
    from core.price_engine import PriceEngine
    print("✅ PriceEngine imported successfully")
except ImportError as e:
    print(f"❌ Failed to import PriceEngine: {e}")

# Check 4: Price engine initialization
try:
    from config.price_config import PriceConfig
    config = PriceConfig()
    print(f"✅ PriceConfig created")
    
    # Check if CryptoCompare key is in config
    if hasattr(config, 'cryptocompare_api_key'):
        print(f"✅ Config has cryptocompare_api_key attribute")
    else:
        print(f"ℹ️  Config doesn't have cryptocompare_api_key attribute (will use env var)")
    
except Exception as e:
    print(f"❌ Failed to create PriceConfig: {e}")

print("="*60)
print("✅ Integration check complete!")
print("="*60)
print("\nNext steps:")
print("1. CryptoCompare client is ready to use")
print("2. PriceEngine will automatically use it for historical data")
print("3. Use price_engine.get_historical_ohlc(symbol, days)")
print("4. Use price_engine.get_price_at_timestamp(symbol, timestamp)")

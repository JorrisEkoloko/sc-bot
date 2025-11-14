#!/usr/bin/env python3
"""
Check OPTIMUS token symbol on CryptoCompare
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# OPTIMUS contract address
optimus_address = "0x562E36288a9Dd867d5d8b0Aa48c2E8d2d215d5d"

# Get CryptoCompare API key
api_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')

if not api_key:
    print("ERROR: No CRYPTOCOMPARE_API_KEY found in .env")
    exit(1)

print(f"Checking OPTIMUS token on CryptoCompare...")
print(f"Contract Address: {optimus_address}")
print()

# Try to search for the token by address
# CryptoCompare doesn't have a direct address lookup, so let's try searching by symbol
symbols_to_try = ['OPTIMUS', 'OPTI', 'OPT', 'OPTIMUSAI']

for symbol in symbols_to_try:
    print(f"\n{'='*60}")
    print(f"Trying symbol: {symbol}")
    print('='*60)
    
    # Try to get current price
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms=USD"
    headers = {'authorization': f'Apikey {api_key}'}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if 'USD' in data and data['USD'] > 0:
            print(f"✓ Found! Symbol '{symbol}' has price: ${data['USD']}")
        else:
            print(f"✗ Symbol '{symbol}' returned: {data}")
    else:
        print(f"✗ Failed to fetch data for '{symbol}'")

print("\n" + "="*60)
print("CHECKING HISTORICAL DATA")
print("="*60)

# Try historical data for each symbol
for symbol in symbols_to_try:
    print(f"\nTrying historical data for: {symbol}")
    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym=USD&limit=1"
    headers = {'authorization': f'Apikey {api_key}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get('Response') == 'Success':
            print(f"✓ Historical data available for '{symbol}'")
            if 'Data' in data and 'Data' in data['Data']:
                candles = data['Data']['Data']
                if candles:
                    print(f"  Latest price: ${candles[-1].get('close', 0)}")
        else:
            print(f"✗ No historical data for '{symbol}': {data.get('Message', 'Unknown error')}")

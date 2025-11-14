#!/usr/bin/env python3
"""
Wrapper script to run historical scraper with proper working directory
"""
import sys
import os
from pathlib import Path

# Change to the crypto-intelligence directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Now run the historical scraper
from scripts.historical_scraper import main
import asyncio

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

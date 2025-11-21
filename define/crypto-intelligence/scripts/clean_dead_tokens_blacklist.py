#!/usr/bin/env python3
"""
Clean up the dead tokens blacklist.

This script removes all entries from the dead tokens blacklist to start fresh.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def clean_dead_tokens_blacklist():
    """Clean the dead tokens blacklist file."""
    
    # Get the script directory and navigate to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    blacklist_path = project_root / "data" / "dead_tokens_blacklist.json"
    
    if not blacklist_path.exists():
        print("❌ Dead tokens blacklist file not found")
        return
    
    # Load current blacklist
    with open(blacklist_path, 'r') as f:
        blacklist = json.load(f)
    
    token_count = len(blacklist)
    
    print(f"📊 Current blacklist contains {token_count} dead tokens")
    
    # Create backup
    backup_path = project_root / "data" / f".backup_dead_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_path, 'w') as f:
        json.dump(blacklist, f, indent=2)
    
    print(f"💾 Backup created: {backup_path}")
    
    # Clear the blacklist
    empty_blacklist = {}
    
    with open(blacklist_path, 'w') as f:
        json.dump(empty_blacklist, f, indent=2)
    
    print(f"✅ Cleaned dead tokens blacklist")
    print(f"   Removed: {token_count} tokens")
    print(f"   New count: 0 tokens")
    print(f"\n🔄 Restart the system to apply changes")

if __name__ == "__main__":
    print("="*70)
    print("Dead Tokens Blacklist Cleanup")
    print("="*70)
    print()
    
    clean_dead_tokens_blacklist()
    
    print()
    print("="*70)

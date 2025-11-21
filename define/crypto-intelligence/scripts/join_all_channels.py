"""
Join all configured Telegram channels and verify access.

This script:
1. Authenticates with Telegram
2. Attempts to join all channels from config
3. Verifies access to each channel
4. Reports which channels are accessible
"""
import asyncio
import json
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError, 
    UsernameInvalidError,
    FloodWaitError,
    InviteHashExpiredError
)
from dotenv import load_dotenv
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Telegram credentials
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')


async def join_channel(client, channel_username):
    """
    Attempt to join a channel and verify access.
    
    Returns:
        dict with status and info
    """
    try:
        # Get channel entity
        channel = await client.get_entity(channel_username)
        
        # Try to join (if not already joined)
        try:
            await client(JoinChannelRequest(channel))
            status = "joined"
        except Exception as e:
            # Already joined or public channel
            status = "already_member"
        
        # Verify we can access messages
        messages = await client.get_messages(channel, limit=1)
        
        return {
            'username': channel_username,
            'title': channel.title,
            'id': channel.id,
            'subscribers': getattr(channel, 'participants_count', 0),
            'status': status,
            'accessible': True,
            'has_messages': len(messages) > 0,
            'error': None
        }
        
    except ChannelPrivateError:
        return {
            'username': channel_username,
            'status': 'private',
            'accessible': False,
            'error': 'Channel is private - need invite link'
        }
    except UsernameInvalidError:
        return {
            'username': channel_username,
            'status': 'invalid',
            'accessible': False,
            'error': 'Invalid username'
        }
    except FloodWaitError as e:
        return {
            'username': channel_username,
            'status': 'rate_limited',
            'accessible': False,
            'error': f'Rate limited - wait {e.seconds} seconds'
        }
    except Exception as e:
        return {
            'username': channel_username,
            'status': 'error',
            'accessible': False,
            'error': str(e)
        }


async def main():
    """Main function."""
    print("="*80)
    print("TELEGRAM CHANNEL JOINER & VERIFIER")
    print("="*80)
    print()
    
    # Load channels from config
    config_path = Path('config/channels.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    channels = [ch['id'] for ch in config['channels'] if ch.get('enabled', True)]
    
    print(f"📋 Found {len(channels)} channels to join/verify")
    print()
    
    # Initialize Telegram client (use same session as main.py)
    print("🔐 Authenticating with Telegram...")
    session_path = 'credentials/crypto_scraper_session'
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    me = await client.get_me()
    print(f"✅ Authenticated as: {me.first_name} {me.last_name or ''}")
    print(f"   Phone: {me.phone}")
    print()
    
    # Import JoinChannelRequest
    from telethon.tl.functions.channels import JoinChannelRequest
    
    # Process each channel
    results = []
    
    for i, channel_username in enumerate(channels, 1):
        print(f"[{i}/{len(channels)}] Processing {channel_username}...")
        
        result = await join_channel(client, channel_username)
        results.append(result)
        
        if result['accessible']:
            print(f"   ✅ {result.get('title', 'Unknown')}")
            print(f"      Status: {result['status']}")
            subs = result.get('subscribers', 0) or 0
            print(f"      Subscribers: {subs:,}")
            print(f"      Has messages: {result.get('has_messages', False)}")
        else:
            print(f"   ❌ {result['error']}")
        
        print()
        
        # Small delay to avoid rate limits
        await asyncio.sleep(2)
    
    await client.disconnect()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    accessible = [r for r in results if r['accessible']]
    not_accessible = [r for r in results if not r['accessible']]
    
    print(f"✅ Accessible: {len(accessible)}/{len(results)} channels")
    print(f"❌ Not accessible: {len(not_accessible)}/{len(results)} channels")
    print()
    
    if accessible:
        print("✅ ACCESSIBLE CHANNELS:")
        for r in accessible:
            subs = r.get('subscribers', 0) or 0
            print(f"   - {r['username']}: {r.get('title', 'Unknown')} ({subs:,} subscribers)")
        print()
    
    if not_accessible:
        print("❌ NOT ACCESSIBLE CHANNELS:")
        for r in not_accessible:
            print(f"   - {r['username']}: {r['error']}")
        print()
    
    # Save results
    report_path = Path('data/channel_access_report.json')
    report = {
        'checked_at': asyncio.get_event_loop().time(),
        'total_channels': len(results),
        'accessible': len(accessible),
        'not_accessible': len(not_accessible),
        'channels': results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"💾 Report saved to: {report_path}")
    print()
    
    if len(accessible) == len(results):
        print("🎉 SUCCESS! All channels are accessible")
        print("   You can now run main.py for full historical scraping")
    else:
        print("⚠️  Some channels are not accessible")
        print("   Fix the issues above, then run this script again")
    
    print()
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())

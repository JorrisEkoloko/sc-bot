"""
Find active, legitimate crypto signal channels for production scraping.

This script helps identify quality crypto channels with:
- Active posting (recent messages)
- Variety of content (not just meme coins)
- Legitimate signals (verifiable addresses)
- Good engagement metrics
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import ChannelPrivateError, UsernameInvalidError
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Telegram credentials
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')


# Curated list of known crypto signal channels (diverse categories)
CANDIDATE_CHANNELS = [
    # Large Cap / General Crypto
    "@CryptoWhaleIO",
    "@CryptoSignalsAdvice",
    "@CryptoVIPSignal",
    "@binancesignals",
    "@CryptoInnerCircle",
    
    # DeFi Focused
    "@DeFiSignals",
    "@YieldFarmingSignals",
    "@DeFiAlpha",
    
    # NFT & Gaming
    "@NFTSignals",
    "@GameFiAlerts",
    "@NFTAlphaGroup",
    
    # On-Chain Analysis
    "@OnChainCollege",
    "@WhaleAlerts",
    "@CryptoQuant",
    
    # Multi-Chain
    "@SolanaSignals",
    "@AvalancheSignals",
    "@PolygonSignals",
    "@BSCSignals",
    
    # Altcoin Gems (Variety)
    "@AltcoinGordon",
    "@CryptoGemHunters",
    "@AltcoinDaily",
    "@CryptoGems",
    
    # Technical Analysis
    "@CryptoTASignals",
    "@TradingViewSignals",
    "@ChartChampions",
    
    # ICO/IDO Launches
    "@ICODrops",
    "@IDOCalendar",
    "@LaunchpadSignals",
    
    # Existing (for comparison)
    "@erics_calls",
]


async def analyze_channel(client, channel_username):
    """Analyze a single channel for quality metrics."""
    try:
        # Get channel entity
        channel = await client.get_entity(channel_username)
        
        # Get recent messages (last 100)
        messages = await client(GetHistoryRequest(
            peer=channel,
            limit=100,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        if not messages.messages:
            return None
        
        # Analyze messages
        total_messages = len(messages.messages)
        recent_24h = 0
        recent_7d = 0
        has_addresses = 0
        has_links = 0
        avg_length = 0
        
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        for msg in messages.messages:
            if not msg.message:
                continue
            
            msg_date = msg.date.replace(tzinfo=None)
            
            # Count recent messages
            if msg_date > day_ago:
                recent_24h += 1
            if msg_date > week_ago:
                recent_7d += 1
            
            # Check for crypto addresses (0x... or base58)
            text = msg.message.lower()
            if '0x' in text or any(len(word) > 30 and word.isalnum() for word in text.split()):
                has_addresses += 1
            
            # Check for links
            if 'http' in text or 't.me' in text:
                has_links += 1
            
            avg_length += len(msg.message)
        
        avg_length = avg_length / total_messages if total_messages > 0 else 0
        
        # Calculate quality score
        activity_score = min(recent_7d / 7, 10)  # Up to 10 points for daily posts
        address_score = min((has_addresses / total_messages) * 20, 20)  # Up to 20 points
        content_score = min(avg_length / 50, 10)  # Up to 10 points for substantial content
        
        quality_score = activity_score + address_score + content_score
        
        # Determine category based on content
        category = "Unknown"
        sample_text = " ".join([m.message.lower() for m in messages.messages[:20] if m.message])
        
        if any(word in sample_text for word in ['defi', 'yield', 'farming', 'liquidity']):
            category = "DeFi"
        elif any(word in sample_text for word in ['nft', 'gaming', 'metaverse']):
            category = "NFT/Gaming"
        elif any(word in sample_text for word in ['btc', 'eth', 'bitcoin', 'ethereum', 'large cap']):
            category = "Large Cap"
        elif any(word in sample_text for word in ['solana', 'sol', 'avalanche', 'avax', 'polygon', 'matic']):
            category = "Multi-Chain"
        elif any(word in sample_text for word in ['gem', 'altcoin', 'low cap', 'micro cap']):
            category = "Altcoin Gems"
        elif any(word in sample_text for word in ['ico', 'ido', 'launch', 'presale']):
            category = "ICO/IDO"
        elif any(word in sample_text for word in ['chart', 'technical', 'ta', 'resistance', 'support']):
            category = "Technical Analysis"
        
        return {
            'username': channel_username,
            'title': channel.title,
            'subscribers': getattr(channel, 'participants_count', 0),
            'category': category,
            'metrics': {
                'total_messages_analyzed': total_messages,
                'messages_24h': recent_24h,
                'messages_7d': recent_7d,
                'messages_with_addresses': has_addresses,
                'messages_with_links': has_links,
                'avg_message_length': round(avg_length, 1),
                'address_percentage': round((has_addresses / total_messages) * 100, 1) if total_messages > 0 else 0
            },
            'quality_score': round(quality_score, 2),
            'recommendation': 'Excellent' if quality_score >= 30 else 'Good' if quality_score >= 20 else 'Fair' if quality_score >= 10 else 'Poor',
            'analyzed_at': datetime.now().isoformat()
        }
        
    except ChannelPrivateError:
        print(f"❌ {channel_username}: Private channel (need to join first)")
        return None
    except UsernameInvalidError:
        print(f"❌ {channel_username}: Invalid username")
        return None
    except Exception as e:
        print(f"❌ {channel_username}: Error - {e}")
        return None


async def main():
    """Main function."""
    print("="*80)
    print("CRYPTO CHANNEL FINDER - Active & Legitimate Channels")
    print("="*80)
    print()
    
    # Initialize Telegram client
    client = TelegramClient('channel_finder_session', API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    print(f"✅ Connected to Telegram")
    print(f"📊 Analyzing {len(CANDIDATE_CHANNELS)} channels...")
    print()
    
    results = []
    
    for i, channel in enumerate(CANDIDATE_CHANNELS, 1):
        print(f"[{i}/{len(CANDIDATE_CHANNELS)}] Analyzing {channel}...")
        result = await analyze_channel(client, channel)
        
        if result:
            results.append(result)
            print(f"   ✅ {result['title']}")
            print(f"      Category: {result['category']}")
            print(f"      Quality Score: {result['quality_score']}/40 ({result['recommendation']})")
            print(f"      Activity: {result['metrics']['messages_7d']} msgs/week")
            print(f"      Addresses: {result['metrics']['address_percentage']}%")
        
        print()
        
        # Small delay to avoid rate limits
        await asyncio.sleep(2)
    
    await client.disconnect()
    
    # Sort by quality score
    results.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # Generate report
    print("="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print()
    
    # Group by category
    by_category = {}
    for result in results:
        cat = result['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(result)
    
    print("📊 CHANNELS BY CATEGORY:")
    print()
    for category, channels in sorted(by_category.items()):
        print(f"  {category}: {len(channels)} channels")
        for ch in sorted(channels, key=lambda x: x['quality_score'], reverse=True)[:3]:
            print(f"    - {ch['username']} (Score: {ch['quality_score']}, {ch['metrics']['messages_7d']} msgs/week)")
    
    print()
    print("🏆 TOP 10 RECOMMENDED CHANNELS:")
    print()
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['username']}")
        print(f"   Title: {result['title']}")
        print(f"   Category: {result['category']}")
        print(f"   Quality: {result['quality_score']}/40 ({result['recommendation']})")
        print(f"   Activity: {result['metrics']['messages_7d']} msgs/week, {result['metrics']['address_percentage']}% with addresses")
        print()
    
    # Save full report
    report_path = Path('data/channel_analysis_report.json')
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_analyzed': len(CANDIDATE_CHANNELS),
        'successful': len(results),
        'by_category': {cat: len(chs) for cat, chs in by_category.items()},
        'channels': results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Full report saved to: {report_path}")
    
    # Generate channels.json for production
    production_channels = []
    
    # Select diverse channels (top from each category)
    for category, channels in by_category.items():
        # Take top 2 from each category
        for ch in sorted(channels, key=lambda x: x['quality_score'], reverse=True)[:2]:
            if ch['quality_score'] >= 20:  # Only good quality
                production_channels.append({
                    'id': ch['username'],
                    'name': ch['title'],
                    'enabled': True,
                    'category': ch['category'],
                    'quality_score': ch['quality_score']
                })
    
    # Save production config
    prod_config_path = Path('config/channels_production_ready.json')
    prod_config = {
        'channels': production_channels,
        'generated_at': datetime.now().isoformat(),
        'note': 'Diverse, high-quality crypto signal channels for production scraping'
    }
    
    with open(prod_config_path, 'w') as f:
        json.dump(prod_config, f, indent=2)
    
    print(f"✅ Production config saved to: {prod_config_path}")
    print(f"   {len(production_channels)} channels selected for production")
    print()
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())

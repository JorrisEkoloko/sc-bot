"""
Analyze dead tokens with 30-day OHLC data to understand their actual ROI.

This script fetches historical price data for dead tokens to see if they
actually had any price movement before dying, or if they were dead from the start.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from utils.logger import setup_logger


async def analyze_dead_token(address: str, chain: str, detected_at: str, reason: str, retriever, logger):
    """
    Analyze a single dead token with 30-day OHLC data.
    
    Args:
        address: Token address
        chain: Blockchain (evm/solana)
        detected_at: When token was detected as dead
        reason: Why token is dead
        retriever: HistoricalPriceRetriever instance
        logger: Logger instance
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Analyzing: {address[:20]}...")
    logger.info(f"Chain: {chain}")
    logger.info(f"Detected: {detected_at}")
    logger.info(f"Reason: {reason}")
    logger.info(f"{'='*80}")
    
    # Parse detection date
    try:
        detected_date = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
    except:
        logger.warning(f"Could not parse date: {detected_at}, using today")
        detected_date = datetime.now()
    
    # Calculate 30 days before detection
    start_date = detected_date - timedelta(days=30)
    
    logger.info(f"Fetching OHLC data from {start_date.date()} to {detected_date.date()} (30 days)")
    
    # Try to get symbol first (for CryptoCompare)
    symbol = None
    try:
        # Try DexScreener to get symbol
        from repositories.api_clients.dexscreener_client import DexScreenerClient
        dex_client = DexScreenerClient()
        
        chain_map = {"evm": "ethereum", "solana": "solana"}
        mapped_chain = chain_map.get(chain, "ethereum")
        
        price_data = await dex_client.get_price(address, mapped_chain)
        if price_data and price_data.symbol:
            symbol = price_data.symbol
            logger.info(f"✅ Found symbol: {symbol}")
        await dex_client.close()
    except Exception as e:
        logger.warning(f"Could not get symbol from DexScreener: {e}")
    
    # Fetch OHLC data
    result = {
        'address': address,
        'chain': chain,
        'symbol': symbol or address[:10],
        'detected_at': detected_at,
        'reason': reason,
        'ohlc_data': None,
        'analysis': {}
    }
    
    try:
        # Try with symbol first if available
        if symbol:
            logger.info(f"Attempting OHLC APIs for {symbol}...")
            ohlc_data = await retriever.fetch_forward_ohlc_with_ath(
                symbol=symbol,
                entry_timestamp=start_date,
                window_days=30,
                address=address,
                chain=chain
            )
        else:
            # Try address-based lookup (DefiLlama, etc.)
            logger.info(f"No symbol found, trying address-based OHLC lookup for {address[:20]}...")
            ohlc_data = await retriever.fetch_forward_ohlc_with_ath(
                symbol=address[:10],  # Use truncated address as placeholder
                entry_timestamp=start_date,
                window_days=30,
                address=address,
                chain=chain
            )
            
            if ohlc_data and ohlc_data.get('candles'):
                candles = ohlc_data['candles']
                logger.info(f"✅ Got {len(candles)} candles from CryptoCompare")
                
                # Analyze the data
                if len(candles) > 0:
                    first_candle = candles[0]
                    last_candle = candles[-1]
                    ath_price = ohlc_data.get('ath_price', 0)
                    ath_day = ohlc_data.get('days_to_ath', 0)
                    
                    entry_price = first_candle.close
                    final_price = last_candle.close
                    
                    roi_multiplier = final_price / entry_price if entry_price > 0 else 0
                    ath_multiplier = ath_price / entry_price if entry_price > 0 else 0
                    
                    result['ohlc_data'] = {
                        'source': 'cryptocompare',
                        'candles_count': len(candles),
                        'first_date': first_candle.timestamp.isoformat(),
                        'last_date': last_candle.timestamp.isoformat(),
                        'entry_price': entry_price,
                        'final_price': final_price,
                        'ath_price': ath_price,
                        'ath_day': ath_day
                    }
                    
                    result['analysis'] = {
                        'entry_price': f"${entry_price:.8f}",
                        'final_price': f"${final_price:.8f}",
                        'ath_price': f"${ath_price:.8f}",
                        'ath_day': f"Day {ath_day:.1f}",
                        'final_roi': f"{roi_multiplier:.3f}x ({(roi_multiplier-1)*100:+.1f}%)",
                        'ath_roi': f"{ath_multiplier:.3f}x ({(ath_multiplier-1)*100:+.1f}%)",
                        'outcome': 'WINNER' if ath_multiplier >= 2.0 else 'LOSER' if ath_multiplier < 1.0 else 'BREAK-EVEN'
                    }
                    
                    logger.info(f"\n📊 ANALYSIS:")
                    logger.info(f"  Entry Price: ${entry_price:.8f}")
                    logger.info(f"  ATH Price:   ${ath_price:.8f} (Day {ath_day:.1f})")
                    logger.info(f"  Final Price: ${final_price:.8f}")
                    logger.info(f"  ATH ROI:     {ath_multiplier:.3f}x ({(ath_multiplier-1)*100:+.1f}%)")
                    logger.info(f"  Final ROI:   {roi_multiplier:.3f}x ({(roi_multiplier-1)*100:+.1f}%)")
                    logger.info(f"  Outcome:     {result['analysis']['outcome']}")
                    
                    return result
            else:
                logger.warning(f"❌ No OHLC data found from any API")
        
        # If we get here, no data was found
        result['analysis'] = {
            'error': 'No OHLC data available',
            'entry_price': '$0.000000',
            'final_price': '$0.000000',
            'ath_price': '$0.000000',
            'final_roi': '0.0x (0.0%)',
            'ath_roi': '0.0x (0.0%)',
            'outcome': 'NO DATA'
        }
        
        logger.warning(f"❌ No OHLC data available for {address[:20]}...")
        
    except Exception as e:
        logger.error(f"Error analyzing token: {e}")
        result['analysis'] = {
            'error': str(e),
            'outcome': 'ERROR'
        }
    
    return result


async def main():
    """Main analysis function."""
    logger = setup_logger('DeadTokenAnalyzer', 'INFO')
    
    logger.info("="*80)
    logger.info("DEAD TOKEN ANALYSIS - 30 Day OHLC Data")
    logger.info("="*80)
    
    # Load dead tokens
    blacklist_path = Path("data/dead_tokens_blacklist.json")
    if not blacklist_path.exists():
        logger.error("No dead tokens blacklist found!")
        return
    
    with open(blacklist_path, 'r') as f:
        dead_tokens = json.load(f)
    
    logger.info(f"\nFound {len(dead_tokens)} dead tokens to analyze")
    
    # Initialize retriever
    import os
    from services.pricing.historical_price_service import HistoricalPriceService
    
    retriever = HistoricalPriceService(
        cryptocompare_api_key=os.getenv('CRYPTOCOMPARE_API_KEY', ''),
        alphavantage_api_key=os.getenv('ALPHAVANTAGE_API_KEY', ''),
        cache_dir="data/cache",
        symbol_mapping_path="data/symbol_mapping.json",
        logger=logger
    )
    
    # Analyze each token
    results = []
    for address, data in dead_tokens.items():
        result = await analyze_dead_token(
            address=address,
            chain=data.get('chain', 'evm'),
            detected_at=data.get('detected_at', ''),
            reason=data.get('reason', ''),
            retriever=retriever,
            logger=logger
        )
        results.append(result)
        
        # Small delay to avoid rate limits
        await asyncio.sleep(1)
    
    # Close retriever
    await retriever.close()
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    
    total = len(results)
    with_data = sum(1 for r in results if r['ohlc_data'] is not None)
    no_data = total - with_data
    
    winners = sum(1 for r in results if r['analysis'].get('outcome') == 'WINNER')
    losers = sum(1 for r in results if r['analysis'].get('outcome') == 'LOSER')
    break_even = sum(1 for r in results if r['analysis'].get('outcome') == 'BREAK-EVEN')
    
    logger.info(f"\nTotal Dead Tokens: {total}")
    logger.info(f"With OHLC Data: {with_data} ({with_data/total*100:.1f}%)")
    logger.info(f"No OHLC Data: {no_data} ({no_data/total*100:.1f}%)")
    
    if with_data > 0:
        logger.info(f"\nOutcomes (for tokens with data):")
        logger.info(f"  Winners (≥2x):     {winners} ({winners/with_data*100:.1f}%)")
        logger.info(f"  Break-even (1-2x): {break_even} ({break_even/with_data*100:.1f}%)")
        logger.info(f"  Losers (<1x):      {losers} ({losers/with_data*100:.1f}%)")
    
    # Save results
    output_path = Path("data/dead_tokens_analysis.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'analyzed_at': datetime.now().isoformat(),
            'total_tokens': total,
            'with_data': with_data,
            'no_data': no_data,
            'summary': {
                'winners': winners,
                'break_even': break_even,
                'losers': losers
            },
            'results': results
        }, f, indent=2, default=str)
    
    logger.info(f"\n✅ Results saved to: {output_path}")
    logger.info(f"{'='*80}\n")


if __name__ == '__main__':
    asyncio.run(main())

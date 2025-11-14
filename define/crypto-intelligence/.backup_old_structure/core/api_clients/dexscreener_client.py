"""DexScreener API client (no key required).

Verified endpoint: https://docs.dexscreener.com/api/reference
"""
import aiohttp
import json
from pathlib import Path
from typing import Optional, Dict

from core.api_clients.base_client import BaseAPIClient, PriceData
from utils.type_converters import safe_float


class DexScreenerClient(BaseAPIClient):
    """DexScreener API client with persistent session and chain mapping."""
    
    def __init__(self, logger=None):
        """Initialize client with persistent session and load chain mapping."""
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('DexScreenerClient')
        
        # Load chain mapping from JSON
        self.chain_mapping = self._load_chain_mapping()
        self.logger.debug(f"Loaded {len(self.chain_mapping)} chain mappings for DexScreener")
    
    def _load_chain_mapping(self) -> Dict[str, str]:
        """
        Load chain ID mapping from JSON file.
        
        Returns:
            Dictionary mapping generic chain names to DexScreener chain IDs
        """
        try:
            mapping_file = Path(__file__).parent.parent.parent / 'config' / 'dexscreener_chain_mapping.json'
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('mappings', {})
        except Exception as e:
            self.logger.warning(f"Failed to load chain mapping, using defaults: {e}")
            # Fallback to basic mapping
            return {
                'evm': 'ethereum',
                'eth': 'ethereum',
                'bnb': 'bsc',
                'matic': 'polygon',
                'avax': 'avalanche',
                'ftm': 'fantom',
                'op': 'optimism'
            }
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_price(self, address: str, chain: str) -> Optional[PriceData]:
        """Fetch price from DexScreener API with chain mapping."""
        await self._ensure_session()
        
        # Map generic chain name to DexScreener-specific chain ID using JSON mapping
        dex_chain = self.chain_mapping.get(chain.lower(), chain.lower())
        
        if dex_chain != chain.lower():
            self.logger.debug(f"Mapped chain '{chain}' → '{dex_chain}' for DexScreener")
        
        # Use v1 API endpoint with chain parameter
        url = f"https://api.dexscreener.com/tokens/v1/{dex_chain}/{address}"
        
        try:
            async with self._session.get(url, timeout=10) as response:
                self.logger.debug(f"DexScreener response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    # v1 API returns array directly, not wrapped in 'pairs' key
                    pairs = data if isinstance(data, list) else data.get('pairs', [])
                    
                    # If no pairs found with /tokens endpoint, try /pairs endpoint (for LP tokens)
                    if not pairs:
                        self.logger.debug(f"No pairs from /tokens, trying /pairs endpoint for {address}")
                        pairs_url = f"https://api.dexscreener.com/latest/dex/pairs/{dex_chain}/{address}"
                        async with self._session.get(pairs_url, timeout=10) as pairs_response:
                            if pairs_response.status == 200:
                                pairs_data = await pairs_response.json()
                                pair = pairs_data.get('pair')
                                if pair:
                                    pairs = [pair]
                                    self.logger.debug(f"Found pair data using /pairs endpoint")
                    
                    if pairs:
                        # Use first pair (usually most liquid)
                        pair = pairs[0]
                        self.logger.debug(f"DexScreener found {len(pairs)} pair(s) for {address}")
                        
                        # Extract price change from priceChange object
                        price_change = pair.get('priceChange', {})
                        price_change_24h = price_change.get('h24')
                        
                        # Extract volume from volume object
                        volume = pair.get('volume', {})
                        volume_24h = volume.get('h24')
                        
                        # Extract symbol from baseToken
                        base_token = pair.get('baseToken', {})
                        symbol = base_token.get('symbol')
                        
                        # Extract liquidity
                        liquidity = pair.get('liquidity', {})
                        liquidity_usd = liquidity.get('usd')
                        
                        # Extract pair creation date
                        pair_created_at = pair.get('pairCreatedAt')
                        
                        return PriceData(
                            price_usd=safe_float(pair.get('priceUsd'), 0.0),
                            market_cap=safe_float(pair.get('marketCap')),
                            volume_24h=safe_float(volume_24h),
                            price_change_24h=safe_float(price_change_24h),
                            liquidity_usd=safe_float(liquidity_usd),
                            pair_created_at=str(pair_created_at) if pair_created_at else None,
                            symbol=symbol,
                            source='dexscreener'
                        )
                    else:
                        self.logger.warning(f"DexScreener: No pairs found for {address}")
                else:
                    response_text = await response.text()
                    self.logger.warning(f"DexScreener HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"DexScreener exception for {address}: {e}")
            raise
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

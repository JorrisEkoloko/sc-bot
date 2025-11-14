"""LP Pair Resolver - Detects and resolves LP pair addresses to underlying tokens.

Handles cases where extracted addresses are Uniswap/Sushiswap/etc. LP pair contracts
instead of the actual token contracts.
"""
import aiohttp
from typing import Optional, Dict
from dataclasses import dataclass
from web3 import Web3
from utils.logger import setup_logger


@dataclass
class PairResolution:
    """Result of pair resolution."""
    is_pair: bool
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    pair_type: Optional[str] = None  # 'uniswap_v2', 'uniswap_v3', 'sushiswap', etc.
    base_token: Optional[Dict] = None
    quote_token: Optional[Dict] = None


class PairResolver:
    """Resolves LP pair addresses to underlying token addresses."""
    
    def __init__(self, logger=None):
        """
        Initialize pair resolver.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('PairResolver')
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Initialize Web3 for contract calls (fallback detection)
        self.w3 = None
        self._init_web3()
        
        self.logger.info("Pair resolver initialized")
    
    def _init_web3(self):
        """Initialize Web3 connection for contract calls."""
        try:
            # Use public Ethereum RPC
            self.w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com', request_kwargs={'timeout': 10}))
            if self.w3.is_connected():
                self.logger.debug("Web3 connected for LP pair detection")
            else:
                self.logger.warning("Web3 connection failed - LP pair detection will be limited")
                self.w3 = None
        except Exception as e:
            self.logger.warning(f"Could not initialize Web3: {e}")
            self.w3 = None
    
    async def _ensure_session(self):
        """Ensure HTTP session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def resolve_address(self, address: str, chain: str) -> PairResolution:
        """
        Check if address is an LP pair and resolve to underlying token.
        
        Strategy:
        1. Query DexScreener with address as pair
        2. If found as pair, extract base token address
        3. Return resolution with token address
        
        Args:
            address: Contract address to check
            chain: Blockchain name ('evm', 'solana')
            
        Returns:
            PairResolution object
        """
        if chain == 'solana':
            # Solana doesn't have the same LP pair confusion issue
            return PairResolution(is_pair=False)
        
        await self._ensure_session()
        
        # Try DexScreener pair endpoint
        try:
            # Map chain to DexScreener chain ID
            chain_map = {
                'evm': 'ethereum',
                'ethereum': 'ethereum',
                'eth': 'ethereum',
                'bsc': 'bsc',
                'polygon': 'polygon',
                'arbitrum': 'arbitrum',
                'avalanche': 'avalanche',
                'optimism': 'optimism',
                'base': 'base'
            }
            dex_chain = chain_map.get(chain.lower(), 'ethereum')
            
            # Query as pair address
            url = f"https://api.dexscreener.com/latest/dex/pairs/{dex_chain}/{address}"
            
            async with self._session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    pair = data.get('pair')
                    
                    if pair:
                        # This is a pair! Extract base token
                        base_token = pair.get('baseToken', {})
                        quote_token = pair.get('quoteToken', {})
                        dex_id = pair.get('dexId', 'unknown')
                        
                        token_address = base_token.get('address')
                        token_symbol = base_token.get('symbol')
                        
                        if token_address:
                            self.logger.info(
                                f"Resolved LP pair {address[:10]}... to token {token_symbol} "
                                f"({token_address[:10]}...) on {dex_id}"
                            )
                            
                            return PairResolution(
                                is_pair=True,
                                token_address=token_address,
                                token_symbol=token_symbol,
                                pair_type=dex_id,
                                base_token=base_token,
                                quote_token=quote_token
                            )
        
        except Exception as e:
            self.logger.debug(f"DexScreener check failed for {address[:10]}...: {e}")
        
        # Fallback: Check if it's an LP pair using Web3 contract calls
        if self.w3 and self.w3.is_connected():
            try:
                pair_check = self._check_lp_pair_web3(address)
                if pair_check['is_pair']:
                    self.logger.info(
                        f"Detected LP pair {address[:10]}... via Web3 contract call "
                        f"(token0: {pair_check['token0'][:10]}...)"
                    )
                    return PairResolution(
                        is_pair=True,
                        token_address=pair_check['token0'],
                        token_symbol=None,  # Symbol unknown without API
                        pair_type='uniswap_v2_compatible',
                        base_token={'address': pair_check['token0']},
                        quote_token={'address': pair_check['token1']}
                    )
            except Exception as e:
                self.logger.debug(f"Web3 LP check failed for {address[:10]}...: {e}")
        
        # Not a pair (or couldn't determine)
        return PairResolution(is_pair=False)
    
    def _check_lp_pair_web3(self, address: str) -> Dict:
        """
        Check if address is a Uniswap V2 LP pair using Web3 contract calls.
        
        Uniswap V2 pairs have token0() and token1() functions that return addresses.
        
        Args:
            address: Contract address to check
            
        Returns:
            Dict with is_pair, token0, token1
        """
        try:
            checksum_addr = Web3.to_checksum_address(address)
            
            # Function signatures for Uniswap V2 pair
            token0_sig = "0x0dfe1681"  # token0()
            token1_sig = "0xd21220a7"  # token1()
            
            # Try calling token0()
            token0_result = self.w3.eth.call({
                'to': checksum_addr,
                'data': token0_sig
            })
            
            # Try calling token1()
            token1_result = self.w3.eth.call({
                'to': checksum_addr,
                'data': token1_sig
            })
            
            # If both calls succeed and return 32 bytes (address), it's an LP pair
            if len(token0_result) == 32 and len(token1_result) == 32:
                token0_addr = '0x' + token0_result[-20:].hex()
                token1_addr = '0x' + token1_result[-20:].hex()
                
                return {
                    'is_pair': True,
                    'token0': token0_addr,
                    'token1': token1_addr
                }
        
        except Exception:
            # Call failed - not an LP pair
            pass
        
        return {'is_pair': False}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

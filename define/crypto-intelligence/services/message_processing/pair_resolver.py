"""LP Pair Resolver - Detects and resolves LP pair addresses to underlying tokens.

Handles cases where extracted addresses are Uniswap/Sushiswap/etc. LP pair contracts
instead of the actual token contracts.
"""
from typing import Optional, Dict
from dataclasses import dataclass
from web3 import Web3

from repositories.api_clients.dexscreener_client import DexScreenerClient
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
    
    def __init__(self, dexscreener_client: DexScreenerClient = None, logger=None):
        """
        Initialize pair resolver.
        
        Args:
            dexscreener_client: DexScreener API client for pair lookups
            logger: Optional logger instance
        """
        self.logger = logger or setup_logger('PairResolver')
        self.dexscreener_client = dexscreener_client or DexScreenerClient(logger=self.logger)
        
        # Initialize Web3 for contract calls (fallback detection)
        self.w3 = None
        self._init_web3()
        
        self.logger.info("Pair resolver initialized")
    
    def _init_web3(self):
        """Initialize Web3 connection for contract calls with fallback RPCs."""
        # List of public RPC endpoints to try (in order of preference)
        rpc_endpoints = [
            'https://eth.llamarpc.com',
            'https://rpc.ankr.com/eth',
            'https://ethereum.publicnode.com'
        ]
        
        for rpc_url in rpc_endpoints:
            try:
                self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if self.w3.is_connected():
                    self.logger.debug(f"Web3 connected to {rpc_url} for LP pair detection")
                    return
                else:
                    self.logger.debug(f"Web3 connection failed for {rpc_url}, trying next...")
            except Exception as e:
                self.logger.debug(f"Could not connect to {rpc_url}: {e}")
                continue
        
        # All RPCs failed
        self.logger.warning("All Web3 RPC endpoints failed - LP pair detection will be limited")
        self.w3 = None
    
    async def close(self):
        """Close DexScreener client session."""
        await self.dexscreener_client.close()
    
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
        
        # Try DexScreener pair endpoint via API client
        try:
            pair = await self.dexscreener_client.get_pair_info(address, chain)
            
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
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

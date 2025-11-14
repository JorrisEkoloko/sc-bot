"""
Etherscan API Client for Token Validation

Checks if tokens are dead/inactive to avoid wasting API calls.
"""
import aiohttp
import logging
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class TokenStats:
    """Token statistics from Etherscan."""
    total_supply: str
    holders: int
    transfers: int
    is_dead: bool
    reason: str


class EtherscanClient:
    """Client for Etherscan API V2."""
    
    def __init__(self, api_key: str, logger=None):
        """
        Initialize Etherscan client.
        
        Args:
            api_key: Etherscan API key
            logger: Logger instance
        """
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/v2/api"
        self.logger = logger or logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_token_supply(self, contract_address: str, chain_id: int = 1) -> Optional[str]:
        """
        Get token total supply.
        
        Args:
            contract_address: Token contract address
            chain_id: Chain ID (1 for Ethereum mainnet)
            
        Returns:
            Total supply as string, or None if failed
        """
        try:
            session = await self._get_session()
            
            params = {
                'chainid': chain_id,
                'module': 'stats',
                'action': 'tokensupply',
                'contractaddress': contract_address,
                'apikey': self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                if data.get('status') == '1' and data.get('message') == 'OK':
                    return data.get('result')
                else:
                    self.logger.warning(f"Etherscan tokensupply failed: {data.get('message')}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Etherscan tokensupply error: {e}")
            return None
    
    async def get_contract_creation_time(self, contract_address: str, chain_id: int = 1) -> Optional[int]:
        """
        Get contract creation timestamp.
        
        Args:
            contract_address: Token contract address
            chain_id: Chain ID (1 for Ethereum mainnet)
            
        Returns:
            Unix timestamp of contract creation, or None if failed
        """
        try:
            session = await self._get_session()
            
            params = {
                'chainid': chain_id,
                'module': 'contract',
                'action': 'getcontractcreation',
                'contractaddresses': contract_address,
                'apikey': self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                if data.get('status') == '1' and data.get('message') == 'OK':
                    result = data.get('result', [])
                    if result and len(result) > 0:
                        timestamp = result[0].get('timestamp')
                        return int(timestamp) if timestamp else None
                    return None
                else:
                    self.logger.warning(f"Etherscan getcontractcreation failed: {data.get('message')}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Etherscan getcontractcreation error: {e}")
            return None
    
    async def get_token_transfer_count(self, contract_address: str, chain_id: int = 1) -> int:
        """
        Get the number of token transfers.
        
        Args:
            contract_address: Token contract address
            chain_id: Chain ID (1 for Ethereum mainnet)
            
        Returns:
            Number of transfers, or -1 if failed
        """
        try:
            session = await self._get_session()
            
            # Get token transfers (limit to 1 to check if any exist)
            params = {
                'chainid': chain_id,
                'module': 'account',
                'action': 'tokentx',
                'contractaddress': contract_address,
                'page': 1,
                'offset': 10000,  # Max allowed
                'sort': 'asc',
                'apikey': self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                if data.get('status') == '1' and data.get('message') == 'OK':
                    result = data.get('result', [])
                    return len(result) if result else 0
                else:
                    self.logger.warning(f"Etherscan tokentx failed: {data.get('message')}")
                    return -1
                    
        except Exception as e:
            self.logger.error(f"Etherscan tokentx error: {e}")
            return -1
    
    async def check_if_dead_token(self, contract_address: str, chain_id: int = 1) -> TokenStats:
        """
        Check if token is dead/inactive.
        
        A token is considered dead if:
        - Total supply is 0 or extremely low (< 1000 wei)
        - Supply is very low AND it's an LP token (< 10000 wei for LP tokens)
        - No holders (requires Pro API, so we skip this check)
        - No transfers in recent history
        
        Args:
            contract_address: Token contract address
            chain_id: Chain ID (1 for Ethereum mainnet)
            
        Returns:
            TokenStats with is_dead flag and reason
        """
        try:
            # Check total supply
            supply = await self.get_token_supply(contract_address, chain_id)
            
            if supply is None:
                return TokenStats(
                    total_supply="unknown",
                    holders=-1,
                    transfers=-1,
                    is_dead=False,
                    reason="Could not fetch supply"
                )
            
            supply_int = int(supply)
            
            # Check if supply is extremely low (< 1000 wei = 0.000000000000001 tokens with 18 decimals)
            if supply_int < 1000:
                return TokenStats(
                    total_supply=supply,
                    holders=0,
                    transfers=0,
                    is_dead=True,
                    reason=f"Extremely low supply: {supply} wei (< 1000)"
                )
            
            # Check transfer count (works with free API!)
            transfer_count = await self.get_token_transfer_count(contract_address, chain_id)
            
            # Get contract creation time to avoid marking new tokens as dead
            creation_time = await self.get_contract_creation_time(contract_address, chain_id)
            
            # Calculate token age in days
            import time
            current_time = int(time.time())
            token_age_days = 0
            if creation_time:
                token_age_days = (current_time - creation_time) / 86400  # seconds to days
            
            # Check if it's a dead LP token (supply < 10000 wei = 0.00000000000001 LP tokens)
            # LP tokens with such low supply are essentially dead/abandoned
            if supply_int < 10000:
                # Check if it's likely an LP token by checking the contract
                is_lp = await self._is_likely_lp_token(contract_address, chain_id)
                if is_lp:
                    return TokenStats(
                        total_supply=supply,
                        holders=0,
                        transfers=transfer_count,
                        is_dead=True,
                        reason=f"Dead LP token: supply {supply} wei (< 10000), {transfer_count} transfers, {token_age_days:.1f} days old, abandoned pool"
                    )
            
            # Check if token has no transfers AND is old enough (> 7 days)
            # Don't mark brand new tokens as dead - give them time to get initial transfers
            if transfer_count == 0:
                if token_age_days > 7:
                    return TokenStats(
                        total_supply=supply,
                        holders=-1,  # Unknown without Pro
                        transfers=0,
                        is_dead=True,
                        reason=f"Dead token: 0 transfers after {token_age_days:.1f} days, never used"
                    )
                else:
                    # New token, give it time
                    return TokenStats(
                        total_supply=supply,
                        holders=-1,
                        transfers=0,
                        is_dead=False,
                        reason=f"New token: {token_age_days:.1f} days old, 0 transfers (too new to judge)"
                    )
            
            # Token has supply and transfers, consider it alive
            return TokenStats(
                total_supply=supply,
                holders=-1,  # Unknown without Pro
                transfers=transfer_count,
                is_dead=False,
                reason=f"Token has supply and {transfer_count} transfers ({token_age_days:.1f} days old)"
            )
            
        except Exception as e:
            self.logger.error(f"Error checking if token is dead: {e}")
            return TokenStats(
                total_supply="error",
                holders=-1,
                transfers=-1,
                is_dead=False,
                reason=f"Error: {e}"
            )
    
    async def _is_likely_lp_token(self, contract_address: str, chain_id: int = 1) -> bool:
        """
        Check if contract is likely an LP token by checking for Uniswap V2 Pair interface.
        
        Args:
            contract_address: Token contract address
            chain_id: Chain ID
            
        Returns:
            True if likely an LP token, False otherwise
        """
        try:
            session = await self._get_session()
            
            # Try to call getReserves() function (exists on Uniswap V2 pairs)
            # Function signature: getReserves() returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)
            params = {
                'chainid': chain_id,
                'module': 'proxy',
                'action': 'eth_call',
                'to': contract_address,
                'data': '0x0902f1ac',  # getReserves() function selector
                'tag': 'latest',
                'apikey': self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                # If the call succeeds and returns data, it's likely an LP token
                if data.get('result') and data.get('result') != '0x':
                    return True
                return False
                
        except Exception as e:
            self.logger.debug(f"LP token check failed: {e}")
            return False

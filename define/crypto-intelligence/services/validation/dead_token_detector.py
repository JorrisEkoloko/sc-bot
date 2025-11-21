"""
Dead Token Detector

Identifies and blacklists dead/inactive tokens to avoid wasting API calls.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from repositories.api_clients.etherscan_client import EtherscanClient, TokenStats


class DeadTokenDetector:
    """Detects and blacklists dead tokens."""
    
    def __init__(self, etherscan_api_key: str, blacklist_path: str = "data/dead_tokens_blacklist.json", logger=None):
        """
        Initialize dead token detector.
        
        Args:
            etherscan_api_key: Etherscan API key
            blacklist_path: Path to blacklist JSON file
            logger: Logger instance
        """
        self.etherscan = EtherscanClient(etherscan_api_key, logger)
        self.blacklist_path = Path(blacklist_path)
        self.logger = logger or logging.getLogger(__name__)
        self.blacklist: Dict[str, Dict] = {}
        
        # Load existing blacklist
        self._load_blacklist()
    
    def _load_blacklist(self):
        """Load blacklist from JSON file."""
        if self.blacklist_path.exists():
            try:
                with open(self.blacklist_path, 'r') as f:
                    self.blacklist = json.load(f)
                self.logger.info(f"Loaded {len(self.blacklist)} dead tokens from blacklist")
            except Exception as e:
                self.logger.error(f"Failed to load blacklist: {e}")
                self.blacklist = {}
        else:
            self.logger.info("No existing blacklist found, starting fresh")
            self.blacklist = {}
    
    def _save_blacklist(self):
        """Save blacklist to JSON file."""
        try:
            # Create directory if it doesn't exist
            self.blacklist_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.blacklist_path, 'w') as f:
                json.dump(self.blacklist, f, indent=2)
            
            self.logger.info(f"Saved {len(self.blacklist)} dead tokens to blacklist")
        except Exception as e:
            self.logger.error(f"Failed to save blacklist: {e}")
    
    def is_blacklisted(self, contract_address: str) -> bool:
        """
        Check if token is in blacklist.
        
        Args:
            contract_address: Token contract address
            
        Returns:
            True if blacklisted, False otherwise
        """
        address_lower = contract_address.lower()
        return address_lower in self.blacklist
    
    def get_blacklist_reason(self, contract_address: str) -> Optional[str]:
        """
        Get reason why token is blacklisted.
        
        Args:
            contract_address: Token contract address
            
        Returns:
            Reason string, or None if not blacklisted
        """
        address_lower = contract_address.lower()
        if address_lower in self.blacklist:
            return self.blacklist[address_lower].get('reason', 'Unknown')
        return None
    
    async def check_and_blacklist_if_dead(
        self, 
        contract_address: str, 
        chain: str = "ethereum",
        has_valid_price: bool = False
    ) -> TokenStats:
        """
        Check if token is dead and add to blacklist if so.
        
        Args:
            contract_address: Token contract address
            chain: Blockchain name (ethereum, bsc, etc.)
            has_valid_price: If True, token has valid price data from DEX/API
            
        Returns:
            TokenStats with is_dead flag
        """
        address_lower = contract_address.lower()
        
        # Check if already blacklisted
        if self.is_blacklisted(address_lower):
            reason = self.get_blacklist_reason(address_lower)
            self.logger.info(f"Token {address_lower[:10]}... already blacklisted: {reason}")
            return TokenStats(
                total_supply="blacklisted",
                holders=0,
                transfers=0,
                is_dead=True,
                reason=reason
            )
        
        # Map chain to chain_id
        chain_id_map = {
            "ethereum": 1,
            "bsc": 56,
            "polygon": 137,
            "arbitrum": 42161,
            "optimism": 10,
            "base": 8453
        }
        chain_id = chain_id_map.get(chain.lower(), 1)
        
        # Check if token is dead using Etherscan
        stats = await self.etherscan.check_if_dead_token(address_lower, chain_id)
        
        # If dead BUT has valid price data, don't blacklist
        # (Some tokens like pump.fun have 0 supply but active trading)
        if stats.is_dead and has_valid_price:
            self.logger.info(
                f"[NOT BLACKLISTING] {address_lower[:10]}... has 0 supply but valid price data "
                f"(likely pump.fun or similar token)"
            )
            # Return stats but mark as not dead since it has valid price
            stats.is_dead = False
            stats.reason = "Has valid price data despite 0 supply"
            return stats
        
        # IMPORTANT: DON'T blacklist based on supply alone
        # Many tokens report 0 supply but may still have active trading
        # Only blacklist if we're certain there's no trading activity (no price data)
        if stats.is_dead:
            self.logger.info(
                f"[NOT BLACKLISTING YET] {address_lower[:10]}... has 0 supply "
                f"(will verify with price APIs before blacklisting)"
            )
            # Mark as potentially dead but don't blacklist yet
            # Let the price engine determine if it's truly dead
            stats.is_dead = False
            stats.reason = "Low supply - needs price verification"
            return stats
        
        # This code path should never be reached now, but keeping for safety
        if stats.is_dead:
            self.blacklist[address_lower] = {
                'address': address_lower,
                'chain': chain,
                'reason': stats.reason,
                'total_supply': stats.total_supply,
                'detected_at': datetime.now().isoformat(),
                'holders': stats.holders,
                'transfers': stats.transfers
            }
            self._save_blacklist()
            self.logger.warning(f"[DEAD TOKEN] Blacklisted {address_lower[:10]}...: {stats.reason}")
        
        return stats
    
    async def close(self):
        """Close Etherscan client."""
        await self.etherscan.close()
    
    def get_blacklist_stats(self) -> Dict:
        """
        Get statistics about blacklisted tokens.
        
        Returns:
            Dictionary with blacklist statistics
        """
        return {
            'total_blacklisted': len(self.blacklist),
            'by_chain': self._count_by_chain(),
            'by_reason': self._count_by_reason()
        }
    
    def _count_by_chain(self) -> Dict[str, int]:
        """Count blacklisted tokens by chain."""
        counts = {}
        for entry in self.blacklist.values():
            chain = entry.get('chain', 'unknown')
            counts[chain] = counts.get(chain, 0) + 1
        return counts
    
    def _count_by_reason(self) -> Dict[str, int]:
        """Count blacklisted tokens by reason."""
        counts = {}
        for entry in self.blacklist.values():
            reason = entry.get('reason', 'unknown')
            # Simplify reason for counting
            if 'low supply' in reason.lower():
                key = 'low_supply'
            elif 'no holders' in reason.lower():
                key = 'no_holders'
            elif 'no transfers' in reason.lower():
                key = 'no_transfers'
            else:
                key = 'other'
            counts[key] = counts.get(key, 0) + 1
        return counts

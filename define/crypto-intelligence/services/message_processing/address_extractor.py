"""Address extraction and validation for blockchain addresses.

Based on verified documentation:
- Ethereum: https://ethereum.org/en/developers/docs/accounts/
- Solana: https://docs.solana.com/terminology#account
- BSC (EVM-compatible): https://docs.bnbchain.org/
- Base58: https://pypi.org/project/base58/
"""
import re
from dataclasses import dataclass
from typing import Optional
from utils.logger import setup_logger


@dataclass
class Address:
    """Blockchain address with metadata."""
    address: str
    chain: str  # 'evm', 'solana', 'unknown'
    is_valid: bool
    ticker: Optional[str] = None
    chain_specific: Optional[str] = None  # Specific chain: 'ethereum', 'bsc', 'polygon', 'arbitrum', 'avalanche'
    is_pair: bool = False  # True if this was an LP pair that was resolved
    original_address: Optional[str] = None  # Original pair address if resolved


class AddressExtractor:
    """Extract and validate blockchain addresses from crypto mentions.
    
    Supports:
    - EVM chains (Ethereum, BSC, Polygon, Arbitrum, Avalanche, Optimism, etc.)
    - Solana
    """
    
    def __init__(self, logger=None, pair_resolver=None):
        """
        Initialize address extractor.
        
        Args:
            logger: Optional logger instance
            pair_resolver: Optional PairResolver instance for LP pair detection
        """
        self.logger = logger or setup_logger('AddressExtractor')
        self.pair_resolver = pair_resolver
        
        # EVM address pattern: 0x followed by 40 hexadecimal characters
        # Used by: Ethereum, BSC, Polygon, Arbitrum, Avalanche, Optimism, etc.
        # Verified: https://ethereum.org/en/developers/docs/accounts/
        # BSC is EVM-compatible: https://docs.bnbchain.org/
        self.evm_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        
        # Solana address pattern: base58 encoded, 32-44 characters
        # Base58 alphabet excludes 0, O, I, l to avoid confusion
        # Verified: https://docs.solana.com/terminology#account
        self.solana_pattern = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
        
        pair_status = "with LP pair resolution" if pair_resolver else "without LP pair resolution"
        self.logger.info(f"Address extractor initialized (supports EVM chains + Solana, {pair_status})")
    
    def extract_addresses(self, crypto_mentions: list[str]) -> list[Address]:
        """
        Extract addresses from crypto mentions list.
        
        Args:
            crypto_mentions: List of strings (tickers and addresses)
            
        Returns:
            List of Address objects with validation status
        """
        if not crypto_mentions:
            return []
        
        self.logger.debug(f"Extracting addresses from {len(crypto_mentions)} crypto mentions")
        
        addresses = []
        for mention in crypto_mentions:
            if self._looks_like_address(mention):
                chain = self.identify_chain(mention)
                is_valid = self.validate_address(mention, chain)
                
                address = Address(
                    address=mention,
                    chain=chain,
                    is_valid=is_valid,
                    chain_specific='ethereum' if chain == 'evm' else chain  # Default EVM to ethereum
                )
                addresses.append(address)
                
                if is_valid:
                    self.logger.debug(f"{chain.upper()} address validated: {mention[:10]}...")
                else:
                    self.logger.warning(f"Invalid address detected: {mention[:10]}...")
        
        if addresses:
            chain_counts = {}
            for addr in addresses:
                chain_counts[addr.chain] = chain_counts.get(addr.chain, 0) + 1
            
            chain_summary = ', '.join([f"{count} {chain}" for chain, count in chain_counts.items()])
            self.logger.info(f"Found {len(addresses)} addresses: {chain_summary}")
        
        return addresses
    
    async def extract_addresses_async(self, crypto_mentions: list[str]) -> list[Address]:
        """
        Extract addresses from crypto mentions list with async LP pair resolution.
        
        Args:
            crypto_mentions: List of strings (tickers and addresses)
            
        Returns:
            List of Address objects with validation status and pair resolution
        """
        # First extract addresses normally
        addresses = self.extract_addresses(crypto_mentions)
        
        # If pair resolver is available, check each address
        if self.pair_resolver and addresses:
            resolved_addresses = []
            
            for addr in addresses:
                if addr.is_valid and addr.chain == 'evm':
                    # Check if this is an LP pair
                    resolution = await self.pair_resolver.resolve_address(addr.address, addr.chain)
                    
                    if resolution.is_pair and resolution.token_address:
                        # This was a pair! Create new address object for the token
                        resolved_addr = Address(
                            address=resolution.token_address,
                            chain=addr.chain,
                            is_valid=True,  # Assume token address is valid
                            ticker=resolution.token_symbol,
                            chain_specific=addr.chain_specific,
                            is_pair=True,
                            original_address=addr.address
                        )
                        resolved_addresses.append(resolved_addr)
                        self.logger.info(
                            f"Resolved LP pair to token: {resolution.token_symbol} "
                            f"({resolution.token_address[:10]}...)"
                        )
                    else:
                        # Not a pair, keep original
                        resolved_addresses.append(addr)
                else:
                    # Not EVM or not valid, keep original
                    resolved_addresses.append(addr)
            
            return resolved_addresses
        
        # No pair resolver, return original addresses
        return addresses
    
    def identify_chain(self, address: str) -> str:
        """
        Identify blockchain from address format.
        
        Args:
            address: Address string
            
        Returns:
            Chain name ('evm', 'solana', 'unknown')
        """
        if self.evm_pattern.match(address):
            return 'evm'
        elif self.solana_pattern.match(address):
            return 'solana'
        return 'unknown'
    
    def validate_address(self, address: str, chain: str) -> bool:
        """
        Validate address format for specific chain.
        
        Args:
            address: Address string
            chain: Blockchain name
            
        Returns:
            True if valid, False otherwise
        """
        if chain == 'evm':
            return self.validate_evm_address(address)
        elif chain == 'solana':
            return self.validate_solana_address(address)
        return False
    
    def validate_evm_address(self, address: str) -> bool:
        """
        Validate EVM address format (Ethereum, BSC, Polygon, etc.).
        
        Checks:
        - Starts with 0x
        - Followed by exactly 40 hexadecimal characters
        
        Args:
            address: Address string
            
        Returns:
            True if valid EVM address format
        """
        if not self.evm_pattern.match(address):
            return False
        
        # Basic format validation passed
        # Note: Full checksum validation (EIP-55) could be added here
        # but basic format validation is sufficient for our use case
        return True
    
    def validate_solana_address(self, address: str) -> bool:
        """
        Validate Solana address format.
        
        Checks:
        - Base58 encoded (no 0, O, I, l characters)
        - Length between 32-44 characters
        - Valid base58 decoding to 32 bytes
        
        Args:
            address: Address string
            
        Returns:
            True if valid Solana address format
        """
        if not self.solana_pattern.match(address):
            return False
        
        # Try to decode as base58 to verify it's valid
        try:
            import base58
            decoded = base58.b58decode(address)
            # Solana addresses should decode to 32 bytes
            return len(decoded) == 32
        except Exception as e:
            self.logger.debug(f"Base58 decode failed for {address[:10]}...: {e}")
            return False
    
    def _looks_like_address(self, text: str) -> bool:
        """
        Quick check if text looks like an address.
        
        This is a fast pre-filter before full validation.
        
        Args:
            text: Text to check
            
        Returns:
            True if text might be an address
        """
        if not text or not isinstance(text, str):
            return False
        
        # EVM: starts with 0x and is 42 characters
        if text.startswith('0x') and len(text) == 42:
            return True
        
        # Solana: 32-44 characters, starts with valid base58 character
        if 32 <= len(text) <= 44 and text[0] in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz':
            return True
        
        return False

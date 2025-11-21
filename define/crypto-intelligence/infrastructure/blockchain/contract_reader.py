"""Contract reader - reads data directly from blockchain contracts."""
from typing import Optional
from utils.logger import get_logger


class ContractReader:
    """
    Reads token information directly from blockchain smart contracts.
    
    Infrastructure layer - handles low-level blockchain interactions.
    """
    
    def __init__(self, logger=None):
        """Initialize contract reader."""
        self.logger = logger or get_logger('ContractReader')
        self._rpc_endpoints = {
            'ethereum': 'https://eth.llamarpc.com',
            'evm': 'https://eth.llamarpc.com',
            'bsc': 'https://bsc-dataseed.binance.org',
            'polygon': 'https://polygon-rpc.com',
            'arbitrum': 'https://arb1.arbitrum.io/rpc',
            'optimism': 'https://mainnet.optimism.io',
            'base': 'https://mainnet.base.org'
        }
    
    async def read_symbol_from_contract(
        self,
        address: str,
        chain: str,
        timeout: int = 5
    ) -> Optional[str]:
        """
        Read token symbol directly from blockchain contract.
        
        This is a last-resort fallback when all APIs fail to provide the symbol.
        Uses Web3 to call the symbol() function on the ERC20 contract.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            timeout: Request timeout in seconds
            
        Returns:
            Token symbol or None if failed
        """
        try:
            # Only works for EVM chains
            if chain == 'solana':
                return None
            
            # Try to import web3 (optional dependency)
            try:
                from web3 import Web3
            except ImportError:
                self.logger.debug("web3 not installed, cannot read symbol from contract")
                return None
            
            # Get RPC endpoint
            rpc_url = self._rpc_endpoints.get(chain.lower(), self._rpc_endpoints['ethereum'])
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': timeout}))
            
            # ERC20 symbol() function signature
            symbol_abi = [{
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }]
            
            # Validate address format
            if not address or len(address) < 40:
                self.logger.debug(f"Invalid address format: {address}")
                return None
            
            # Create contract instance
            try:
                checksum_address = Web3.to_checksum_address(address)
            except Exception as e:
                self.logger.debug(f"Invalid address checksum: {address} - {e}")
                return None
            
            contract = w3.eth.contract(address=checksum_address, abi=symbol_abi)
            
            # Call symbol() function with timeout
            try:
                symbol = contract.functions.symbol().call()
            except Exception as call_error:
                # Contract might not have symbol() function or it reverted
                self.logger.debug(f"Contract call failed for {address[:10]}...: {call_error}")
                return None
            
            if symbol and isinstance(symbol, str) and len(symbol) > 0:
                self.logger.info(f"✅ Read symbol from contract: {symbol}")
                return symbol
            
            self.logger.debug(f"Contract returned empty symbol for {address[:10]}...")
            return None
            
        except Exception as e:
            error_type = type(e).__name__
            self.logger.warning(
                f"Failed to read symbol from contract {address[:10]}...: "
                f"{error_type}: {str(e)[:100]}"
            )
            return None
    
    def add_rpc_endpoint(self, chain: str, endpoint: str):
        """
        Add or update RPC endpoint for a chain.
        
        Args:
            chain: Chain name
            endpoint: RPC endpoint URL
        """
        self._rpc_endpoints[chain.lower()] = endpoint
        self.logger.info(f"Added RPC endpoint for {chain}: {endpoint}")
    
    def get_rpc_endpoint(self, chain: str) -> str:
        """
        Get RPC endpoint for a chain.
        
        Args:
            chain: Chain name
            
        Returns:
            RPC endpoint URL
        """
        return self._rpc_endpoints.get(chain.lower(), self._rpc_endpoints['ethereum'])

"""GoPlusLabs Security API client (no key required).

Provides token security audit, scam detection, and risk analysis.
Verified endpoint: https://api.gopluslabs.io/api/v1/token_security/{chain_id}
"""
import aiohttp
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class TokenSecurityData:
    """Token security audit data from GoPlusLabs."""
    is_honeypot: bool
    is_proxy: bool
    buy_tax: float
    sell_tax: float
    holder_count: int
    liquidity_usd: float
    is_open_source: bool
    can_take_back_ownership: bool
    hidden_owner: bool
    external_call: bool
    reputation: str  # 'safe', 'warning', 'danger'
    risk_score: float  # 0-100, higher is riskier


class GoPlusClient:
    """GoPlusLabs Security API client (no API key required)."""
    
    def __init__(self, request_timeout: int = 10, logger=None):
        """
        Initialize client with persistent session.
        
        Args:
            request_timeout: HTTP request timeout in seconds (default: 10)
            logger: Logger instance
        """
        self.request_timeout = request_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        from utils.logger import setup_logger
        self.logger = logger or setup_logger('GoPlusClient')
        
        # Chain ID mapping
        self.chain_ids = {
            'ethereum': '1',
            'evm': '1',
            'bsc': '56',
            'polygon': '137',
            'arbitrum': '42161',
            'optimism': '10',
            'base': '8453',
            'avalanche': '43114'
        }
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def get_token_security(self, address: str, chain: str) -> Optional[TokenSecurityData]:
        """
        Fetch token security audit from GoPlusLabs.
        
        Args:
            address: Token contract address
            chain: Blockchain name
            
        Returns:
            TokenSecurityData with security info, or None if not found
        """
        await self._ensure_session()
        
        # Get chain ID
        chain_id = self.chain_ids.get(chain.lower(), '1')
        
        # Build URL
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
        params = {'contract_addresses': address}
        
        try:
            async with self._session.get(url, params=params, timeout=self.request_timeout) as response:
                self.logger.debug(f"GoPlus response status: {response.status} for {address}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if request was successful
                    if data.get('code') != 1:
                        self.logger.warning(f"GoPlus error: {data.get('message')}")
                        return None
                    
                    # Extract token data
                    result = data.get('result', {})
                    token_data = result.get(address.lower(), {})
                    
                    if not token_data:
                        self.logger.warning(f"GoPlus: No data for {address}")
                        return None
                    
                    # Parse security data
                    is_honeypot = token_data.get('is_honeypot', '0') == '1'
                    is_proxy = token_data.get('is_proxy', '0') == '1'
                    buy_tax = float(token_data.get('buy_tax', '0'))
                    sell_tax = float(token_data.get('sell_tax', '0'))
                    holder_count = int(token_data.get('holder_count', '0'))
                    
                    # Calculate liquidity from DEX data
                    liquidity_usd = 0.0
                    dex_list = token_data.get('dex', [])
                    if dex_list:
                        for dex in dex_list:
                            liquidity_usd += float(dex.get('liquidity', '0'))
                    
                    # Security flags
                    is_open_source = token_data.get('is_open_source', '0') == '1'
                    can_take_back_ownership = token_data.get('can_take_back_ownership', '0') == '1'
                    hidden_owner = token_data.get('hidden_owner', '0') == '1'
                    external_call = token_data.get('external_call', '0') == '1'
                    
                    # Calculate risk score and reputation
                    risk_score = self._calculate_risk_score(token_data)
                    reputation = self._determine_reputation(risk_score, is_honeypot)
                    
                    self.logger.debug(
                        f"GoPlus: {address[:10]}... - Reputation: {reputation}, "
                        f"Risk: {risk_score:.1f}, Honeypot: {is_honeypot}"
                    )
                    
                    return TokenSecurityData(
                        is_honeypot=is_honeypot,
                        is_proxy=is_proxy,
                        buy_tax=buy_tax,
                        sell_tax=sell_tax,
                        holder_count=holder_count,
                        liquidity_usd=liquidity_usd,
                        is_open_source=is_open_source,
                        can_take_back_ownership=can_take_back_ownership,
                        hidden_owner=hidden_owner,
                        external_call=external_call,
                        reputation=reputation,
                        risk_score=risk_score
                    )
                else:
                    response_text = await response.text()
                    self.logger.warning(f"GoPlus HTTP {response.status} for {address}: {response_text[:200]}")
                
                return None
        except Exception as e:
            self.logger.error(f"GoPlus exception for {address}: {e}")
            return None
    
    def _calculate_risk_score(self, token_data: Dict) -> float:
        """
        Calculate risk score (0-100, higher is riskier).
        
        Args:
            token_data: Raw token data from GoPlus
            
        Returns:
            Risk score from 0 (safe) to 100 (very risky)
        """
        risk = 0.0
        
        # Critical risks (30 points each)
        if token_data.get('is_honeypot', '0') == '1':
            risk += 30
        if token_data.get('hidden_owner', '0') == '1':
            risk += 30
        
        # High risks (20 points each)
        if token_data.get('can_take_back_ownership', '0') == '1':
            risk += 20
        if token_data.get('is_proxy', '0') == '1':
            risk += 10
        
        # Medium risks (10 points each)
        if token_data.get('external_call', '0') == '1':
            risk += 10
        if token_data.get('is_open_source', '0') == '0':
            risk += 5
        
        # Tax risks (up to 15 points)
        buy_tax = float(token_data.get('buy_tax', '0'))
        sell_tax = float(token_data.get('sell_tax', '0'))
        if buy_tax > 0.1 or sell_tax > 0.1:  # > 10% tax
            risk += 15
        elif buy_tax > 0.05 or sell_tax > 0.05:  # > 5% tax
            risk += 10
        elif buy_tax > 0.02 or sell_tax > 0.02:  # > 2% tax
            risk += 5
        
        return min(risk, 100.0)
    
    def _determine_reputation(self, risk_score: float, is_honeypot: bool) -> str:
        """
        Determine reputation based on risk score.
        
        Args:
            risk_score: Calculated risk score
            is_honeypot: Whether token is a honeypot
            
        Returns:
            Reputation string: 'safe', 'warning', or 'danger'
        """
        if is_honeypot or risk_score >= 50:
            return 'danger'
        elif risk_score >= 25:
            return 'warning'
        else:
            return 'safe'
    
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

"""Tests for token filtering system."""
import pytest
from config.token_registry import TokenRegistry
from services.filtering.token_filter import TokenFilter, TokenCandidate


class TestTokenRegistry:
    """Test TokenRegistry functionality."""
    
    def test_is_major_token(self):
        """Test major token detection."""
        assert TokenRegistry.is_major_token("ETH") is True
        assert TokenRegistry.is_major_token("BTC") is True
        assert TokenRegistry.is_major_token("WETH") is True
        assert TokenRegistry.is_major_token("SMOON") is False
        assert TokenRegistry.is_major_token("UNKNOWN") is False
    
    def test_get_canonical_address(self):
        """Test canonical address retrieval."""
        eth_addr = TokenRegistry.get_canonical_address("ETH", "ethereum")
        assert eth_addr == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        
        btc_addr = TokenRegistry.get_canonical_address("BTC", "ethereum")
        assert btc_addr == "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
        
        # Test alias
        weth_addr = TokenRegistry.get_canonical_address("WETH", "ethereum")
        assert weth_addr == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    def test_should_filter_token_major(self):
        """Test filtering for major tokens."""
        # ETH with correct price - should pass
        should_filter, reason = TokenRegistry.should_filter_token("ETH", 3000.0, 400_000_000_000)
        assert should_filter is False
        
        # ETH with scam price - should filter
        should_filter, reason = TokenRegistry.should_filter_token("ETH", 0.002, 1000)
        assert should_filter is True
        assert "too low" in reason.lower()
    
    def test_should_filter_token_regular(self):
        """Test filtering for regular tokens."""
        # Valid token - should pass
        should_filter, reason = TokenRegistry.should_filter_token("SMOON", 0.00032, 316_000)
        assert should_filter is False
        
        # Token with low market cap but valid price - should pass (MIN_MARKET_CAP = 0)
        should_filter, reason = TokenRegistry.should_filter_token("SMOON", 0.00032, 100)
        assert should_filter is False
        
        # Token with price below minimum - should filter
        should_filter, reason = TokenRegistry.should_filter_token("SCAM", 0.0000001, 100)
        assert should_filter is True
        assert "price" in reason.lower()
    
    def test_detect_chain_context(self):
        """Test chain detection from message."""
        assert TokenRegistry.detect_chain_context("Buy on Uniswap") == "ethereum"
        assert TokenRegistry.detect_chain_context("Raydium pool live") == "solana"
        assert TokenRegistry.detect_chain_context("0x123abc...") == "ethereum"


class TestTokenFilter:
    """Test TokenFilter functionality."""
    
    def test_is_market_commentary(self):
        """Test market commentary detection."""
        filter = TokenFilter()
        
        # Market commentary - should be detected
        assert filter.is_market_commentary("ETH rally coming!", ["ETH"]) is True
        assert filter.is_market_commentary("BTC bullish trend", ["BTC"]) is True
        
        # Token call - should not be detected
        assert filter.is_market_commentary("Buy SMOON at 0x123...", ["SMOON"]) is False
        assert filter.is_market_commentary("ETH gem call", ["ETH"]) is False
    
    def test_should_skip_processing(self):
        """Test message skip logic."""
        filter = TokenFilter()
        
        # Market commentary - should skip
        should_skip, reason = filter.should_skip_processing("ETH rally coming!", ["ETH"])
        assert should_skip is True
        assert "commentary" in reason.lower()
        
        # Token call - should not skip
        should_skip, reason = filter.should_skip_processing("Buy SMOON at 0x123...", ["SMOON"])
        assert should_skip is False
    
    def test_filter_symbol_candidates_major_token(self):
        """Test filtering for major token candidates."""
        filter = TokenFilter()
        
        # Create candidates: 1 real ETH, 2 scams
        candidates = [
            TokenCandidate(
                address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                chain="ethereum",
                symbol="ETH",
                price_usd=3000.0,
                market_cap=400_000_000_000
            ),
            TokenCandidate(
                address="0xscam1",
                chain="ethereum",
                symbol="ETH",
                price_usd=0.002,
                market_cap=1000
            ),
            TokenCandidate(
                address="0xscam2",
                chain="solana",
                symbol="ETH",
                price_usd=0.00003,
                market_cap=500
            )
        ]
        
        # Filter - should only keep the real ETH
        filtered = filter.filter_symbol_candidates("ETH", candidates, "ETH rally")
        assert len(filtered) == 1
        assert filtered[0].address == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    def test_filter_symbol_candidates_regular_token(self):
        """Test filtering for regular token candidates."""
        filter = TokenFilter()
        
        # Create candidates: 1 valid, 1 with very low price
        candidates = [
            TokenCandidate(
                address="0xvalid",
                chain="ethereum",
                symbol="SMOON",
                price_usd=0.00032,
                market_cap=316_000
            ),
            TokenCandidate(
                address="0xscam",
                chain="ethereum",
                symbol="SMOON",
                price_usd=0.0000001,  # Below MIN_PRICE
                market_cap=100
            )
        ]
        
        # Filter - should only keep the valid token (scam has price below minimum)
        filtered = filter.filter_symbol_candidates("SMOON", candidates, "Buy SMOON")
        assert len(filtered) == 1
        assert filtered[0].address == "0xvalid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

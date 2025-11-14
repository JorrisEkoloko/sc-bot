"""
HDRB (Holistic Digital Reputation-Based) scorer.

Implements the IEEE research-compliant formula:
IC = forwards + (2 × reactions) + (0.5 × replies)
"""

from utils.logger import get_logger


class HDRBScorer:
    """
    HDRB (Holistic Digital Reputation-Based) scorer.
    
    Implements the research-based formula:
    IC = forwards + (2 × reactions) + (0.5 × replies)
    
    This formula is IEEE research-compliant and must not be modified.
    """
    
    def __init__(self, max_ic: float = 1000.0):
        """
        Initialize HDRB scorer.
        
        Args:
            max_ic: Maximum IC value for normalization (default: 1000.0)
        """
        self.max_ic = max_ic
        self.logger = get_logger('HDRBScorer')
        self.logger.info(f"HDRB scorer initialized with max_ic={max_ic}")
    
    def calculate_ic(self, forwards: int, reactions: int, replies: int) -> float:
        """
        Calculate Importance Coefficient using research formula.
        
        Formula: IC = forwards + (2 × reactions) + (0.5 × replies)
        
        Args:
            forwards: Number of message forwards
            reactions: Number of message reactions/likes
            replies: Number of message replies/comments
            
        Returns:
            Raw IC value
        """
        # Research formula - DO NOT MODIFY
        ic = forwards + (2.0 * reactions) + (0.5 * replies)
        
        self.logger.debug(
            f"IC calculated: forwards={forwards}, reactions={reactions}, "
            f"replies={replies} → IC={ic:.1f}"
        )
        
        return ic
    
    def normalize_score(self, ic: float) -> float:
        """
        Normalize IC to 0-100 range.
        
        Args:
            ic: Raw Importance Coefficient value
            
        Returns:
            Normalized score (0-100)
        """
        if ic <= 0:
            return 0.0
        
        # Normalize to 0-100 range
        normalized = min(100.0, (ic / self.max_ic) * 100.0)
        
        self.logger.debug(f"Score normalized: IC={ic:.1f} → {normalized:.2f}/100")
        
        return normalized
    
    def calculate_score(self, forwards: int, reactions: int, replies: int) -> dict:
        """
        Calculate complete HDRB score.
        
        Args:
            forwards: Number of message forwards
            reactions: Number of message reactions/likes
            replies: Number of message replies/comments
            
        Returns:
            Dictionary with 'raw_ic' and 'normalized_score'
        """
        try:
            # Calculate raw IC
            raw_ic = self.calculate_ic(forwards, reactions, replies)
            
            # Normalize to 0-100
            normalized = self.normalize_score(raw_ic)
            
            self.logger.info(
                f"HDRB score calculated: IC={raw_ic:.1f}, normalized={normalized:.2f}/100"
            )
            
            return {
                'raw_ic': raw_ic,
                'normalized_score': normalized
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating HDRB score: {e}")
            return {
                'raw_ic': 0.0,
                'normalized_score': 0.0
            }

"""
Few-shot Strategy Implementation (Stub)

Will be implemented in the future to support few-shot learning.
"""

from .zero_shot import ZeroShotStrategy
from .base import StrategyResult


class FewShotStrategy(ZeroShotStrategy):
    """Few-shot strategy (currently inherits from zero-shot)."""
    
    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "few-shot" 
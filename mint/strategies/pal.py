"""
Program-Aided Language Strategy Implementation (Stub)

Will be implemented in the future to support PAL approach.
"""

from .zero_shot import ZeroShotStrategy


class PALStrategy(ZeroShotStrategy):
    """Program-Aided Language strategy (currently inherits from zero-shot)."""
    
    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "pal" 
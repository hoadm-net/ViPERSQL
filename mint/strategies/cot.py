"""
Chain-of-Thought Strategy Implementation (Stub)

Will be implemented in the future to support CoT reasoning.
"""

from .zero_shot import ZeroShotStrategy


class CoTStrategy(ZeroShotStrategy):
    """Chain-of-Thought strategy (currently inherits from zero-shot)."""
    
    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "cot" 
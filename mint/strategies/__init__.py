"""
Strategy Implementations for ViPERSQL

Provides different approaches to Vietnamese Text-to-SQL conversion:
- Zero-shot: Direct conversion without examples
- Few-shot: Uses examples to guide conversion
- Chain-of-Thought (CoT): Step-by-step reasoning approach
"""

from .zero_shot import ZeroShotStrategy
from .few_shot import FewShotStrategy
from .cot import CoTStrategy

def create_strategy(strategy_name: str, config):
    """Factory function to create strategy instances."""
    if strategy_name == 'zero-shot':
        from .zero_shot import ZeroShotStrategy
        return ZeroShotStrategy(config)
    elif strategy_name == 'few-shot':
        from .few_shot import FewShotStrategy
        return FewShotStrategy(config)
    elif strategy_name == 'cot':
        from .cot import CoTStrategy
        return CoTStrategy(config)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

__all__ = [
    'ZeroShotStrategy',
    'FewShotStrategy',
    'CoTStrategy',
    'create_strategy'
]

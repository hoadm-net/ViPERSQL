"""
MINT - Modern Integration for Natural language Text-to-SQL

A comprehensive toolkit for Vietnamese Text-to-SQL conversion with support for
multiple strategies: Zero-shot, Few-shot, and Chain-of-Thought (CoT).

Core Components:
- LLM Interface: Unified interface for OpenAI and Anthropic models
- Template System: Flexible prompt template management
- Evaluation Engine: Comprehensive evaluation metrics with component-wise analysis
"""

# Core components
from .enhanced_metrics import EnhancedEvaluationMetrics
from .utils import load_dataset, normalize_sql, load_tables_info

# New unified components
try:
    from .config import ViPERConfig
    from .llm_interface import LLMInterface
    from .template_manager import TemplateManager

    # Strategy implementations
    from .strategies import (
        ZeroShotStrategy,
        FewShotStrategy, 
        CoTStrategy
    )
    
    # Evaluation
    from .evaluator import UnifiedEvaluator
except ImportError as e:
    print(f"Warning: Some MINT components failed to import: {e}")
    # Provide minimal fallbacks
    ViPERConfig = None
    LLMInterface = None

__version__ = "2.1.0"
__author__ = "ViPERSQL Research Team"

__all__ = [
    # Core components
    "EnhancedEvaluationMetrics",
    "load_dataset",
    "normalize_sql",
    "load_tables_info",

    # Unified components
    "ViPERConfig",
    "LLMInterface", 
    "TemplateManager",

    # Strategy implementations
    "ZeroShotStrategy",
    "FewShotStrategy",
    "CoTStrategy",
    
    # Evaluation
    "UnifiedEvaluator",

    # Convenience functions
    "create_strategy",
    "create_unified_system"
]

# Convenience imports for common usage patterns
def create_strategy(strategy_name: str = None, **kwargs):
    """
    Factory function to create strategy instances.
    
    Args:
        strategy_name: 'zero-shot', 'few-shot', or 'cot'
        **kwargs: Additional parameters for strategy initialization

    Returns:
        Strategy instance based on the selected strategy
    """
    if not strategy_name:
        strategy_name = "zero-shot"

    # Create a ViPERConfig from kwargs if not already provided
    if 'config' in kwargs:
        config = kwargs['config']
    else:
        config = ViPERConfig(**kwargs)

    # Normalize strategy name
    strategy_name = strategy_name.lower().replace("_", "-")

    if strategy_name == "zero-shot":
        return ZeroShotStrategy(config)
    elif strategy_name == "few-shot":
        return FewShotStrategy(config)
    elif strategy_name == "cot":
        return CoTStrategy(config)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

def create_unified_system(config: ViPERConfig):
    """
    Create a complete ViPERSQL system with all components.

    Args:
        config: ViPERConfig instance

    Returns:
        Tuple of (strategy, evaluator) instances
    """
    strategy = create_strategy(config.strategy, **config.to_dict())
    evaluator = UnifiedEvaluator(config)

    return strategy, evaluator

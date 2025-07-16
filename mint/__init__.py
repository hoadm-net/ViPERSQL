"""
MINT - Modern Integration for Natural language Text-to-SQL

A comprehensive toolkit for Vietnamese Text-to-SQL conversion with support for
multiple strategies: Zero-shot, Few-shot, Chain-of-Thought (CoT), and Program-Aided Language (PAL).

Core Components:
- Strategy Manager: Orchestrates different NL2SQL approaches
- LLM Interface: Unified interface for OpenAI and Anthropic models
- Template System: Flexible prompt template management
- Evaluation Engine: Comprehensive evaluation metrics
- Database Manager: SQLite database creation and management
"""

# Core components
from .database import SQLiteBuilder
from .executor import SQLExecutor  
from .metrics import EvaluationMetrics
from .utils import load_dataset, normalize_sql

# New unified components
try:
    from .config import ViPERConfig
    from .llm_interface import LLMInterface
    from .template_manager import TemplateManager
    from .strategy_manager import StrategyManager
    
    # Strategy implementations
    from .strategies import (
        ZeroShotStrategy,
        FewShotStrategy, 
        CoTStrategy,
        PALStrategy
    )
    
    # Evaluation and logging
    from .logger import ViPERLogger
    from .evaluator import UnifiedEvaluator
except ImportError as e:
    print(f"Warning: Some MINT components failed to import: {e}")
    # Provide minimal fallbacks
    ViPERConfig = None
    LLMInterface = None

__version__ = "2.0.0"
__author__ = "ViPERSQL Research Team"

__all__ = [
    # Legacy components (for backward compatibility)
    "SQLiteBuilder",
    "SQLExecutor", 
    "EvaluationMetrics",
    "load_dataset",
    "normalize_sql",
    
    # New unified components
    "ViPERConfig",
    "LLMInterface", 
    "TemplateManager",
    "StrategyManager",
    
    # Strategy implementations
    "ZeroShotStrategy",
    "FewShotStrategy",
    "CoTStrategy", 
    "PALStrategy",
    
    # Evaluation and logging
    "ViPERLogger",
    "UnifiedEvaluator"
]

# Convenience imports for common usage patterns
def create_strategy(strategy_name: str = None, **kwargs):
    """
    Factory function to create strategy instances.
    
    Args:
        strategy_name: 'zero-shot', 'few-shot', 'cot', or 'pal'
        **kwargs: Additional configuration parameters
        
    Returns:
        Strategy instance
    """
    config = ViPERConfig(**kwargs)
    strategy_name = strategy_name or config.default_strategy
    
    strategy_map = {
        'zero-shot': ZeroShotStrategy,
        'few-shot': FewShotStrategy,
        'cot': CoTStrategy,
        'pal': PALStrategy
    }
    
    if strategy_name not in strategy_map:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(strategy_map.keys())}")
    
    return strategy_map[strategy_name](config)

def create_unified_system(**kwargs):
    """
    Create a complete ViPERSQL system with all components.
    
    Returns:
        StrategyManager instance with all strategies loaded
    """
    config = ViPERConfig(**kwargs)
    return StrategyManager(config)

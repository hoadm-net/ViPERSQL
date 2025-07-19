"""
Strategy Manager for ViPERSQL

Orchestrates different NL2SQL strategies and provides unified interface.
"""

from typing import Dict, Any, List, Optional
from .config import ViPERConfig
from .strategies import (
    BaseStrategy, ZeroShotStrategy, FewShotStrategy,
    CoTStrategy
)

# Nếu có đường dẫn mặc định cho schema/dataset, chuyển sang std-level
DEFAULT_SCHEMA_PATH = 'dataset/ViText2SQL/std-level/tables.json'
DEFAULT_DATASET_PATH = 'dataset/ViText2SQL/std-level'


class StrategyManager:
    """Manages and orchestrates different NL2SQL strategies."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize strategy manager with configuration."""
        self.config = config
        self.strategies = self._initialize_strategies()
        self.current_strategy = self.strategies[config.strategy]
    
    def _initialize_strategies(self) -> Dict[str, BaseStrategy]:
        """Initialize all available strategies."""
        strategies = {}
        
        # Create instances of all strategies
        strategy_classes = {
            'zero-shot': ZeroShotStrategy,
            'few-shot': FewShotStrategy,
            'cot': CoTStrategy
        }
        
        for name, strategy_class in strategy_classes.items():
            try:
                # Create config for this specific strategy
                strategy_config = self.config.update(strategy=name)
                strategies[name] = strategy_class(strategy_config)
            except Exception as e:
                print(f"Warning: Failed to initialize {name} strategy: {e}")
        
        return strategies
    
    def get_strategy(self, strategy_name: str) -> BaseStrategy:
        """Get a specific strategy by name."""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return self.strategies[strategy_name]
    
    def set_strategy(self, strategy_name: str):
        """Set the current active strategy."""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        self.current_strategy = self.strategies[strategy_name]
        self.config = self.config.update(strategy=strategy_name)
    
    def generate_sql(
        self,
        question: str,
        schema_info: Dict[str, Any],
        db_id: str,
        strategy: Optional[str] = None,
        examples: Optional[List[Dict]] = None
    ):
        """Generate SQL using specified or current strategy."""
        if strategy:
            selected_strategy = self.get_strategy(strategy)
        else:
            selected_strategy = self.current_strategy
        
        return selected_strategy.generate_sql(
            question=question,
            schema_info=schema_info,
            db_id=db_id,
            examples=examples
        )
    
    def compare_strategies(
        self,
        question: str,
        schema_info: Dict[str, Any],
        db_id: str,
        strategies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare results from multiple strategies."""
        if strategies is None:
            strategies = list(self.strategies.keys())
        
        results = {}
        
        for strategy_name in strategies:
            if strategy_name in self.strategies:
                try:
                    result = self.strategies[strategy_name].generate_sql(
                        question, schema_info, db_id
                    )
                    results[strategy_name] = result
                except Exception as e:
                    results[strategy_name] = {
                        'error': str(e),
                        'strategy': strategy_name
                    }
        
        return results
    
    def list_strategies(self) -> List[str]:
        """List all available strategies."""
        return list(self.strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """Get information about a specific strategy."""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy = self.strategies[strategy_name]
        return {
            'name': strategy_name,
            'class': strategy.__class__.__name__,
            'strategy_name': strategy.strategy_name,
            'config': strategy.config.to_dict()
        } 
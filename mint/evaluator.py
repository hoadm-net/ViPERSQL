"""
Unified Evaluator for ViPERSQL

Provides evaluation functionality for all strategies.
"""

from typing import Dict, Any, List
from .config import ViPERConfig
from .metrics import EvaluationMetrics


class UnifiedEvaluator:
    """Unified evaluator for all strategies."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize evaluator with configuration."""
        self.config = config
        self.metrics = EvaluationMetrics()
    
    def evaluate_single(
        self,
        predicted_sql: str,
        gold_sql: str,
        db_id: str,
        request_id: str
    ) -> Dict[str, Any]:
        """Evaluate a single prediction."""
        # Basic evaluation
        exact_match = self._exact_match(predicted_sql, gold_sql)
        syntax_valid = self._validate_syntax(predicted_sql)
        
        result = {
            'exact_match': exact_match,
            'syntax_valid': syntax_valid,
            'request_id': request_id
        }
        
        # Add execution accuracy if enabled
        if self.config.enable_execution_accuracy:
            result['execution_accuracy'] = self._execution_accuracy(
                predicted_sql, gold_sql, db_id
            )
        
        return result
    
    def calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not results:
            return {'total_samples': 0}
        
        valid_results = [r for r in results if 'error' not in r]
        total = len(valid_results)
        
        if total == 0:
            return {
                'total_samples': len(results),
                'errors': len(results)
            }
        
        # Calculate basic metrics
        exact_matches = sum(
            1 for r in valid_results 
            if r.get('evaluation', {}).get('exact_match', False)
        )
        syntax_valid = sum(
            1 for r in valid_results
            if r.get('evaluation', {}).get('syntax_valid', False)
        )
        
        summary = {
            'total_samples': len(results),
            'valid_results': total,
            'exact_match_accuracy': (exact_matches / total) * 100,
            'syntax_validity': (syntax_valid / total) * 100,
            'errors': len(results) - total
        }
        
        # Add execution accuracy if available
        execution_accurate = sum(
            1 for r in valid_results
            if r.get('evaluation', {}).get('execution_accuracy', False)
        )
        summary['execution_accuracy'] = (execution_accurate / total) * 100
        
        return summary
    
    def _exact_match(self, predicted: str, gold: str) -> bool:
        """Check exact match after normalization."""
        def normalize(sql):
            sql = sql.strip().lower()
            sql = ' '.join(sql.split())
            return sql
        
        return normalize(predicted) == normalize(gold)
    
    def _validate_syntax(self, sql: str) -> bool:
        """Validate SQL syntax."""
        try:
            import sqlparse
            parsed = sqlparse.parse(sql)
            return len(parsed) > 0
        except:
            return False
    
    def _execution_accuracy(self, predicted: str, gold: str, db_id: str) -> bool:
        """Check execution accuracy (simplified)."""
        # This would require database execution
        # For now, return False as placeholder
        return False 
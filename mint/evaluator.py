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
        request_id: str,
        schema_path: str = None
    ) -> Dict[str, Any]:
        """Evaluate a single prediction."""
        # Basic evaluation
        exact_match = self._exact_match(predicted_sql, gold_sql)
        syntax_valid = self._validate_syntax(predicted_sql)
        # Component-wise F1e for single query
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'
        component_f1 = self.metrics.component_wise_f1_score([predicted_sql], [gold_sql], [db_id], schema_path)
        result = {
            'exact_match': exact_match,
            'syntax_valid': syntax_valid,
            'component_f1_scores': component_f1,
            'request_id': request_id
        }
        return result
    
    def calculate_summary(self, results: List[Dict[str, Any]], schema_path: str = None) -> Dict[str, Any]:
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
        # Component F1-score
        predicted_queries = [r['predicted_sql'] for r in valid_results]
        gold_queries = [r['gold_sql'] for r in valid_results]
        db_ids = [r['db_id'] for r in valid_results]
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'
        component_f1_scores = self.metrics.component_wise_f1_score(predicted_queries, gold_queries, db_ids, schema_path)
        # Calculate average F1 across all components
        avg_component_f1 = sum(component_f1_scores.values()) / len(component_f1_scores) if component_f1_scores else 0.0  
        summary = {
            'total_samples': len(results),
            'valid_results': total,
            'exact_match_accuracy': (exact_matches / total) * 100,
            'component_f1_scores': component_f1_scores,
            'avg_component_f1_score': avg_component_f1 * 100,
            'syntax_validity': (syntax_valid / total) * 100,
            'errors': len(results) - total
        }
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
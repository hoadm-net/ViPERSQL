"""
Unified Evaluator for ViPERSQL

Provides evaluation functionality for all strategies.
Uses enhanced evaluation metrics for better analysis.
"""

from typing import Dict, Any, List, Optional
from .config import ViPERConfig
from .enhanced_metrics import EnhancedEvaluationMetrics
import re
import json
import os
from datetime import datetime


class UnifiedEvaluator:
    """Unified evaluator for all strategies using enhanced metrics."""

    def __init__(self, config: ViPERConfig):
        """Initialize evaluator with configuration."""
        self.config = config
        self.metrics = EnhancedEvaluationMetrics()

    def evaluate_single(
        self,
        predicted_sql: str,
        gold_sql: str,
        db_id: str,
        request_id: str,
        schema_path: str = None
    ) -> Dict[str, Any]:
        """Evaluate a single prediction with enhanced metrics."""
        # Normalize predicted SQL
        predicted_sql = self._normalize_sql_query(predicted_sql)

        # Basic evaluation
        exact_match = self._exact_match(predicted_sql, gold_sql)
        syntax_valid = self._validate_syntax(predicted_sql)
        
        # Enhanced component analysis
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'

        # Get component F1 scores
        component_f1 = self.metrics.component_wise_f1_score(
            [predicted_sql], [gold_sql], [db_id], schema_path
        )

        # Error analysis
        error_analysis = self.metrics.analyze_errors([predicted_sql], [gold_sql])

        # Query complexity
        query_complexity = self.metrics.difficulty_classifier.classify_query(gold_sql)

        # Create details object
        details = {
            'exact_match': exact_match,
            'syntax_valid': syntax_valid,
            'component_f1': component_f1,
            'error_analysis': error_analysis,
            'query_complexity': query_complexity
        }

        return {
            'request_id': request_id,
            'db_id': db_id,
            'predicted_sql': predicted_sql,
            'gold_sql': gold_sql,
            'exact_match': exact_match,
            'syntax_valid': syntax_valid,
            'avg_f1': component_f1['avg_f1'],
            'f1_scores': component_f1['f1_scores'],
            'details': details
        }

    def evaluate_batch(
        self,
        predictions: List[Dict[str, Any]],
        schema_path: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate a batch of predictions with enhanced metrics.

        Args:
            predictions: List of prediction objects with 'predicted', 'gold', 'db_id'
            schema_path: Path to the schema definition

        Returns:
            Dict with evaluation metrics
        """
        if not predictions:
            return {'error': 'No predictions to evaluate'}

        # Extract prediction components
        predicted_queries = [p['predicted'] for p in predictions]
        gold_queries = [p['gold'] for p in predictions]
        db_ids = [p['db_id'] for p in predictions]

        # Set default schema path if not provided
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'

        # Run comprehensive evaluation
        evaluation_results = self.metrics.comprehensive_evaluation(
            predicted_queries=predicted_queries,
            gold_queries=gold_queries,
            db_ids=db_ids,
            schema_path=schema_path
        )

        # Add configuration metadata to results
        evaluation_results['experiment_config'] = {
            'model_name': self.config.model_name,
            'strategy': self.config.strategy,
            'level': self.config.level,
            'split': self.config.split,
            'num_samples': len(predictions),
            'timestamp': datetime.now().isoformat(),
            'schema_path': schema_path
        }

        # Add raw predictions to results
        evaluation_results['predictions'] = predictions

        return evaluation_results

    def generate_report(self, evaluation_results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Generate human-readable report and save results to file.

        Args:
            evaluation_results: Results from evaluate_batch
            output_dir: Directory to save reports

        Returns:
            Dict with paths to saved files
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw results
        json_path = os.path.join(output_dir, f"eval_results_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, indent=2, ensure_ascii=False)

        # Generate human-readable report
        exact_match = evaluation_results['exact_match']
        component_f1 = evaluation_results['component_f1']
        difficulty_analysis = evaluation_results['difficulty_analysis']
        error_analysis = evaluation_results['error_analysis']

        # Format report
        report = []
        report.append("=" * 80)
        report.append("📊 EVALUATION REPORT")
        report.append("=" * 80)

        # Add experiment configuration info
        config = evaluation_results.get('experiment_config', {})
        if config:
            report.append(f"🤖 Model: {config.get('model_name', 'Unknown')}")
            report.append(f"🎯 Strategy: {config.get('strategy', 'Unknown').upper()}")
            report.append(f"📊 Dataset: {config.get('level', 'Unknown')}-level, {config.get('split', 'Unknown')} split")
            report.append(f"📅 Timestamp: {config.get('timestamp', 'Unknown')}")
            report.append("=" * 80)

        total_queries = exact_match['total_queries']
        report.append(f"Total Samples: {total_queries}")
        report.append(f"Valid Results: {total_queries}")
        report.append(f"Exact Match Accuracy: {exact_match['em_accuracy']*100:.2f}%")

        # Calculate syntax validity
        syntax_error_rate = error_analysis.get('syntax_errors', {}).get('percentage', 0)
        syntax_validity = 100 - syntax_error_rate
        report.append(f"Syntax Validity: {syntax_validity:.2f}%")

        avg_f1 = component_f1['avg_f1'] * 100
        report.append(f"Overall F1 Score: {avg_f1:.2f}%")

        report.append("\n" + "-" * 40)
        report.append("COMPONENT-WISE SCORES")
        report.append("-" * 40)

        # Component scores table header
        report.append(f"{'Component':<15} {'F1 Score':<10} {'Precision':<12} {'Recall':<12}")
        report.append("-" * 50)

        # Component scores table rows
        f1_scores = component_f1['f1_scores']
        precision_scores = component_f1['precision_scores']
        recall_scores = component_f1['recall_scores']

        for component, f1 in f1_scores.items():
            precision = precision_scores[component]
            recall = recall_scores[component]
            report.append(f"{component:<15} {f1*100:>8.2f}% {precision*100:>10.2f}% {recall*100:>10.2f}%")

        report.append("\n" + "-" * 40)
        report.append("QUERY COMPLEXITY DISTRIBUTION")
        report.append("-" * 40)

        # Query complexity distribution
        distribution = difficulty_analysis['distribution']
        for complexity, stats in distribution.items():
            count = stats['count']
            percentage = stats['percentage']
            report.append(f"{complexity:<12}: {count:>5} queries ({percentage:.2f}%)")

        report.append("\n" + "-" * 40)
        report.append("ERROR ANALYSIS")
        report.append("-" * 40)

        # Error statistics
        syntax_errors = error_analysis.get('syntax_errors', {}).get('count', 0)
        semantic_errors = error_analysis.get('semantic_errors', {}).get('count', 0)
        total_errors = syntax_errors + semantic_errors

        report.append(f"Syntax Error Rate: {syntax_error_rate:.2f}%")
        report.append(f"Semantic Error Rate: {semantic_errors/total_queries*100 if total_queries else 0:.2f}%")
        report.append(f"Total Queries with Errors: {total_errors}")

        report.append("\nComponent Error Distribution:")
        for error_type, stats in error_analysis.items():
            if error_type not in ['syntax_errors', 'semantic_errors']:
                count = stats.get('count', 0)
                if count > 0:
                    report.append(f"  - {error_type}: {count} queries ({stats.get('percentage', 0):.2f}%)")

        # Save report
        report_path = os.path.join(output_dir, f"eval_report_{timestamp}.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))

        return {
            'report_path': report_path,
            'json_path': json_path
        }

    def _normalize_sql_query(self, sql: str) -> str:
        """Normalize SQL query for evaluation."""
        if not sql:
            return ""

        # Basic normalization
        sql = sql.strip()

        return sql

    def _exact_match(self, predicted: str, gold: str) -> bool:
        """Check if predicted SQL exactly matches gold SQL."""
        if not predicted or not gold:
            return False

        # Normalize before comparison
        pred_norm = self.metrics._normalize_sql_comprehensive(predicted)
        gold_norm = self.metrics._normalize_sql_comprehensive(gold)

        return pred_norm == gold_norm

    def _validate_syntax(self, sql: str) -> bool:
        """Validate SQL syntax."""
        return self.metrics._is_valid_sql(sql)

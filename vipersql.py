#!/usr/bin/env python3
"""
ViPERSQL - Unified Vietnamese Text-to-SQL CLI Tool
===================================================

A unified command-line interface for Vietnamese Text-to-SQL conversion
supporting multiple strategies: Zero-shot, Few-shot, and Chain-of-Thought (CoT).

Usage:
    # Zero-shot strategy (default)
    python vipersql.py --samples 10
    
    # Few-shot strategy with examples
    python vipersql.py --strategy few-shot --samples 10
    
    # Chain-of-thought reasoning
    python vipersql.py --strategy cot --samples 5
    
    # Different models and datasets
    python vipersql.py --model claude-3-sonnet --split test --samples 20
    
    # Custom configuration
    python vipersql.py --config custom.env --strategy cot
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import MINT components with updated structure
from mint import (
    ViPERConfig, 
    create_strategy, 
    load_dataset,
    load_tables_info
)
from mint.core import UnifiedEvaluator
from mint.constants import (
    SEPARATOR_LENGTH, LONG_SEPARATOR_LENGTH,
    QUESTION_PREVIEW_LENGTH, SQL_PREVIEW_LENGTH,
    INTERMEDIATE_SAVE_INTERVAL
)


class ViPERSQLCLI:
    """
    Unified CLI for ViPERSQL system.
    
    Provides a single entry point for all Vietnamese NL2SQL operations
    with support for multiple strategies and comprehensive evaluation.
    """
    
    def __init__(self, config: ViPERConfig):
        """Initialize CLI with configuration."""
        self.config = config
        self.strategy = create_strategy(config.strategy, config)
        self.evaluator = UnifiedEvaluator(config)
        
        print("🚀 ViPERSQL - Vietnamese Text-to-SQL System")
        print("=" * SEPARATOR_LENGTH)

    def run_evaluation(self) -> Dict[str, Any]:
        """Run evaluation with simple sequential processing."""
        print(f"🚀 Starting ViPERSQL Evaluation")
        print(f"Strategy: {self.config.strategy.upper()}")
        print(f"Model: {self.config.model_name}")
        print(f"Dataset: ViText2SQL {self.config.level}-level, {self.config.split} split")
        print(f"Samples: {self.config.num_samples or 'all'}")
        print("=" * SEPARATOR_LENGTH)

        start_time = time.time()

        # Load ViText2SQL dataset with correct parameters
        dataset = load_dataset(
            dataset_name="vitext2sql",
            split=self.config.split,
            level=self.config.level
        )

        # Apply num_samples limit if specified
        if self.config.num_samples:
            dataset = dataset[:self.config.num_samples]

        # Load tables info for schema information
        tables_info = load_tables_info(
            dataset_name="vitext2sql",
            level=self.config.level
        )

        # Create output directory with strategy-specific naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        samples_suffix = f"{len(dataset)}" if self.config.num_samples is None else str(self.config.num_samples)

        # Add example selection strategy to folder name for few-shot and CoT
        strategy_suffix = self.config.strategy
        if self.config.strategy == 'few-shot':
            example_strategy = getattr(self.config, 'example_selection_strategy', 'random')
            strategy_suffix = f"few-shot-{example_strategy}"
        elif self.config.strategy == 'cot':
            # Include CoT examples info if enabled
            if getattr(self.config, 'cot_include_examples', False):
                cot_selection = getattr(self.config, 'cot_selection_strategy', 'random')
                cot_k = getattr(self.config, 'cot_examples', 2)
                strategy_suffix = f"cot-{cot_selection}-{cot_k}ex"
            else:
                strategy_suffix = "cot"

        output_dir = f"results/vitext2sql_{strategy_suffix}_{samples_suffix}_{timestamp}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize results
        results = []

        print(f"Processing {len(dataset)} samples sequentially...")

        # Simple sequential processing - no batches needed
        for i, item in enumerate(dataset, 1):
            db_id = item['db_id']
            question = item['question']
            gold_sql = item.get('query', '')

            # Get database schema for the given db_id
            db_schema = tables_info.get(db_id, {})

            # Generate SQL from natural language
            print(f"[{i}/{len(dataset)}] Processing: {question[:QUESTION_PREVIEW_LENGTH]}...")
            try:
                predicted_sql = self.strategy.generate_sql(question, db_schema, db_id)

                # Extract SQL string from result if it's a StrategyResult object
                if hasattr(predicted_sql, 'sql_query'):
                    predicted_sql = predicted_sql.sql_query

                # Add to results
                results.append({
                    'db_id': db_id,
                    'question': question,
                    'predicted': predicted_sql,
                    'gold': gold_sql
                })

                print(f"✓ Generated SQL: {predicted_sql[:SQL_PREVIEW_LENGTH]}...")

            except Exception as e:
                print(f"✗ Error generating SQL: {e}")
                results.append({
                    'db_id': db_id,
                    'question': question,
                    'predicted': "",
                    'gold': gold_sql,
                    'error': str(e)
                })

            # Save intermediate results every 10 samples
            if i % INTERMEDIATE_SAVE_INTERVAL == 0:
                intermediate_path = os.path.join(output_dir, f"intermediate_results_{i}.json")
                with open(intermediate_path, 'w', encoding='utf-8') as f:
                    json.dump({'predictions': results}, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved intermediate results ({i} samples)")

        # Save final predictions
        predictions_path = os.path.join(output_dir, 'predictions.json')
        with open(predictions_path, 'w', encoding='utf-8') as f:
            json.dump({'predictions': results}, f, indent=2, ensure_ascii=False)

        print(f"✅ SQL Generation completed in {time.time() - start_time:.2f} seconds")
        print(f"✅ Generated {len(results)} predictions")
        print(f"✅ Results saved to: {predictions_path}")

        # Now run enhanced evaluation
        print("\n🔍 Starting Enhanced Evaluation...")
        evaluation_start = time.time()
        evaluation_results = None

        try:
            evaluation_results = self.evaluator.evaluate_batch(
                results,
                schema_path=f"dataset/ViText2SQL/{self.config.level}-level/tables.json"
            )

            # Add timing information to evaluation results
            sql_generation_time = evaluation_start - start_time
            evaluation_time = time.time() - evaluation_start
            total_time = time.time() - start_time

            # Add timing and config info to evaluation results
            evaluation_results['timing_info'] = {
                'sql_generation_time': sql_generation_time,
                'evaluation_time': evaluation_time,
                'total_execution_time': total_time,
                'start_time': datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Add experiment configuration
            evaluation_results['experiment_config'] = {
                'model_name': self.config.model_name,
                'strategy': self.config.strategy,
                'level': self.config.level,
                'split': self.config.split,
                'num_samples': len(dataset),
                'example_selection_strategy': getattr(self.config, 'example_selection_strategy', 'N/A'),
                'cot_include_examples': getattr(self.config, 'cot_include_examples', False),
                'cot_examples': getattr(self.config, 'cot_examples', 0) if getattr(self.config, 'cot_include_examples', False) else 'N/A',
                'cot_selection_strategy': getattr(self.config, 'cot_selection_strategy', 'N/A') if getattr(self.config, 'cot_include_examples', False) else 'N/A',
                'timestamp': timestamp
            }

            # Generate and save enhanced report
            report_files = self.evaluator.generate_report(evaluation_results, output_dir)

            evaluation_time = time.time() - evaluation_start
            print(f"✅ Enhanced Evaluation completed in {evaluation_time:.2f} seconds")
            print(f"📊 Report saved to: {report_files.get('report_path', 'N/A')}")

            # Print summary metrics
            self._print_evaluation_summary(evaluation_results)

        except Exception as e:
            print(f"⚠️ Enhanced evaluation failed: {str(e)}")
            print("💾 SQL predictions have been saved successfully")

        elapsed_time = time.time() - start_time
        return {
            'predictions': results,
            'evaluation': evaluation_results,
            'total_time': elapsed_time
        }

    def _print_evaluation_summary(self, evaluation_results: Dict[str, Any]):
        """Print enhanced evaluation summary."""
        print("\n" + "=" * LONG_SEPARATOR_LENGTH)
        print("📊 ENHANCED EVALUATION SUMMARY")
        print("=" * LONG_SEPARATOR_LENGTH)
        print(f"🤖 Model: {self.config.model_name}")
        print(f"🎯 Strategy: {self.config.strategy.upper()}")

        # Get results directly (not under 'comprehensive_evaluation')
        comprehensive = evaluation_results

        # Exact Match Results
        em_results = comprehensive.get('exact_match', {})
        print(f"🎯 Exact Match Accuracy: {em_results.get('em_accuracy', 0)*100:.2f}%")
        print(f"   Total Queries: {em_results.get('total_queries', 0)}")
        print(f"   Exact Matches: {em_results.get('exact_matches', 0)}")

        # Component F1 Results
        f1_results = comprehensive.get('component_f1', {})
        f1_scores = f1_results.get('f1_scores', {})

        print(f"\n🔍 COMPONENT-WISE F1 SCORES:")
        print("-" * 50)
        for component, score in f1_scores.items():
            print(f"  {component:12}: {score*100:6.2f}%")

        # Calculate and show overall average F1
        if f1_scores:
            overall_avg = sum(f1_scores.values()) / len(f1_scores)
            print(f"  {'Overall F1':12}: {overall_avg*100:6.2f}%")

        print(f"\n💾 For detailed precision & recall scores, check the saved JSON report.")
        print("=" * LONG_SEPARATOR_LENGTH)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='ViPERSQL - Vietnamese Text-to-SQL System')

    # Basic configuration
    parser.add_argument('--strategy', type=str, default='zero-shot',
                        choices=['zero-shot', 'few-shot', 'cot'],
                        help='Strategy to use for text-to-SQL generation')

    parser.add_argument('--model', type=str, default=None,
                        help='LLM model to use (defaults to DEFAULT_MODEL from .env)')

    parser.add_argument('--level', type=str, default='std',
                        choices=['std', 'syllable', 'word'],
                        help='Level of Vietnamese text segmentation')

    parser.add_argument('--split', type=str, default='test',
                        choices=['train', 'dev', 'test'],
                        help='Dataset split to use')

    parser.add_argument('--samples', type=int, default=None,
                        help='Number of samples to process (default: all)')

    parser.add_argument('--example-selection-strategy', type=str, default='random',
                        choices=['random', 'skill_knn', 'dicl', 'astres', 'vir2', 'vir2-no-pos', 'vir2-no-diversity', 'vir2-no-beam-search'],
                        help='Example selection strategy for few-shot (random, skill_knn, dicl, astres, vir2, vir2-no-pos, vir2-no-diversity, or vir2-no-beam-search)')

    # CoT-specific arguments
    parser.add_argument('--cot-include-examples', action='store_true',
                        help='Include examples in CoT reasoning')
    
    parser.add_argument('--cot-examples', type=int, default=2,
                        help='Number of examples for CoT (default: 2)')
    
    parser.add_argument('--cot-selection-strategy', type=str, default='random',
                        choices=['random', 'skill_knn', 'dicl', 'astres', 'vir2', 'vir2-no-pos', 'vir2-no-diversity', 'vir2-no-beam-search'],
                        help='Example selection strategy for CoT (random, skill_knn, dicl, astres, vir2, etc.)')

    parser.add_argument('--config', type=str, default='.env',
                        help='Path to configuration file')

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Load configuration
    config_params = {}
    # Always set num_samples explicitly to avoid string/int conversion issues
    config_params['num_samples'] = args.samples  # This will be None if not provided

    # Only pass model_name if it's explicitly provided by user
    if args.model is not None:
        config_params['model_name'] = args.model

    # Pass example selection strategy for few-shot
    config_params['example_selection_strategy'] = args.example_selection_strategy
    
    # Pass CoT-specific parameters
    config_params['cot_include_examples'] = args.cot_include_examples
    config_params['cot_examples'] = args.cot_examples
    config_params['cot_selection_strategy'] = args.cot_selection_strategy

    config = ViPERConfig(
        strategy=args.strategy,
        level=args.level,
        split=args.split,
        **config_params
    )

    # Create and run CLI
    cli = ViPERSQLCLI(config)
    cli.run_evaluation()


if __name__ == '__main__':
    main()

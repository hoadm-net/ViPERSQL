#!/usr/bin/env python3
"""
Configuration and Setup Script for ViPERSQL Zero-shot NL2SQL
============================================================

This script helps users configure and run the Zero-shot NL2SQL system
with different models and evaluation settings.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

from zeroshot_nl2sql import VietnameseNL2SQL, NL2SQLEvaluator
from sample_viewer import load_dataset, load_tables

class NL2SQLRunner:
    """Runner class for batch processing and evaluation."""
    
    def __init__(self, model_name: str, dataset_path: str, level: str = "syllable"):
        self.model_name = model_name
        self.dataset_path = dataset_path
        self.level = level
        self.nl2sql = VietnameseNL2SQL(model_name)
        self.evaluator = NL2SQLEvaluator(self.nl2sql.logger)
        
    def run_evaluation(self, split: str = "dev", num_samples: int = 10) -> Dict:
        """Run evaluation on a dataset split."""
        print(f"🔄 Running evaluation on {split} split with {num_samples} samples")
        print(f"📊 Model: {self.model_name}")
        print(f"📁 Dataset: {self.dataset_path}/{self.level}-level")
        print("=" * 60)
        
        # Load data
        dataset_level_path = f"{self.dataset_path}/{self.level}-level"
        data = load_dataset(dataset_level_path, split)
        tables = load_tables(dataset_level_path)
        
        # Limit samples if specified
        if num_samples > 0:
            data = data[:num_samples]
        
        print(f"✅ Loaded {len(data)} samples from {split} split")
        
        results = []
        success_count = 0
        
        for i, sample in enumerate(data):
            print(f"\n📝 Processing {i+1}/{len(data)}: {sample['db_id']}")
            
            # Get schema
            schema_info = tables.get(sample['db_id'])
            if not schema_info:
                print(f"❌ Schema not found for {sample['db_id']}")
                continue
            
            try:
                # Generate SQL
                predicted_sql, request_id = self.nl2sql.generate_sql(
                    sample['question'], schema_info, sample['db_id']
                )
                
                # Evaluate
                db_path = f"sqlite_dbs/{self.level}-level/{sample['db_id']}.sqlite"
                metrics = self.evaluator.evaluate_prediction(
                    request_id, predicted_sql, sample['query'], db_path
                )
                
                metrics.update({
                    'sample_index': i,
                    'db_id': sample['db_id'],
                    'question': sample['question']
                })
                
                results.append(metrics)
                
                if metrics['exact_match']:
                    success_count += 1
                    print(f"✅ Exact match!")
                elif metrics['execution_accuracy']:
                    print(f"🟡 Execution accurate but different syntax")
                elif metrics['sql_syntax_valid']:
                    print(f"🟠 Valid SQL but incorrect result")
                else:
                    print(f"❌ Invalid SQL generated")
                    
            except Exception as e:
                print(f"❌ Error processing sample: {e}")
                continue
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        # Save results
        results_file = f"results/{self.model_name}_{split}_{self.level}_{len(results)}samples.json"
        Path("results").mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'config': {
                    'model': self.model_name,
                    'split': split,
                    'level': self.level,
                    'num_samples': len(results)
                },
                'summary': summary,
                'detailed_results': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 EVALUATION SUMMARY")
        print("=" * 40)
        for metric, value in summary.items():
            if isinstance(value, float):
                print(f"{metric}: {value:.2f}%")
            else:
                print(f"{metric}: {value}")
        
        print(f"\n💾 Results saved to: {results_file}")
        return summary
    
    def _calculate_summary(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics from results."""
        if not results:
            return {}
        
        total = len(results)
        
        summary = {
            'total_samples': total,
            'exact_match_accuracy': sum(1 for r in results if r.get('exact_match', False)) / total * 100,
            'execution_accuracy': sum(1 for r in results if r.get('execution_accuracy', False)) / total * 100,
            'syntax_validity': sum(1 for r in results if r.get('sql_syntax_valid', False)) / total * 100,
            'average_response_time': 0  # Would need to track this separately
        }
        
        # Component accuracy
        component_stats = {}
        for component in ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']:
            correct = sum(1 for r in results 
                         if r.get('component_accuracy', {}).get(component, False))
            total_with_component = sum(1 for r in results 
                                     if component in r.get('component_accuracy', {}))
            if total_with_component > 0:
                component_stats[f'{component.lower()}_accuracy'] = correct / total_with_component * 100
        
        summary.update(component_stats)
        
        return summary

def main():
    parser = argparse.ArgumentParser(
        description="ViPERSQL Zero-shot NL2SQL Evaluation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with GPT-4 on dev set
  python config_nl2sql.py --model gpt-4o-mini --split dev --samples 20
  
  # Run with Claude on test set
  python config_nl2sql.py --model claude-3-haiku-20240307 --split test --samples 50
  
  # Full evaluation on train set
  python config_nl2sql.py --model gpt-4o --split train --samples -1
        """
    )
    
    parser.add_argument(
        '--model', '-m',
        default='gpt-4o-mini',
        help='Model to use (gpt-4o-mini, gpt-4o, claude-3-haiku-20240307, etc.)'
    )
    
    parser.add_argument(
        '--split', '-s',
        choices=['train', 'dev', 'test'],
        default='dev',
        help='Dataset split to evaluate on'
    )
    
    parser.add_argument(
        '--samples', '-n',
        type=int,
        default=10,
        help='Number of samples to evaluate (-1 for all)'
    )
    
    parser.add_argument(
        '--level', '-l',
        choices=['syllable', 'word'],
        default='syllable',
        help='Tokenization level'
    )
    
    parser.add_argument(
        '--dataset-path',
        default='dataset/ViText2SQL',
        help='Path to ViText2SQL dataset'
    )
    
    args = parser.parse_args()
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: No API keys found in environment!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        return
    
    if 'gpt' in args.model.lower() and not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OpenAI API key required for GPT models")
        return
    
    if 'claude' in args.model.lower() and not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: Anthropic API key required for Claude models")
        return
    
    # Run evaluation
    try:
        runner = NL2SQLRunner(args.model, args.dataset_path, args.level)
        summary = runner.run_evaluation(args.split, args.samples)
        
        print(f"\n🎉 Evaluation completed successfully!")
        print(f"📈 Overall accuracy: {summary.get('exact_match_accuracy', 0):.1f}%")
        
    except FileNotFoundError as e:
        print(f"❌ Dataset not found: {e}")
        print("Please ensure the ViText2SQL dataset is properly loaded")
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
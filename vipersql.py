#!/usr/bin/env python3
"""
ViPERSQL - Unified Vietnamese Text-to-SQL CLI Tool
===================================================

A unified command-line interface for Vietnamese Text-to-SQL conversion
supporting multiple strategies: Zero-shot, Few-shot, Chain-of-Thought (CoT), 
and Program-Aided Language (PAL).

Usage:
    # Zero-shot strategy (default)
    python vipersql.py --samples 10
    
    # Few-shot strategy with examples
    python vipersql.py --strategy few-shot --samples 10
    
    # Chain-of-Thought reasoning
    python vipersql.py --strategy cot --samples 5
    
    # Different models and datasets
    python vipersql.py --model claude-3-sonnet --split test --samples 20
    
    # Custom configuration
    python vipersql.py --config custom.env --strategy pal
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import MINT components
from mint import (
    ViPERConfig, 
    create_strategy, 
    create_unified_system,
    load_dataset,
    SQLiteBuilder,
    UnifiedEvaluator
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
        self.strategy = create_strategy(config.strategy, **config.to_dict())
        self.evaluator = UnifiedEvaluator(config)
        
        print("🚀 ViPERSQL - Vietnamese Text-to-SQL System")
        print("=" * 60)
        print(f"📊 Strategy: {config.strategy.upper()}")
        print(f"🧠 Model: {config.model_name}")
        print(f"📁 Dataset: {config.dataset_full_path}")
        print(f"📝 Template: {config.template_path}")
        print("=" * 60)
    
    def run_single_query(self, question: str, schema_info: Dict, db_id: str):
        """Run a single query for testing."""
        print(f"\n🔍 Single Query Test")
        print(f"Question: {question}")
        print(f"Database: {db_id}")
        
        result = self.strategy.generate_sql(question, schema_info, db_id)
        
        print(f"Generated SQL: {result.sql_query}")
        print(f"Confidence: {result.confidence_score:.2f}")
        if result.reasoning:
            print(f"Reasoning: {result.reasoning}")
        
        return result
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run evaluation on dataset."""
        print(f"\n📊 Running Evaluation")
        print(f"Split: {self.config.split}")
        print(f"Samples: {self.config.samples}")
        print(f"Level: {self.config.level}")
        
        # Load dataset
        dataset_file = Path(self.config.dataset_full_path) / f"{self.config.split}.json"
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_file}")
        
        print(f"📁 Loading dataset from: {dataset_file}")
        dataset = load_dataset(str(dataset_file))
        
        # Load tables schema
        tables_file = Path(self.config.dataset_full_path) / "tables.json"
        if not tables_file.exists():
            raise FileNotFoundError(f"Tables file not found: {tables_file}")
        
        with open(tables_file, 'r', encoding='utf-8') as f:
            tables_list = json.load(f)
        tables_info = {table['db_id']: table for table in tables_list}
        
        # Limit samples if specified
        if self.config.samples > 0:
            dataset = dataset[:self.config.samples]
        
        print(f"✅ Loaded {len(dataset)} samples")
        
        # Process samples
        results = []
        start_time = time.time()
        
        for i, sample in enumerate(dataset, 1):
            print(f"\n📝 Processing {i}/{len(dataset)}: {sample['db_id']}")
            
            # Get schema info
            schema_info = tables_info.get(sample['db_id'])
            if not schema_info:
                print(f"❌ Schema not found for {sample['db_id']}")
                continue
            
            # Generate SQL
            try:
                result = self.strategy.generate_sql(
                    sample['question'], 
                    schema_info, 
                    sample['db_id']
                )
                
                # Evaluate result
                evaluation = self.evaluator.evaluate_single(
                    predicted_sql=result.sql_query,
                    gold_sql=sample.get('query', ''),
                    db_id=sample['db_id'],
                    request_id=result.request_id
                )
                
                # Store result
                sample_result = {
                    'index': i - 1,
                    'db_id': sample['db_id'],
                    'question': sample['question'],
                    'predicted_sql': result.sql_query,
                    'gold_sql': sample.get('query', ''),
                    'strategy_result': result,
                    'evaluation': evaluation
                }
                results.append(sample_result)
                
                # Print immediate feedback
                if evaluation.get('exact_match', False):
                    print("✅ Exact match!")
                elif evaluation.get('execution_accuracy', False):
                    print("🟡 Execution accurate but different syntax")
                else:
                    print("❌ Incorrect result")
                    
            except Exception as e:
                print(f"❌ Error processing sample: {str(e)}")
                results.append({
                    'index': i - 1,
                    'db_id': sample['db_id'],
                    'question': sample['question'],
                    'error': str(e)
                })
        
        # Calculate summary
        total_time = time.time() - start_time
        summary = self.evaluator.calculate_summary(results)
        
        evaluation_results = {
            'config': {
                'strategy': self.config.strategy,
                'model': self.config.model_name,
                'split': self.config.split,
                'level': self.config.level,
                'template': self.config.template_path,
                'num_samples': len(dataset),
                'timestamp': datetime.now().isoformat(),
                'total_time': total_time
            },
            'summary': summary,
            'detailed_results': results
        }
        
        return evaluation_results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save evaluation results to file."""
        # Create output directory
        Path(self.config.results_dir).mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy = results['config']['strategy']
        model_name = results['config']['model'].replace('/', '_')
        split = results['config']['split']
        filename = f"evaluation_{strategy}_{model_name}_{split}_{timestamp}.json"
        filepath = Path(self.config.results_dir) / filename
        
        # Save results
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")
        return str(filepath)
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print evaluation summary."""
        print("\n" + "=" * 60)
        print("📊 EVALUATION SUMMARY")
        print("=" * 60)
        
        print(f"Strategy: {self.config.strategy.upper()}")
        print(f"Total samples: {summary.get('total_samples', 0)}")
        print(f"Exact Match: {summary.get('exact_match_accuracy', 0):.1f}%")
        print(f"Execution Accuracy: {summary.get('execution_accuracy', 0):.1f}%")
        print(f"Syntax Validity: {summary.get('syntax_validity', 0):.1f}%")
        
        if 'confidence_stats' in summary:
            conf_stats = summary['confidence_stats']
            print(f"Average Confidence: {conf_stats.get('mean', 0):.2f}")
            print(f"Confidence Range: {conf_stats.get('min', 0):.2f} - {conf_stats.get('max', 0):.2f}")
        
        if 'component_accuracy' in summary:
            print(f"\nComponent Accuracy:")
            for component, accuracy in summary['component_accuracy'].items():
                print(f"  {component}: {accuracy:.1f}%")
        
        if 'errors' in summary and summary['errors'] > 0:
            print(f"\n⚠️  Errors: {summary['errors']}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="ViPERSQL - Unified Vietnamese Text-to-SQL CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Zero-shot evaluation (default)
  python vipersql.py --samples 10
  
  # Few-shot with examples
  python vipersql.py --strategy few-shot --samples 20
  
  # Chain-of-Thought reasoning
  python vipersql.py --strategy cot --samples 5
  
  # Different model and dataset
  python vipersql.py --model claude-3-sonnet --split test --samples 50
  
  # Custom configuration file
  python vipersql.py --config custom.env --strategy pal
        """
    )
    
    # Strategy selection
    parser.add_argument(
        "--strategy", "-s",
        choices=["zero-shot", "few-shot", "cot", "pal"],
        help="Strategy to use for NL2SQL conversion"
    )
    
    # Model selection
    parser.add_argument(
        "--model", "-m",
        help="Model to use (e.g., gpt-4o-mini, claude-3-sonnet)"
    )
    
    # Dataset options
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        help="Dataset split to evaluate"
    )
    
    parser.add_argument(
        "--level", "-l",
        choices=["syllable", "word"],
        help="Tokenization level"
    )
    
    parser.add_argument(
        "--samples", "-n",
        type=int,
        help="Number of samples to evaluate (-1 for all)"
    )
    
    # Configuration
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--template", "-t",
        help="Path to custom template file"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    # Special modes
    parser.add_argument(
        "--demo",
        action="store_true", 
        help="Run interactive demo mode"
    )
    
    parser.add_argument(
        "--test-query",
        help="Test a single Vietnamese query"
    )
    
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available strategies and exit"
    )
    
    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle special modes
    if args.list_strategies:
        print("Available strategies:")
        print("  zero-shot: Direct conversion without examples")
        print("  few-shot:  Uses examples to guide conversion")
        print("  cot:       Chain-of-Thought reasoning approach")
        print("  pal:       Program-Aided Language approach")
        return
    
    try:
        # Create configuration
        config_kwargs = {}
        
        # Override config with command line arguments
        if args.strategy:
            config_kwargs['strategy'] = args.strategy
        if args.model:
            config_kwargs['model_name'] = args.model
        if args.split:
            config_kwargs['split'] = args.split
        if args.level:
            config_kwargs['level'] = args.level
        if args.samples is not None:
            config_kwargs['samples'] = args.samples
        if args.template:
            config_kwargs['template_name'] = args.template
        if args.output_dir:
            config_kwargs['results_dir'] = args.output_dir
        
        # Load custom config file if specified
        if args.config:
            import os
            from dotenv import load_dotenv
            if Path(args.config).exists():
                load_dotenv(args.config, override=True)
            else:
                print(f"❌ Config file not found: {args.config}")
                sys.exit(1)
        
        # Create configuration
        config = ViPERConfig(**config_kwargs)
        
        # Create CLI instance
        cli = ViPERSQLCLI(config)
        
        # Handle test query mode
        if args.test_query:
            print(f"\n🧪 Testing single query: {args.test_query}")
            # For demo, use first available schema
            # In real usage, user would specify database
            print("Note: Using demo schema. Specify --db-id for specific database.")
            return
        
        # Handle demo mode
        if args.demo:
            print("\n🎮 Demo mode not implemented yet")
            print("Use --test-query 'your question' for single query testing")
            return
        
        # Run evaluation
        results = cli.run_evaluation()
        
        # Print summary
        cli.print_summary(results['summary'])
        
        # Save results unless disabled
        if not args.no_save:
            output_file = cli.save_results(results)
            print(f"📄 Detailed results: {output_file}")
        
        print(f"\n🎉 Evaluation completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
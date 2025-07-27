#!/usr/bin/env python3
"""
BIRD Vietnamese Random Few-Shot Script
=====================================

Reimplementation of few-shot strategy with random example selection
specifically for BIRD Vietnamese dataset.

Usage:
    python scripts/bird/vi_random.py --samples 10 --k-examples 3
    python scripts/bird/vi_random.py --model claude-3-sonnet --samples 20
"""

import argparse
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent

# Import mint components directly (now that we're in root)
from mint.core.evaluator import UnifiedEvaluator
from mint.config import ViPERConfig
from mint.core.llm_interface import LLMInterface


class BirdViRandomScript:
    """
    BIRD Vietnamese Random Few-Shot implementation.
    """

    def __init__(self, config):
        self.config = config
        self.llm = LLMInterface(config)
        self.evaluator = UnifiedEvaluator(config)

        # Load BIRD Vietnamese data
        self.test_data = self._load_test_data()
        self.candidates_data = self._load_candidates_data()
        self.tables_info = self._load_tables_info()

        # Load few-shot template
        self.template = self._load_template()

    def _load_test_data(self):
        """Load BIRD Vietnamese test data."""
        test_path = project_root / "dataset" / "BIRD" / "vi" / "test.json"
        print(f"Loading test data from: {test_path}")

        with open(test_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} test samples")
        return data

    def _load_candidates_data(self):
        """Load BIRD Vietnamese candidates data for few-shot examples."""
        candidates_path = project_root / "dataset" / "BIRD" / "vi" / "candidates.json"
        print(f"Loading candidates data from: {candidates_path}")

        try:
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} candidate examples")
            return data
        except Exception as e:
            print(f"Warning: Could not load candidates data: {e}")
            print("Using test data as candidates pool")
            # Fallback: use test data as candidates
            return self.test_data.copy()  # Use test data for candidates

    def _load_tables_info(self):
        """Load BIRD tables information."""
        tables_path = project_root / "dataset" / "BIRD" / "tables.json"
        print(f"Loading tables info from: {tables_path}")

        with open(tables_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to dict with db_id as key for easier lookup
        tables_dict = {}
        for db_info in data:
            db_id = db_info['db_id']
            tables_dict[db_id] = db_info

        print(f"Loaded tables info for {len(tables_dict)} databases")
        return tables_dict

    def _load_template(self):
        """Load few-shot template."""
        template_path = project_root / "templates" / "few_shot_vietnamese_nl2sql.txt"
        print(f"Loading template from: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        return template

    def _prepare_schema_context(self, db_schema):
        """Prepare schema context for template."""
        if not db_schema:
            return {
                'tables': 'No table information available',
                'columns': 'No column information available',
                'foreign_keys': 'No foreign key information available',
                'primary_keys': 'No primary key information available'
            }

        # Extract table information
        tables = []
        columns = []
        foreign_keys = []
        primary_keys = []

        for table_info in db_schema.get('table_names_original', []):
            tables.append(table_info)

        for i, (table_idx, col_name) in enumerate(db_schema.get('column_names_original', [])):
            if table_idx >= 0:  # Skip * column
                table_name = db_schema['table_names_original'][table_idx]
                columns.append(f"{table_name}.{col_name}")

        for fk in db_schema.get('foreign_keys', []):
            col1_idx, col2_idx = fk
            if col1_idx < len(db_schema['column_names_original']) and col2_idx < len(db_schema['column_names_original']):
                col1_table_idx, col1_name = db_schema['column_names_original'][col1_idx]
                col2_table_idx, col2_name = db_schema['column_names_original'][col2_idx]

                if col1_table_idx >= 0 and col2_table_idx >= 0:
                    col1_table = db_schema['table_names_original'][col1_table_idx]
                    col2_table = db_schema['table_names_original'][col2_table_idx]
                    foreign_keys.append(f"{col1_table}.{col1_name} -> {col2_table}.{col2_name}")

        # Fix primary keys processing - BIRD schema has different structure
        pks = db_schema.get('primary_keys', [])
        if pks:
            for pk in pks:
                if isinstance(pk, int) and pk < len(db_schema['column_names_original']):
                    # Single primary key column index
                    col_table_idx, col_name = db_schema['column_names_original'][pk]
                    if col_table_idx >= 0 and col_table_idx < len(db_schema['table_names_original']):
                        table_name = db_schema['table_names_original'][col_table_idx]
                        primary_keys.append(f"{table_name}.{col_name}")
                elif isinstance(pk, list):
                    # Multiple primary key columns
                    for pk_col in pk:
                        if pk_col < len(db_schema['column_names_original']):
                            col_table_idx, col_name = db_schema['column_names_original'][pk_col]
                            if col_table_idx >= 0 and col_table_idx < len(db_schema['table_names_original']):
                                table_name = db_schema['table_names_original'][col_table_idx]
                                primary_keys.append(f"{table_name}.{col_name}")

        return {
            'tables': ', '.join(tables) if tables else 'No tables',
            'columns': ', '.join(columns) if columns else 'No columns',
            'foreign_keys': '; '.join(foreign_keys) if foreign_keys else 'No foreign keys',
            'primary_keys': ', '.join(primary_keys) if primary_keys else 'No primary keys'
        }

    def _select_random_examples(self, question, db_id, k=3):
        """Select k random examples for few-shot learning."""
        print(f"Selecting {k} random examples for db_id: {db_id}")

        # Use candidates data if available, otherwise use test data
        if self.candidates_data:
            candidate_pool = self.candidates_data
        else:
            # Use test data but exclude current question
            candidate_pool = [item for item in self.test_data if item['question'] != question]

        # Filter by db_id if specified and available
        filtered_candidates = []
        for candidate in candidate_pool:
            candidate_db_id = candidate.get('db_id')
            if db_id and candidate_db_id == db_id:
                filtered_candidates.append(candidate)

        # If no matches for specific db_id, use all candidates
        if not filtered_candidates:
            print(f"No examples found for db_id {db_id}, using all available examples")
            filtered_candidates = candidate_pool

        # Randomly select k examples
        if len(filtered_candidates) <= k:
            selected = filtered_candidates.copy()
        else:
            selected = random.sample(filtered_candidates, k)

        print(f"Selected {len(selected)} examples")
        return selected

    def _format_examples(self, examples):
        """Format examples for template insertion."""
        if not examples:
            return ""

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            question = example.get('question', "")
            # Use 'SQL' field for BIRD data, fallback to 'query'
            sql = example.get('SQL', example.get('query', ""))

            if question and sql:
                formatted_example = f"Example {i}:\nQuestion: {question}\nSQL: {sql}"
                formatted_examples.append(formatted_example)

        return "\n\n".join(formatted_examples)

    def _clean_sql_response(self, response):
        """Clean and extract SQL from LLM response."""
        # Remove common prefixes and suffixes
        response = response.strip()

        # Remove SQL: prefix if present
        if response.lower().startswith('sql:'):
            response = response[4:].strip()

        # Remove markdown code blocks
        if response.startswith('```sql'):
            response = response[6:]
        elif response.startswith('```'):
            response = response[3:]

        if response.endswith('```'):
            response = response[:-3]

        return response.strip()

    def generate_sql(self, question, db_schema, db_id, k_examples=3):
        """Generate SQL using few-shot approach with random examples."""
        try:
            # Select random examples
            examples = self._select_random_examples(question, db_id, k_examples)

            # Prepare schema context
            schema_context = self._prepare_schema_context(db_schema)

            # Format examples
            examples_str = self._format_examples(examples)

            # Fill template
            filled_template = self.template.format(
                question=question,
                examples=examples_str,
                **schema_context
            )

            # DEBUG: Print template and first part of prompt
            print(f"DEBUG - Template length: {len(filled_template)}")
            print(f"DEBUG - First 200 chars of prompt:")
            print(filled_template[:200] + "...")
            print(f"DEBUG - Examples used: {len(examples)}")

            # Generate SQL
            print(f"Generating SQL for: {question[:50]}...")
            response = self.llm.generate(
                prompt=filled_template,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # DEBUG: Print raw response
            print(f"DEBUG - Raw LLM response: '{response}'")
            print(f"DEBUG - Response length: {len(response)}")

            # Clean response
            sql = self._clean_sql_response(response)

            # DEBUG: Print cleaned SQL
            print(f"DEBUG - Cleaned SQL: '{sql}'")

            return sql, len(examples)

        except Exception as e:
            print(f"Error generating SQL: {e}")
            import traceback
            traceback.print_exc()
            return "", 0

    def run_evaluation(self, num_samples=None):
        """Run evaluation on BIRD Vietnamese test data."""
        print("=" * 50)
        print("BIRD Vietnamese Random Few-Shot Evaluation")
        print("=" * 50)

        # Prepare test samples
        test_samples = self.test_data[:num_samples] if num_samples else self.test_data
        print(f"Evaluating on {len(test_samples)} samples")

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "results" / f"bird_vi_random_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        start_time = time.time()

        # Process each test sample
        for i, item in enumerate(test_samples, 1):
            db_id = item['db_id']
            question = item['question']
            gold_sql = item['SQL']  # BIRD uses 'SQL' field

            print(f"\n[{i}/{len(test_samples)}] Processing question for {db_id}")
            print(f"Question: {question[:100]}...")

            # Get database schema
            db_schema = self.tables_info.get(db_id, {})

            # Generate SQL
            try:
                k_examples = getattr(self, 'simple_config', self.config).k_examples if hasattr(getattr(self, 'simple_config', self.config), 'k_examples') else 3
                predicted_sql, num_examples = self.generate_sql(
                    question, db_schema, db_id, k_examples
                )

                print(f"Generated SQL: {predicted_sql[:100]}...")
                print(f"Used {num_examples} examples")

                # Add to results
                results.append({
                    'db_id': db_id,
                    'question': question,
                    'predicted': predicted_sql,
                    'gold': gold_sql,
                    'examples_used': num_examples
                })

            except Exception as e:
                print(f"Error: {e}")
                results.append({
                    'db_id': db_id,
                    'question': question,
                    'predicted': "",
                    'gold': gold_sql,
                    'error': str(e),
                    'examples_used': 0
                })

            # Save intermediate results every 10 samples
            if i % 10 == 0:
                intermediate_path = output_dir / f"intermediate_results_{i}.json"
                with open(intermediate_path, 'w', encoding='utf-8') as f:
                    json.dump({'predictions': results}, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved intermediate results ({i} samples)")

        # Save final predictions
        predictions_path = output_dir / 'predictions.json'
        with open(predictions_path, 'w', encoding='utf-8') as f:
            json.dump({'predictions': results}, f, indent=2, ensure_ascii=False)

        generation_time = time.time() - start_time
        print(f"\n✅ SQL Generation completed in {generation_time:.2f} seconds")
        print(f"✅ Generated {len(results)} predictions")
        print(f"✅ Results saved to: {predictions_path}")

        # Run evaluation
        print("\n🔍 Starting Evaluation...")
        eval_start_time = time.time()

        try:
            # Use BIRD tables for evaluation
            evaluation_results = self.evaluator.evaluate_batch(
                results,
                schema_path=str(project_root / "dataset" / "BIRD" / "tables.json")
            )

            # Add timing and config info
            eval_time = time.time() - eval_start_time
            total_time = time.time() - start_time

            evaluation_results['timing_info'] = {
                'sql_generation_time': generation_time,
                'evaluation_time': eval_time,
                'total_execution_time': total_time,
                'start_time': datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            evaluation_results['experiment_config'] = {
                'model_name': self.config.model_name,
                'strategy': 'few-shot-random',
                'dataset': 'BIRD-Vietnamese',
                'num_samples': len(test_samples),
                'k_examples': self.config.k_examples,
                'timestamp': timestamp
            }

            # Generate report
            report_files = self.evaluator.generate_report(evaluation_results, str(output_dir))

            print(f"✅ Evaluation completed in {eval_time:.2f} seconds")
            print(f"📊 Report saved to: {report_files.get('report_path', 'N/A')}")

            # Print summary
            self._print_summary(evaluation_results)

        except Exception as e:
            print(f"Evaluation error: {e}")

        return str(output_dir)

    def _print_summary(self, eval_results):
        """Print evaluation summary."""
        print("\n" + "=" * 50)
        print("EVALUATION SUMMARY")
        print("=" * 50)

        metrics = eval_results.get('detailed_metrics', {})

        # Extract key metrics
        exact_match = metrics.get('exact_match_accuracy', 0)
        execution_accuracy = metrics.get('execution_accuracy', 0)

        print(f"📊 Exact Match Accuracy: {exact_match:.2%}")
        print(f"📊 Execution Accuracy: {execution_accuracy:.2%}")

        # Additional metrics if available
        if 'pos_accuracy' in metrics:
            print(f"📊 POS Accuracy: {metrics['pos_accuracy']:.2%}")

        # Timing info
        timing = eval_results.get('timing_info', {})
        if timing:
            print(f"⏱️  Total Time: {timing.get('total_execution_time', 0):.2f}s")
            print(f"⏱️  Generation Time: {timing.get('sql_generation_time', 0):.2f}s")
            print(f"⏱️  Evaluation Time: {timing.get('evaluation_time', 0):.2f}s")


def main():
    parser = argparse.ArgumentParser(description='BIRD Vietnamese Random Few-Shot Evaluation')
    parser.add_argument('--model', default='claude-3-5-haiku-20241022',
                       help='Model name (default: claude-3-5-haiku-20241022)')
    parser.add_argument('--samples', type=int,
                       help='Number of samples to evaluate (default: all)')
    parser.add_argument('--k-examples', type=int, default=3,
                       help='Number of few-shot examples (default: 3)')
    parser.add_argument('--temperature', type=float, default=0.0,
                       help='Model temperature (default: 0.0)')
    parser.add_argument('--max-tokens', type=int, default=1024,
                       help='Maximum tokens (default: 1024)')
    parser.add_argument('--config', default='.env',
                       help='Config file path (default: .env)')

    args = parser.parse_args()

    # Create ViPERConfig with k_examples support
    config = ViPERConfig(
        model_name=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        strategy='few-shot',  # Fixed strategy for BIRD
        level='std',  # Default level
        split='test'  # Default split
    )

    # Add k_examples to config
    config.k_examples = args.k_examples

    # Run evaluation
    script = BirdViRandomScript(config)
    output_dir = script.run_evaluation(args.samples)

    print(f"\n🎉 Evaluation completed!")
    print(f"📁 Results saved to: {output_dir}")


if __name__ == "__main__":
    main()

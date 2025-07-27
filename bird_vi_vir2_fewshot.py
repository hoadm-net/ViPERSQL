#!/usr/bin/env python3
"""
BIRD Vietnamese ViR2 Few-Shot Script
===================================

Implements ViR2 (Two-Stage Example Selection) for BIRD Vietnamese dataset.
ViR2 uses PhoBERT + beam search with POS matching and diversity optimization.

Usage:
    python bird_vi_vir2_fewshot.py --samples 10 --k-examples 3
    python bird_vi_vir2_fewshot.py --model claude-3-5-sonnet-20241022 --samples 20
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
from mint.selectors.vir2_selector import ViR2Selector


class BirdViR2Script:
    """
    BIRD Vietnamese ViR2 Few-Shot implementation.
    """

    def __init__(self, config):
        self.config = config
        self.llm = LLMInterface(config)
        self.evaluator = UnifiedEvaluator(config)

        # Initialize ViR2 selector
        self.vir2_selector = ViR2Selector(config)

        # Load BIRD Vietnamese data
        self.test_data = self._load_test_data()
        self.candidates_data = self._load_candidates_data()
        self.tables_info = self._load_tables_info()

        # Load few-shot template
        self.template = self._load_template()

        # Load ViR2 meaning pool from candidates
        self._setup_vir2_meaning_pool()

    def _load_test_data(self):
        """Load BIRD Vietnamese test data."""
        test_path = project_root / "dataset" / "BIRD" / "vi" / "test.json"
        print(f"Loading test data from: {test_path}")

        with open(test_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} test samples")
        return data

    def _load_candidates_data(self):
        """Load BIRD Vietnamese candidates data for ViR2 meaning pool."""
        candidates_path = project_root / "dataset" / "BIRD" / "vi" / "candidates.json"
        print(f"Loading candidates data from: {candidates_path}")

        try:
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} candidate examples for ViR2")
            return data
        except Exception as e:
            print(f"Warning: Could not load candidates data: {e}")
            print("Using test data as candidates pool")
            # Fallback: use test data as candidates
            return self.test_data.copy()

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

    def _setup_vir2_meaning_pool(self):
        """Setup ViR2 meaning pool from BIRD candidates."""
        print("Setting up ViR2 meaning pool...")

        # Convert BIRD candidates format to ViR2 format
        meaning_pool = []
        for item in self.candidates_data:
            # Convert BIRD format to ViR2 format
            vir2_item = {
                'question': item['question'],
                'query': item.get('SQL', item.get('query', '')),  # Handle both field names
                'db_id': item.get('db_id', ''),
                # Note: No pre-computed embeddings, ViR2 will compute them
            }
            meaning_pool.append(vir2_item)

        # Set meaning pool for ViR2 selector
        self.vir2_selector.meaning_pool = meaning_pool

        # Compute embeddings for the meaning pool
        if self.vir2_selector.tokenizer is not None:
            self.vir2_selector._compute_meaning_pool_embeddings()
        else:
            print("Warning: PhoBERT not loaded, ViR2 will not work properly")

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

    def _select_vir2_examples(self, question, k=3):
        """Select k examples using ViR2 two-stage approach."""
        print(f"Using ViR2 to select {k} examples")

        try:
            # Use ViR2 selector
            selected = self.vir2_selector.select(question, k)
            print(f"ViR2 selected {len(selected)} examples")
            return selected
        except Exception as e:
            print(f"Error in ViR2 selection: {e}")
            print("Falling back to random selection")
            # Fallback to random selection
            if len(self.candidates_data) <= k:
                return self.candidates_data.copy()
            else:
                return random.sample(self.candidates_data, k)

    def _format_examples(self, examples):
        """Format examples for template insertion."""
        if not examples:
            return ""

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            question = example.get('question', "")
            # Use 'query' field (ViR2 format) or 'SQL' field (BIRD format)
            sql = example.get('query', example.get('SQL', ""))

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
        """Generate SQL using ViR2 few-shot approach."""
        try:
            # Select examples using ViR2
            examples = self._select_vir2_examples(question, k_examples)

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

            # DEBUG: Print info
            print(f"DEBUG - Template length: {len(filled_template)}")
            print(f"DEBUG - ViR2 examples used: {len(examples)}")

            # Generate SQL
            print(f"Generating SQL for: {question[:50]}...")
            response = self.llm.generate(
                prompt=filled_template,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Clean response
            sql = self._clean_sql_response(response)

            print(f"DEBUG - Generated SQL: '{sql[:100]}...'")

            return sql, len(examples)

        except Exception as e:
            print(f"Error generating SQL: {e}")
            import traceback
            traceback.print_exc()
            return "", 0

    def run_evaluation(self, num_samples=None):
        """Run evaluation on BIRD Vietnamese test data using ViR2."""
        print("=" * 50)
        print("BIRD Vietnamese ViR2 Few-Shot Evaluation")
        print("=" * 50)

        # Prepare test samples
        test_samples = self.test_data[:num_samples] if num_samples else self.test_data
        print(f"Evaluating on {len(test_samples)} samples")

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "results" / f"bird_vi_vir2_{timestamp}"
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

            # Generate SQL using ViR2
            try:
                predicted_sql, num_examples = self.generate_sql(
                    question, db_schema, db_id, self.config.k_examples
                )

                print(f"Generated SQL: {predicted_sql[:100]}...")
                print(f"Used {num_examples} ViR2 examples")

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

        # Run evaluation using UnifiedEvaluator
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
                'strategy': 'few-shot-vir2',
                'dataset': 'BIRD-Vietnamese',
                'num_samples': len(test_samples),
                'k_examples': self.config.k_examples,
                'vir2_candidate_pool_size': getattr(self.config, 'vir2_candidate_pool_size', 50),
                'vir2_beam_size': getattr(self.config, 'vir2_beam_size', 5),
                'vir2_diversity_weight': getattr(self.config, 'vir2_diversity_weight', 0.3),
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
        print("ViR2 EVALUATION SUMMARY")
        print("=" * 50)

        # Check if we have component F1 scores (from UnifiedEvaluator)
        if 'component_f1' in eval_results:
            component_f1 = eval_results['component_f1']
            f1_scores = component_f1.get('f1_scores', {})

            print("📊 COMPONENT F1-SCORES:")
            for component, score in f1_scores.items():
                print(f"  {component:12}: {score:.3f}")

            if f1_scores:
                avg_f1 = sum(f1_scores.values()) / len(f1_scores)
                print(f"  {'Average F1':12}: {avg_f1:.3f}")

        # Basic metrics
        exact_match = eval_results.get('exact_match', {}).get('em_accuracy', 0)
        print(f"\n📊 Exact Match Accuracy: {exact_match:.2%}")

        # Timing info
        timing = eval_results.get('timing_info', {})
        if timing:
            print(f"⏱️  Total Time: {timing.get('total_execution_time', 0):.2f}s")
            print(f"⏱️  Generation Time: {timing.get('sql_generation_time', 0):.2f}s")
            print(f"⏱️  Evaluation Time: {timing.get('evaluation_time', 0):.2f}s")


def main():
    parser = argparse.ArgumentParser(description='BIRD Vietnamese ViR2 Few-Shot Evaluation')
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

    # ViR2 specific parameters
    parser.add_argument('--vir2-pool-size', type=int, default=50,
                       help='ViR2 candidate pool size M (default: 50)')
    parser.add_argument('--vir2-beam-size', type=int, default=5,
                       help='ViR2 beam search size (default: 5)')
    parser.add_argument('--vir2-diversity-weight', type=float, default=0.3,
                       help='ViR2 diversity weight λ (default: 0.3)')

    args = parser.parse_args()

    # Create ViPERConfig with ViR2 parameters
    config = ViPERConfig(
        model_name=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        strategy='few-shot',  # Fixed strategy for BIRD
        level='std',  # Default level
        split='test'  # Default split
    )

    # Add ViR2 specific config
    config.k_examples = args.k_examples
    config.vir2_candidate_pool_size = args.vir2_pool_size
    config.vir2_beam_size = args.vir2_beam_size
    config.vir2_diversity_weight = args.vir2_diversity_weight

    # Run evaluation
    script = BirdViR2Script(config)
    output_dir = script.run_evaluation(args.samples)

    print(f"\n🎉 ViR2 Evaluation completed!")
    print(f"📁 Results saved to: {output_dir}")


if __name__ == "__main__":
    main()

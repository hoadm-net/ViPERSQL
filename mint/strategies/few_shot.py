import time
import random
from typing import Dict, List, Any, Optional
from .base import BaseStrategy, StrategyResult

class FewShotStrategy(BaseStrategy):
    """
    Few-shot strategy for Vietnamese NL2SQL conversion.
    This strategy generates SQL queries using k examples from the training set
    to guide the LLM's understanding of the task.
    """
    def __init__(self, config):
        super().__init__(config)
        self.k_examples = getattr(config, 'few_shot_examples', 3)
        self.selection_strategy = getattr(config, 'example_selection_strategy', 'random')
        self._training_examples = None

    def _get_strategy_name(self) -> str:
        return "few-shot"

    def load_training_examples(self, dataset_path: str, db_id: str = None) -> List[Dict]:
        """Load training examples from dataset."""
        try:
            import json
            from pathlib import Path
            train_file = Path(dataset_path) / "train.json"
            if not train_file.exists():
                self.logger.log_warning(f"Training file not found: {train_file}")
                return []
            with open(train_file, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            if db_id:
                filtered_data = [ex for ex in train_data if ex.get('db_id') == db_id]
                if not filtered_data:
                    self.logger.log_warning(f"No examples found for database {db_id}, using all examples")
                    filtered_data = train_data
            else:
                filtered_data = train_data
            self._training_examples = filtered_data
            self.logger.log_info(f"Loaded {len(filtered_data)} training examples")
            return filtered_data
        except Exception as e:
            self.logger.log_error(f"Failed to load training examples: {e}")
            return []

    def select_examples(self, question: str, db_id: str = None, k: int = None) -> List[Dict]:
        """Select k examples using the specified strategy."""
        if k is None:
            k = self.k_examples
        if self._training_examples is None:
            dataset_path = self.config.dataset_full_path
            self.load_training_examples(dataset_path, db_id)
        if not self._training_examples:
            self.logger.log_warning("No training examples available")
            return []
        if self.selection_strategy == 'random':
            selected = self._select_random_examples(k)
        else:
            self.logger.log_warning(f"Strategy {self.selection_strategy} not implemented, using random")
            selected = self._select_random_examples(k)
        self.logger.log_info(f"Selected {len(selected)} examples using {self.selection_strategy} strategy")
        return selected

    def _select_random_examples(self, k: int) -> List[Dict]:
        if len(self._training_examples) <= k:
            return self._training_examples.copy()
        return random.sample(self._training_examples, k)

    def format_examples(self, examples: List[Dict]) -> str:
        """Format examples for template insertion."""
        if not examples:
            return ""
        formatted_examples = []
        for i, example in enumerate(examples, 1):
            question = example.get('question', "")
            query = example.get('query', "")
            if question and query:
                formatted_example = f"Example {i}:\nQuestion: {question}\nSQL: {query}"
                formatted_examples.append(formatted_example)
        return "\n\n".join(formatted_examples)

    def generate_sql(
        self,
        question: str,
        schema_info: Dict[str, Any],
        db_id: str,
        examples: Optional[List[Dict]] = None
    ) -> StrategyResult:
        """Generate SQL query using few-shot approach."""
        request_id = f"few_shot_{int(time.time() * 1000000)}"
        try:
            if examples is None:
                examples = self.select_examples(question, db_id)
            schema_context = self.prepare_schema_context(schema_info)
            examples_str = self.format_examples(examples)
            template_vars = {
                'question': question,
                'examples': examples_str,
                **schema_context
            }
            template = self.templates.get_template('few-shot')
            formatted_prompt = template.format(**template_vars)
            self.logger.log_info(f"Request {request_id}: Few-shot generation for {db_id} with {len(examples)} examples")
            start_time = time.time()
            raw_response = self.llm.generate(
                prompt=formatted_prompt,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            latency = time.time() - start_time
            sql_query = self.clean_sql_response(raw_response)
            is_valid = self.validate_sql_syntax(sql_query)
            result = StrategyResult(
                sql_query=sql_query,
                request_id=request_id,
                reasoning=f"Few-shot generation with {len(examples)} examples using {self.selection_strategy} strategy",
                intermediate_steps=[
                    "1. Load training examples",
                    "2. Select examples using strategy",
                    "3. Format examples for template",
                    "4. Generate SQL with examples",
                    "5. Clean and validate response"
                ],
                confidence_score=0.8 if is_valid else 0.3,
                metadata={
                    'strategy': 'few-shot',
                    'model': self.config.model_name,
                    'latency': latency,
                    'syntax_valid': is_valid,
                    'template_used': self.config.template_path,
                    'prompt_length': len(formatted_prompt),
                    'response_length': len(raw_response),
                    'examples_used': len(examples),
                    'selection_strategy': self.selection_strategy,
                    'k_examples': self.k_examples
                }
            )
            self.logger.log_info(
                f"Request {request_id}: Generated SQL in {latency:.2f}s - Valid: {is_valid}"
            )
            self.log_strategy_execution(request_id, question, db_id, result)
            return result
        except Exception as e:
            error_msg = f"Few-shot generation failed: {str(e)}"
            self.logger.log_error(f"Request {request_id}: {error_msg}")
            return self.create_error_result(request_id, error_msg, 'few-shot') 
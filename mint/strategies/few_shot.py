import time
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

        # Initialize the appropriate selector based on strategy
        self._selector = self._create_selector()

    def _create_selector(self):
        """Create and return the appropriate example selector."""
        if self.selection_strategy == 'skill_knn':
            from ..selectors import SkillKNNSelector
            return SkillKNNSelector(self.config)
        elif self.selection_strategy == 'dicl':
            from ..selectors import DICLSelector
            return DICLSelector(self.config)
        elif self.selection_strategy == 'astres':
            from ..selectors import ASTRESSelector
            return ASTRESSelector(self.config)
        elif self.selection_strategy == 'vir2':
            from ..selectors import ViR2Selector
            selector = ViR2Selector(self.config)
            # Load training data for ViR2
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'vir2-no-pos':
            from ..selectors import ViR2NoPOSSelector
            selector = ViR2NoPOSSelector(self.config)
            # Load training data for ViR2 No POS
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'vir2-no-diversity':
            from ..selectors import ViR2NoDiversitySelector
            selector = ViR2NoDiversitySelector(self.config)
            # Load training data for ViR2 No Diversity
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'vir2-no-beam-search':
            from ..selectors import ViR2NoBeamSearchSelector
            selector = ViR2NoBeamSearchSelector(self.config)
            # Load training data for ViR2 No Beam Search
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'random':
            from ..selectors import RandomSelector
            return RandomSelector(self.config)
        else:
            print(f"[FewShot] Unknown selection strategy '{self.selection_strategy}', falling back to random")
            from ..selectors import RandomSelector
            return RandomSelector(self.config)

    def _get_strategy_name(self) -> str:
        return "few-shot"

    def select_examples(self, question: str, db_id: str = None, k: int = None, schema_info: Dict[str, Any] = None) -> List[Dict]:
        """Select k examples using the configured strategy."""
        if k is None:
            k = self.k_examples

        try:
            print(f"[FewShot] Using {self.selection_strategy} selection strategy")

            # For ASTRES, pass schema_info if available
            if self.selection_strategy == 'astres' and schema_info is not None:
                return self._selector.select_examples(question, k, db_id, schema_info)
            else:
                return self._selector.select_examples(question, k, db_id)

        except Exception as e:
            print(f"[FewShot] Error in {self.selection_strategy} selection: {e}")
            # Fallback to random if current strategy fails
            if self.selection_strategy != 'random':
                print(f"[FewShot] Falling back to random selection")
                from ..selectors import RandomSelector
                fallback_selector = RandomSelector(self.config)
                return fallback_selector.select_examples(question, k, db_id)
            else:
                print(f"[FewShot] Random selection also failed")
                return []

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
                examples = self.select_examples(question, db_id, schema_info=schema_info)
            schema_context = self.prepare_schema_context(schema_info)
            examples_str = self.format_examples(examples)
            template_vars = {
                'question': question,
                'examples': examples_str,
                **schema_context
            }
            template = self.templates.get_template('few-shot')
            formatted_prompt = template.format(**template_vars)
            print(f"[FewShot] Request {request_id}: Few-shot generation for {db_id} with {len(examples)} examples")
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
            print(
                f"[FewShot] Request {request_id}: Generated SQL in {latency:.2f}s - Valid: {is_valid}"
            )
            self.log_strategy_execution(request_id, question, db_id, result)
            return result
        except Exception as e:
            error_msg = f"Few-shot generation failed: {str(e)}"
            print(f"[FewShot] Request {request_id}: {error_msg}")
            return self.create_error_result(request_id, error_msg, 'few-shot')

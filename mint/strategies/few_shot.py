"""
Few-shot Strategy Implementation

Implements few-shot learning by including relevant examples in the prompt.
"""

import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from .base import BaseStrategy, StrategyResult
from ..logger import ViPERLogger


class FewShotStrategy(BaseStrategy):
    """Few-shot strategy with example-based learning."""
    
    def __init__(self, config):
        """Initialize few-shot strategy."""
        super().__init__(config)
        self.num_examples = getattr(config, 'few_shot_examples', 3)
        self.template_name = getattr(config, 'few_shot_template', 'few_shot_vietnamese_nl2sql.txt')
        self._training_examples: Optional[List[Dict[str, Any]]] = None
        
        # Use inherited components
        self.llm_interface = self.llm
        self.template_manager = self.templates
    
    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "few-shot"
    
    def _load_training_examples(self) -> List[Dict[str, Any]]:
        """Load training examples for few-shot learning."""
        if self._training_examples is not None:
            return self._training_examples
            
        try:
            # Load training data
            train_path = Path(self.config.dataset_path) / f"{self.config.level}-level" / "train.json"
            
            if not train_path.exists():
                self.logger.log_warning(f"Training data not found: {train_path}. Using empty examples list.")
                return []
            
            with open(train_path, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            # Convert to list of examples with question and SQL
            examples = []
            for item in train_data:
                if 'question' in item and 'query' in item:
                    examples.append({
                        'question': item['question'],
                        'sql': item['query'],
                        'db_id': item.get('db_id', 'unknown')
                    })
            
            self._training_examples = examples
            self.logger.log_info(f"Loaded {len(examples)} training examples from {train_path}")
            
            return examples
            
        except Exception as e:
            self.logger.log_error(f"Failed to load training examples: {str(e)}. Using empty examples list.")
            return []
    
    def _select_examples(self, current_db_id: str) -> List[Dict[str, Any]]:
        """Select relevant examples for few-shot learning."""
        training_examples = self._load_training_examples()
        
        if not training_examples:
            return []
        
        # Strategy 1: Prefer examples from the same database
        same_db_examples = [ex for ex in training_examples if ex['db_id'] == current_db_id]
        
        if len(same_db_examples) >= self.num_examples:
            # Randomly select from same database
            selected = random.sample(same_db_examples, self.num_examples)
        else:
            # Use all same-db examples and fill with random others
            other_examples = [ex for ex in training_examples if ex['db_id'] != current_db_id]
            remaining_needed = self.num_examples - len(same_db_examples)
            
            if remaining_needed > 0 and other_examples:
                additional = random.sample(
                    other_examples, 
                    min(remaining_needed, len(other_examples))
                )
                selected = same_db_examples + additional
            else:
                selected = same_db_examples
        
        same_db_count = len([ex for ex in training_examples if ex['db_id'] == current_db_id])
        self.logger.log_info(f"Selected {len(selected)}/{self.num_examples} examples. Available: {len(training_examples)} total, {same_db_count} from same DB.")
        
        return selected
    
    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format examples for inclusion in the prompt."""
        if not examples:
            return "No examples available."
        
        formatted_examples = []
        for i, example in enumerate(examples, 1):
            formatted_examples.append(f"""Example {i}:
Vietnamese Question: {example['question']}
SQL Query: {example['sql']}""")
        
        return "\n\n".join(formatted_examples)
    
    def generate_sql(
        self, 
        question: str, 
        schema_info: Dict[str, Any], 
        db_id: str,
        examples: Optional[List[Dict]] = None
    ) -> StrategyResult:
        """Process a question using few-shot strategy."""
        try:
            # Select relevant examples
            selected_examples = self._select_examples(db_id)
            formatted_examples = self._format_examples(selected_examples)
            
            # Prepare schema context
            schema_context = self.prepare_schema_context(schema_info)
            
            # Get template
            template = self.template_manager.get_template(self._get_strategy_name())
            
            # Prepare template variables
            template_vars = {
                'question': question,
                'examples': formatted_examples,
                **schema_context
            }
            
            # Generate prompt
            prompt = template.format(**template_vars)
            
            # Log request
            self.logger.log_request(
                request_id=f"few_shot_{hash(question)}",
                strategy=self._get_strategy_name(),
                question=question,
                db_id=db_id,
                result="pending",
                metadata={
                    'model': self.config.model_name,
                    'examples_count': len(selected_examples),
                    'prompt_length': len(prompt)
                }
            )
            
            # Get LLM response
            response = self.llm_interface.generate(prompt)
            
            # Extract SQL query
            sql_query = self._extract_sql_query(response)
            
            # Log response
            self.logger.log_llm_response(
                request_id=f"few_shot_{hash(question)}",
                model=self.config.model_name,
                prompt=prompt,
                response=response,
                latency=0.0,  # TODO: measure actual latency
                metadata={
                    'strategy': self._get_strategy_name(),
                    'sql_query': sql_query,
                    'response_length': len(response)
                }
            )
            
            return StrategyResult(
                sql_query=sql_query,
                request_id=f"few_shot_{hash(question)}",
                reasoning=f"Used {len(selected_examples)} examples for few-shot learning",
                metadata={
                    'strategy': self._get_strategy_name(),
                    'examples_used': len(selected_examples),
                    'db_id': db_id,
                    'template': self.template_name,
                    'raw_response': response
                }
            )
            
        except Exception as e:
            error_msg = f"Few-shot strategy failed: {str(e)}"
            self.logger.log_error(error_msg)
            
            return StrategyResult(
                sql_query="",
                request_id=f"few_shot_error_{hash(question)}",
                reasoning=f"Error occurred: {error_msg}",
                metadata={
                    'strategy': self._get_strategy_name(),
                    'error': error_msg
                }
            ) 
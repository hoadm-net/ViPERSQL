"""
Chain-of-Thought (CoT) Strategy Implementation

Implements Chain-of-Thought reasoning for Vietnamese NL2SQL conversion.
This strategy encourages the LLM to think step-by-step before generating SQL.
"""

import time
from typing import Dict, List, Any, Optional
from .base import BaseStrategy, StrategyResult


class CoTStrategy(BaseStrategy):
    """
    Chain-of-Thought (CoT) strategy for Vietnamese NL2SQL conversion.
    
    This strategy encourages the LLM to think step-by-step before generating SQL,
    breaking down the complex task into logical reasoning steps.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.reasoning_steps = getattr(config, 'cot_reasoning_steps', True)
        self.include_examples = getattr(config, 'cot_include_examples', False)
        self.k_examples = getattr(config, 'cot_examples', 2) if self.include_examples else 0
        self.selection_strategy = getattr(config, 'cot_selection_strategy', 'random')
        
        # Initialize the appropriate selector based on strategy
        self._selector = self._create_selector() if self.include_examples else None

    def _create_selector(self):
        """Create and return the appropriate example selector (same as FewShotStrategy)."""
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
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'vir2-no-diversity':
            from ..selectors import ViR2NoDiversitySelector
            selector = ViR2NoDiversitySelector(self.config)
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'vir2-no-beam-search':
            from ..selectors import ViR2NoBeamSearchSelector
            selector = ViR2NoBeamSearchSelector(self.config)
            dataset_path = f"{self.config.dataset_path}/{self.config.level}-level/dicl_candidates.json"
            selector.load_training_data(dataset_path)
            return selector
        elif self.selection_strategy == 'random':
            from ..selectors import RandomSelector
            return RandomSelector(self.config)
        else:
            print(f"[CoT] Unknown selection strategy '{self.selection_strategy}', falling back to random")
            from ..selectors import RandomSelector
            return RandomSelector(self.config)

    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "cot"
    
    def select_examples(self, question: str, db_id: str = None, k: int = None, schema_info: Dict[str, Any] = None) -> List[Dict]:
        """Select k examples using the configured strategy (same as FewShotStrategy)."""
        if not self.include_examples or self._selector is None:
            return []
        
        if k is None:
            k = self.k_examples

        try:
            print(f"[CoT] Using {self.selection_strategy} selection strategy")

            # For ASTRES, pass schema_info if available
            if self.selection_strategy == 'astres' and schema_info is not None:
                return self._selector.select_examples(question, k, db_id, schema_info)
            else:
                return self._selector.select_examples(question, k, db_id)

        except Exception as e:
            print(f"[CoT] Error in {self.selection_strategy} selection: {e}")
            # Fallback to random if current strategy fails
            if self.selection_strategy != 'random':
                print(f"[CoT] Falling back to random selection")
                from ..selectors import RandomSelector
                fallback_selector = RandomSelector(self.config)
                return fallback_selector.select_examples(question, k, db_id)
            else:
                print(f"[CoT] Random selection also failed")
                return []

    def format_cot_examples(self, examples: List[Dict]) -> str:
        """Format examples with step-by-step reasoning for CoT template."""
        if not examples:
            return ""
        
        formatted_examples = []
        for i, example in enumerate(examples, 1):
            question = example.get('question', "")
            query = example.get('query', "")
            if question and query:
                # Create a step-by-step reasoning example
                reasoning_steps = self._generate_reasoning_steps(question, query)
                formatted_example = f"""Example {i}:
Question: {question}

Let me think step by step:
{reasoning_steps}

SQL: {query}"""
                formatted_examples.append(formatted_example)
        
        return "\n\n".join(formatted_examples)

    def _generate_reasoning_steps(self, question: str, query: str) -> str:
        """Generate step-by-step reasoning for an example."""
        # This is a simplified reasoning generation
        # In practice, you might want to use a more sophisticated approach
        steps = [
            "1. First, I need to understand what information is being requested",
            "2. Then, I identify which tables and columns are relevant",
            "3. Next, I determine the type of query (SELECT, COUNT, etc.)",
            "4. I consider any filtering conditions (WHERE clauses)",
            "5. Finally, I construct the SQL query with proper syntax"
        ]
        return "\n".join(steps)

    def generate_sql(
        self, 
        question: str, 
        schema_info: Dict[str, Any], 
        db_id: str,
        examples: Optional[List[Dict]] = None
    ) -> StrategyResult:
        """
        Generate SQL query using Chain-of-Thought reasoning.
        
        Args:
            question: Vietnamese natural language question
            schema_info: Database schema information
            db_id: Database identifier
            examples: Optional examples for CoT reasoning
            
        Returns:
            StrategyResult with generated SQL and metadata
        """
        # Generate unique request ID
        request_id = f"cot_{int(time.time() * 1000000)}"
        
        try:
            # Prepare schema context
            schema_context = self.prepare_schema_context(schema_info)
            
            # Get CoT examples if enabled
            cot_examples = ""
            if self.include_examples:
                if examples is None:
                    examples = self.select_examples(question, db_id, schema_info=schema_info)
                cot_examples = self.format_cot_examples(examples)
            
            # Prepare template variables
            template_vars = {
                'question': question,
                'examples': cot_examples,
                'reasoning_steps': self.reasoning_steps,
                **schema_context
            }
            
            # Load and format template
            template = self.templates.get_template('cot')
            formatted_prompt = template.format(**template_vars)
            
            # Log the request
            print(f"[CoT] Request {request_id}: CoT generation for {db_id}")
            
            # Generate SQL using LLM with CoT reasoning
            start_time = time.time()
            raw_response = self.llm.generate(
                prompt=formatted_prompt,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            latency = time.time() - start_time
            
            # Extract reasoning and SQL from response
            reasoning, sql_query = self._extract_reasoning_and_sql(raw_response)
            
            # Clean the SQL response
            sql_query = self.clean_sql_response(sql_query)
            
            # Validate syntax
            is_valid = self.validate_sql_syntax(sql_query)
            
            # Create result
            result = StrategyResult(
                sql_query=sql_query,
                request_id=request_id,
                reasoning=reasoning or "Chain-of-Thought reasoning applied",
                intermediate_steps=[
                    "1. Parse Vietnamese question",
                    "2. Analyze database schema",
                    "3. Apply step-by-step reasoning",
                    "4. Generate SQL with reasoning",
                    "5. Extract and validate SQL"
                ],
                confidence_score=0.85 if is_valid else 0.4,
                metadata={
                    'strategy': 'cot',
                    'model': self.config.model_name,
                    'latency': latency,
                    'syntax_valid': is_valid,
                    'template_used': self.config.template_path,
                    'prompt_length': len(formatted_prompt),
                    'response_length': len(raw_response),
                    'reasoning_steps': self.reasoning_steps,
                    'include_examples': self.include_examples,
                    'selection_strategy': self.selection_strategy if self.include_examples else 'N/A',
                    'examples_used': len(examples) if examples else 0
                }
            )
            
            # Log successful generation
            print(
                f"[CoT] Request {request_id}: Generated SQL in {latency:.2f}s - Valid: {is_valid}"
            )
            
            # Log detailed execution info
            self.log_strategy_execution(request_id, question, db_id, result)
            
            return result
            
        except Exception as e:
            # Log error and return error result
            error_msg = f"CoT generation failed: {str(e)}"
            print(f"[CoT] Request {request_id}: {error_msg}")
            
            return self.create_error_result(request_id, error_msg, 'cot')

    def _extract_reasoning_and_sql(self, response: str) -> tuple[str, str]:
        """Extract reasoning steps and SQL query from LLM response."""
        # Look for SQL code blocks first
        import re
        
        # Pattern to match SQL code blocks
        sql_pattern = r'```sql\s*\n(.*?)\n```'
        sql_match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if sql_match:
            sql_query = sql_match.group(1).strip()
            # Remove the SQL block from response to get reasoning
            reasoning = re.sub(sql_pattern, '', response, flags=re.DOTALL | re.IGNORECASE).strip()
            return reasoning, sql_query
        
        # Fallback: look for SQL after keywords
        lines = response.strip().split('\n')
        reasoning_lines = []
        sql_lines = []
        in_sql_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering SQL section
            if any(keyword in line.lower() for keyword in ['sql:', 'query:', 'select', 'with']):
                in_sql_section = True
            
            if in_sql_section:
                sql_lines.append(line)
            else:
                reasoning_lines.append(line)
        
        reasoning = '\n'.join(reasoning_lines) if reasoning_lines else ""
        sql = '\n'.join(sql_lines) if sql_lines else response
        
        return reasoning, sql
    
 
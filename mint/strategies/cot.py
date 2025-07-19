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
        self._training_examples = None

    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "cot"
    
    def load_training_examples(self, dataset_path: str, db_id: str = None) -> List[Dict]:
        """Load training examples for CoT reasoning (if enabled)."""
        if not self.include_examples:
            return []
        
        try:
            import json
            from pathlib import Path
            train_file = Path(dataset_path) / "train.json"
            if not train_file.exists():
                print(f"[CoT] Training file not found: {train_file}")
                return []
            
            with open(train_file, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            if db_id:
                filtered_data = [ex for ex in train_data if ex.get('db_id') == db_id]
                if not filtered_data:
                    print(f"[CoT] No examples found for database {db_id}, using all examples")
                    filtered_data = train_data
            else:
                filtered_data = train_data
            
            self._training_examples = filtered_data
            print(f"[CoT] Loaded {len(filtered_data)} training examples for CoT")
            return filtered_data
        except Exception as e:
            print(f"[CoT] Failed to load training examples for CoT: {e}")
            return []

    def select_cot_examples(self, question: str, db_id: str = None) -> List[Dict]:
        """Select examples for CoT reasoning."""
        if not self.include_examples or self.k_examples == 0:
            return []
        
        if self._training_examples is None:
            dataset_path = self.config.dataset_full_path
            self.load_training_examples(dataset_path, db_id)
        
        if not self._training_examples:
            return []
        
        # Select examples that demonstrate step-by-step reasoning
        import random
        if len(self._training_examples) <= self.k_examples:
            return self._training_examples.copy()
        return random.sample(self._training_examples, self.k_examples)

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
                    examples = self.select_cot_examples(question, db_id)
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
    
 
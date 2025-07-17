"""
Zero-shot Strategy Implementation

Implements zero-shot Vietnamese NL2SQL conversion without using examples.
This is the baseline approach that relies on the LLM's pre-trained knowledge.
"""

import time
from typing import Dict, List, Any, Optional
from .base import BaseStrategy, StrategyResult


class ZeroShotStrategy(BaseStrategy):
    """
    Zero-shot strategy for Vietnamese NL2SQL conversion.
    
    This strategy generates SQL queries directly from Vietnamese questions
    without using any examples. It relies on the LLM's pre-trained knowledge
    and carefully crafted prompts.
    """
    
    def _get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "zero-shot"
    
    def generate_sql(
        self, 
        question: str, 
        schema_info: Dict[str, Any], 
        db_id: str,
        examples: Optional[List[Dict]] = None
    ) -> StrategyResult:
        """
        Generate SQL query using zero-shot approach.
        
        Args:
            question: Vietnamese natural language question
            schema_info: Database schema information
            db_id: Database identifier
            examples: Ignored for zero-shot strategy
            
        Returns:
            StrategyResult with generated SQL and metadata
        """
        # Generate unique request ID
        request_id = f"zero_shot_{int(time.time() * 1000000)}"
        
        try:
            # Prepare schema context
            schema_context = self.prepare_schema_context(schema_info)
            
            # Prepare template variables
            template_vars = {
                'question': question,
                'examples': '',  # Empty for zero-shot
                **schema_context
            }
            
            # Load and format template
            template = self.templates.get_template('zero-shot')
            formatted_prompt = template.format(**template_vars)
            
            # Log the request
            self.logger.log_info(f"Request {request_id}: Zero-shot generation for {db_id}")
            
            # Generate SQL using LLM
            start_time = time.time()
            raw_response = self.llm.generate(
                prompt=formatted_prompt,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            latency = time.time() - start_time
            
            # Clean the response
            sql_query = self.clean_sql_response(raw_response)
            
            # Validate syntax
            is_valid = self.validate_sql_syntax(sql_query)
            
            # Create result
            result = StrategyResult(
                sql_query=sql_query,
                request_id=request_id,
                reasoning="Zero-shot generation without examples",
                intermediate_steps=[
                    "1. Parse Vietnamese question",
                    "2. Analyze database schema", 
                    "3. Generate SQL directly",
                    "4. Clean and validate response"
                ],
                confidence_score=0.8 if is_valid else 0.3,
                metadata={
                    'strategy': 'zero-shot',
                    'model': self.config.model_name,
                    'latency': latency,
                    'syntax_valid': is_valid,
                    'template_used': self.config.template_path,
                    'prompt_length': len(formatted_prompt),
                    'response_length': len(raw_response)
                }
            )
            
            # Log successful generation
            self.logger.log_info(
                f"Request {request_id}: Generated SQL in {latency:.2f}s - Valid: {is_valid}"
            )
            
            # Log detailed execution info
            self.log_strategy_execution(request_id, question, db_id, result)
            
            return result
            
        except Exception as e:
            # Log error and return error result
            error_msg = f"Zero-shot generation failed: {str(e)}"
            self.logger.log_error(f"Request {request_id}: {error_msg}")
            
            return self.create_error_result(request_id, error_msg, 'zero-shot')
    
 
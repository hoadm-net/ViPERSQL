"""
Base Strategy Class for ViPERSQL

Defines the common interface and shared functionality for all NL2SQL strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..config import ViPERConfig


@dataclass 
class StrategyResult:
    """Result object returned by strategy execution."""
    sql_query: str
    request_id: str
    reasoning: Optional[str] = None
    intermediate_steps: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseStrategy(ABC):
    """
    Abstract base class for all NL2SQL strategies.
    
    Defines the common interface that all strategies must implement,
    and provides shared functionality for logging, evaluation, etc.
    """
    
    def __init__(self, config: ViPERConfig):
        """
        Initialize strategy with configuration.
        
        Args:
            config: ViPERConfig instance with all settings
        """
        self.config = config
        self.strategy_name = self._get_strategy_name()
        
        # Import dependencies here to avoid circular imports
        from ..llm_interface import LLMInterface
        from ..template_manager import TemplateManager
        
        self.llm = LLMInterface(config)
        self.templates = TemplateManager(config)
        
    @abstractmethod
    def _get_strategy_name(self) -> str:
        """Return the name of this strategy."""
        pass
    
    @abstractmethod
    def generate_sql(
        self, 
        question: str, 
        schema_info: Dict[str, Any], 
        db_id: str,
        examples: Optional[List[Dict]] = None
    ) -> StrategyResult:
        """
        Generate SQL query from Vietnamese question.
        
        Args:
            question: Vietnamese natural language question
            schema_info: Database schema information
            db_id: Database identifier
            examples: Optional examples for few-shot strategies
            
        Returns:
            StrategyResult with generated SQL and metadata
        """
        pass
    
    def prepare_schema_context(self, schema_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare schema information for template formatting.
        
        Args:
            schema_info: Raw schema information from dataset
            
        Returns:
            Formatted schema context for templates
        """
        # Extract and format schema components
        table_names = schema_info.get('table_names', [])
        column_names = schema_info.get('column_names', [])
        foreign_keys = schema_info.get('foreign_keys', [])
        primary_keys = schema_info.get('primary_keys', [])
        
        # Format tables
        tables_str = ', '.join(table_names) if table_names else 'None'
        
        # Format columns (skip the first "*" entry if present)
        if column_names and len(column_names) > 1:
            formatted_columns = []
            for i, (table_idx, col_name) in enumerate(column_names[1:], 1):
                if table_idx < len(table_names):
                    table_name = table_names[table_idx]
                    formatted_columns.append(f"{table_name}.{col_name}")
                else:
                    formatted_columns.append(col_name)
            columns_str = ', '.join(formatted_columns)
        else:
            columns_str = 'None'
        
        # Format foreign keys
        if foreign_keys:
            fk_descriptions = []
            for fk in foreign_keys:
                if len(fk) >= 2 and len(column_names) > max(fk):
                    col1_name = self._get_column_name(fk[0], column_names, table_names)
                    col2_name = self._get_column_name(fk[1], column_names, table_names)
                    fk_descriptions.append(f"{col1_name} -> {col2_name}")
            foreign_keys_str = ', '.join(fk_descriptions) if fk_descriptions else 'None'
        else:
            foreign_keys_str = 'None'
        
        # Format primary keys
        if primary_keys:
            pk_names = []
            for pk in primary_keys:
                if len(column_names) > pk:
                    pk_name = self._get_column_name(pk, column_names, table_names)
                    pk_names.append(pk_name)
            primary_keys_str = ', '.join(pk_names) if pk_names else 'None'
        else:
            primary_keys_str = 'None'
        
        return {
            'tables': tables_str,
            'columns': columns_str,
            'foreign_keys': foreign_keys_str,
            'primary_keys': primary_keys_str
        }
    
    def _get_column_name(self, col_index: int, column_names: List, table_names: List) -> str:
        """Get formatted column name from index."""
        if col_index >= len(column_names):
            return f"column_{col_index}"
        
        table_idx, col_name = column_names[col_index]
        if table_idx >= 0 and table_idx < len(table_names):
            return f"{table_names[table_idx]}.{col_name}"
        else:
            return col_name
    
    def clean_sql_response(self, response: str) -> str:
        """
        Clean and normalize SQL response from LLM.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned SQL query
        """
        # Remove common prefixes/suffixes
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith('```sql'):
            response = response[6:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "SQL Query:",
            "Query:",
            "Answer:",
            "Result:",
            "SQL:"
        ]
        
        for prefix in prefixes_to_remove:
            if response.strip().startswith(prefix):
                response = response.strip()[len(prefix):].strip()
        
        # Remove trailing semicolon if present
        response = response.rstrip(';').strip()
        
        return response
    
    def create_error_result(self, request_id: str, error_msg: str, strategy_name: str) -> StrategyResult:
        """Create standardized error result."""
        return StrategyResult(
            sql_query=f"ERROR: {error_msg}",
            request_id=request_id,
            reasoning=f"Error during {strategy_name} generation: {error_msg}",
            confidence_score=0.0,
            metadata={
                'strategy': strategy_name,
                'error': error_msg,
                'model': self.config.model_name
            }
        )
    
    def validate_sql_syntax(self, sql: str) -> bool:
        """
        Validate SQL syntax using sqlparse.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            import sqlparse
            parsed = sqlparse.parse(sql)
            return len(parsed) > 0 and not any(
                token.ttype is sqlparse.tokens.Error 
                for token in parsed[0].flatten()
            )
        except Exception:
            return False
    
    def generate_batch(
        self,
        questions: List[str],
        schema_infos: List[Dict[str, Any]], 
        db_ids: List[str]
    ) -> List[StrategyResult]:
        """
        Generate SQL queries for multiple questions in batch.
        
        Args:
            questions: List of Vietnamese questions
            schema_infos: List of database schema information
            db_ids: List of database identifiers
            
        Returns:
            List of StrategyResult objects
        """
        if not (len(questions) == len(schema_infos) == len(db_ids)):
            raise ValueError("All input lists must have the same length")
        
        results = []
        total = len(questions)
        
        print(f"Starting {self.strategy_name} batch generation for {total} questions")
        
        for i, (question, schema_info, db_id) in enumerate(zip(questions, schema_infos, db_ids)):
            print(f"Processing {i+1}/{total}: {db_id}")
            
            result = self.generate_sql(question, schema_info, db_id)
            results.append(result)
            
            # Log progress
            if (i + 1) % 10 == 0:
                success_count = sum(1 for r in results if not r.sql_query.startswith("ERROR"))
                print(f"Progress: {i+1}/{total}, Success: {success_count}")
        
        # Log final summary
        success_count = sum(1 for r in results if not r.sql_query.startswith("ERROR"))
        avg_confidence = sum(r.confidence_score or 0 for r in results) / len(results)
        
        print(
            f"{self.strategy_name} batch completed: {success_count}/{total} successful, "
            f"avg confidence: {avg_confidence:.2f}"
        )
        
        return results
    
    def log_strategy_execution(
        self, 
        request_id: str, 
        question: str, 
        db_id: str,
        result: StrategyResult
    ):
        """Log strategy execution details."""
        # The original code had logger.log_request, which was removed.
        # This method is now effectively a no-op or needs to be re-evaluated
        # if specific logging is required. For now, removing the call.
        pass
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(strategy={self.strategy_name})" 
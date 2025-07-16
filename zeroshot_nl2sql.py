#!/usr/bin/env python3
"""
Zero-shot NL2SQL System for ViText2SQL using LangChain
====================================================

A comprehensive zero-shot Natural Language to SQL generation system
specifically designed for Vietnamese ViText2SQL dataset using LangChain.

Features:
- Multiple LLM support (OpenAI GPT-4, Anthropic Claude)
- Comprehensive logging and response tracking
- Detailed evaluation metrics
- Vietnamese language support
- Schema-aware SQL generation
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import sqlparse
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()

class NL2SQLLogger:
    """Comprehensive logging system for NL2SQL operations."""
    
    def __init__(self, log_file: str = "logs/nl2sql_logs.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logging
        logging.basicConfig(
            level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def log_request(self, question: str, db_id: str, schema_info: Dict) -> str:
        """Log incoming request and return request ID."""
        request_id = f"req_{int(time.time() * 1000000)}"
        
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "REQUEST",
            "question": question,
            "db_id": db_id,
            "schema_info": {
                "num_tables": len(schema_info.get('table_names', [])),
                "num_columns": len(schema_info.get('column_names', [])) - 1,  # -1 for "*"
                "tables": schema_info.get('table_names', [])
            }
        }
        
        self._write_log(log_entry)
        self.logger.info(f"Request {request_id}: Processing question for {db_id}")
        return request_id
        
    def log_llm_response(self, request_id: str, model_name: str, prompt: str, 
                        response: str, latency: float, tokens_used: Optional[int] = None):
        """Log LLM response details."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "LLM_RESPONSE",
            "model_name": model_name,
            "prompt": prompt,
            "response": response,
            "latency_seconds": latency,
            "tokens_used": tokens_used,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }
        
        self._write_log(log_entry)
        self.logger.info(f"Request {request_id}: LLM response from {model_name} in {latency:.2f}s")
        
    def log_sql_execution(self, request_id: str, sql_query: str, 
                         execution_success: bool, error_message: Optional[str] = None,
                         execution_time: Optional[float] = None, 
                         result_count: Optional[int] = None):
        """Log SQL execution results."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "SQL_EXECUTION",
            "sql_query": sql_query,
            "execution_success": execution_success,
            "error_message": error_message,
            "execution_time_seconds": execution_time,
            "result_count": result_count,
            "query_complexity": self._analyze_sql_complexity(sql_query)
        }
        
        self._write_log(log_entry)
        status = "SUCCESS" if execution_success else "FAILED"
        self.logger.info(f"Request {request_id}: SQL execution {status}")
        
    def log_evaluation(self, request_id: str, metrics: Dict[str, Any]):
        """Log evaluation metrics."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "EVALUATION",
            "metrics": metrics
        }
        
        self._write_log(log_entry)
        self.logger.info(f"Request {request_id}: Evaluation completed")
        
    def _write_log(self, log_entry: Dict):
        """Write log entry to file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write log: {e}")
            
    def _analyze_sql_complexity(self, sql_query: str) -> Dict[str, Any]:
        """Analyze SQL query complexity."""
        try:
            parsed = sqlparse.parse(sql_query)[0]
            tokens = [token for token in parsed.flatten() if not token.is_whitespace]
            
            keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 
                       'HAVING', 'UNION', 'INTERSECT', 'EXCEPT', 'LIMIT']
            
            complexity = {
                'total_tokens': len(tokens),
                'keywords_used': [kw for kw in keywords if kw.upper() in sql_query.upper()],
                'has_subquery': '(' in sql_query and 'SELECT' in sql_query[sql_query.find('('): ],
                'has_aggregation': any(agg in sql_query.upper() for agg in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']),
                'estimated_difficulty': 'Easy'
            }
            
            score = len(complexity['keywords_used'])
            if complexity['has_subquery']: score += 3
            if complexity['has_aggregation']: score += 2
            
            if score >= 6: complexity['estimated_difficulty'] = 'Extra Hard'
            elif score >= 4: complexity['estimated_difficulty'] = 'Hard'
            elif score >= 2: complexity['estimated_difficulty'] = 'Medium'
            
            return complexity
        except:
            return {'error': 'Failed to parse SQL', 'estimated_difficulty': 'Unknown'}

class VietnameseNL2SQL:
    """Zero-shot NL2SQL system for Vietnamese ViText2SQL dataset."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('TEMPERATURE', 0.1))
        self.max_tokens = int(os.getenv('MAX_TOKENS', 2000))
        self.logger = NL2SQLLogger()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Create prompt template
        self.prompt_template = self._create_prompt_template()
        
        # Create chain
        self.chain = self._create_chain()
        
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on model name."""
        if 'gpt' in self.model_name.lower():
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
        elif 'claude' in self.model_name.lower():
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for Vietnamese NL2SQL."""
        template = """You are an expert in converting Vietnamese natural language questions to SQL queries.

Given a Vietnamese question and database schema, generate a SQL query that answers the question.

Database Schema:
Tables: {tables}
Columns: {columns}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Important Guidelines:
1. Generate ONLY the SQL query without any explanation
2. Use exact table and column names from the schema
3. Handle Vietnamese text carefully - preserve original column values
4. Use proper SQL syntax and formatting
5. Consider relationships between tables when using JOINs
6. Be precise with WHERE conditions

Vietnamese Question: {question}

SQL Query:"""
        
        return PromptTemplate(
            input_variables=["question", "tables", "columns", "foreign_keys", "primary_keys"],
            template=template
        )
    
    def _create_chain(self):
        """Create the LangChain processing chain."""
        return (
            RunnablePassthrough() |
            self.prompt_template |
            self.llm |
            StrOutputParser()
        )
    
    def _format_schema(self, schema_info: Dict) -> Dict[str, str]:
        """Format schema information for the prompt."""
        # Format tables
        tables = "\n".join([f"  {i}: {name}" for i, name in enumerate(schema_info.get('table_names', []))])
        
        # Format columns
        columns = []
        table_names = schema_info.get('table_names', [])
        for i, (table_idx, col_name) in enumerate(schema_info.get('column_names', [])):
            if table_idx == -1:  # Skip "*" column
                continue
            table_name = table_names[table_idx] if table_idx < len(table_names) else "Unknown"
            columns.append(f"  {i}: {table_name}.{col_name}")
        columns_str = "\n".join(columns)
        
        # Format foreign keys
        foreign_keys = []
        for fk in schema_info.get('foreign_keys', []):
            foreign_keys.append(f"  Column {fk[0]} -> Column {fk[1]}")
        foreign_keys_str = "\n".join(foreign_keys) if foreign_keys else "  None"
        
        # Format primary keys
        primary_keys = []
        for pk in schema_info.get('primary_keys', []):
            primary_keys.append(f"  Column {pk}")
        primary_keys_str = "\n".join(primary_keys) if primary_keys else "  None"
        
        return {
            "tables": tables,
            "columns": columns_str,
            "foreign_keys": foreign_keys_str,
            "primary_keys": primary_keys_str
        }
    
    def generate_sql(self, question: str, schema_info: Dict, db_id: str) -> Tuple[str, str]:
        """Generate SQL query for a Vietnamese question."""
        # Log the request
        request_id = self.logger.log_request(question, db_id, schema_info)
        
        try:
            # Format schema
            formatted_schema = self._format_schema(schema_info)
            
            # Prepare input
            input_data = {
                "question": question,
                **formatted_schema
            }
            
            # Create full prompt for logging
            full_prompt = self.prompt_template.format(**input_data)
            
            # Generate SQL
            start_time = time.time()
            sql_response = self.chain.invoke(input_data)
            latency = time.time() - start_time
            
            # Clean up the response
            sql_query = self._clean_sql_response(sql_response)
            
            # Log LLM response
            self.logger.log_llm_response(
                request_id, self.model_name, full_prompt, 
                sql_response, latency
            )
            
            return sql_query, request_id
            
        except Exception as e:
            self.logger.logger.error(f"Request {request_id}: Error generating SQL - {e}")
            return f"ERROR: {str(e)}", request_id
    
    def _clean_sql_response(self, response: str) -> str:
        """Clean and format the SQL response."""
        # Remove common prefixes/suffixes
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith('```sql'):
            response = response[6:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        # Remove extra whitespace and newlines
        response = ' '.join(response.split())
        
        return response.strip()

class NL2SQLEvaluator:
    """Comprehensive evaluation system for NL2SQL predictions."""
    
    def __init__(self, logger: NL2SQLLogger):
        self.logger = logger
        
    def evaluate_prediction(self, request_id: str, predicted_sql: str, 
                          gold_sql: str, db_path: str) -> Dict[str, Any]:
        """Comprehensive evaluation of a single prediction."""
        metrics = {
            "request_id": request_id,
            "predicted_sql": predicted_sql,
            "gold_sql": gold_sql,
            "exact_match": False,
            "execution_accuracy": False,
            "sql_syntax_valid": False,
            "component_accuracy": {},
            "error_analysis": {}
        }
        
        try:
            # 1. Exact Match
            metrics["exact_match"] = self._exact_match(predicted_sql, gold_sql)
            
            # 2. SQL Syntax Validation
            metrics["sql_syntax_valid"] = self._validate_sql_syntax(predicted_sql)
            
            # 3. Component-wise Analysis
            metrics["component_accuracy"] = self._component_analysis(predicted_sql, gold_sql)
            
            # 4. Execution Accuracy
            if os.path.exists(db_path):
                metrics["execution_accuracy"] = self._execution_accuracy(
                    predicted_sql, gold_sql, db_path, request_id
                )
            
            # 5. Error Analysis
            if not metrics["exact_match"]:
                metrics["error_analysis"] = self._error_analysis(predicted_sql, gold_sql)
                
        except Exception as e:
            metrics["evaluation_error"] = str(e)
            self.logger.logger.error(f"Request {request_id}: Evaluation error - {e}")
        
        # Log evaluation results
        self.logger.log_evaluation(request_id, metrics)
        
        return metrics
    
    def _exact_match(self, predicted: str, gold: str) -> bool:
        """Check exact match after normalization."""
        def normalize_sql(sql):
            # Basic normalization
            sql = sql.strip().lower()
            sql = ' '.join(sql.split())  # Normalize whitespace
            return sql
        
        return normalize_sql(predicted) == normalize_sql(gold)
    
    def _validate_sql_syntax(self, sql: str) -> bool:
        """Validate SQL syntax using sqlparse."""
        try:
            parsed = sqlparse.parse(sql)
            return len(parsed) > 0 and not any(token.ttype is sqlparse.tokens.Error 
                                              for token in parsed[0].flatten())
        except:
            return False
    
    def _component_analysis(self, predicted: str, gold: str) -> Dict[str, bool]:
        """Analyze individual SQL components."""
        def extract_components(sql):
            try:
                sql_upper = sql.upper()
                components = {
                    'SELECT': 'SELECT' in sql_upper,
                    'FROM': 'FROM' in sql_upper,
                    'WHERE': 'WHERE' in sql_upper,
                    'GROUP BY': 'GROUP BY' in sql_upper,
                    'ORDER BY': 'ORDER BY' in sql_upper,
                    'HAVING': 'HAVING' in sql_upper,
                    'LIMIT': 'LIMIT' in sql_upper,
                    'JOIN': 'JOIN' in sql_upper,
                    'UNION': 'UNION' in sql_upper
                }
                return components
            except:
                return {}
        
        pred_components = extract_components(predicted)
        gold_components = extract_components(gold)
        
        accuracy = {}
        for component in gold_components:
            accuracy[component] = (component in pred_components and 
                                 pred_components[component] == gold_components[component])
        
        return accuracy
    
    def _execution_accuracy(self, predicted: str, gold: str, db_path: str, request_id: str) -> bool:
        """Check if predicted SQL produces the same results as gold SQL."""
        try:
            conn = sqlite3.connect(db_path)
            
            # Execute gold query
            start_time = time.time()
            gold_cursor = conn.execute(gold)
            gold_results = gold_cursor.fetchall()
            gold_time = time.time() - start_time
            
            self.logger.log_sql_execution(
                request_id + "_gold", gold, True, 
                execution_time=gold_time, result_count=len(gold_results)
            )
            
            # Execute predicted query
            try:
                start_time = time.time()
                pred_cursor = conn.execute(predicted)
                pred_results = pred_cursor.fetchall()
                pred_time = time.time() - start_time
                
                self.logger.log_sql_execution(
                    request_id + "_pred", predicted, True,
                    execution_time=pred_time, result_count=len(pred_results)
                )
                
                conn.close()
                return set(gold_results) == set(pred_results)
                
            except Exception as e:
                self.logger.log_sql_execution(
                    request_id + "_pred", predicted, False, 
                    error_message=str(e)
                )
                conn.close()
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Database execution error: {e}")
            return False
    
    def _error_analysis(self, predicted: str, gold: str) -> Dict[str, Any]:
        """Analyze types of errors in prediction."""
        analysis = {
            "length_difference": len(predicted.split()) - len(gold.split()),
            "missing_keywords": [],
            "extra_keywords": [],
            "structural_differences": []
        }
        
        try:
            pred_upper = predicted.upper()
            gold_upper = gold.upper()
            
            keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN']
            
            for keyword in keywords:
                if keyword in gold_upper and keyword not in pred_upper:
                    analysis["missing_keywords"].append(keyword)
                elif keyword in pred_upper and keyword not in gold_upper:
                    analysis["extra_keywords"].append(keyword)
        except:
            analysis["parsing_error"] = True
        
        return analysis

def main():
    """Main function to demonstrate the Zero-shot NL2SQL system."""
    print("🚀 ViPERSQL Zero-shot NL2SQL System")
    print("=" * 50)
    
    # Initialize system
    nl2sql = VietnameseNL2SQL()
    evaluator = NL2SQLEvaluator(nl2sql.logger)
    
    # Load sample data for testing
    try:
        from sample_viewer import load_dataset, load_tables
        
        # Load a few samples for testing
        dataset_path = "dataset/ViText2SQL/syllable-level"
        train_data = load_dataset(dataset_path, "train")
        tables = load_tables(dataset_path)
        
        print(f"✅ Loaded {len(train_data)} training samples")
        print(f"✅ Loaded {len(tables)} database schemas")
        
        # Test with first few samples
        test_samples = train_data[:3]  # Test with first 3 samples
        
        results = []
        
        for i, sample in enumerate(test_samples):
            print(f"\n📝 Processing Sample {i+1}/3")
            print(f"Question: {sample['question']}")
            print(f"Database: {sample['db_id']}")
            
            # Get schema info
            schema_info = tables.get(sample['db_id'])
            if not schema_info:
                print(f"❌ Schema not found for {sample['db_id']}")
                continue
            
            # Generate SQL
            predicted_sql, request_id = nl2sql.generate_sql(
                sample['question'], schema_info, sample['db_id']
            )
            
            print(f"Generated SQL: {predicted_sql}")
            print(f"Gold SQL: {sample['query']}")
            
            # Evaluate
            db_path = f"sqlite_dbs/syllable-level/{sample['db_id']}.sqlite"
            metrics = evaluator.evaluate_prediction(
                request_id, predicted_sql, sample['query'], db_path
            )
            
            results.append(metrics)
            
            # Print evaluation results
            print(f"✅ Exact Match: {metrics['exact_match']}")
            print(f"✅ Syntax Valid: {metrics['sql_syntax_valid']}")
            print(f"✅ Execution Accuracy: {metrics['execution_accuracy']}")
            print("-" * 40)
        
        # Summary
        exact_matches = sum(1 for r in results if r['exact_match'])
        syntax_valid = sum(1 for r in results if r['sql_syntax_valid'])
        execution_accurate = sum(1 for r in results if r['execution_accuracy'])
        
        print(f"\n📊 SUMMARY RESULTS")
        print(f"Exact Match: {exact_matches}/{len(results)} ({exact_matches/len(results)*100:.1f}%)")
        print(f"Syntax Valid: {syntax_valid}/{len(results)} ({syntax_valid/len(results)*100:.1f}%)")
        print(f"Execution Accuracy: {execution_accurate}/{len(results)} ({execution_accurate/len(results)*100:.1f}%)")
        
        print(f"\n📄 Logs saved to: {nl2sql.logger.log_file}")
        
    except ImportError:
        print("❌ Error: sample_viewer module not found. Please ensure it's in the same directory.")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure the dataset is properly loaded.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 
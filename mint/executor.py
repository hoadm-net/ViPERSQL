"""
SQL Executor module for MINT package.
Provides SQLExecutor class for executing SQL queries and comparing results.
"""

import sqlite3
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from .utils import normalize_sql

class SQLExecutor:
    """
    A class to execute SQL queries on SQLite databases and compare results.
    
    This class provides functionality to run SQL queries, handle timeouts,
    and compare execution results for evaluation purposes.
    """
    
    def __init__(self, db_directory: str = "sqlite_dbs", timeout: int = 30):
        """
        Initialize SQLExecutor.
        
        Args:
            db_directory (str): Directory containing SQLite databases
            timeout (int): Query execution timeout in seconds
        """
        self.db_directory = Path(db_directory)
        self.timeout = timeout
        self.logger = self._setup_logger()
        
        if not self.db_directory.exists():
            raise FileNotFoundError(f"Database directory {db_directory} not found")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the executor."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_database_path(self, db_name: str) -> Path:
        """
        Get full path to database file.
        
        Args:
            db_name (str): Database name (with or without .db extension)
            
        Returns:
            Path: Full path to database file
        """
        if not db_name.endswith('.db'):
            db_name += '.db'
        return self.db_directory / db_name
    
    def _execute_with_timeout(self, cursor: sqlite3.Cursor, query: str) -> Tuple[List[Tuple], Optional[str]]:
        """
        Execute query with timeout handling.
        
        Args:
            cursor (sqlite3.Cursor): Database cursor
            query (str): SQL query to execute
            
        Returns:
            Tuple[List[Tuple], Optional[str]]: Query results and error message
        """
        try:
            start_time = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            execution_time = time.time() - start_time
            
            if execution_time > self.timeout:
                return [], f"Query timeout after {execution_time:.2f}s"
            
            return results, None
            
        except sqlite3.Error as e:
            return [], f"SQLite error: {str(e)}"
        except Exception as e:
            return [], f"Execution error: {str(e)}"
    
    def execute_query(self, query: str, db_name: str) -> Dict[str, Any]:
        """
        Execute a single SQL query.
        
        Args:
            query (str): SQL query to execute
            db_name (str): Database name
            
        Returns:
            Dict[str, Any]: Execution result with metadata
        """
        db_path = self._get_database_path(db_name)
        
        if not db_path.exists():
            return {
                'success': False,
                'error': f"Database {db_name} not found",
                'results': [],
                'execution_time': 0,
                'row_count': 0
            }
        
        try:
            start_time = time.time()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Execute query
            results, error = self._execute_with_timeout(cursor, query)
            execution_time = time.time() - start_time
            
            conn.close()
            
            if error:
                return {
                    'success': False,
                    'error': error,
                    'results': [],
                    'execution_time': execution_time,
                    'row_count': 0
                }
            
            return {
                'success': True,
                'error': None,
                'results': results,
                'execution_time': execution_time,
                'row_count': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection error: {str(e)}",
                'results': [],
                'execution_time': time.time() - start_time if 'start_time' in locals() else 0,
                'row_count': 0
            }
    
    def compare_results(self, result1: List[Tuple], result2: List[Tuple]) -> Dict[str, Any]:
        """
        Compare two query result sets.
        
        Args:
            result1 (List[Tuple]): First result set
            result2 (List[Tuple]): Second result set
            
        Returns:
            Dict[str, Any]: Comparison result
        """
        # Convert to sets for comparison (order-independent)
        set1 = set(result1) if result1 else set()
        set2 = set(result2) if result2 else set()
        
        exact_match = set1 == set2
        
        # Calculate overlap metrics
        if len(set1) == 0 and len(set2) == 0:
            precision = recall = f1 = 1.0
        elif len(set1) == 0 or len(set2) == 0:
            precision = recall = f1 = 0.0
        else:
            intersection = set1.intersection(set2)
            precision = len(intersection) / len(set1) if set1 else 0
            recall = len(intersection) / len(set2) if set2 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'exact_match': exact_match,
            'result1_count': len(result1) if result1 else 0,
            'result2_count': len(result2) if result2 else 0,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'common_rows': len(set1.intersection(set2)) if set1 and set2 else 0
        }
    
    def execute_and_compare(self, query1: str, query2: str, db_name: str) -> Dict[str, Any]:
        """
        Execute two queries and compare their results.
        
        Args:
            query1 (str): First SQL query (usually predicted)
            query2 (str): Second SQL query (usually gold/reference)
            db_name (str): Database name
            
        Returns:
            Dict[str, Any]: Comparison result with execution details
        """
        # Execute both queries
        result1 = self.execute_query(query1, db_name)
        result2 = self.execute_query(query2, db_name)
        
        # Compare results if both succeeded
        comparison = None
        if result1['success'] and result2['success']:
            comparison = self.compare_results(result1['results'], result2['results'])
        
        return {
            'query1_result': result1,
            'query2_result': result2,
            'comparison': comparison,
            'both_successful': result1['success'] and result2['success']
        }
    
    def batch_execute(self, queries: List[str], db_name: str) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in batch.
        
        Args:
            queries (List[str]): List of SQL queries
            db_name (str): Database name
            
        Returns:
            List[Dict[str, Any]]: List of execution results
        """
        results = []
        
        for i, query in enumerate(queries):
            self.logger.info(f"Executing query {i+1}/{len(queries)}")
            result = self.execute_query(query, db_name)
            results.append(result)
        
        return results
    
    def batch_compare(self, query_pairs: List[Tuple[str, str]], db_name: str) -> List[Dict[str, Any]]:
        """
        Execute and compare multiple query pairs in batch.
        
        Args:
            query_pairs (List[Tuple[str, str]]): List of (predicted, gold) query pairs
            db_name (str): Database name
            
        Returns:
            List[Dict[str, Any]]: List of comparison results
        """
        results = []
        
        for i, (pred_query, gold_query) in enumerate(query_pairs):
            self.logger.info(f"Comparing queries {i+1}/{len(query_pairs)}")
            result = self.execute_and_compare(pred_query, gold_query, db_name)
            results.append(result)
        
        return results
    
    def get_execution_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate execution statistics from batch results.
        
        Args:
            results (List[Dict[str, Any]]): List of execution results
            
        Returns:
            Dict[str, Any]: Execution statistics
        """
        total_queries = len(results)
        successful_queries = sum(1 for r in results if r.get('success', False))
        
        if successful_queries > 0:
            execution_times = [r['execution_time'] for r in results if r.get('success', False)]
            avg_execution_time = sum(execution_times) / len(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
        else:
            avg_execution_time = max_execution_time = min_execution_time = 0
        
        # Count error types
        error_types = {}
        for result in results:
            if not result.get('success', False) and result.get('error'):
                error_type = result['error'].split(':')[0]  # Get first part of error message
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': total_queries - successful_queries,
            'success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max_execution_time,
            'min_execution_time': min_execution_time,
            'error_types': error_types
        }
    
    def get_comparison_stats(self, comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comparison statistics from batch comparison results.
        
        Args:
            comparison_results (List[Dict[str, Any]]): List of comparison results
            
        Returns:
            Dict[str, Any]: Comparison statistics
        """
        total_comparisons = len(comparison_results)
        valid_comparisons = sum(1 for r in comparison_results if r.get('both_successful', False))
        
        if valid_comparisons == 0:
            return {
                'total_comparisons': total_comparisons,
                'valid_comparisons': 0,
                'execution_accuracy': 0.0,
                'avg_precision': 0.0,
                'avg_recall': 0.0,
                'avg_f1_score': 0.0
            }
        
        # Calculate metrics for valid comparisons
        exact_matches = 0
        precisions = []
        recalls = []
        f1_scores = []
        
        for result in comparison_results:
            if result.get('both_successful', False) and result.get('comparison'):
                comp = result['comparison']
                if comp['exact_match']:
                    exact_matches += 1
                precisions.append(comp['precision'])
                recalls.append(comp['recall'])
                f1_scores.append(comp['f1_score'])
        
        return {
            'total_comparisons': total_comparisons,
            'valid_comparisons': valid_comparisons,
            'execution_accuracy': exact_matches / valid_comparisons,
            'avg_precision': sum(precisions) / len(precisions) if precisions else 0,
            'avg_recall': sum(recalls) / len(recalls) if recalls else 0,
            'avg_f1_score': sum(f1_scores) / len(f1_scores) if f1_scores else 0
        }
    
    def test_database_connection(self, db_name: str) -> Dict[str, Any]:
        """
        Test database connection and basic functionality.
        
        Args:
            db_name (str): Database name to test
            
        Returns:
            Dict[str, Any]: Test results
        """
        db_path = self._get_database_path(db_name)
        
        if not db_path.exists():
            return {
                'success': False,
                'error': f"Database {db_name} not found",
                'tables': []
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Test simple query on each table
            table_tests = {}
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}" LIMIT 1;')
                    count = cursor.fetchone()[0]
                    table_tests[table] = {'success': True, 'row_count': count}
                except Exception as e:
                    table_tests[table] = {'success': False, 'error': str(e)}
            
            conn.close()
            
            return {
                'success': True,
                'error': None,
                'tables': tables,
                'table_count': len(tables),
                'table_tests': table_tests
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection error: {str(e)}",
                'tables': []
            } 
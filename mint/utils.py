"""
Utility functions for MINT package.
Provides common functions for data loading, SQL normalization, and other helpers.
"""

import re
import json
import sqlparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

def normalize_sql(query: str) -> str:
    """
    Normalize SQL query for comparison.
    
    Args:
        query (str): SQL query to normalize
        
    Returns:
        str: Normalized SQL query
    """
    if not query or not isinstance(query, str):
        return ""
    
    try:
        # Parse and format the SQL
        parsed = sqlparse.parse(query)[0]
        formatted = sqlparse.format(
            str(parsed),
            reindent=True,
            strip_comments=True,
            keyword_case='upper',
            identifier_case='lower'
        )
        
        # Additional normalization
        # Remove extra whitespace
        formatted = re.sub(r'\s+', ' ', formatted)
        
        # Remove trailing semicolon
        formatted = formatted.rstrip(';').strip()
        
        return formatted.lower()
        
    except Exception:
        # Fallback normalization if parsing fails
        normalized = query.strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Collapse whitespace
        normalized = normalized.rstrip(';')  # Remove trailing semicolon
        return normalized.lower()

def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    """
    Load dataset from JSON file.
    
    Args:
        file_path (str): Path to JSON dataset file
        
    Returns:
        List[Dict[str, Any]]: Loaded dataset
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise FileNotFoundError(f"Failed to load dataset from {file_path}: {e}")

def extract_queries_from_dataset(dataset: List[Dict[str, Any]], query_key: str = 'query') -> List[str]:
    """
    Extract SQL queries from dataset.
    
    Args:
        dataset (List[Dict[str, Any]]): Dataset containing SQL queries
        query_key (str): Key name for SQL query in dataset
        
    Returns:
        List[str]: List of SQL queries
    """
    queries = []
    for item in dataset:
        if query_key in item:
            queries.append(item[query_key])
        else:
            # Try common alternative keys
            alt_keys = ['sql', 'SQL', 'query_sql', 'target']
            for alt_key in alt_keys:
                if alt_key in item:
                    queries.append(item[alt_key])
                    break
            else:
                queries.append("")  # Empty query if not found
    
    return queries

def extract_database_names_from_dataset(dataset: List[Dict[str, Any]], db_key: str = 'db_id') -> List[str]:
    """
    Extract database names from dataset.
    
    Args:
        dataset (List[Dict[str, Any]]): Dataset containing database references
        db_key (str): Key name for database ID in dataset
        
    Returns:
        List[str]: List of database names
    """
    db_names = []
    for item in dataset:
        if db_key in item:
            db_names.append(item[db_key])
        else:
            # Try common alternative keys
            alt_keys = ['database', 'db_name', 'database_id']
            for alt_key in alt_keys:
                if alt_key in item:
                    db_names.append(item[alt_key])
                    break
            else:
                db_names.append("")  # Empty if not found
    
    return db_names

def safe_execute_sql(query: str) -> bool:
    """
    Check if SQL query is safe to execute (basic validation).
    
    Args:
        query (str): SQL query to check
        
    Returns:
        bool: True if query appears safe, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    query_upper = query.upper().strip()
    
    # Check for dangerous operations
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
        'CREATE', 'TRUNCATE', 'REPLACE', 'MERGE'
    ]
    
    for keyword in dangerous_keywords:
        if f' {keyword} ' in f' {query_upper} ':
            return False
    
    # Must contain SELECT
    if 'SELECT' not in query_upper:
        return False
    
    return True

def create_query_pairs(predicted_queries: List[str], gold_queries: List[str]) -> List[tuple]:
    """
    Create pairs of predicted and gold queries for comparison.
    
    Args:
        predicted_queries (List[str]): Predicted SQL queries
        gold_queries (List[str]): Gold/reference SQL queries
        
    Returns:
        List[tuple]: List of (predicted, gold) query pairs
    """
    if len(predicted_queries) != len(gold_queries):
        raise ValueError("Predicted and gold query lists must have the same length")
    
    return list(zip(predicted_queries, gold_queries))

def batch_normalize_queries(queries: List[str]) -> List[str]:
    """
    Normalize a batch of SQL queries.
    
    Args:
        queries (List[str]): List of SQL queries to normalize
        
    Returns:
        List[str]: List of normalized SQL queries
    """
    return [normalize_sql(query) for query in queries]

def get_query_statistics(queries: List[str]) -> Dict[str, Any]:
    """
    Get statistics about a list of SQL queries.
    
    Args:
        queries (List[str]): List of SQL queries
        
    Returns:
        Dict[str, Any]: Query statistics
    """
    if not queries:
        return {
            'total_queries': 0,
            'avg_length': 0,
            'max_length': 0,
            'min_length': 0,
            'empty_queries': 0,
            'unique_queries': 0
        }
    
    lengths = [len(query) for query in queries]
    empty_count = sum(1 for query in queries if not query.strip())
    unique_count = len(set(queries))
    
    return {
        'total_queries': len(queries),
        'avg_length': sum(lengths) / len(lengths),
        'max_length': max(lengths),
        'min_length': min(lengths),
        'empty_queries': empty_count,
        'unique_queries': unique_count
    }

def validate_dataset_format(dataset: List[Dict[str, Any]], 
                          required_keys: List[str] = None) -> Dict[str, Any]:
    """
    Validate dataset format and check for required keys.
    
    Args:
        dataset (List[Dict[str, Any]]): Dataset to validate
        required_keys (List[str]): Required keys in each dataset item
        
    Returns:
        Dict[str, Any]: Validation results
    """
    if required_keys is None:
        required_keys = ['question', 'query', 'db_id']
    
    validation_result = {
        'valid': True,
        'total_items': len(dataset),
        'issues': [],
        'missing_keys': {},
        'empty_values': {}
    }
    
    if not isinstance(dataset, list):
        validation_result['valid'] = False
        validation_result['issues'].append("Dataset must be a list")
        return validation_result
    
    # Check each item
    for i, item in enumerate(dataset):
        if not isinstance(item, dict):
            validation_result['valid'] = False
            validation_result['issues'].append(f"Item {i} is not a dictionary")
            continue
        
        # Check required keys
        for key in required_keys:
            if key not in item:
                if key not in validation_result['missing_keys']:
                    validation_result['missing_keys'][key] = []
                validation_result['missing_keys'][key].append(i)
                validation_result['valid'] = False
            elif not item[key] or (isinstance(item[key], str) and not item[key].strip()):
                if key not in validation_result['empty_values']:
                    validation_result['empty_values'][key] = []
                validation_result['empty_values'][key].append(i)
    
    return validation_result

def filter_valid_queries(dataset: List[Dict[str, Any]], 
                        query_key: str = 'query') -> List[Dict[str, Any]]:
    """
    Filter dataset to keep only items with valid SQL queries.
    
    Args:
        dataset (List[Dict[str, Any]]): Dataset to filter
        query_key (str): Key name for SQL query in dataset
        
    Returns:
        List[Dict[str, Any]]: Filtered dataset with valid queries
    """
    valid_items = []
    
    for item in dataset:
        if query_key in item and item[query_key]:
            query = item[query_key]
            if isinstance(query, str) and query.strip() and safe_execute_sql(query):
                valid_items.append(item)
    
    return valid_items

def save_results_to_json(results: Dict[str, Any], output_path: str) -> None:
    """
    Save evaluation results to JSON file.
    
    Args:
        results (Dict[str, Any]): Results to save
        output_path (str): Output file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to save results to {output_path}: {e}")

def load_results_from_json(input_path: str) -> Dict[str, Any]:
    """
    Load evaluation results from JSON file.
    
    Args:
        input_path (str): Input file path
        
    Returns:
        Dict[str, Any]: Loaded results
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Failed to load results from {input_path}: {e}")

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a decimal value as percentage string.
    
    Args:
        value (float): Decimal value (0.0 to 1.0)
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value * 100:.{decimal_places}f}%"

def create_directory_if_not_exists(directory_path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory_path (str): Directory path to create
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True) 
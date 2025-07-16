"""
MINT - Modern Integration for Natural language Text-to-SQL

A comprehensive toolkit for evaluating Vietnamese Text-to-SQL models.
Provides database creation, SQL execution, and evaluation metrics.
"""

from .database import SQLiteBuilder
from .executor import SQLExecutor  
from .metrics import EvaluationMetrics
from .utils import load_dataset, normalize_sql

__version__ = "1.0.0"
__author__ = "Vi_NL2SQL Research Team"

__all__ = [
    "SQLiteBuilder",
    "SQLExecutor", 
    "EvaluationMetrics",
    "load_dataset",
    "normalize_sql"
]

"""
Evaluation Metrics module for MINT package.
Provides comprehensive evaluation metrics for Text-to-SQL models.
"""

import re
import json
import sqlparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
from .utils import normalize_sql, load_dataset

class EvaluationMetrics:
    """
    A comprehensive evaluation metrics calculator for Text-to-SQL models.
    
    Provides various metrics including exact match, component-wise accuracy,
    SQL similarity, and difficulty-based analysis.
    """
    
    def __init__(self):
        """Initialize EvaluationMetrics."""
        self.difficulty_classifier = SQLDifficultyClassifier()
    
    def exact_match_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> float:
        """
        Calculate exact match accuracy between predicted and gold queries.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            float: Exact match accuracy (0.0 to 1.0)
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        if not predicted_queries:
            return 0.0
        
        exact_matches = 0
        for pred, gold in zip(predicted_queries, gold_queries):
            pred_normalized = normalize_sql(pred)
            gold_normalized = normalize_sql(gold)
            
            if pred_normalized == gold_normalized:
                exact_matches += 1
        
        return exact_matches / len(predicted_queries)
    
    def component_wise_f1_score(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, float]:
        """
        Calculate F1-score for SQL clauses using set-based component matching.
        
        For each SQL clause (SELECT, WHERE, ORDER BY, GROUP BY, KEYWORDS):
        - Extract components as sets
        - Calculate Precision = |Predicted ∩ Gold| / |Predicted|
        - Calculate Recall = |Predicted ∩ Gold| / |Gold|
        - F1 = 2× (P × R) / (P + R)
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            Dict[str, float]: F1-score for each SQL clause
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        # Define all SQL clauses to evaluate
        clauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'KEYWORDS']
        clause_stats = {clause: {'tp': 0, 'fp': 0, 'fn': 0} for clause in clauses}
        
        for pred, gold in zip(predicted_queries, gold_queries):
            # Extract components as sets for each clause
            pred_components = self._extract_components_as_sets(pred)
            gold_components = self._extract_components_as_sets(gold)
            
            # Evaluate each clause using set-based matching
            for clause in clauses:
                pred_set = pred_components.get(clause, set())
                gold_set = gold_components.get(clause, set())
                
                # Calculate intersection
                intersection = pred_set & gold_set
                
                # Calculate precision and recall
                precision = len(intersection) / len(pred_set) if len(pred_set) > 0 else 0.0
                recall = len(intersection) / len(gold_set) if len(gold_set) > 0 else 0.0
                
                # Calculate F1-score for this query
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                # Accumulate for overall statistics
                if len(gold_set) > 0:  # Only count if gold has this clause
                    if f1_score > 0:
                        clause_stats[clause]['tp'] += 1
                    else:
                        clause_stats[clause]['fn'] += 1
                
                if len(pred_set) > 0 and len(gold_set) == 0:  # Extra clause
                    clause_stats[clause]['fp'] += 1        
        # Calculate overall F1-score for each clause
        f1_scores = {}
        for clause, stats in clause_stats.items():
            precision = stats['tp'] / (stats['tp'] + stats['fp']) if (stats['tp'] + stats['fp']) > 0 else 0.0
            recall = stats['tp'] / (stats['tp'] + stats['fn']) if (stats['tp'] + stats['fn']) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores[clause] = f1_score
        
        return f1_scores
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract SQL keywords from a query.
        
        Args:
            query (str): SQL query string
            
        Returns:
            List[str]: List of SQL keywords found in the query
        """
        query_upper = query.upper()
        keywords = []
        
        # Common SQL keywords
        sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
            'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
            'UNION', 'INTERSECT', 'EXCEPT', 'WITH', 'AS INCT',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN', 'END',
            'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'LIKE', 'BETWEEN', 'IS NULL', 'NULL',
            'ASC', 'DESC', 'LIMIT', 'OFFSET'
        ]
        
        for keyword in sql_keywords:
            if keyword in query_upper:
                keywords.append(keyword)
        
        return keywords
    
    def _normalize_component(self, component: str) -> str:
        """
        Normalize a SQL component for comparison.
        
        Args:
            component (str): SQL component string
            
        Returns:
            str: Normalized component
        """
        if not component:
            return ""
        # Remove extra whitespace and convert to lowercase
        normalized = " ".join(component.split()).lower()
        return normalized

    def component_wise_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, float]:
        """
        Calculate component-wise accuracy for SQL clauses.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            Dict[str, float]: Component-wise accuracy scores
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        components = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
        component_matches = {comp: 0 for comp in components}
        component_totals = {comp: 0 for comp in components}
        
        for pred, gold in zip(predicted_queries, gold_queries):
            pred_components = self._extract_sql_components(pred)
            gold_components = self._extract_sql_components(gold)
            
            for component in components:
                if component in gold_components:
                    component_totals[component] += 1
                    
                    if (component in pred_components and 
                        self._normalize_component(pred_components[component]) == self._normalize_component(gold_components[component])):
                        component_matches[component] += 1        
        # Calculate accuracy for each component
        accuracies = {}
        for component in components:
            if component_totals[component] > 0:
                accuracies[component] = component_matches[component] / component_totals[component]
            else:
                accuracies[component] = 1.0 # Perfect score if component never appears
        
        return accuracies
    
    def sql_similarity(self, predicted_queries: List[str], gold_queries: List[str]) -> List[float]:
        """
        Calculate SQL similarity scores using string similarity.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            List[float]: Similarity scores for each query pair
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        similarities = []
        for pred, gold in zip(predicted_queries, gold_queries):
            pred_normalized = normalize_sql(pred)
            gold_normalized = normalize_sql(gold)
            
            similarity = SequenceMatcher(None, pred_normalized, gold_normalized).ratio()
            similarities.append(similarity)
        
        return similarities
    
    def difficulty_breakdown_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate accuracy breakdown by SQL difficulty level.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            Dict[str, Dict[str, Any]]: Accuracy breakdown by difficulty
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        # Classify queries by difficulty
        difficulty_groups = defaultdict(list)
        for i, (pred, gold) in enumerate(zip(predicted_queries, gold_queries)):
            difficulty = self.difficulty_classifier.classify_query(gold)
            difficulty_groups[difficulty].append((i, pred, gold))
        
        # Calculate accuracy for each difficulty level
        breakdown = {}
        for difficulty, queries in difficulty_groups.items():
            if not queries:
                continue
                
            exact_matches = 0
            similarities = []
            
            for _, pred, gold in queries:
                # Exact match
                pred_normalized = normalize_sql(pred)
                gold_normalized = normalize_sql(gold)
                if pred_normalized == gold_normalized:
                    exact_matches += 1
                
                # Similarity
                similarity = SequenceMatcher(None, pred_normalized, gold_normalized).ratio()
                similarities.append(similarity)
            
            breakdown[difficulty] = {
                'count': len(queries),
                'exact_match_accuracy': exact_matches / len(queries),
                'avg_similarity': sum(similarities) / len(similarities),
                'percentage_of_total': len(queries) / len(predicted_queries) * 100
            }
        
        return breakdown
    
    def _extract_sql_components(self, query: str) -> Dict[str, str]:
        """
        Extract SQL components from a query.
        
        Args:
            query (str): SQL query string
            
        Returns:
            Dict[str, str]: Dictionary of SQL components
        """
        try:
            parsed = sqlparse.parse(query)[0]
            components = {}
            
            # Convert to string and split by keywords
            query_upper = query.upper()
            
            # Extract SELECT
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
            if select_match:
                components['SELECT'] = select_match.group(1).strip()
            
            # Extract FROM
            from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if from_match:
                components['FROM'] = from_match.group(1).strip()
            
            # Extract WHERE
            where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if where_match:
                components['WHERE'] = where_match.group(1).strip()
            
            # Extract GROUP BY
            group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if group_match:
                components['GROUP BY'] = group_match.group(1).strip()
            
            # Extract ORDER BY
            order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+HAVING|$)', query_upper, re.DOTALL)
            if order_match:
                components['ORDER BY'] = order_match.group(1).strip()
            
            # Extract HAVING
            having_match = re.search(r'HAVING\s+(.*?)$', query_upper, re.DOTALL)
            if having_match:
                components['HAVING'] = having_match.group(1).strip()
            
            return components
            
        except Exception:
            return {}
    
    def _extract_components_as_sets(self, query: str) -> Dict[str, set]:
        """
        Extract SQL components as sets of individual elements.
        
        Args:
            query (str): SQL query string
            
        Returns:
            Dict[str, set]: Dictionary mapping clause names to sets of components
        """
        components = {}
        query_upper = query.upper()
        
        # Extract SELECT components (columns)
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
        if select_match:
            select_clause = select_match.group(1).strip()
            select_components = self._parse_select_clause(select_clause)
            components['SELECT'] = select_components
        
        # Extract FROM components (tables)
        from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
        if from_match:
            from_clause = from_match.group(1).strip()
            from_components = self._parse_from_clause(from_clause)
            components['FROM'] = from_components
        
        # Extract WHERE components (conditions)
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            where_components = self._parse_where_clause(where_clause)
            components['WHERE'] = where_components
        
        # Extract GROUP BY components
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
        if group_match:
            group_clause = group_match.group(1).strip()
            group_components = self._parse_group_by_clause(group_clause)
            components['GROUP BY'] = group_components
        
        # Extract ORDER BY components
        order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+HAVING|$)', query_upper, re.DOTALL)
        if order_match:
            order_clause = order_match.group(1).strip()
            order_components = self._parse_order_by_clause(order_clause)
            components['ORDER BY'] = order_components
        
        # Extract HAVING components
        having_match = re.search(r'HAVING\s+(.*?)$', query_upper, re.DOTALL)
        if having_match:
            having_clause = having_match.group(1).strip()
            having_components = self._parse_having_clause(having_clause)
            components['HAVING'] = having_components
        
        # Extract KEYWORDS
        keywords = self._extract_keywords(query)
        components['KEYWORDS'] = set(keywords)
        
        return components
    
    def _parse_select_clause(self, clause: str) -> set:
        """
        Parse SELECT clause into set of column identifiers.
        """
        components = set()
        # Split by comma and clean up
        parts = [part.strip() for part in clause.split(',')]
        for part in parts:
            # Remove AS aliases
            if ' AS ' in part.upper():
                part = part.split(' AS ')[0].strip()
            # Remove function calls, keep column names
            if '(' in part and ')' in part:
                # Extract column name from function calls like COUNT(*), SUM(column)
                match = re.search(r'\(([^)]+)\)', part)
                if match:
                    components.add(match.group(1).strip())
            else:
                components.add(part)
        return components
    
    def _parse_from_clause(self, clause: str) -> set:
        """
        Parse FROM clause into set of table identifiers.
        """
        components = set()
        # Split by JOIN, LEFT JOIN, etc.
        parts = re.split(r'\b(?:JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN)\b', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part:
                # Extract table name (remove alias)
                if ' AS ' in part.upper():
                    table_name = part.split(' AS ')[0].strip()
                elif part and not part.startswith('ON'):
                    table_name = part.split()[0].strip()
                else:
                    table_name = part
                components.add(table_name)
        return components
    
    def _parse_where_clause(self, clause: str) -> set:
        """
        Parse WHERE clause into set of condition identifiers.
        """
        components = set()
        # Split by AND, OR
        parts = re.split(r'\b(?:AND|OR)\b', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part:
                # Extract column names from conditions
                # Pattern: column operator value
                match = re.search(r'(\w+(?:\.\w+)?)\s*[=<>!]+\s*', part)
                if match:
                    components.add(match.group(1).strip())
        return components
    
    def _parse_group_by_clause(self, clause: str) -> set:
        """
        Parse GROUP BY clause into set of column identifiers.
        """
        components = set()
        parts = [part.strip() for part in clause.split(',')]
        for part in parts:
            components.add(part)
        return components
    
    def _parse_order_by_clause(self, clause: str) -> set:
        """
        Parse ORDER BY clause into set of column identifiers.
        """
        components = set()
        parts = [part.strip() for part in clause.split(',')]
        for part in parts:
            # Remove ASC/DESC
            if ' ASC' in part.upper() or ' DESC' in part.upper():
                part = re.sub(r'(?:ASC|DESC)\b', '', part, flags=re.IGNORECASE)
            components.add(part)
        return components
    
    def _parse_having_clause(self, clause: str) -> set:
        """
        Parse HAVING clause into set of condition identifiers.
        """
        components = set()
        # Split by AND, OR
        parts = re.split(r'\b(?:AND|OR)\b', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part:
                # Extract aggregate functions and conditions
                if 'COUNT' in part.upper() or 'SUM' in part.upper() or 'AVG' in part.upper():
                    components.add(part)
                else:
                    # Extract column names from conditions
                    match = re.search(r'(\w+(?:\.\w+)?)\s*[=<>!]+\s*', part)
                    if match:
                        components.add(match.group(1).strip())
        return components
    
    def comprehensive_evaluation(self, predicted_queries: List[str], gold_queries: List[str], 
                               execution_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive evaluation with all metrics.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            execution_results (Optional[List[Dict[str, Any]]]): Execution comparison results
            
        Returns:
            Dict[str, Any]: Comprehensive evaluation results
        """
        results = {
            'total_queries': len(predicted_queries),
            'exact_match_accuracy': self.exact_match_accuracy(predicted_queries, gold_queries),
            'component_wise_accuracy': self.component_wise_accuracy(predicted_queries, gold_queries),
            'avg_sql_similarity': sum(self.sql_similarity(predicted_queries, gold_queries)) / len(predicted_queries) if predicted_queries else 0,
            'difficulty_breakdown': self.difficulty_breakdown_accuracy(predicted_queries, gold_queries)
        }
        
        # Add execution metrics if provided
        if execution_results:
            valid_comparisons = [r for r in execution_results if r and r.get('comparison')]
            if valid_comparisons:
                execution_accuracy = sum(1 for r in valid_comparisons 
                                       if r.get('comparison', {}).get('exact_match', False)) / len(valid_comparisons)
                results['execution_accuracy'] = execution_accuracy
            else:
                results['execution_accuracy'] = 0.0
            
            # Execution stats
            valid_executions = sum(1 for r in execution_results if r and r.get('both_successful', False))
            results['execution_success_rate'] = valid_executions / len(execution_results) if execution_results else 0.0
        
        return results
    
    def evaluation_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable evaluation summary.
        
        Args:
            results (Dict[str, Any]): Evaluation results from comprehensive_evaluation
            
        Returns:
            str: Formatted evaluation summary
        """
        summary = []
        summary.append("=== SQL Evaluation Results ===")
        summary.append(f"Total queries: {results['total_queries']}")
        summary.append(f"Exact Match Accuracy: {results['exact_match_accuracy']:.2%}")
        summary.append(f"Average SQL Similarity: {results['avg_sql_similarity']:.2%}")
        
        if 'execution_accuracy' in results:
            summary.append(f"Execution Accuracy: {results['execution_accuracy']:.2%}")
            summary.append(f"Execution Success Rate: {results['execution_success_rate']:.2%}")
        
        summary.append("\n=== Component-wise Accuracy ===")
        for component, accuracy in results['component_wise_accuracy'].items():
            summary.append(f"{component}: {accuracy:.2%}")
        
        summary.append("\n=== Difficulty Breakdown ===")
        for difficulty, stats in results['difficulty_breakdown'].items():
            summary.append(f"{difficulty.capitalize()}: {stats['exact_match_accuracy']:.2%} "
                         f"({stats['count']} queries, {stats['percentage_of_total']:.1f}%)")
        
        return "\n".join(summary)


class SQLDifficultyClassifier:
    """
    Classifier for determining SQL query difficulty levels.
    """
    
    def classify_query(self, query: str) -> str:
        """
        Classify SQL query difficulty.
        
        Args:
            query (str): SQL query to classify
            
        Returns:
            str: Difficulty level ('easy', 'medium', 'hard', 'extra')
        """
        query_upper = query.upper()
        
        # Count different SQL features
        has_join = bool(re.search(r'\bJOIN\b', query_upper))
        has_subquery = '(' in query and 'SELECT' in query_upper[query_upper.find('(')+1:]
        has_union = bool(re.search(r'\bUNION\b', query_upper))
        has_intersect = bool(re.search(r'\bINTERSECT\b', query_upper))
        has_except = bool(re.search(r'\bEXCEPT\b', query_upper))
        has_window = bool(re.search(r'\bOVER\s*\(', query_upper))
        has_cte = bool(re.search(r'\bWITH\b', query_upper))
        
        # Aggregate functions
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        has_aggregation = any(func in query_upper for func in agg_functions)
        
        # Clauses
        has_group_by = bool(re.search(r'\bGROUP\s+BY\b', query_upper))
        has_order_by = bool(re.search(r'\bORDER\s+BY\b', query_upper))
        has_having = bool(re.search(r'\bHAVING\b', query_upper))
        has_where = bool(re.search(r'\bWHERE\b', query_upper))
        
        # Complex WHERE conditions
        where_operators = ['AND', 'OR', 'IN', 'NOT IN', 'EXISTS', 'NOT EXISTS', 'LIKE', 'BETWEEN']
        complex_where = has_where and sum(1 for op in where_operators if op in query_upper) >= 2
        
        # Classification logic
        if (has_subquery or has_union or has_intersect or has_except or 
            has_window or has_cte or (has_join and has_aggregation and has_having)):
            return 'extra'
        elif (has_join and (has_aggregation or complex_where)) or (has_aggregation and has_group_by and has_having):
            return 'hard'
        elif has_group_by or has_order_by or has_aggregation or (has_join and not has_aggregation):
            return 'medium'
        else:
            return 'easy' 
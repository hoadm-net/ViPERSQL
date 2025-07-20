"""
Enhanced Evaluation Metrics module for ViPERSQL
Based on Spider evaluation approach with improvements for Vietnamese Text-to-SQL
"""

import re
import json
import sqlparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
from collections import defaultdict
import unicodedata

class EnhancedEvaluationMetrics:
    """
    Enhanced evaluation metrics calculator for Vietnamese Text-to-SQL models.
    
    Features:
    - Exact Match (EM) accuracy
    - Component-wise F1 scores
    - Advanced SQL parsing and normalization
    - Error analysis and debugging
    - Query difficulty classification
    """
    
    def __init__(self):
        """Initialize EnhancedEvaluationMetrics."""
        self.difficulty_classifier = QueryDifficultyClassifier()
        self.error_analyzer = SQLErrorAnalyzer()
    
    def exact_match_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, Any]:
        """
        Calculate exact match accuracy with detailed analysis.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            
        Returns:
            Dict[str, Any]: EM accuracy and detailed statistics
        """
        if len(predicted_queries) != len(gold_queries):
            raise ValueError("Predicted and gold query lists must have the same length")
        
        if not predicted_queries:
            return {
                'em_accuracy': 0.0,
                'total_queries': 0,
                'exact_matches': 0,
                'match_indices': []
            }
        
        exact_matches = 0
        match_indices = []
        
        for i, (pred, gold) in enumerate(zip(predicted_queries, gold_queries)):
            pred_normalized = self._normalize_sql_comprehensive(pred)
            gold_normalized = self._normalize_sql_comprehensive(gold)
            
            if pred_normalized == gold_normalized:
                exact_matches += 1
                match_indices.append(i)
        
        return {
            'em_accuracy': exact_matches / len(predicted_queries),
            'total_queries': len(predicted_queries),
            'exact_matches': exact_matches,
            'match_indices': match_indices
        }
    
    def component_wise_f1_score(self, predicted_queries: List[str], gold_queries: List[str], 
                               db_ids: List[str], schema_path: str) -> Dict[str, Any]:
        """
        Calculate comprehensive F1-scores for SQL components.
        
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            db_ids (List[str]): List of db_id for each query
            schema_path (str): Path to tables.json
            
        Returns:
            Dict[str, Any]: F1-scores and detailed component analysis
        """
        if len(predicted_queries) != len(gold_queries) or len(predicted_queries) != len(db_ids):
            raise ValueError("Predicted, gold query lists, and db_ids must have the same length")
        
        # Define components to evaluate
        components = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'KEYWORDS']
        
        # Initialize statistics
        clause_stats = {clause: {'tp': 0, 'fp': 0, 'fn': 0, 'total': 0} for clause in components}
        component_details = {clause: [] for clause in components}
        
        for i, (pred, gold, db_id) in enumerate(zip(predicted_queries, gold_queries, db_ids)):
            try:
                # Load schema
                schema = self._load_schema(db_id, schema_path)
                schema_tables, schema_columns = self._get_schema_sets(schema)
                
                # Extract components
                pred_components = self._extract_components_advanced(pred, schema_tables, schema_columns)
                gold_components = self._extract_components_advanced(gold, schema_tables, schema_columns)
                
                # Calculate metrics for each component
                for clause in components:
                    pred_set = pred_components.get(clause, set())
                    gold_set = gold_components.get(clause, set())
                    
                    # Count all queries for total
                    clause_stats[clause]['total'] += 1

                    # Handle empty sets - if both are empty, it's a perfect match
                    if len(pred_set) == 0 and len(gold_set) == 0:
                        clause_stats[clause]['tp'] += 1
                        # This is correct - but we need to make sure F1 is 1.0
                    elif len(gold_set) > 0 or len(pred_set) > 0:  # At least one has this component
                        tp = len(pred_set & gold_set)
                        fp = len(pred_set - gold_set)
                        fn = len(gold_set - pred_set)
                        
                        clause_stats[clause]['tp'] += tp
                        clause_stats[clause]['fp'] += fp
                        clause_stats[clause]['fn'] += fn
                        
                        # Store detailed analysis
                        component_details[clause].append({
                            'query_index': i,
                            'db_id': db_id,
                            'predicted': list(pred_set),
                            'gold': list(gold_set),
                            'tp': tp,
                            'fp': fp,
                            'fn': fn
                        })
                
            except Exception as e:
                print(f"Error processing query {i}: {e}")
                continue
        
        # Calculate F1-scores
        f1_scores = {}
        precision_scores = {}
        recall_scores = {}
        
        for clause in components:
            tp = clause_stats[clause]['tp']
            fp = clause_stats[clause]['fp']
            fn = clause_stats[clause]['fn']
            total = clause_stats[clause]['total']
            
            # Calculate precision and recall properly
            if tp + fp > 0:
                precision = tp / (tp + fp)
            else:
                precision = 1.0 if tp + fn == 0 else 0.0  # Perfect if no gold instances

            if tp + fn > 0:
                recall = tp / (tp + fn)
            else:
                recall = 1.0 if tp + fp == 0 else 0.0  # Perfect if no predicted instances

            # Calculate F1 score
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0

            f1_scores[clause] = f1
            precision_scores[clause] = precision
            recall_scores[clause] = recall
        
        return {
            'f1_scores': f1_scores,
            'precision_scores': precision_scores,
            'recall_scores': recall_scores,
            'component_stats': clause_stats,
            'component_details': component_details,
            'avg_f1': sum(f1_scores.values()) / len(f1_scores) if f1_scores else 0.0
        }
    
    def comprehensive_evaluation(self, predicted_queries: List[str], gold_queries: List[str],
                               db_ids: List[str], schema_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive evaluation with multiple metrics.

        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            db_ids (List[str]): List of db_id for each query
            schema_path (str): Path to tables.json

        Returns:
            Dict[str, Any]: Comprehensive evaluation results
        """
        # Calculate exact match accuracy
        em_results = self.exact_match_accuracy(predicted_queries, gold_queries)

        # Calculate component-wise F1 scores
        f1_results = self.component_wise_f1_score(predicted_queries, gold_queries, db_ids, schema_path)

        # Analyze query complexity
        difficulty_analysis = self._analyze_query_complexity(gold_queries)

        # Analyze errors
        error_analysis = self.analyze_errors(predicted_queries, gold_queries)

        # Categorize queries by performance
        query_categories = self._categorize_queries(predicted_queries, gold_queries, f1_results['component_details'])

        return {
            'exact_match': em_results,
            'component_f1': f1_results,
            'difficulty_analysis': difficulty_analysis,
            'error_analysis': error_analysis,
            'query_categories': query_categories
        }

    def analyze_errors(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, Any]:
        """
        Analyze errors in predicted queries.

        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries

        Returns:
            Dict[str, Any]: Error analysis results
        """
        error_categories = {
            'syntax_errors': [],
            'semantic_errors': [],
            'column_selection_errors': [],
            'table_selection_errors': [],
            'condition_errors': [],
            'join_errors': [],
            'aggregation_errors': [],
            'operator_errors': []
        }

        for i, (pred, gold) in enumerate(zip(predicted_queries, gold_queries)):
            # Check for syntax errors
            if not self._is_valid_sql(pred):
                error_categories['syntax_errors'].append(i)
                continue

            # Check for different components
            pred_components = self._extract_sql_components_simple(pred)
            gold_components = self._extract_sql_components_simple(gold)

            # Column selection errors
            if pred_components.get('columns', set()) != gold_components.get('columns', set()):
                error_categories['column_selection_errors'].append(i)

            # Table selection errors
            if pred_components.get('tables', set()) != gold_components.get('tables', set()):
                error_categories['table_selection_errors'].append(i)

            # Condition errors
            if pred_components.get('conditions', set()) != gold_components.get('conditions', set()):
                error_categories['condition_errors'].append(i)

            # Join errors
            if pred_components.get('joins', set()) != gold_components.get('joins', set()):
                error_categories['join_errors'].append(i)

            # Aggregation errors
            if pred_components.get('aggregations', set()) != gold_components.get('aggregations', set()):
                error_categories['aggregation_errors'].append(i)

            # Operator errors
            if pred_components.get('operators', set()) != gold_components.get('operators', set()):
                error_categories['operator_errors'].append(i)

            # Check for semantic errors
            if self._normalize_sql_comprehensive(pred) != self._normalize_sql_comprehensive(gold):
                error_categories['semantic_errors'].append(i)

        # Summarize errors
        error_summary = {
            category: {
                'count': len(indices),
                'percentage': len(indices) / len(predicted_queries) * 100 if predicted_queries else 0,
                'affected_queries': indices
            }
            for category, indices in error_categories.items()
        }

        return error_summary

    def _is_valid_sql(self, sql: str) -> bool:
        """Check if SQL syntax is valid."""
        try:
            parsed = sqlparse.parse(sql)
            return len(parsed) > 0 and bool(parsed[0].tokens)
        except:
            return False

    def _extract_sql_components_simple(self, sql: str) -> Dict[str, Set[str]]:
        """
        Extract SQL components in a simplified way for error analysis.

        Args:
            sql (str): SQL query

        Returns:
            Dict[str, Set[str]]: Extracted components
        """
        components = {
            'columns': set(),
            'tables': set(),
            'conditions': set(),
            'joins': set(),
            'aggregations': set(),
            'operators': set()
        }

        try:
            # Lowercase for case-insensitive matching
            sql_lower = sql.lower()

            # Extract columns (simplistic approach)
            for match in re.finditer(r'select\s+(.*?)\s+from', sql_lower):
                select_clause = match.group(1)
                columns = [c.strip() for c in select_clause.split(',')]
                components['columns'].update(columns)

            # Extract tables
            for match in re.finditer(r'from\s+(.*?)(?:\s+where|\s+group|\s+order|\s+having|$)', sql_lower, re.DOTALL):
                from_clause = match.group(1)
                tables = [t.strip() for t in from_clause.split(',')]
                components['tables'].update(tables)

            # Extract conditions
            for match in re.finditer(r'where\s+(.*?)(?:\s+group|\s+order|\s+having|$)', sql_lower, re.DOTALL):
                where_clause = match.group(1)
                # Simple tokenization of conditions
                conditions = re.split(r'\s+and\s+|\s+or\s+', where_clause)
                components['conditions'].update([c.strip() for c in conditions])

            # Extract joins
            components['joins'].update(re.findall(r'(inner join|left join|right join|outer join|join)', sql_lower))

            # Extract aggregations
            components['aggregations'].update(re.findall(r'(count\(.*?\)|sum\(.*?\)|avg\(.*?\)|min\(.*?\)|max\(.*?\))', sql_lower))

            # Extract operators
            components['operators'].update(re.findall(r'(=|!=|<>|<|>|<=|>=|like|not like|in|not in)', sql_lower))

        except Exception as e:
            print(f"Error extracting simple components: {e}")

        return components

    def _analyze_query_complexity(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyze query complexity distribution.

        Args:
            queries (List[str]): List of SQL queries

        Returns:
            Dict[str, Any]: Complexity analysis results
        """
        complexity_categories = {
            'simple': 0,
            'moderate': 0,
            'complex': 0,
            'very_complex': 0
        }

        query_complexity_scores = []

        for query in queries:
            difficulty = self.difficulty_classifier.classify_query(query)
            complexity_categories[difficulty] += 1
            query_complexity_scores.append({
                'query': query,
                'complexity': difficulty,
                'score': self.difficulty_classifier.calculate_complexity_score(query)
            })

        return {
            'distribution': {
                category: {
                    'count': count,
                    'percentage': count / len(queries) * 100 if queries else 0
                }
                for category, count in complexity_categories.items()
            },
            'query_details': query_complexity_scores
        }

    def _categorize_queries(self, predicted_queries: List[str], gold_queries: List[str],
                          component_details: Dict[str, List]) -> Dict[str, List[int]]:
        """
        Categorize queries based on performance.

        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            component_details (Dict[str, List]): Component-wise evaluation details

        Returns:
            Dict[str, List[int]]: Query categories
        """
        categories = {
            'perfect_match': [],
            'high_similarity': [],
            'partial_match': [],
            'low_similarity': [],
            'complete_mismatch': []
        }

        for i, (pred, gold) in enumerate(zip(predicted_queries, gold_queries)):
            # Check exact match
            if self._normalize_sql_comprehensive(pred) == self._normalize_sql_comprehensive(gold):
                categories['perfect_match'].append(i)
                continue

            # Calculate similarity score
            similarity = SequenceMatcher(None, pred, gold).ratio()

            # Categorize based on similarity
            if similarity >= 0.9:
                categories['high_similarity'].append(i)
            elif similarity >= 0.7:
                categories['partial_match'].append(i)
            elif similarity >= 0.4:
                categories['low_similarity'].append(i)
            else:
                categories['complete_mismatch'].append(i)

        return categories

    def _normalize_sql_comprehensive(self, sql: str) -> str:
        """
        Comprehensive SQL normalization for exact match comparison.
        
        Args:
            sql (str): SQL query to normalize
            
        Returns:
            str: Normalized SQL query
        """
        if not sql:
            return ""
        
        # Basic normalization
        sql = sql.strip()
        sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace
        sql = sql.lower()  # Convert to lowercase
        
        # Remove semicolons
        sql = sql.rstrip(';')
        
        # Normalize quotes
        sql = sql.replace('"', "'")
        
        # Normalize operators
        sql = sql.replace('<>', '!=')
        sql = sql.replace('<=', '<=')
        sql = sql.replace('>=', '>=')
        
        # Normalize Vietnamese characters
        sql = unicodedata.normalize('NFC', sql)
        
        # Remove extra spaces around operators
        sql = re.sub(r'\s*([=<>!])\s*', r'\1', sql)
        
        # Normalize aggregation functions (e.g., count ( * ) -> count(*))
        sql = self._normalize_aggregation_functions(sql)

        # NORMALIZE ALIASES - This is the key improvement
        sql = self._normalize_aliases_in_sql(sql)

        return sql

    def _normalize_aggregation_functions(self, sql: str) -> str:
        """
        Normalize aggregation functions like count ( * ) -> count(*).

        Args:
            sql (str): SQL query to normalize

        Returns:
            str: Normalized SQL query
        """
        # Normalize common aggregation functions
        agg_functions = ['count', 'sum', 'avg', 'min', 'max']

        for func in agg_functions:
            # Replace patterns like 'count ( * )' with 'count(*)'
            pattern = rf'{func}\s*\(\s*([^)]*?)\s*\)'
            sql = re.sub(pattern, f'{func}(\\1)', sql, flags=re.IGNORECASE)

        return sql

    def _normalize_aliases_in_sql(self, sql: str) -> str:
        """
        Normalize table aliases in SQL to handle alias inconsistencies.

        This method:
        1. Replaces all table aliases with standardized ones (t1, t2, t3, etc.)
        2. Handles cases where one query uses aliases and another doesn't
        3. Maintains semantic equivalence while normalizing syntax

        Args:
            sql (str): SQL query to normalize

        Returns:
            str: SQL with normalized aliases
        """
        try:
            # Parse the SQL to identify tables and aliases
            parsed = sqlparse.parse(sql)
            if not parsed:
                return sql

            # Extract table names and their aliases
            table_mappings = self._extract_table_aliases(sql)

            # If no aliases found, try to add standard aliases
            if not table_mappings:
                return self._add_standard_aliases(sql)

            # Replace aliases with standardized ones
            normalized_sql = sql

            # Sort by alias length (longest first) to avoid partial replacements
            sorted_mappings = sorted(table_mappings.items(), key=lambda x: len(x[1]), reverse=True)

            alias_counter = 1
            for table_name, current_alias in sorted_mappings:
                standard_alias = f"t{alias_counter}"

                # Replace the alias in the query
                # Pattern: table_name as current_alias -> table_name as standard_alias
                pattern1 = rf'\b{re.escape(table_name)}\s+as\s+{re.escape(current_alias)}\b'
                replacement1 = f"{table_name} as {standard_alias}"
                normalized_sql = re.sub(pattern1, replacement1, normalized_sql, flags=re.IGNORECASE)

                # Pattern: table_name current_alias -> table_name standard_alias
                pattern2 = rf'\b{re.escape(table_name)}\s+{re.escape(current_alias)}\b'
                replacement2 = f"{table_name} {standard_alias}"
                normalized_sql = re.sub(pattern2, replacement2, normalized_sql, flags=re.IGNORECASE)

                # Replace alias references in the rest of the query
                # Pattern: current_alias.column -> standard_alias.column
                pattern3 = rf'\b{re.escape(current_alias)}\.'
                replacement3 = f"{standard_alias}."
                normalized_sql = re.sub(pattern3, replacement3, normalized_sql, flags=re.IGNORECASE)

                alias_counter += 1

            return normalized_sql

        except Exception as e:
            print(f"Error normalizing aliases: {e}")
            return sql

    def _extract_table_aliases(self, sql: str) -> Dict[str, str]:
        """
        Extract table names and their aliases from SQL.

        Args:
            sql (str): SQL query

        Returns:
            Dict[str, str]: Mapping of table_name -> alias
        """
        table_mappings = {}

        # Pattern 1: table_name AS alias
        pattern1 = r'\bfrom\s+(\w+)\s+as\s+(\w+)\b|\bjoin\s+(\w+)\s+as\s+(\w+)\b'
        matches = re.findall(pattern1, sql, re.IGNORECASE)

        for match in matches:
            if match[0] and match[1]:  # FROM table AS alias
                table_mappings[match[0]] = match[1]
            elif match[2] and match[3]:  # JOIN table AS alias
                table_mappings[match[2]] = match[3]

        # Pattern 2: table_name alias (without AS keyword)
        pattern2 = r'\bfrom\s+(\w+)\s+(\w+)\b|\bjoin\s+(\w+)\s+(\w+)\b'
        matches = re.findall(pattern2, sql, re.IGNORECASE)

        for match in matches:
            if match[0] and match[1]:  # FROM table alias
                # Make sure it's not a keyword
                if match[1].lower() not in ['where', 'group', 'order', 'having', 'join', 'on', 'inner', 'left', 'right', 'outer']:
                    table_mappings[match[0]] = match[1]
            elif match[2] and match[3]:  # JOIN table alias
                if match[3].lower() not in ['where', 'group', 'order', 'having', 'join', 'on', 'inner', 'left', 'right', 'outer']:
                    table_mappings[match[2]] = match[3]

        return table_mappings

    def _add_standard_aliases(self, sql: str) -> str:
        """
        Add standard aliases to tables that don't have aliases.

        Args:
            sql (str): SQL query without aliases

        Returns:
            str: SQL with standard aliases added
        """
        try:
            # Extract table names without aliases
            tables = self._extract_table_names_without_aliases(sql)

            if not tables:
                return sql

            normalized_sql = sql
            alias_counter = 1

            for table in tables:
                standard_alias = f"t{alias_counter}"

                # Add alias to FROM clause
                pattern1 = rf'\bfrom\s+{re.escape(table)}\b(?!\s+as|\s+\w+)'
                replacement1 = f"from {table} as {standard_alias}"
                normalized_sql = re.sub(pattern1, replacement1, normalized_sql, flags=re.IGNORECASE)

                # Add alias to JOIN clauses
                pattern2 = rf'\bjoin\s+{re.escape(table)}\b(?!\s+as|\s+\w+)'
                replacement2 = f"join {table} as {standard_alias}"
                normalized_sql = re.sub(pattern2, replacement2, normalized_sql, flags=re.IGNORECASE)

                # Replace table.column references with alias.column
                pattern3 = rf'\b{re.escape(table)}\.'
                replacement3 = f"{standard_alias}."
                normalized_sql = re.sub(pattern3, replacement3, normalized_sql, flags=re.IGNORECASE)

                alias_counter += 1

            return normalized_sql

        except Exception as e:
            print(f"Error adding standard aliases: {e}")
            return sql

    def _extract_table_names_without_aliases(self, sql: str) -> List[str]:
        """
        Extract table names that don't have aliases.

        Args:
            sql (str): SQL query

        Returns:
            List[str]: List of table names without aliases
        """
        tables = []

        # Find all table references in FROM and JOIN clauses
        # Pattern for tables without aliases
        pattern = r'\b(?:from|join)\s+(\w+)\b(?!\s+(?:as\s+\w+|\w+\s*(?:on|where|group|order|having|join|$)))'
        matches = re.findall(pattern, sql, re.IGNORECASE)

        for match in matches:
            if match not in tables:
                tables.append(match)

        return tables

    def _load_schema(self, db_id: str, schema_path: str) -> dict:
        """Load database schema."""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schemas = json.load(f)

            for schema in schemas:
                if schema.get('db_id') == db_id:
                    return schema

            raise ValueError(f"Schema not found for db_id: {db_id}")
        except Exception as e:
            raise ValueError(f"Error loading schema: {e}")

    def _get_schema_sets(self, schema: dict) -> Tuple[Set[str], Set[str]]:
        """Extract table and column sets from schema."""
        tables = set()
        columns = set()

        if 'table_names' in schema:
            tables.update(schema['table_names'])

        if 'column_names' in schema:
            for col_info in schema['column_names']:
                if len(col_info) >= 2:
                    columns.add(col_info[1])

        return tables, columns

    def _extract_components_advanced(self, query: str, schema_tables: Set[str],
                                   schema_columns: Set[str]) -> Dict[str, Set[str]]:
        """
        Advanced component extraction with better parsing and alias handling.

        Args:
            query (str): SQL query
            schema_tables (Set[str]): Set of table names
            schema_columns (Set[str]): Set of column names

        Returns:
            Dict[str, Set[str]]: Extracted components
        """
        components = {}

        try:
            # First normalize aliases to ensure consistent comparison
            normalized_query = self._normalize_aliases_in_sql(query)

            # Parse SQL using sqlparse
            parsed = sqlparse.parse(normalized_query)
            if not parsed:
                return components

            stmt = parsed[0]
            query_upper = normalized_query.upper()

            # Extract SELECT clause
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
            if select_match:
                select_clause = select_match.group(1).strip()
                components['SELECT'] = self._parse_select_clause_with_aliases(select_clause, schema_columns)

            # Extract FROM clause
            from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if from_match:
                from_clause = from_match.group(1).strip()
                components['FROM'] = self._parse_from_clause_with_aliases(from_clause, schema_tables)

            # Extract WHERE clause
            where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if where_match:
                where_clause = where_match.group(1).strip()
                components['WHERE'] = self._parse_where_clause_with_aliases(where_clause, schema_columns)

            # Extract GROUP BY clause
            group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
            if group_match:
                group_clause = group_match.group(1).strip()
                components['GROUP BY'] = self._parse_group_clause(group_clause)

            # Extract ORDER BY clause
            order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+HAVING|$)', query_upper, re.DOTALL)
            if order_match:
                order_clause = order_match.group(1).strip()
                components['ORDER BY'] = self._parse_order_clause(order_clause)

            # Extract HAVING clause
            having_match = re.search(r'HAVING\s+(.*?)$', query_upper, re.DOTALL)
            if having_match:
                having_clause = having_match.group(1).strip()
                components['HAVING'] = self._parse_having_clause_with_aliases(having_clause, schema_columns)

            # Extract keywords
            components['KEYWORDS'] = self._extract_keywords(normalized_query)

        except Exception as e:
            print(f"Error extracting components: {e}")

        return components

    def _parse_select_clause_with_aliases(self, select_clause: str, schema_columns: Set[str]) -> Set[str]:
        """Parse SELECT clause and extract columns, handling aliases properly."""
        columns = set()

        # Split by commas, but be aware of function calls
        in_parentheses = 0
        current_item = ""

        for char in select_clause:
            if char == '(' and in_parentheses == 0:
                in_parentheses += 1
                current_item += char
            elif char == '(' and in_parentheses > 0:
                in_parentheses += 1
                current_item += char
            elif char == ')' and in_parentheses > 0:
                in_parentheses -= 1
                current_item += char
            elif char == ',' and in_parentheses == 0:
                # End of item
                normalized_item = self._normalize_column_reference(current_item.strip().lower())
                columns.add(normalized_item)
                current_item = ""
            else:
                current_item += char

        # Add the last item if there is one
        if current_item.strip():
            normalized_item = self._normalize_column_reference(current_item.strip().lower())
            columns.add(normalized_item)

        # Handle special case of 'SELECT *'
        if '*' in columns:
            columns.remove('*')
            columns.add('*')

        return columns

    def _parse_from_clause_with_aliases(self, from_clause: str, schema_tables: Set[str]) -> Set[str]:
        """Parse FROM clause and extract tables, handling aliases properly."""
        tables = set()

        # Remove any alias information and just get table names
        # Pattern: table_name [AS] alias -> table_name
        table_pattern = r'\b(\w+)(?:\s+(?:as\s+)?\w+)?\b'
        matches = re.findall(table_pattern, from_clause.lower())

        for match in matches:
            # Check if it's a table name from schema or a common table name
            if match in schema_tables or match in ['join', 'inner', 'left', 'right', 'outer', 'on']:
                if match not in ['join', 'inner', 'left', 'right', 'outer', 'on']:
                    tables.add(match)

        # Also extract JOIN tables
        join_pattern = r'(?:inner\s+join|left\s+join|right\s+join|outer\s+join|join)\s+(\w+)'
        join_matches = re.findall(join_pattern, from_clause.lower())

        for match in join_matches:
            if match in schema_tables:
                tables.add(match)

        return tables

    def _parse_where_clause_with_aliases(self, where_clause: str, schema_columns: Set[str]) -> Set[str]:
        """Parse WHERE clause and extract conditions, handling aliases properly."""
        conditions = set()

        # Normalize column references in conditions
        normalized_where = self._normalize_column_references_in_clause(where_clause, schema_columns)

        # Use a simpler approach with regex splitting to avoid infinite loop
        # Split by AND/OR while respecting parentheses depth
        try:
            # Simple regex-based splitting for better reliability
            parts = re.split(r'\s+(?:AND|OR)\s+', normalized_where, flags=re.IGNORECASE)
            for part in parts:
                if part.strip():
                    conditions.add(part.strip().lower())
        except Exception as e:
            # Fallback: treat the entire where clause as one condition
            conditions.add(normalized_where.strip().lower())

        return conditions

    def _parse_having_clause_with_aliases(self, having_clause: str, schema_columns: Set[str]) -> Set[str]:
        """Parse HAVING clause and extract conditions, handling aliases properly."""
        conditions = set()

        # Similar to WHERE clause parsing, but for HAVING
        normalized_having = self._normalize_column_references_in_clause(having_clause, schema_columns)

        for condition in re.split(r'\s+AND\s+|\s+OR\s+', normalized_having, flags=re.IGNORECASE):
            if condition.strip():
                conditions.add(condition.strip().lower())

        return conditions

    def _parse_group_clause(self, group_clause: str) -> Set[str]:
        """Parse GROUP BY clause and extract grouping expressions."""
        groups = set()

        for item in group_clause.split(','):
            normalized_item = self._normalize_column_reference(item.strip().lower())
            groups.add(normalized_item)

        return groups

    def _parse_order_clause(self, order_clause: str) -> Set[str]:
        """Parse ORDER BY clause and extract ordering expressions."""
        orders = set()

        for item in order_clause.split(','):
            item = item.strip().lower()
            # Capture ASC/DESC if present
            if ' asc' in item:
                item = item.replace(' asc', '') + ' asc'
            elif ' desc' in item:
                item = item.replace(' desc', '') + ' desc'

            normalized_item = self._normalize_column_reference(item)
            orders.add(normalized_item)

        return orders

    def _extract_keywords(self, query: str) -> Set[str]:
        """Extract SQL keywords from query."""
        keywords = set()

        # List of keywords to check
        keyword_list = [
            'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
            'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'OUTER JOIN',
            'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT', 'DISTINCT', 'LIMIT'
        ]

        for keyword in keyword_list:
            if re.search(f'\\b{keyword}\\b', query.upper()):
                keywords.add(keyword.lower())

        return keywords

    def _normalize_column_reference(self, column_ref: str) -> str:
        """
        Normalize column reference by removing alias prefixes.

        Args:
            column_ref (str): Column reference (e.g., "t1.column_name", "table_name.column_name", or "column_name")

        Returns:
            str: Normalized column reference (just the column name)
        """
        # Remove table alias or table name prefix if present
        if '.' in column_ref:
            parts = column_ref.split('.')
            if len(parts) == 2:
                table_part, column_part = parts
                # Return just the column name part, regardless of whether it's an alias or full table name
                return column_part.strip()

        return column_ref.strip()

    def _normalize_column_references_in_clause(self, clause: str, schema_columns: Set[str]) -> str:
        """
        Normalize column references in a SQL clause.

        Args:
            clause (str): SQL clause
            schema_columns (Set[str]): Set of column names from schema

        Returns:
            str: Clause with normalized column references
        """
        normalized_clause = clause

        # Find all column references with table prefixes (both aliases and full table names)
        pattern = r'\b(\w+)\.(\w+)\b'
        matches = re.findall(pattern, normalized_clause, re.IGNORECASE)

        for table_part, column_part in matches:
            # Replace table_part.column with just column if it's in schema
            if column_part.lower() in schema_columns:
                old_ref = f"{table_part}.{column_part}"
                normalized_clause = normalized_clause.replace(old_ref, column_part)

        return normalized_clause

    def _parse_select_clause(self, select_clause: str, schema_columns: Set[str]) -> Set[str]:
        """Parse SELECT clause and extract columns."""
        return self._parse_select_clause_with_aliases(select_clause, schema_columns)

    def _parse_from_clause(self, from_clause: str, schema_tables: Set[str]) -> Set[str]:
        """Parse FROM clause and extract tables and join conditions."""
        return self._parse_from_clause_with_aliases(from_clause, schema_tables)

    def _parse_where_clause(self, where_clause: str, schema_columns: Set[str]) -> Set[str]:
        """Parse WHERE clause and extract conditions."""
        return self._parse_where_clause_with_aliases(where_clause, schema_columns)


class QueryDifficultyClassifier:
    """Classifier to determine SQL query complexity."""

    def __init__(self):
        """Initialize query difficulty classifier."""
        pass

    def classify_query(self, query: str) -> str:
        """
        Classify query complexity.

        Args:
            query (str): SQL query to classify

        Returns:
            str: Complexity category ('simple', 'moderate', 'complex', 'very_complex')
        """
        score = self.calculate_complexity_score(query)

        if score < 3:
            return 'simple'
        elif score < 6:
            return 'moderate'
        elif score < 9:
            return 'complex'
        else:
            return 'very_complex'

    def calculate_complexity_score(self, query: str) -> float:
        """
        Calculate complexity score based on SQL query features.

        Args:
            query (str): SQL query

        Returns:
            float: Complexity score (higher means more complex)
        """
        query = query.upper()
        score = 0.0

        # Base query elements
        if 'SELECT' in query:
            score += 1.0

        if 'WHERE' in query:
            score += 1.0

        # Joins
        join_count = query.count('JOIN')
        score += join_count * 0.5

        # Aggregations
        aggregation_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        for func in aggregation_functions:
            if func in query:
                score += 0.5

        # Group by and having
        if 'GROUP BY' in query:
            score += 1.0

        if 'HAVING' in query:
            score += 1.5

        # Order by and limit
        if 'ORDER BY' in query:
            score += 0.5

        if 'LIMIT' in query:
            score += 0.2

        # Subqueries
        subquery_count = query.count('(SELECT')
        score += subquery_count * 2.0

        # Set operations
        set_operations = ['UNION', 'INTERSECT', 'EXCEPT']
        for op in set_operations:
            if op in query:
                score += 1.5

        # Window functions
        if 'OVER' in query or 'PARTITION BY' in query:
            score += 2.0

        # Common Table Expressions (CTE)
        if 'WITH' in query and ' AS (' in query:
            score += 1.5

        # Nested queries by counting parentheses pairs
        open_paren_count = query.count('(')
        close_paren_count = query.count(')')
        paren_count = min(open_paren_count, close_paren_count)
        score += max(0, (paren_count - subquery_count)) * 0.2

        return score


class SQLErrorAnalyzer:
    """Analyzer for SQL query errors."""

    def __init__(self):
        """Initialize SQL error analyzer."""
        pass

    def analyze_query_errors(self, query: str) -> Dict[str, Any]:
        """
        Analyze potential errors in SQL query.

        Args:
            query (str): SQL query to analyze

        Returns:
            Dict[str, Any]: Identified errors
        """
        errors = {
            'syntax_errors': [],
            'semantic_issues': [],
            'warning_flags': []
        }

        # Check for basic syntax errors
        try:
            parsed = sqlparse.parse(query)
            if not parsed or not parsed[0].tokens:
                errors['syntax_errors'].append('Invalid SQL syntax - parsing failed')
        except Exception as e:
            errors['syntax_errors'].append(f'SQL parsing error: {str(e)}')

        # Check missing clauses
        query_upper = query.upper()
        if 'SELECT' not in query_upper:
            errors['syntax_errors'].append('Missing SELECT clause')

        if 'FROM' not in query_upper and not re.search(r'SELECT\s+\d+', query_upper):
            errors['semantic_issues'].append('Missing FROM clause (may be intentional for scalar queries)')

        # Check for unbalanced parentheses
        open_paren_count = query.count('(')
        close_paren_count = query.count(')')
        if open_paren_count != close_paren_count:
            errors['syntax_errors'].append(f'Unbalanced parentheses: {open_paren_count} opening vs {close_paren_count} closing')

        # Check for unclosed quotes
        single_quotes = query.count("'")
        if single_quotes % 2 != 0:
            errors['syntax_errors'].append('Unclosed single quotes')

        double_quotes = query.count('"')
        if double_quotes % 2 != 0:
            errors['syntax_errors'].append('Unclosed double quotes')

        # Check for common semantic issues
        if 'GROUP BY' in query_upper and 'SELECT' in query_upper:
            # Check for aggregation with GROUP BY
            select_clause = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
            if select_clause:
                select_items = select_clause.group(1)
                has_aggregation = any(agg in select_items for agg in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX'])
                if not has_aggregation:
                    errors['warning_flags'].append('GROUP BY without aggregation functions in SELECT')

        # Check for potential cartesian products
        from_clause = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', query_upper, re.DOTALL)
        if from_clause:
            from_tables = from_clause.group(1)
            if ',' in from_tables and 'JOIN' not in from_tables and 'WHERE' not in query_upper:
                errors['warning_flags'].append('Potential cartesian product - multiple tables without join condition')

        # Check for mismatched comparison operators
        if re.search(r'WHERE\s+.*?=\s*NULL', query_upper) or re.search(r'HAVING\s+.*?=\s*NULL', query_upper):
            errors['semantic_issues'].append('Comparing with NULL using = instead of IS NULL')

        return errors


class SQLAliasNormalizer:
    """
    Comprehensive SQL alias normalizer that handles all alias scenarios:
    1. Different aliases between gold and predicted queries
    2. Only one query uses aliases
    3. Both queries use different alias patterns
    4. Schema-aware column validation
    """

    def __init__(self, schema: dict):
        """
        Initialize with database schema.

        Args:
            schema (dict): Database schema from tables.json
        """
        self.schema = schema
        self.table_to_columns = self._build_table_column_mapping()
        self.column_to_table = self._build_column_table_mapping()

    def _build_table_column_mapping(self) -> Dict[str, Set[str]]:
        """Build mapping from table name to its columns."""
        mapping = {}

        table_names = self.schema.get('table_names', [])
        column_names = self.schema.get('column_names', [])

        for table_idx, table_name in enumerate(table_names):
            mapping[table_name] = set()

        for col_info in column_names:
            if len(col_info) >= 2:
                table_idx, column_name = col_info[0], col_info[1]
                if table_idx >= 0 and table_idx < len(table_names):
                    table_name = table_names[table_idx]
                    mapping[table_name].add(column_name)

        return mapping

    def _build_column_table_mapping(self) -> Dict[str, Set[str]]:
        """Build mapping from column name to possible tables (handle duplicate column names)."""
        mapping = {}

        table_names = self.schema.get('table_names', [])
        column_names = self.schema.get('column_names', [])

        for col_info in column_names:
            if len(col_info) >= 2:
                table_idx, column_name = col_info[0], col_info[1]
                if table_idx >= 0 and table_idx < len(table_names):
                    table_name = table_names[table_idx]
                    if column_name not in mapping:
                        mapping[column_name] = set()
                    mapping[column_name].add(table_name)

        return mapping

    def normalize_sql_with_schema(self, sql: str) -> str:
        """
        Normalize SQL query by standardizing all aliases and column references.

        This method:
        1. Extracts all table references (with/without aliases)
        2. Maps aliases to actual table names using schema
        3. Standardizes all aliases to t1, t2, t3... format
        4. Validates column references against schema
        5. Normalizes column references to just column names where unambiguous

        Args:
            sql (str): SQL query to normalize

        Returns:
            str: Schema-aware normalized SQL
        """
        try:
            # Step 1: Parse and extract table information
            table_info = self._extract_table_info_comprehensive(sql)

            # Step 2: Validate table names against schema
            validated_tables = self._validate_tables_against_schema(table_info)

            # Step 3: Create standardized alias mapping
            alias_mapping = self._create_standard_alias_mapping(validated_tables)

            # Step 4: Apply alias normalization
            normalized_sql = self._apply_alias_normalization(sql, alias_mapping)

            # Step 5: Normalize column references based on schema
            normalized_sql = self._normalize_column_references_with_schema(normalized_sql, alias_mapping)

            return normalized_sql

        except Exception as e:
            print(f"Error in schema-aware normalization: {e}")
            return sql

    def _extract_table_info_comprehensive(self, sql: str) -> List[Dict[str, str]]:
        """
        Extract comprehensive table information including aliases.

        Returns list of dicts with keys: 'table_name', 'alias', 'context' (FROM/JOIN)
        """
        table_info = []
        sql_lower = sql.lower()

        # Pattern 1: FROM/JOIN table_name AS alias
        pattern1 = r'\b(from|join)\s+(\w+)\s+as\s+(\w+)\b'
        matches = re.finditer(pattern1, sql_lower)
        for match in matches:
            context, table_name, alias = match.groups()
            table_info.append({
                'table_name': table_name,
                'alias': alias,
                'context': context,
                'has_explicit_alias': True
            })

        # Pattern 2: FROM/JOIN table_name alias (without AS)
        pattern2 = r'\b(from|join)\s+(\w+)\s+(\w+)\b(?!\s*(?:on|where|group|order|having|limit|join|inner|left|right|outer))'
        matches = re.finditer(pattern2, sql_lower)
        for match in matches:
            context, table_name, potential_alias = match.groups()
            # Verify it's not a keyword
            if potential_alias not in ['on', 'where', 'group', 'order', 'having', 'limit', 'join', 'inner', 'left', 'right', 'outer']:
                table_info.append({
                    'table_name': table_name,
                    'alias': potential_alias,
                    'context': context,
                    'has_explicit_alias': True
                })

        # Pattern 3: FROM/JOIN table_name (no alias)
        pattern3 = r'\b(from|join)\s+(\w+)\b(?!\s+(?!on|where|group|order|having|limit|join|inner|left|right|outer)\w+)'
        matches = re.finditer(pattern3, sql_lower)
        for match in matches:
            context, table_name = match.groups()
            # Check if this table already found with alias
            already_found = any(t['table_name'] == table_name for t in table_info)
            if not already_found:
                table_info.append({
                    'table_name': table_name,
                    'alias': None,
                    'context': context,
                    'has_explicit_alias': False
                })

        return table_info

    def _validate_tables_against_schema(self, table_info: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate table names against schema and filter valid ones."""
        valid_tables = []
        schema_table_names = set(self.schema.get('table_names', []))

        for table_entry in table_info:
            table_name = table_entry['table_name']
            if table_name in schema_table_names:
                valid_tables.append(table_entry)
            else:
                print(f"Warning: Table '{table_name}' not found in schema")

        return valid_tables

    def _create_standard_alias_mapping(self, validated_tables: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Create mapping from current references to standardized aliases.

        Returns dict mapping: current_reference -> standard_alias
        """
        mapping = {}
        alias_counter = 1

        # Sort tables by appearance order for consistency
        for table_entry in validated_tables:
            table_name = table_entry['table_name']
            current_alias = table_entry['alias']
            standard_alias = f"t{alias_counter}"

            # Map table name to standard alias
            mapping[table_name] = standard_alias

            # If there's a current alias, map it too
            if current_alias:
                mapping[current_alias] = standard_alias

            alias_counter += 1

        return mapping

    def _apply_alias_normalization(self, sql: str, alias_mapping: Dict[str, str]) -> str:
        """Apply alias normalization to SQL query."""
        normalized_sql = sql

        # Sort by length (longest first) to avoid partial replacements
        sorted_mappings = sorted(alias_mapping.items(), key=lambda x: len(x[0]), reverse=True)

        for current_ref, standard_alias in sorted_mappings:
            # Replace table references in FROM/JOIN clauses
            # Pattern: FROM/JOIN table_name [AS alias] -> FROM/JOIN table_name AS standard_alias

            # Case 1: table_name AS current_alias -> table_name AS standard_alias
            pattern1 = rf'\b{re.escape(current_ref)}\s+as\s+\w+\b'
            replacement1 = f"{current_ref} as {standard_alias}"
            normalized_sql = re.sub(pattern1, replacement1, normalized_sql, flags=re.IGNORECASE)

            # Case 2: table_name current_alias -> table_name standard_alias (no AS)
            pattern2 = rf'\b{re.escape(current_ref)}\s+(?!as\s+)\w+\b(?!\s*\.)'
            replacement2 = f"{current_ref} {standard_alias}"
            normalized_sql = re.sub(pattern2, replacement2, normalized_sql, flags=re.IGNORECASE)

            # Case 3: table_name (no alias) -> table_name AS standard_alias
            pattern3 = rf'\b(from|join)\s+{re.escape(current_ref)}\b(?!\s+(?:as\s+)?\w+)'
            replacement3 = rf'\1 {current_ref} as {standard_alias}'
            normalized_sql = re.sub(pattern3, replacement3, normalized_sql, flags=re.IGNORECASE)

            # Replace column references: current_ref.column -> standard_alias.column
            pattern4 = rf'\b{re.escape(current_ref)}\.'
            replacement4 = f"{standard_alias}."
            normalized_sql = re.sub(pattern4, replacement4, normalized_sql, flags=re.IGNORECASE)

        return normalized_sql

    def _normalize_column_references_with_schema(self, sql: str, alias_mapping: Dict[str, str]) -> str:
        """
        Normalize column references using schema information.

        For unambiguous columns (appear in only one table), remove table prefix.
        For ambiguous columns, keep table prefix for clarity.
        """
        normalized_sql = sql

        # Find all column references with table/alias prefix
        pattern = r'\b(\w+)\.(\w+)\b'
        matches = re.findall(pattern, normalized_sql, re.IGNORECASE)

        for table_ref, column_name in matches:
            # Check if column is unambiguous (appears in only one table)
            possible_tables = self.column_to_table.get(column_name, set())

            if len(possible_tables) == 1:
                # Unambiguous column - can remove table prefix
                old_ref = f"{table_ref}.{column_name}"
                normalized_sql = normalized_sql.replace(old_ref, column_name)
            # For ambiguous columns, keep the standardized table prefix

        return normalized_sql

    def normalize_column_list(self, columns: List[str]) -> List[str]:
        """
        Normalize a list of column references for comparison.

        Args:
            columns (List[str]): List of column references (may include table prefixes)

        Returns:
            List[str]: Normalized column list (just column names, sorted)
        """
        normalized = []

        for col_ref in columns:
            if '.' in col_ref:
                # Extract column name from table.column or alias.column
                parts = col_ref.split('.')
                if len(parts) == 2:
                    table_part, column_part = parts
                    # Always use just the column name for consistency
                    normalized.append(column_part.strip())
                else:
                    normalized.append(col_ref.strip())
            else:
                # No table prefix - use as is
                normalized.append(col_ref.strip())

        return sorted(set(normalized))  # Remove duplicates and sort for consistent comparison

    def _resolve_table_reference(self, table_ref: str) -> Optional[str]:
        """
        Resolve a table reference (could be table name or alias) to actual table name.

        Args:
            table_ref (str): Table reference from SQL

        Returns:
            Optional[str]: Actual table name if found, None otherwise
        """
        schema_tables = set(self.schema.get('table_names', []))

        # Check if it's a direct table name
        if table_ref in schema_tables:
            return table_ref

        # Could be an alias - for now, return None
        # In a more sophisticated implementation, we'd track alias mappings
        return None


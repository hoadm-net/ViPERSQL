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
import unicodedata

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
    
    def component_wise_f1_score(self, predicted_queries: List[str], gold_queries: List[str], db_ids: List[str], schema_path: str) -> Dict[str, float]:
        """
        Calculate F1-score for SQL clauses using set-based component matching, schema-aware.
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            db_ids (List[str]): List of db_id for each query
            schema_path (str): Path to tables.json
        Returns:
            Dict[str, float]: F1-score for each SQL clause
        """
        if len(predicted_queries) != len(gold_queries) or len(predicted_queries) != len(db_ids):
            raise ValueError("Predicted, gold query lists, and db_ids must have the same length")
        clauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'KEYWORDS']
        clause_stats = {clause: {'tp': 0, 'fp': 0, 'fn': 0} for clause in clauses}
        for pred, gold, db_id in zip(predicted_queries, gold_queries, db_ids):
            schema = self.load_schema(db_id, schema_path)
            schema_tables, schema_columns = self.get_table_and_column_sets(schema)
            pred_components = self.extract_components_as_sets(pred, schema_tables, schema_columns)
            gold_components = self.extract_components_as_sets(gold, schema_tables, schema_columns)
            for clause in clauses:
                pred_set = pred_components.get(clause, set())
                gold_set = gold_components.get(clause, set())
                tp = len(pred_set & gold_set)
                fp = len(pred_set - gold_set)
                fn = len(gold_set - pred_set)
                clause_stats[clause]['tp'] += tp
                clause_stats[clause]['fp'] += fp
                clause_stats[clause]['fn'] += fn
        f1_scores = {}
        for clause in clauses:
            tp = clause_stats[clause]['tp']
            fp = clause_stats[clause]['fp']
            fn = clause_stats[clause]['fn']
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores[clause] = f1
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

    def component_wise_accuracy(self, predicted_queries: List[str], gold_queries: List[str], db_ids: List[str], schema_path: str) -> Dict[str, float]:
        """
        Calculate component-wise accuracy for SQL clauses, schema-aware.
        Args:
            predicted_queries (List[str]): List of predicted SQL queries
            gold_queries (List[str]): List of gold/reference SQL queries
            db_ids (List[str]): List of db_id for each query
            schema_path (str): Path to tables.json
        Returns:
            Dict[str, float]: Component-wise accuracy scores
        """
        if len(predicted_queries) != len(gold_queries) or len(predicted_queries) != len(db_ids):
            raise ValueError("Predicted, gold query lists, and db_ids must have the same length")
        components = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
        component_matches = {comp: 0 for comp in components}
        component_totals = {comp: 0 for comp in components}
        for pred, gold, db_id in zip(predicted_queries, gold_queries, db_ids):
            schema = self.load_schema(db_id, schema_path)
            schema_tables, schema_columns = self.get_table_and_column_sets(schema)
            pred_components = self.extract_components_as_sets(pred, schema_tables, schema_columns)
            gold_components = self.extract_components_as_sets(gold, schema_tables, schema_columns)
            for component in components:
                if component in gold_components:
                    component_totals[component] += 1
                    if (component in pred_components and 
                        self._normalize_component(' '.join(pred_components[component])) == self._normalize_component(' '.join(gold_components[component]))):
                        component_matches[component] += 1
        accuracies = {}
        for component in components:
            if component_totals[component] > 0:
                accuracies[component] = component_matches[component] / component_totals[component]
            else:
                accuracies[component] = 1.0
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
    
    def load_schema(self, db_id: str, schema_path: str) -> dict:
        """
        Load schema for a given db_id from tables.json.
        """
        with open(schema_path, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
        for schema in schemas:
            if schema['db_id'] == db_id:
                return schema
        return {}

    def get_table_and_column_sets(self, schema: dict) -> (set, set):
        """
        Get set of table names and set of full column names (table.column) from schema.
        """
        tables = set(schema.get('table_names', []))
        columns = set()
        table_names = schema.get('table_names', [])
        for idx, col in schema.get('column_names', []):
            if idx >= 0 and idx < len(table_names):
                columns.add(f"{table_names[idx]}.{col}")
        return tables, columns

    def extract_components_as_sets(self, query: str, schema_tables: set, schema_columns: set) -> Dict[str, set]:
        """
        Extract SQL components from a query as sets of normalized strings.
        Luôn chuẩn hóa alias về tên bảng gốc trước khi tách trường/điều kiện.
        """
        components = {}
        query_upper = query.upper()
        # Parse alias mapping từ FROM/JOIN
        alias_map = self._extract_alias_mapping(query)
        # Helper: thay alias về tên bảng gốc trong toàn bộ query
        def replace_alias_all(sql, alias_map):
            for alias, table in alias_map.items():
                sql = re.sub(rf'\b{re.escape(alias)}\.', f'{table}.', sql)
            return sql
        query_no_alias = replace_alias_all(query, alias_map)
        # SELECT
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_no_alias, re.DOTALL | re.IGNORECASE)
        if select_match:
            select_clause = select_match.group(1).strip()
            fields = [self._normalize_token(f.split(' AS ')[0]) for f in select_clause.split(',')]
            components['SELECT'] = set(fields)
        # FROM
        from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', query_no_alias, re.DOTALL | re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1).strip()
            tables = [self._normalize_token(t.split()[0]) for t in from_clause.split(',')]
            components['FROM'] = set(tables)
        # WHERE
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+HAVING|$)', query_no_alias, re.DOTALL | re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1).strip()
            # Tách điều kiện theo AND/OR
            conds = re.split(r'\b(?:AND|OR)\b', where_clause, flags=re.IGNORECASE)
            conds = [self._normalize_token(c) for c in conds if c.strip()]
            components['WHERE'] = set(conds)
        # GROUP BY
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER|\s+HAVING|$)', query_no_alias, re.DOTALL | re.IGNORECASE)
        if group_match:
            group_by_clause = group_match.group(1).strip()
            fields = [self._normalize_token(f) for f in group_by_clause.split(',')]
            components['GROUP BY'] = set(fields)
        # ORDER BY
        order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+HAVING|$)', query_no_alias, re.DOTALL | re.IGNORECASE)
        if order_match:
            order_by_clause = order_match.group(1).strip()
            fields = [self._normalize_token(f.split()[0]) for f in order_by_clause.split(',')]
            components['ORDER BY'] = set(fields)
        # HAVING
        having_match = re.search(r'HAVING\s+(.*?)$', query_no_alias, re.DOTALL | re.IGNORECASE)
        if having_match:
            having_clause = having_match.group(1).strip()
            conds = re.split(r'\b(?:AND|OR)\b', having_clause, flags=re.IGNORECASE)
            conds = [self._normalize_token(c) for c in conds if c.strip()]
            components['HAVING'] = set(conds)
        # KEYWORDS
        keywords = self._extract_keywords(query)
        components['KEYWORDS'] = set(keywords)
        # Cảnh báo nếu alias không mapping được
        for m in re.finditer(r'\b(\w+)\.', query):
            alias = m.group(1)
            if alias not in alias_map and not self._normalize_token(alias) in schema_tables:
                print(f"[WARNING] Alias '{alias}' không mapping được trong query: {query}")
        return components

    def _extract_alias_mapping(self, query: str) -> dict:
        """
        Parse FROM/JOIN để lấy mapping alias -> table.
        Luôn normalize alias và tên bảng về lowercase, strip, thay underscore thành dấu cách, unicode NFC.
        """
        alias_map = {}
        from_join_pattern = re.compile(r'(FROM|JOIN)\s+([\w\s]+?)(?:\s+AS)?\s+(\w+)', re.IGNORECASE)
        for match in from_join_pattern.finditer(query):
            table_part = match.group(2).strip()
            alias = match.group(3).strip()
            # Normalize alias và table_name
            alias_norm = self._normalize_token(alias)
            table_name = table_part.split()[0]
            table_name_norm = self._normalize_token(table_name)
            alias_map[alias_norm] = table_name_norm
        return alias_map

    def _normalize_token(self, token: str) -> str:
        """
        Chuẩn hóa token: lowercase, strip, unicode NFC, nhiều space->1, rồi thay toàn bộ space thành _
        """
        token = token.lower().strip()
        token = ' '.join(token.split())
        token = unicodedata.normalize('NFC', token)
        token = token.replace(' ', '_')
        return token

    def _parse_select_clause_with_alias(self, clause: str, schema_columns: set, alias_map: dict) -> set:
        components = set()
        parts = [part.strip() for part in clause.split(',')]
        for part in parts:
            # Remove AS alias
            if ' AS ' in part.upper():
                part = part.split(' AS ')[0].strip()
            # Remove function calls, keep column names
            if '(' in part and ')' in part:
                match = re.search(r'\(([^)]+)\)', part)
                if match:
                    col = match.group(1).strip()
                    col = self._normalize_column_alias(col, alias_map)
                    for schema_col in schema_columns:
                        # DEBUG: In ra cặp so sánh
                        print(f"[DEBUG SELECT FUNC] Compare: '{col}' <-> '{schema_col}'")
                        if col == schema_col or schema_col.endswith(f'.{col}'):
                            components.add(schema_col)
            else:
                col = self._normalize_column_alias(part, alias_map)
                for schema_col in schema_columns:
                    # DEBUG: In ra cặp so sánh
                    print(f"[DEBUG SELECT] Compare: '{col}' <-> '{schema_col}'")
                    if col == schema_col or schema_col.endswith(f'.{col}'):
                        components.add(schema_col)
        return components

    def _parse_from_clause_with_alias(self, clause: str, schema_tables: set, alias_map: dict) -> set:
        components = set()
        parts = re.split(r'\b(?:JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN)\b', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part:
                tokens = part.split()
                if len(tokens) >= 1:
                    table_name = tokens[0]
                    # Nếu là alias, map về bảng gốc
                    if table_name in alias_map:
                        table_name = alias_map[table_name]
                    if table_name in schema_tables:
                        components.add(table_name)
        return components

    def _parse_where_clause_with_alias(self, clause: str, schema_columns: set, alias_map: dict) -> set:
        components = set()
        parts = re.split(r'\b(?:AND|OR)\b', clause, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part:
                match = re.search(r'(\w+)(?:\.(\w+))?\s*[=<>!]+\s*', part)
                if match:
                    prefix = match.group(1)
                    col = match.group(2) if match.group(2) else prefix
                    # Nếu prefix là alias, map về bảng gốc
                    if prefix in alias_map:
                        col_full = f"{alias_map[prefix]}.{col}"
                    else:
                        col_full = f"{prefix}.{col}" if match.group(2) else prefix
                    for schema_col in schema_columns:
                        if col_full == schema_col or schema_col.endswith(f'.{col}'):
                            components.add(schema_col)
        return components

    def _normalize_column_alias(self, col: str, alias_map: dict) -> str:
        """
        Nếu col có dạng alias.column thì map alias về bảng gốc.
        Ngoài ra, chuẩn hóa: lowercase, strip, thay underscore thành dấu cách, unicode normalize.
        Nếu phát hiện underscore ở std-level, in warning.
        """
        orig_col = col
        col = col.lower().strip()
        col = col.replace('_', ' ')
        col = ' '.join(col.split())
        col = unicodedata.normalize('NFC', col)
        if '_' in orig_col and orig_col != col:
            print(f"[WARNING] Underscore detected in column '{orig_col}' at std-level! (normalized: '{col}')")
        if '.' in col:
            prefix, colname = col.split('.', 1)
            prefix_norm = self._normalize_token(prefix)
            if prefix_norm in alias_map:
                return f"{alias_map[prefix_norm]}.{colname.strip()}"
        return col
    
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
    
    def simple_compare_where(self, pred_sql: str, gold_sql: str) -> bool:
        """
        So sánh mệnh đề WHERE của hai câu SQL một cách đơn giản:
        1. Dùng sqlparse lấy WHERE clause
        2. Tìm alias trong FROM/JOIN
        3. Thay alias về tên bảng gốc
        4. Xóa dấu phẩy, chuẩn hóa
        5. So sánh
        """
        def normalize(text):
            text = text.lower().strip()
            text = text.replace('_', ' ')
            text = unicodedata.normalize('NFC', text)
            text = text.replace(',', '')
            text = ' '.join(text.split())
            return text

        def extract_where_clause(sql):
            parsed = sqlparse.parse(sql)
            for stmt in parsed:
                found = False
                for token in stmt.tokens:
                    if found:
                        # Lấy phần sau WHERE
                        return str(token).strip()
                    if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'WHERE':
                        found = True
            return ''

        def extract_alias_mapping(sql):
            alias_map = {}
            parsed = sqlparse.parse(sql)
            for stmt in parsed:
                for token in stmt.tokens:
                    if token.ttype is None and token.is_group:
                        subtokens = list(token.flatten())
                        for i, sub in enumerate(subtokens):
                            if sub.match(sqlparse.tokens.Keyword, ('FROM', 'JOIN')):
                                # Tìm table và alias
                                if i+2 < len(subtokens):
                                    table_token = subtokens[i+1]
                                    alias_token = subtokens[i+2]
                                    if alias_token.ttype == sqlparse.tokens.Name:
                                        alias_map[alias_token.value] = table_token.value
            return alias_map

        def replace_alias(where_clause, alias_map):
            for alias, table in alias_map.items():
                where_clause = re.sub(rf'\b{re.escape(alias)}\.', f'{table}.', where_clause)
            return where_clause

        pred_where = extract_where_clause(pred_sql)
        gold_where = extract_where_clause(gold_sql)
        pred_alias = extract_alias_mapping(pred_sql)
        gold_alias = extract_alias_mapping(gold_sql)
        pred_where = replace_alias(pred_where, pred_alias)
        gold_where = replace_alias(gold_where, gold_alias)
        pred_where = normalize(pred_where)
        gold_where = normalize(gold_where)
        return pred_where == gold_where
    
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

if __name__ == '__main__':
    # Test case: SELECT F1 và so sánh WHERE đơn giản
    pred_sql = "SELECT t.id tài sản FROM tài sản t WHERE t.id tài sản = 1"
    gold_sql = "SELECT t1.id tài sản FROM tài sản t1 WHERE t1.id tài sản = 1"
    db_id = 'dummy_db'  # Không dùng schema thật cho test này
    schema_path = 'dataset/ViText2SQL/std-level/tables.json'  # Đường dẫn giả định

    em = EvaluationMetrics()
    # Test simple_compare_where
    print('Test simple_compare_where:', em.simple_compare_where(pred_sql, gold_sql))

    # Test F1 SELECT (giả lập schema)
    # Tạo schema giả cho extract_components_as_sets
    schema = {
        'table_names': ['tài sản'],
        'column_names': [(0, 'id tài sản')]
    }
    schema_tables, schema_columns = em.get_table_and_column_sets(schema)
    pred_components = em.extract_components_as_sets(pred_sql, schema_tables, schema_columns)
    gold_components = em.extract_components_as_sets(gold_sql, schema_tables, schema_columns)
    print('Pred SELECT:', pred_components['SELECT'])
    print('Gold SELECT:', gold_components['SELECT'])
    tp = len(pred_components['SELECT'] & gold_components['SELECT'])
    fp = len(pred_components['SELECT'] - gold_components['SELECT'])
    fn = len(gold_components['SELECT'] - pred_components['SELECT'])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    print(f'SELECT F1: {f1:.2f}') 
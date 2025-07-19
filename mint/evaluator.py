"""
Unified Evaluator for ViPERSQL

Provides evaluation functionality for all strategies.
"""

from typing import Dict, Any, List
from .config import ViPERConfig
from .metrics import EvaluationMetrics
import re


class UnifiedEvaluator:
    """Unified evaluator for all strategies."""
    
    def __init__(self, config: ViPERConfig):
        """Initialize evaluator with configuration."""
        self.config = config
        self.metrics = EvaluationMetrics()
    
    def evaluate_single(
        self,
        predicted_sql: str,
        gold_sql: str,
        db_id: str,
        request_id: str,
        schema_path: str = None
    ) -> Dict[str, Any]:
        """Evaluate a single prediction."""
        # Chuẩn hóa predicted_sql trước khi evaluation
        predicted_sql = self.normalize_sql_query(predicted_sql)
        predicted_sql = self.normalize_sql_functions(predicted_sql)
        
        # Chuẩn hóa gold_sql
        gold_sql = self.normalize_sql_functions(gold_sql)
        
        # Basic evaluation
        exact_match = self._exact_match(predicted_sql, gold_sql)
        syntax_valid = self._validate_syntax(predicted_sql)
        
        # Extract SQL clauses for detailed analysis
        predicted_clauses = self.extract_sql_clauses(predicted_sql)
        gold_clauses = self.extract_sql_clauses(gold_sql)
        
        # Component-wise F1e for single query
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'
        component_f1 = self.metrics.component_wise_f1_score([predicted_sql], [gold_sql], [db_id], schema_path)
        
        # Create details object
        details = {}
        for clause in ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']:
            predicted_clause = predicted_clauses.get(clause, '')
            gold_clause = gold_clauses.get(clause, '')
            
            # Nếu cả gold và predicted đều rỗng thì score = 1.0
            if not predicted_clause and not gold_clause:
                score = 1.0
            else:
                score = component_f1.get(clause, 0.0) if clause in component_f1 else 0.0
            
            details[clause] = {
                'predicted': predicted_clause,
                'gold': gold_clause,
                'score': score
            }
        
        result = {
            'exact_match': exact_match,
            'syntax_valid': syntax_valid,
            'component_f1_scores': component_f1,
            'details': details,
            'request_id': request_id
        }
        return result

    def normalize_sql_query(self, sql_query: str) -> str:
        """
        Chuẩn hóa SQL query:
        1. Replace ký tự xuống dòng (\n) thành khoảng trắng
        2. Replace 2 hoặc nhiều khoảng trắng = 1 khoảng trắng
        """
        if not sql_query:
            return sql_query
        
        # 1. Replace \n thành khoảng trắng
        sql_query = sql_query.replace('\n', ' ')
        
        # 2. Replace nhiều khoảng trắng thành 1 khoảng trắng
        sql_query = re.sub(r'\s+', ' ', sql_query)
        
        # 3. Trim khoảng trắng đầu cuối
        sql_query = sql_query.strip()
        
        return sql_query

    def normalize_sql_functions(self, sql_query: str) -> str:
        """
        Chuẩn hóa các hàm SQL như COUNT, MIN, MAX, SUM, AVG:
        Bỏ khoảng trắng không cần thiết trong hàm.
        Ví dụ: max ( t1.chiều_dài_theo_mét ) -> max(t1.chiều_dài_theo_mét)
        """
        if not sql_query:
            return sql_query
        
        # Danh sách các hàm SQL cần chuẩn hóa
        sql_functions = [
            'COUNT', 'MIN', 'MAX', 'SUM', 'AVG', 'COUNT_DISTINCT',
            'count', 'min', 'max', 'sum', 'avg', 'count_distinct'
        ]
        
        # Chuẩn hóa từng hàm
        for func in sql_functions:
            # Pattern: function ( ... ) -> function(...)
            # Xử lý cả trường hợp có khoảng trắng và không có
            patterns = [
                rf'{func}\s*\(\s*([^)]+)\s*\)',  # function ( ... )
                rf'{func}\s*\(\s*([^)]+)\s*\)',  # function(...)
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, sql_query, re.IGNORECASE)
                for match in reversed(list(matches)):  # Xử lý từ cuối để không ảnh hưởng index
                    full_match = match.group(0)
                    content = match.group(1).strip()
                    # Tạo lại với format chuẩn: function(content)
                    replacement = f"{func}({content})"
                    sql_query = sql_query[:match.start()] + replacement + sql_query[match.end():]
        
        return sql_query
    
    def calculate_summary(self, results: List[Dict[str, Any]], schema_path: str = None) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not results:
            return {'total_samples': 0}
        valid_results = [r for r in results if 'error' not in r]
        total = len(valid_results)
        if total == 0:
            return {
                'total_samples': len(results),
                'errors': len(results)
            }
        # Calculate basic metrics
        exact_matches = sum(
            1 for r in valid_results 
            if r.get('evaluation', {}).get('exact_match', False)
        )
        syntax_valid = sum(
            1 for r in valid_results
            if r.get('evaluation', {}).get('syntax_valid', False)
        )
        # Component F1-score
        predicted_queries = [r['predicted_sql'] for r in valid_results]
        gold_queries = [r['gold_sql'] for r in valid_results]
        db_ids = [r['db_id'] for r in valid_results]
        if schema_path is None:
            schema_path = self.config.schema_path if hasattr(self.config, 'schema_path') else 'dataset/ViText2SQL/std-level/tables.json'
        component_f1_scores = self.metrics.component_wise_f1_score(predicted_queries, gold_queries, db_ids, schema_path)
        # Calculate average F1 across all components
        avg_component_f1 = sum(component_f1_scores.values()) / len(component_f1_scores) if component_f1_scores else 0.0  
        summary = {
            'total_samples': len(results),
            'valid_results': total,
            'exact_match_accuracy': (exact_matches / total) * 100,
            'component_f1_scores': component_f1_scores,
            'avg_component_f1_score': avg_component_f1 * 100,
            'syntax_validity': (syntax_valid / total) * 100,
            'errors': len(results) - total
        }
        return summary
    
    def _exact_match(self, predicted: str, gold: str) -> bool:
        """Check exact match after normalization."""
        def normalize(sql):
            sql = sql.strip().lower()
            sql = ' '.join(sql.split())
            return sql
        
        return normalize(predicted) == normalize(gold)
    
    def _validate_syntax(self, sql: str) -> bool:
        """Validate SQL syntax."""
        try:
            import sqlparse
            parsed = sqlparse.parse(sql)
            return len(parsed) > 0
        except:
            return False 

    def extract_sql_clauses(self, sql_query: str) -> Dict[str, str]:
        """Extract SQL clauses for detailed analysis."""
        clauses = {}
        
        # SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
        if select_match:
            clauses['SELECT'] = select_match.group(1).strip()
        
        # FROM clause
        from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+HAVING|$)', sql_query, re.IGNORECASE | re.DOTALL)
        if from_match:
            clauses['FROM'] = from_match.group(1).strip()
        
        # WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+HAVING|$)', sql_query, re.IGNORECASE | re.DOTALL)
        if where_match:
            clauses['WHERE'] = where_match.group(1).strip()
        
        # GROUP BY clause
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER|\s+HAVING|$)', sql_query, re.IGNORECASE | re.DOTALL)
        if group_match:
            clauses['GROUP BY'] = group_match.group(1).strip()
        
        # ORDER BY clause
        order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+HAVING|$)', sql_query, re.IGNORECASE | re.DOTALL)
        if order_match:
            clauses['ORDER BY'] = order_match.group(1).strip()
        
        # HAVING clause
        having_match = re.search(r'HAVING\s+(.*?)$', sql_query, re.IGNORECASE | re.DOTALL)
        if having_match:
            clauses['HAVING'] = having_match.group(1).strip()
        
        return clauses 
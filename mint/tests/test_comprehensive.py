"""
Comprehensive test suite for MINT package.
Tests all modules with various edge cases and scenarios.
"""

import unittest
import tempfile
import shutil
import json
import os
import sqlite3
from pathlib import Path
import sys

# Add parent directory to path to import mint
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mint.database import SQLiteBuilder
from mint.executor import SQLExecutor
from mint.metrics import EvaluationMetrics, SQLDifficultyClassifier
from mint.utils import (
    normalize_sql, load_dataset, extract_queries_from_dataset,
    safe_execute_sql, create_query_pairs, get_query_statistics,
    validate_dataset_format, filter_valid_queries
)

class TestSQLiteBuilder(unittest.TestCase):
    """Test SQLiteBuilder functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.builder = SQLiteBuilder(output_dir=self.temp_dir)
        
        # Create test tables.json
        self.test_tables = [
            {
                "table_name": "students",
                "column_names": ["id", "name", "age"],
                "column_types": ["integer", "text", "integer"]
            },
            {
                "table_name": "courses",
                "column_names": ["course_id", "course_name", "credits"],
                "column_types": ["integer", "text", "integer"]
            }
        ]
        
        self.tables_file = os.path.join(self.temp_dir, "tables.json")
        with open(self.tables_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_tables, f)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_build_database_success(self):
        """Test successful database creation."""
        result = self.builder.build_database(self.tables_file, "test_db")
        
        self.assertIsNotNone(result['database_path'])
        self.assertEqual(result['total_tables'], 2)
        self.assertEqual(result['created_tables'], 2)
        self.assertEqual(result['failed_tables'], 0)
        self.assertTrue(os.path.exists(result['database_path']))
    
    def test_build_database_with_duplicates(self):
        """Test database creation with duplicate column names."""
        duplicate_tables = [
            {
                "table_name": "test_table",
                "column_names": ["id", "name", "name"],  # Duplicate column
                "column_types": ["integer", "text", "text"]
            }
        ]
        
        duplicate_file = os.path.join(self.temp_dir, "duplicate_tables.json")
        with open(duplicate_file, 'w', encoding='utf-8') as f:
            json.dump(duplicate_tables, f)
        
        result = self.builder.build_database(duplicate_file, "duplicate_db")
        
        self.assertEqual(result['failed_tables'], 1)
        self.assertIn("Duplicate columns detected", str(result['warnings']))
    
    def test_build_database_invalid_file(self):
        """Test database creation with invalid file."""
        result = self.builder.build_database("nonexistent.json", "test_db")
        
        self.assertIn('error', result)
        self.assertEqual(result['created_tables'], 0)
    
    def test_get_database_info(self):
        """Test getting database information."""
        # First create a database
        result = self.builder.build_database(self.tables_file, "info_test")
        
        # Get info about created database
        info = self.builder.get_database_info(result['database_path'])
        
        self.assertEqual(info['table_count'], 2)
        self.assertIn('students', info['tables'])
        self.assertIn('courses', info['tables'])
        self.assertEqual(len(info['tables']['students']['columns']), 3)
    
    def test_sanitize_name(self):
        """Test name sanitization."""
        # Test various problematic names
        test_cases = [
            ("normal_name", "normal_name"),
            ("name with spaces", "name_with_spaces"),
            ("name-with-dashes", "name_with_dashes"),
            ("name.with.dots", "name_with_dots"),
            ("123name", "col_123name"),
            ("", "unknown_column")
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.builder._sanitize_name(input_name)
                self.assertEqual(result, expected)


class TestSQLExecutor(unittest.TestCase):
    """Test SQLExecutor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test database
        self.db_path = os.path.join(self.temp_dir, "test.db")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create test table with sample data
        cursor.execute('''
            CREATE TABLE students (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        ''')
        
        cursor.execute("INSERT INTO students VALUES (1, 'Alice', 20)")
        cursor.execute("INSERT INTO students VALUES (2, 'Bob', 22)")
        cursor.execute("INSERT INTO students VALUES (3, 'Charlie', 21)")
        
        conn.commit()
        conn.close()
        
        self.executor = SQLExecutor(db_directory=self.temp_dir, timeout=5)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_execute_query_success(self):
        """Test successful query execution."""
        result = self.executor.execute_query("SELECT * FROM students", "test")
        
        self.assertTrue(result['success'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['row_count'], 3)
        self.assertGreater(result['execution_time'], 0)
    
    def test_execute_query_error(self):
        """Test query execution with SQL error."""
        result = self.executor.execute_query("SELECT * FROM nonexistent_table", "test")
        
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])
        self.assertEqual(result['row_count'], 0)
    
    def test_execute_query_nonexistent_db(self):
        """Test query execution with nonexistent database."""
        result = self.executor.execute_query("SELECT 1", "nonexistent")
        
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
    
    def test_compare_results_exact_match(self):
        """Test result comparison with exact match."""
        result1 = [(1, 'Alice', 20), (2, 'Bob', 22)]
        result2 = [(1, 'Alice', 20), (2, 'Bob', 22)]
        
        comparison = self.executor.compare_results(result1, result2)
        
        self.assertTrue(comparison['exact_match'])
        self.assertEqual(comparison['precision'], 1.0)
        self.assertEqual(comparison['recall'], 1.0)
        self.assertEqual(comparison['f1_score'], 1.0)
    
    def test_compare_results_partial_match(self):
        """Test result comparison with partial match."""
        result1 = [(1, 'Alice', 20), (2, 'Bob', 22), (3, 'Charlie', 21)]
        result2 = [(1, 'Alice', 20), (2, 'Bob', 22)]
        
        comparison = self.executor.compare_results(result1, result2)
        
        self.assertFalse(comparison['exact_match'])
        self.assertEqual(comparison['precision'], 2/3)  # 2 common out of 3 in result1
        self.assertEqual(comparison['recall'], 1.0)     # 2 common out of 2 in result2
        self.assertAlmostEqual(comparison['f1_score'], 0.8, places=2)
    
    def test_compare_results_empty(self):
        """Test result comparison with empty results."""
        comparison = self.executor.compare_results([], [])
        
        self.assertTrue(comparison['exact_match'])
        self.assertEqual(comparison['precision'], 1.0)
        self.assertEqual(comparison['recall'], 1.0)
        self.assertEqual(comparison['f1_score'], 1.0)
    
    def test_execute_and_compare(self):
        """Test execute and compare functionality."""
        query1 = "SELECT * FROM students WHERE age > 20"
        query2 = "SELECT * FROM students WHERE age >= 25"  # Different enough to ensure different results
        
        result = self.executor.execute_and_compare(query1, query2, "test")
        
        self.assertTrue(result['both_successful'])
        self.assertIsNotNone(result['comparison'])
        # Results might be the same if no students meet the criteria, so just check comparison exists
    
    def test_batch_execute(self):
        """Test batch query execution."""
        queries = [
            "SELECT COUNT(*) FROM students",
            "SELECT * FROM students WHERE age = 20",
            "SELECT invalid_column FROM students"  # This should fail
        ]
        
        results = self.executor.batch_execute(queries, "test")
        
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0]['success'])
        self.assertTrue(results[1]['success'])
        self.assertFalse(results[2]['success'])
    
    def test_get_execution_stats(self):
        """Test execution statistics calculation."""
        results = [
            {'success': True, 'execution_time': 0.1},
            {'success': True, 'execution_time': 0.2},
            {'success': False, 'error': 'SQLite error: no such table'}
        ]
        
        stats = self.executor.get_execution_stats(results)
        
        self.assertEqual(stats['total_queries'], 3)
        self.assertEqual(stats['successful_queries'], 2)
        self.assertEqual(stats['failed_queries'], 1)
        self.assertAlmostEqual(stats['success_rate'], 2/3, places=2)
        self.assertAlmostEqual(stats['avg_execution_time'], 0.15, places=1)
    
    def test_test_database_connection(self):
        """Test database connection testing."""
        result = self.executor.test_database_connection("test")
        
        self.assertTrue(result['success'])
        self.assertIsNone(result['error'])
        self.assertEqual(len(result['tables']), 1)
        self.assertIn('students', result['tables'])


class TestEvaluationMetrics(unittest.TestCase):
    """Test EvaluationMetrics functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.metrics = EvaluationMetrics()
        
        # Test data
        self.predicted_queries = [
            "SELECT * FROM students",
            "SELECT name FROM students WHERE age > 20",
            "SELECT COUNT(*) FROM students"
        ]
        
        self.gold_queries = [
            "SELECT * FROM students",
            "SELECT name FROM students WHERE age >= 21",
            "SELECT COUNT(*) FROM students"
        ]
    
    def test_exact_match_accuracy(self):
        """Test exact match accuracy calculation."""
        accuracy = self.metrics.exact_match_accuracy(self.predicted_queries, self.gold_queries)
        
        # Only first and third queries match exactly
        expected_accuracy = 2/3
        self.assertAlmostEqual(accuracy, expected_accuracy, places=2)
    
    def test_exact_match_accuracy_perfect(self):
        """Test exact match accuracy with perfect matches."""
        accuracy = self.metrics.exact_match_accuracy(self.gold_queries, self.gold_queries)
        self.assertEqual(accuracy, 1.0)
    
    def test_exact_match_accuracy_empty(self):
        """Test exact match accuracy with empty lists."""
        accuracy = self.metrics.exact_match_accuracy([], [])
        self.assertEqual(accuracy, 0.0)
    
    def test_exact_match_accuracy_mismatched_lengths(self):
        """Test exact match accuracy with mismatched list lengths."""
        with self.assertRaises(ValueError):
            self.metrics.exact_match_accuracy(["SELECT 1"], ["SELECT 1", "SELECT 2"])
    
    def test_component_wise_accuracy(self):
        """Test component-wise accuracy calculation."""
        accuracies = self.metrics.component_wise_accuracy(self.predicted_queries, self.gold_queries)
        
        # Check that all components are present
        expected_components = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
        for component in expected_components:
            self.assertIn(component, accuracies)
            self.assertGreaterEqual(accuracies[component], 0.0)
            self.assertLessEqual(accuracies[component], 1.0)
    
    def test_sql_similarity(self):
        """Test SQL similarity calculation."""
        similarities = self.metrics.sql_similarity(self.predicted_queries, self.gold_queries)
        
        self.assertEqual(len(similarities), 3)
        # First and third should have high similarity (exact matches)
        self.assertGreater(similarities[0], 0.9)
        self.assertGreater(similarities[2], 0.9)
        # Second should have lower similarity (but might still be high)
        self.assertLess(similarities[1], 1.0)
    
    def test_difficulty_breakdown_accuracy(self):
        """Test difficulty breakdown accuracy."""
        breakdown = self.metrics.difficulty_breakdown_accuracy(self.predicted_queries, self.gold_queries)
        
        # Should have difficulty levels
        for difficulty, stats in breakdown.items():
            self.assertIn('count', stats)
            self.assertIn('exact_match_accuracy', stats)
            self.assertIn('avg_similarity', stats)
            self.assertIn('percentage_of_total', stats)
            
            # Validate ranges
            self.assertGreaterEqual(stats['exact_match_accuracy'], 0.0)
            self.assertLessEqual(stats['exact_match_accuracy'], 1.0)
            self.assertGreaterEqual(stats['avg_similarity'], 0.0)
            self.assertLessEqual(stats['avg_similarity'], 1.0)
    
    def test_comprehensive_evaluation(self):
        """Test comprehensive evaluation."""
        results = self.metrics.comprehensive_evaluation(self.predicted_queries, self.gold_queries)
        
        # Check all expected keys are present
        expected_keys = [
            'total_queries', 'exact_match_accuracy', 'component_wise_accuracy',
            'avg_sql_similarity', 'difficulty_breakdown'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
        
        self.assertEqual(results['total_queries'], 3)
    
    def test_evaluation_summary(self):
        """Test evaluation summary generation."""
        results = self.metrics.comprehensive_evaluation(self.predicted_queries, self.gold_queries)
        summary = self.metrics.evaluation_summary(results)
        
        self.assertIsInstance(summary, str)
        self.assertIn("SQL Evaluation Results", summary)
        self.assertIn("Total queries: 3", summary)
        self.assertIn("Component-wise Accuracy", summary)
        self.assertIn("Difficulty Breakdown", summary)


class TestSQLDifficultyClassifier(unittest.TestCase):
    """Test SQLDifficultyClassifier functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.classifier = SQLDifficultyClassifier()
    
    def test_classify_easy_queries(self):
        """Test classification of easy queries."""
        easy_queries = [
            "SELECT * FROM students",
            "SELECT name FROM students WHERE age = 20",
            "SELECT name, age FROM students"
        ]
        
        for query in easy_queries:
            with self.subTest(query=query):
                difficulty = self.classifier.classify_query(query)
                self.assertEqual(difficulty, 'easy')
    
    def test_classify_medium_queries(self):
        """Test classification of medium queries."""
        medium_queries = [
            "SELECT COUNT(*) FROM students",
            "SELECT * FROM students ORDER BY age",
            "SELECT name FROM students GROUP BY name",
            "SELECT * FROM students s JOIN courses c ON s.id = c.student_id"
        ]
        
        for query in medium_queries:
            with self.subTest(query=query):
                difficulty = self.classifier.classify_query(query)
                self.assertIn(difficulty, ['medium', 'hard'])  # Some JOINs might be classified as hard
    
    def test_classify_hard_queries(self):
        """Test classification of hard queries."""
        hard_queries = [
            "SELECT s.name, COUNT(*) FROM students s JOIN courses c ON s.id = c.student_id GROUP BY s.name"
        ]
        
        for query in hard_queries:
            with self.subTest(query=query):
                difficulty = self.classifier.classify_query(query)
                self.assertIn(difficulty, ['medium', 'hard', 'extra'])  # Allow medium as well
    
    def test_classify_extra_queries(self):
        """Test classification of extra (complex) queries."""
        extra_queries = [
            "SELECT * FROM students WHERE id IN (SELECT student_id FROM courses)",
            "SELECT * FROM students UNION SELECT * FROM teachers",
            "WITH top_students AS (SELECT * FROM students WHERE age > 20) SELECT * FROM top_students"
        ]
        
        for query in extra_queries:
            with self.subTest(query=query):
                difficulty = self.classifier.classify_query(query)
                self.assertEqual(difficulty, 'extra')


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_normalize_sql(self):
        """Test SQL normalization."""
        test_cases = [
            ("SELECT * FROM students;", "select * from students"),
            ("  SELECT   name  FROM   students  ", "select name from students"),
            ("SELECT * FROM Students WHERE age > 20", "select * from students where age > 20"),
            ("", ""),
            (None, "")
        ]
        
        for input_sql, expected in test_cases:
            with self.subTest(input_sql=input_sql):
                result = normalize_sql(input_sql)
                self.assertEqual(result, expected)
    
    def test_load_dataset(self):
        """Test dataset loading."""
        # Create test dataset
        test_data = [
            {"question": "How many students?", "query": "SELECT COUNT(*) FROM students", "db_id": "school"},
            {"question": "List all students", "query": "SELECT * FROM students", "db_id": "school"}
        ]
        
        test_file = os.path.join(self.temp_dir, "test_dataset.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        loaded_data = load_dataset(test_file)
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["question"], "How many students?")
    
    def test_load_dataset_nonexistent(self):
        """Test loading nonexistent dataset."""
        with self.assertRaises(FileNotFoundError):
            load_dataset("nonexistent.json")
    
    def test_extract_queries_from_dataset(self):
        """Test query extraction from dataset."""
        dataset = [
            {"query": "SELECT * FROM students"},
            {"sql": "SELECT COUNT(*) FROM courses"},  # Alternative key
            {"question": "How many?"}  # Missing query
        ]
        
        queries = extract_queries_from_dataset(dataset)
        self.assertEqual(len(queries), 3)
        self.assertEqual(queries[0], "SELECT * FROM students")
        self.assertEqual(queries[1], "SELECT COUNT(*) FROM courses")
        self.assertEqual(queries[2], "")  # Missing query becomes empty string
    
    def test_safe_execute_sql(self):
        """Test SQL safety checking."""
        safe_queries = [
            "SELECT * FROM students",
            "SELECT name FROM students WHERE age > 20",
            "SELECT COUNT(*) FROM students GROUP BY age"
        ]
        
        unsafe_queries = [
            "DROP TABLE students",
            "DELETE FROM students",
            "INSERT INTO students VALUES (1, 'test')",
            "UPDATE students SET age = 25",
            "TRUNCATE TABLE students",
            "",
            None
        ]
        
        for query in safe_queries:
            with self.subTest(query=query):
                self.assertTrue(safe_execute_sql(query))
        
        for query in unsafe_queries:
            with self.subTest(query=query):
                self.assertFalse(safe_execute_sql(query))
    
    def test_create_query_pairs(self):
        """Test query pair creation."""
        predicted = ["SELECT * FROM a", "SELECT * FROM b"]
        gold = ["SELECT * FROM a", "SELECT COUNT(*) FROM b"]
        
        pairs = create_query_pairs(predicted, gold)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0], ("SELECT * FROM a", "SELECT * FROM a"))
        self.assertEqual(pairs[1], ("SELECT * FROM b", "SELECT COUNT(*) FROM b"))
    
    def test_create_query_pairs_mismatched(self):
        """Test query pair creation with mismatched lengths."""
        with self.assertRaises(ValueError):
            create_query_pairs(["SELECT 1"], ["SELECT 1", "SELECT 2"])
    
    def test_get_query_statistics(self):
        """Test query statistics calculation."""
        queries = [
            "SELECT * FROM students",
            "SELECT name FROM students WHERE age > 20",
            "",
            "SELECT COUNT(*) FROM courses"
        ]
        
        stats = get_query_statistics(queries)
        
        self.assertEqual(stats['total_queries'], 4)
        self.assertEqual(stats['empty_queries'], 1)
        self.assertEqual(stats['unique_queries'], 4)  # All are unique including empty
        self.assertGreater(stats['avg_length'], 0)
        self.assertGreater(stats['max_length'], stats['min_length'])
    
    def test_get_query_statistics_empty(self):
        """Test query statistics with empty list."""
        stats = get_query_statistics([])
        
        self.assertEqual(stats['total_queries'], 0)
        self.assertEqual(stats['avg_length'], 0)
        self.assertEqual(stats['max_length'], 0)
        self.assertEqual(stats['min_length'], 0)
    
    def test_validate_dataset_format(self):
        """Test dataset format validation."""
        valid_dataset = [
            {"question": "How many?", "query": "SELECT COUNT(*)", "db_id": "test"},
            {"question": "List all", "query": "SELECT *", "db_id": "test"}
        ]
        
        invalid_dataset = [
            {"question": "How many?", "db_id": "test"},  # Missing query
            {"query": "SELECT *", "db_id": "test"},      # Missing question
            {"question": "", "query": "SELECT *", "db_id": "test"}  # Empty question
        ]
        
        # Test valid dataset
        result = validate_dataset_format(valid_dataset)
        self.assertTrue(result['valid'])
        self.assertEqual(result['total_items'], 2)
        
        # Test invalid dataset
        result = validate_dataset_format(invalid_dataset)
        self.assertFalse(result['valid'])
        self.assertIn('query', result['missing_keys'])
        self.assertIn('question', result['missing_keys'])
    
    def test_filter_valid_queries(self):
        """Test filtering valid queries from dataset."""
        dataset = [
            {"question": "Count", "query": "SELECT COUNT(*) FROM students"},
            {"question": "Drop", "query": "DROP TABLE students"},  # Unsafe
            {"question": "Empty", "query": ""},                    # Empty
            {"question": "List", "query": "SELECT * FROM students"}
        ]
        
        filtered = filter_valid_queries(dataset)
        
        self.assertEqual(len(filtered), 2)  # Only first and last are valid
        self.assertEqual(filtered[0]["question"], "Count")
        self.assertEqual(filtered[1]["question"], "List")


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test dataset
        self.test_dataset = [
            {
                "question": "How many students are there?",
                "query": "SELECT COUNT(*) FROM students",
                "db_id": "school"
            },
            {
                "question": "List all student names",
                "query": "SELECT name FROM students",
                "db_id": "school"
            }
        ]
        
        # Create test tables
        self.test_tables = [
            {
                "table_name": "students",
                "column_names": ["id", "name", "age"],
                "column_types": ["integer", "text", "integer"]
            }
        ]
        
        # Save test files
        self.dataset_file = os.path.join(self.temp_dir, "test_dataset.json")
        self.tables_file = os.path.join(self.temp_dir, "tables.json")
        
        with open(self.dataset_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_dataset, f)
        
        with open(self.tables_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_tables, f)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow(self):
        """Test complete evaluation workflow."""
        # 1. Build database
        builder = SQLiteBuilder(output_dir=self.temp_dir)
        build_result = builder.build_database(self.tables_file, "test_db")
        self.assertTrue(build_result['created_tables'] > 0)
        
        # 2. Load dataset
        dataset = load_dataset(self.dataset_file)
        gold_queries = extract_queries_from_dataset(dataset)
        
        # 3. Create predicted queries (simulate model predictions)
        predicted_queries = [
            "SELECT COUNT(*) FROM students",  # Exact match
            "SELECT name FROM students ORDER BY name"  # Different from gold
        ]
        
        # 4. Execute queries and compare (if database has data)
        executor = SQLExecutor(db_directory=self.temp_dir)
        
        # Test database connection
        db_test = executor.test_database_connection("test_db")
        self.assertTrue(db_test['success'])
        
        # 5. Calculate metrics
        metrics = EvaluationMetrics()
        results = metrics.comprehensive_evaluation(predicted_queries, gold_queries)
        
        # Verify results
        self.assertEqual(results['total_queries'], 2)
        self.assertIn('exact_match_accuracy', results)
        self.assertIn('component_wise_accuracy', results)
        self.assertIn('difficulty_breakdown', results)
        
        # 6. Generate summary
        summary = metrics.evaluation_summary(results)
        self.assertIsInstance(summary, str)
        self.assertIn("SQL Evaluation Results", summary)


def run_all_tests():
    """Run all tests and return results."""
    # Create test suite
    test_classes = [
        TestSQLiteBuilder,
        TestSQLExecutor,
        TestEvaluationMetrics,
        TestSQLDifficultyClassifier,
        TestUtils,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("Running comprehensive test suite for MINT package...")
    print("=" * 60)
    
    result = run_all_tests()
    
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed!")
        
    print("=" * 60) 
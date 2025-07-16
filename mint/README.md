# MINT - Modern Integration for Natural language Text-to-SQL

**MINT** is a comprehensive toolkit for evaluating Vietnamese Text-to-SQL models. The package provides functionality from SQLite database creation, SQL query execution, to detailed evaluation metrics calculation.

## 🚀 Key Features

### 1. SQLite Database Builder (`mint.database`)
- **Automatically create SQLite databases** from JSON metadata
- **Handle Vietnamese text** and special characters
- **Check duplicate columns** and validation
- **Support multiple database versions** (syllable-level, word-level)

### 2. SQL Query Executor (`mint.executor`) 
- **Execute SQL queries** safely with timeout protection
- **Compare execution results** between predicted and gold queries
- **Batch processing** for multiple queries
- **Detailed error handling** and statistics

### 3. Evaluation Metrics (`mint.metrics`)
- **Exact Match Accuracy**: Precise comparison between SQL strings
- **Component-wise Accuracy**: Evaluate each SQL component (SELECT, FROM, WHERE, etc.)
- **SQL Similarity**: Similarity based on string matching
- **Difficulty Breakdown**: Analysis by query difficulty (Easy, Medium, Hard, Extra)
- **Execution Accuracy**: Evaluation based on execution results

### 4. Utility Functions (`mint.utils`)
- **SQL normalization** for comparison
- **Dataset loading and validation**
- **Query safety checking**
- **Statistics calculation**

## 📦 Installation

```bash
# Clone repository
git clone <repository-url>
cd Vi_NL2SQL

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install pandas numpy sqlparse
```

## 🔧 Quick Start

### 1. Import MINT modules

```python
from mint import SQLiteBuilder, SQLExecutor, EvaluationMetrics
from mint.utils import load_dataset, extract_queries_from_dataset
```

### 2. Create SQLite Database

```python
# Initialize builder
builder = SQLiteBuilder(output_dir="sqlite_dbs")

# Create database from tables.json
result = builder.build_database(
    tables_json_path="dataset/ViText2SQL/syllable-level/tables.json",
    db_name="syllable-level"
)

print(f"Created {result['created_tables']}/{result['total_tables']} tables")
print(f"Database path: {result['database_path']}")
```

### 3. Load Dataset and Extract Queries

```python
# Load dataset
dataset = load_dataset("dataset/ViText2SQL/syllable-level/dev.json")

# Extract SQL queries
gold_queries = extract_queries_from_dataset(dataset, query_key='query')
db_names = extract_database_names_from_dataset(dataset, db_key='db_id')

# Predicted queries from your model
predicted_queries = [
    "SELECT COUNT(*) FROM students",
    "SELECT name FROM students WHERE age > 20",
    # ... more predictions
]
```

### 4. Evaluate with Execution Accuracy

```python
# Initialize executor
executor = SQLExecutor(db_directory="sqlite_dbs", timeout=30)

# Compare execution results
comparison_results = []
for pred, gold, db_name in zip(predicted_queries, gold_queries, db_names):
    result = executor.execute_and_compare(pred, gold, db_name)
    comparison_results.append(result)

# Calculate execution statistics
exec_stats = executor.get_comparison_stats(comparison_results)
print(f"Execution Accuracy: {exec_stats['execution_accuracy']:.2%}")
```

### 5. Calculate Evaluation Metrics

```python
# Initialize metrics calculator
metrics = EvaluationMetrics()

# Calculate comprehensive evaluation
results = metrics.comprehensive_evaluation(
    predicted_queries=predicted_queries,
    gold_queries=gold_queries,
    execution_results=comparison_results
)

# Print summary
summary = metrics.evaluation_summary(results)
print(summary)
```

## 📊 Example Output

```
=== SQL Evaluation Results ===
Total queries: 954
Exact Match Accuracy: 67.50%
Average SQL Similarity: 84.32%
Execution Accuracy: 71.25%
Execution Success Rate: 89.62%

=== Component-wise Accuracy ===
SELECT: 89.45%
FROM: 94.38%
WHERE: 78.23%
GROUP BY: 85.71%
ORDER BY: 92.31%
HAVING: 80.00%

=== Difficulty Breakdown ===
Easy: 78.25% (378 queries, 39.6%)
Medium: 69.84% (129 queries, 13.5%)
Hard: 58.73% (340 queries, 35.6%)
Extra: 45.10% (107 queries, 11.2%)
```

## 🧪 Advanced Usage

### Custom Database Builder

```python
# Build all databases in dataset
builder = SQLiteBuilder(output_dir="custom_dbs")
results = builder.build_all_databases("dataset/ViText2SQL")

for version, result in results.items():
    print(f"{version}: {result['created_tables']} tables created")
```

### Batch Query Execution

```python
# Execute multiple queries at once
executor = SQLExecutor(db_directory="sqlite_dbs")

# Batch execution
results = executor.batch_execute(predicted_queries, "syllable-level")

# Get execution statistics
stats = executor.get_execution_stats(results)
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average execution time: {stats['avg_execution_time']:.3f}s")
```

### Custom Difficulty Classification

```python
from mint.metrics import SQLDifficultyClassifier

classifier = SQLDifficultyClassifier()

query = "SELECT s.name, COUNT(*) FROM students s JOIN courses c ON s.id = c.student_id GROUP BY s.name"
difficulty = classifier.classify_query(query)
print(f"Query difficulty: {difficulty}")  # Output: hard
```

### SQL Normalization and Validation

```python
from mint.utils import normalize_sql, safe_execute_sql

# Normalize SQL for comparison
query1 = "SELECT * FROM students;"
query2 = "  select   *   from   Students  "
print(normalize_sql(query1) == normalize_sql(query2))  # True

# Check SQL safety
dangerous_query = "DROP TABLE students"
safe_query = "SELECT * FROM students"
print(safe_execute_sql(dangerous_query))  # False
print(safe_execute_sql(safe_query))       # True
```

## 🔍 Testing

MINT package comes with comprehensive test suite:

```bash
# Run all tests
python -m mint.tests.test_comprehensive

# Test specific module
python -m unittest mint.tests.test_comprehensive.TestSQLiteBuilder
```

Test suite includes:
- **40+ test cases** covering all modules
- **Edge cases**: Empty queries, invalid databases, error handling
- **Integration tests**: Complete workflow from database creation to evaluation
- **Performance tests**: Timeout handling, batch processing

## 🏗️ Architecture

```
mint/
├── __init__.py          # Package initialization and exports
├── database.py          # SQLiteBuilder class
├── executor.py          # SQLExecutor class  
├── metrics.py           # EvaluationMetrics and SQLDifficultyClassifier
├── utils.py             # Utility functions
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_comprehensive.py
└── README.md            # Documentation
```

## 📋 API Reference

### SQLiteBuilder

```python
class SQLiteBuilder:
    def __init__(self, output_dir: str = "sqlite_dbs")
    def build_database(self, tables_json_path: str, db_name: Optional[str] = None) -> Dict[str, Any]
    def build_all_databases(self, dataset_root: str = "dataset/ViText2SQL") -> Dict[str, Dict[str, Any]]
    def get_database_info(self, db_path: str) -> Dict[str, Any]
```

### SQLExecutor

```python
class SQLExecutor:
    def __init__(self, db_directory: str = "sqlite_dbs", timeout: int = 30)
    def execute_query(self, query: str, db_name: str) -> Dict[str, Any]
    def execute_and_compare(self, query1: str, query2: str, db_name: str) -> Dict[str, Any]
    def batch_execute(self, queries: List[str], db_name: str) -> List[Dict[str, Any]]
    def batch_compare(self, query_pairs: List[Tuple[str, str]], db_name: str) -> List[Dict[str, Any]]
```

### EvaluationMetrics

```python
class EvaluationMetrics:
    def exact_match_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> float
    def component_wise_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, float]
    def sql_similarity(self, predicted_queries: List[str], gold_queries: List[str]) -> List[float]
    def difficulty_breakdown_accuracy(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, Dict[str, Any]]
    def comprehensive_evaluation(self, predicted_queries: List[str], gold_queries: List[str], execution_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]
```

## 🚨 Error Handling

MINT package handles common errors:

- **File not found**: Graceful handling when dataset or database doesn't exist
- **SQL syntax errors**: Detailed error messages for invalid queries  
- **Timeout errors**: Protection against long-running queries
- **Database connection errors**: Robust connection handling
- **Validation errors**: Input validation with clear error messages

## 🎯 Best Practices

### 1. Database Management
```python
# Create databases once and reuse
builder = SQLiteBuilder(output_dir="sqlite_dbs")
builder.build_all_databases()  # Create all databases

# Reuse executor for multiple evaluations
executor = SQLExecutor(db_directory="sqlite_dbs")
```

### 2. Memory Management
```python
# Use batch processing for large datasets
batch_size = 100
for i in range(0, len(queries), batch_size):
    batch = queries[i:i+batch_size]
    results = executor.batch_execute(batch, db_name)
    # Process results immediately
```

### 3. Error Recovery
```python
# Handle individual query failures
results = []
for pred, gold, db_name in zip(predicted_queries, gold_queries, db_names):
    try:
        result = executor.execute_and_compare(pred, gold, db_name)
        results.append(result)
    except Exception as e:
        print(f"Failed to execute query: {e}")
        # Add default failed result
        results.append({'both_successful': False, 'error': str(e)})
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Submit Pull Request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd Vi_NL2SQL

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -e .

# Run tests
python -m mint.tests.test_comprehensive
```

## 📝 License

This project is released under MIT License. See `LICENSE` file for details.

## 🙏 Acknowledgments

- **ViText2SQL Dataset**: Vietnamese Text-to-SQL dataset
- **SQLite**: Lightweight database engine
- **sqlparse**: SQL parsing library
- **Python unittest**: Testing framework

## 📞 Support

If you encounter issues or have questions:

1. Check existing [Issues](../../issues)
2. Create new issue with appropriate template  
3. Provide complete context and error logs

---

**MINT - Making Text-to-SQL evaluation simple and comprehensive** 🚀 
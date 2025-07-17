# MINT - Vietnamese Text-to-SQL Evaluation Toolkit

A comprehensive toolkit for evaluating Vietnamese Text-to-SQL models, providing database creation, query execution, and detailed evaluation metrics.

## Features

- **SQLite Database Builder**: Automatically create SQLite databases from JSON metadata
- **SQL Query Executor**: Execute SQL queries safely with timeout protection and result comparison
- **Evaluation Metrics**: Exact match, component-wise F1-score, syntax validity, and error analysis
- **Vietnamese Support**: Proper handling of Vietnamese characters and text
- **Batch Processing**: Efficient processing of multiple queries and databases
- **Component Analysis**: Detailed F1-score analysis for SQL clauses (SELECT, FROM, WHERE, GROUP BY, ORDER BY, HAVING, KEYWORDS)

## Installation

```bash
# Activate your virtual environment
source venv/bin/activate

# Required dependencies are already installed:
# pandas, numpy, sqlparse
```

## Quick Start

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

# Your model's predicted queries
predicted_queries = [
    "SELECT COUNT(*) FROM students",
    "SELECT name FROM students WHERE age > 20",
    # ... more predictions
]
```

### 4. Execute and Compare Queries

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

## Evaluation Metrics

### Core Metrics
- **Exact Match**: Perfect string match after normalization
- **Syntax Validity**: Valid SQL syntax using sqlparse
- **Component F1-score**: Set-based analysis of SQL clauses

### Component Analysis
The system provides detailed F1-score analysis for each SQL clause:
- **SELECT**: Column selection accuracy
- **FROM**: Table selection accuracy  
- **WHERE**: Condition accuracy
- **GROUP BY**: Grouping clause accuracy
- **ORDER BY**: Sorting clause accuracy
- **HAVING**: Aggregate condition accuracy
- **KEYWORDS**: SQL keyword usage accuracy

### F1-score Calculation
Component F1-scores are calculated using set-based matching:
- **Precision**: Intersection of predicted and gold components
- **Recall**: Coverage of gold components by predictions
- **F1-score**: Harmonic mean of precision and recall

## Advanced Usage

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

## API Reference

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
    def component_wise_f1_score(self, predicted_queries: List[str], gold_queries: List[str]) -> Dict[str, float]
    def syntax_validity(self, queries: List[str]) -> List[bool]
    def comprehensive_evaluation(self, predicted_queries: List[str], gold_queries: List[str], execution_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]
```

## Error Handling

MINT handles common errors gracefully:

- **File not found**: Clear messages when dataset or database doesn't exist
- **SQL syntax errors**: Detailed error messages for invalid queries  
- **Timeout errors**: Protection against long-running queries
- **Database connection errors**: Robust connection handling
- **Validation errors**: Input validation with clear error messages

## Best Practices

### Database Management
```python
# Create databases once and reuse
builder = SQLiteBuilder(output_dir="sqlite_dbs")
builder.build_all_databases()  # Create all databases

# Reuse executor for multiple evaluations
executor = SQLExecutor(db_directory="sqlite_dbs")
```

### Memory Management
```python
# Use batch processing for large datasets
batch_size = 100
for i in range(0, len(queries), batch_size):
    batch = queries[i:i+batch_size]
    results = executor.batch_execute(batch, db_name)
    # Process results immediately
```

### Error Recovery
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

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m mint.tests.test_comprehensive

# Test specific module
python -m unittest mint.tests.test_comprehensive.TestSQLiteBuilder
```

The test suite includes:
- Database creation and validation
- Query execution and comparison
- Evaluation metrics calculation
- Error handling and edge cases
- Performance and timeout testing

## Project Structure

```
mint/
├── __init__.py          # Package initialization and exports
├── database.py          # SQLiteBuilder class
├── executor.py          # SQLExecutor class  
├── metrics.py           # EvaluationMetrics and component analysis
├── utils.py             # Utility functions
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_comprehensive.py
└── README.md            # This documentation
```

## Troubleshooting

### Common Issues

#### Database Creation Fails
```python
# Check if tables.json exists and is valid
import json
with open("dataset/ViText2SQL/syllable-level/tables.json", 'r') as f:
    tables = json.load(f)
print(f"Loaded {len(tables)} table definitions")
```

#### Query Execution Timeout
```python
# Increase timeout for complex queries
executor = SQLExecutor(db_directory="sqlite_dbs", timeout=60)
```

#### Memory Issues with Large Datasets
```python
# Process in smaller batches
batch_size = 50  # Reduce if needed
for i in range(0, len(queries), batch_size):
    batch = queries[i:i+batch_size]
    results.extend(process_batch(batch))
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -e .

# Run tests
python -m mint.tests.test_comprehensive
```

## License

This project is released under MIT License.

## Support

For issues and questions:
- Check existing documentation
- Review error messages and logs
- Create GitHub issues with complete context
- Provide sample data for reproduction

---

**MINT** - Making Vietnamese Text-to-SQL evaluation comprehensive and accessible. 
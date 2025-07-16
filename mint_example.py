#!/usr/bin/env python3
"""
MINT Package Example Usage
Demonstrates how to use MINT for Text-to-SQL evaluation.
"""

import os
import json
from pathlib import Path

# Import MINT modules
from mint import SQLiteBuilder, SQLExecutor, EvaluationMetrics
from mint.utils import (
    load_dataset, extract_queries_from_dataset, 
    extract_database_names_from_dataset, get_query_statistics
)

def main():
    """Main example function demonstrating MINT usage."""
    
    print("🚀 MINT - Modern Integration for Natural language Text-to-SQL")
    print("=" * 60)
    
    # 1. Setup paths
    dataset_root = "dataset/ViText2SQL"
    output_dir = "sqlite_dbs"
    version = "syllable-level"  # or "word-level"
    
    print(f"\n📂 Setting up paths...")
    print(f"Dataset root: {dataset_root}")
    print(f"SQLite output: {output_dir}")
    print(f"Version: {version}")
    
    # 2. Build SQLite databases
    print(f"\n🏗️  Building SQLite databases...")
    builder = SQLiteBuilder(output_dir=output_dir)
    
    # Build database for specific version
    tables_file = f"{dataset_root}/{version}/tables.json"
    if os.path.exists(tables_file):
        result = builder.build_database(tables_file, version)
        print(f"✅ Created {result['created_tables']}/{result['total_tables']} tables")
        print(f"Database: {result['database_path']}")
        
        if result['failed_tables'] > 0:
            print(f"⚠️  {result['failed_tables']} tables failed:")
            for name in result['failed_table_names'][:3]:  # Show first 3
                print(f"   - {name}")
    else:
        print(f"❌ Tables file not found: {tables_file}")
        return
    
    # 3. Load dataset
    print(f"\n📊 Loading dataset...")
    dev_file = f"{dataset_root}/{version}/dev.json"
    
    if not os.path.exists(dev_file):
        print(f"❌ Dataset file not found: {dev_file}")
        return
    
    dataset = load_dataset(dev_file)
    print(f"✅ Loaded {len(dataset)} samples from dev set")
    
    # Extract information
    gold_queries = extract_queries_from_dataset(dataset, query_key='query')
    db_names = extract_database_names_from_dataset(dataset, db_key='db_id')
    questions = [item.get('question', '') for item in dataset]
    
    # Get query statistics
    stats = get_query_statistics(gold_queries)
    print(f"📈 Query statistics:")
    print(f"   Average length: {stats['avg_length']:.1f} characters")
    print(f"   Unique queries: {stats['unique_queries']}")
    print(f"   Empty queries: {stats['empty_queries']}")
    
    # 4. Simulate model predictions (for demo purposes)
    print(f"\n🤖 Simulating model predictions...")
    
    # For demo, create some "predicted" queries based on gold queries
    # In real usage, these would come from your Text-to-SQL model
    predicted_queries = []
    
    for i, gold_query in enumerate(gold_queries[:10]):  # Demo with first 10 queries
        if i % 3 == 0:
            # Perfect prediction
            predicted_queries.append(gold_query)
        elif i % 3 == 1:
            # Slightly different prediction
            predicted = gold_query.replace('*', 'name').replace('SELECT name', 'SELECT *')
            predicted_queries.append(predicted)
        else:
            # Very different prediction
            predicted_queries.append("SELECT COUNT(*) FROM students")
    
    # Trim to match size
    gold_queries_sample = gold_queries[:len(predicted_queries)]
    db_names_sample = db_names[:len(predicted_queries)]
    questions_sample = questions[:len(predicted_queries)]
    
    print(f"✅ Created {len(predicted_queries)} predicted queries for demo")
    
    # 5. Test database connections
    print(f"\n🔗 Testing database connections...")
    executor = SQLExecutor(db_directory=output_dir, timeout=30)
    
    # Get unique database names to test
    unique_dbs = list(set(db_names_sample))[:3]  # Test first 3 unique DBs
    
    for db_name in unique_dbs:
        test_result = executor.test_database_connection(db_name)
        if test_result['success']:
            print(f"✅ {db_name}: {test_result['table_count']} tables")
        else:
            print(f"❌ {db_name}: {test_result['error']}")
    
    # 6. Execute queries and compare results
    print(f"\n⚡ Executing queries and comparing results...")
    
    comparison_results = []
    successful_executions = 0
    
    for i, (pred, gold, db_name) in enumerate(zip(predicted_queries, gold_queries_sample, db_names_sample)):
        if i < 5:  # Show progress for first 5
            print(f"   Query {i+1}/{len(predicted_queries)}: {db_name}")
        
        try:
            result = executor.execute_and_compare(pred, gold, db_name)
            comparison_results.append(result)
            
            if result and result.get('both_successful'):
                successful_executions += 1
        except Exception as e:
            print(f"   ⚠️  Failed to execute query {i+1}: {e}")
            comparison_results.append({'both_successful': False, 'error': str(e)})
    
    print(f"✅ Completed {len(comparison_results)} query comparisons")
    print(f"📊 Successful executions: {successful_executions}/{len(comparison_results)}")
    
    # 7. Calculate evaluation metrics
    print(f"\n📏 Calculating evaluation metrics...")
    
    metrics = EvaluationMetrics()
    
    # Calculate comprehensive evaluation
    eval_results = metrics.comprehensive_evaluation(
        predicted_queries=predicted_queries,
        gold_queries=gold_queries_sample,
        execution_results=comparison_results
    )
    
    # 8. Display results
    print(f"\n📋 Evaluation Results:")
    print("=" * 40)
    
    summary = metrics.evaluation_summary(eval_results)
    print(summary)
    
    # 9. Detailed analysis
    print(f"\n🔍 Detailed Analysis:")
    print("-" * 40)
    
    # Show some example comparisons
    print("Example Query Comparisons:")
    for i, (pred, gold, result) in enumerate(zip(predicted_queries[:3], gold_queries_sample[:3], comparison_results[:3])):
        print(f"\n{i+1}. Question: {questions_sample[i][:60]}...")
        print(f"   Predicted: {pred}")
        print(f"   Gold:      {gold}")
        print(f"   Match:     {'✅' if pred.strip().lower() == gold.strip().lower() else '❌'}")
        
        if result['both_successful'] and result['comparison']:
            print(f"   Exec Match: {'✅' if result['comparison']['exact_match'] else '❌'}")
    
    # 10. Save results
    print(f"\n💾 Saving results...")
    
    # Save detailed results
    results_file = "mint_evaluation_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'evaluation_metrics': eval_results,
            'sample_size': len(predicted_queries),
            'version': version,
            'successful_executions': successful_executions
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to: {results_file}")
    
    # 11. Performance tips
    print(f"\n💡 Performance Tips:")
    print("- Build databases once and reuse SQLExecutor")
    print("- Use batch processing for large datasets")
    print("- Set appropriate timeout for complex queries")
    print("- Filter valid queries before evaluation")
    
    print(f"\n🎉 MINT evaluation completed successfully!")
    print("=" * 60)

def demo_advanced_features():
    """Demonstrate advanced MINT features."""
    
    print("\n🔬 Advanced Features Demo:")
    print("-" * 30)
    
    # 1. Custom difficulty classification
    from mint.metrics import SQLDifficultyClassifier
    
    classifier = SQLDifficultyClassifier()
    
    test_queries = [
        "SELECT * FROM students",
        "SELECT COUNT(*) FROM students GROUP BY age",
        "SELECT s.name FROM students s JOIN courses c ON s.id = c.student_id",
        "SELECT * FROM students WHERE id IN (SELECT student_id FROM enrollments)"
    ]
    
    print("SQL Difficulty Classification:")
    for query in test_queries:
        difficulty = classifier.classify_query(query)
        print(f"  {difficulty.upper()}: {query}")
    
    # 2. SQL normalization demo
    from mint.utils import normalize_sql, safe_execute_sql
    
    print("\nSQL Normalization:")
    query1 = "SELECT * FROM students;"
    query2 = "  select   *   from   Students  "
    print(f"Query 1: '{query1}'")
    print(f"Query 2: '{query2}'")
    print(f"Normalized equal: {normalize_sql(query1) == normalize_sql(query2)}")
    
    # 3. Safety checking
    print("\nSQL Safety Checking:")
    safe_query = "SELECT * FROM students"
    unsafe_query = "DROP TABLE students"
    print(f"Safe query: {safe_execute_sql(safe_query)}")
    print(f"Unsafe query: {safe_execute_sql(unsafe_query)}")

if __name__ == "__main__":
    try:
        main()
        demo_advanced_features()
    except KeyboardInterrupt:
        print("\n\n⏹️  Execution interrupted by user")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc() 
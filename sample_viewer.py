#!/usr/bin/env python3
"""
ViText2SQL Sample Viewer
========================

A comprehensive tool to load and display detailed information about samples 
from the ViText2SQL dataset including question, SQL query, schema information, 
and structural analysis.

Usage:
    python sample_viewer.py --split train --index 0 --level syllable
    python sample_viewer.py --split test --index 5 --level word
    python sample_viewer.py -s dev -i 10 -l syllable --show-sql-structure
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

def load_dataset(dataset_path: str, split: str) -> List[Dict]:
    """Load the specified split of the dataset."""
    file_path = os.path.join(dataset_path, f"{split}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_tables(dataset_path: str) -> Dict[str, Dict]:
    """Load the tables schema information."""
    tables_path = os.path.join(dataset_path, "tables.json")
    if not os.path.exists(tables_path):
        raise FileNotFoundError(f"Tables file not found: {tables_path}")
    
    with open(tables_path, 'r', encoding='utf-8') as f:
        tables_list = json.load(f)
    
    # Convert list to dict indexed by db_id for faster lookup
    return {table['db_id']: table for table in tables_list}

def get_table_info(db_id: str, tables: Dict[str, Dict]) -> Optional[Dict]:
    """Get table schema information for a specific database."""
    return tables.get(db_id)

def format_columns(column_names: List[List], table_names: List[str]) -> str:
    """Format column information in a readable way."""
    result = []
    for i, (table_idx, col_name) in enumerate(column_names):
        if table_idx == -1:
            continue  # Skip the "*" column
        table_name = table_names[table_idx] if table_idx < len(table_names) else "Unknown"
        result.append(f"  [{i}] {table_name}.{col_name}")
    return "\n".join(result)

def format_tables(table_names: List[str]) -> str:
    """Format table names with indices."""
    result = []
    for i, table_name in enumerate(table_names):
        result.append(f"  [{i}] {table_name}")
    return "\n".join(result)

def analyze_sql_structure(sql_dict: Dict) -> Dict[str, Any]:
    """Analyze SQL structure and extract key components."""
    analysis = {
        'has_select': bool(sql_dict.get('select')),
        'has_where': bool(sql_dict.get('where')),
        'has_groupby': bool(sql_dict.get('groupBy')),
        'has_having': bool(sql_dict.get('having')),
        'has_orderby': bool(sql_dict.get('orderBy')),
        'has_limit': bool(sql_dict.get('limit')),
        'has_union': bool(sql_dict.get('union')),
        'has_intersect': bool(sql_dict.get('intersect')),
        'has_except': bool(sql_dict.get('except')),
        'num_tables': len(sql_dict.get('from', {}).get('table_units', [])),
        'num_conditions': len(sql_dict.get('where', [])),
        'complexity': 'Simple'
    }
    
    # Determine complexity
    complexity_score = 0
    if analysis['has_where']: complexity_score += 1
    if analysis['has_groupby']: complexity_score += 2
    if analysis['has_having']: complexity_score += 2
    if analysis['has_orderby']: complexity_score += 1
    if analysis['num_tables'] > 1: complexity_score += 2
    if analysis['has_union'] or analysis['has_intersect'] or analysis['has_except']: complexity_score += 3
    
    if complexity_score >= 6:
        analysis['complexity'] = 'Extra Hard'
    elif complexity_score >= 4:
        analysis['complexity'] = 'Hard'
    elif complexity_score >= 2:
        analysis['complexity'] = 'Medium'
    else:
        analysis['complexity'] = 'Easy'
    
    return analysis

def display_sample_info(sample: Dict, table_info: Optional[Dict], 
                       index: int, split: str, level: str, show_sql_structure: bool = False):
    """Display comprehensive information about a sample."""
    
    print("=" * 80)
    print(f"📊 ViText2SQL Sample Information")
    print("=" * 80)
    
    # Basic information
    print(f"📍 Sample Index: {index}")
    print(f"📁 Split: {split.upper()}")
    print(f"🔤 Level: {level}")
    print(f"🗄️  Database ID: {sample['db_id']}")
    print()
    
    # Question information
    print("❓ QUESTION INFORMATION")
    print("-" * 40)
    print(f"Vietnamese Question: {sample['question']}")
    print(f"Tokenized Question: {' | '.join(sample['question_toks'])}")
    print(f"Question Length: {len(sample['question_toks'])} tokens")
    print()
    
    # SQL Query information
    print("🗃️  SQL QUERY INFORMATION")
    print("-" * 40)
    print(f"SQL Query: {sample['query']}")
    print(f"Tokenized SQL: {' | '.join(sample['query_toks'])}")
    print(f"SQL Tokens (no values): {' | '.join(sample['query_toks_no_value'])}")
    print(f"SQL Length: {len(sample['query_toks'])} tokens")
    print()
    
    # SQL Structure Analysis
    if show_sql_structure and 'sql' in sample:
        print("🔍 SQL STRUCTURE ANALYSIS")
        print("-" * 40)
        analysis = analyze_sql_structure(sample['sql'])
        print(f"Complexity: {analysis['complexity']}")
        print(f"Number of tables: {analysis['num_tables']}")
        print(f"Number of conditions: {analysis['num_conditions']}")
        print("Components:")
        for component, has_component in analysis.items():
            if component.startswith('has_') and has_component:
                component_name = component[4:].replace('_', ' ').title()
                print(f"  ✓ {component_name}")
        print()
        
        print("🏗️  DETAILED SQL STRUCTURE")
        print("-" * 40)
        print(json.dumps(sample['sql'], indent=2, ensure_ascii=False))
        print()
    
    # Database schema information
    if table_info:
        print("🗂️  DATABASE SCHEMA INFORMATION")
        print("-" * 40)
        print(f"Database: {table_info['db_id']}")
        print(f"Number of tables: {len(table_info['table_names'])}")
        print(f"Number of columns: {len(table_info['column_names']) - 1}")  # -1 for "*"
        print()
        
        print("📋 TABLES:")
        print(format_tables(table_info['table_names']))
        print()
        
        print("📊 COLUMNS:")
        print(format_columns(table_info['column_names'], table_info['table_names']))
        print()
        
        if table_info.get('foreign_keys'):
            print("🔗 FOREIGN KEYS:")
            for fk in table_info['foreign_keys']:
                print(f"  Column {fk[0]} -> Column {fk[1]}")
            print()
        
        if table_info.get('primary_keys'):
            print("🔑 PRIMARY KEYS:")
            for pk in table_info['primary_keys']:
                print(f"  Column {pk}")
            print()
    else:
        print("⚠️  Database schema information not found")
        print()
    
    # Summary statistics
    print("📈 SUMMARY STATISTICS")
    print("-" * 40)
    print(f"Question-SQL token ratio: {len(sample['question_toks'])/len(sample['query_toks']):.2f}")
    if table_info:
        analysis = analyze_sql_structure(sample['sql']) # Re-analyze for summary stats
        print(f"Tables used: {analysis.get('num_tables', 'N/A')} out of {len(table_info['table_names'])}")
    print()
    
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description="Load and display detailed information about ViText2SQL samples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sample_viewer.py --split train --index 0 --level syllable
  python sample_viewer.py -s test -i 5 -l word
  python sample_viewer.py -s dev -i 10 --show-sql-structure
        """
    )
    
    parser.add_argument(
        '-s', '--split',
        choices=['train', 'dev', 'test'],
        required=True,
        help='Dataset split to load from'
    )
    
    parser.add_argument(
        '-i', '--index',
        type=int,
        required=True,
        help='Index of the sample to display (0-based)'
    )
    
    parser.add_argument(
        '-l', '--level',
        choices=['syllable', 'word'],
        default='syllable',
        help='Tokenization level (default: syllable)'
    )
    
    parser.add_argument(
        '--dataset-path',
        default='dataset/ViText2SQL',
        help='Path to the ViText2SQL dataset directory (default: dataset/ViText2SQL)'
    )
    
    parser.add_argument(
        '--show-sql-structure',
        action='store_true',
        help='Show detailed SQL structure analysis'
    )
    
    args = parser.parse_args()
    
    # Construct dataset path
    dataset_path = os.path.join(args.dataset_path, f"{args.level}-level")
    
    try:
        # Load dataset and tables
        print(f"Loading {args.split} dataset from {dataset_path}...")
        dataset = load_dataset(dataset_path, args.split)
        tables = load_tables(dataset_path)
        
        # Validate index
        if args.index < 0 or args.index >= len(dataset):
            print(f"❌ Error: Index {args.index} out of range. Dataset has {len(dataset)} samples (0-{len(dataset)-1})")
            sys.exit(1)
        
        # Get sample and table info
        sample = dataset[args.index]
        table_info = get_table_info(sample['db_id'], tables)
        
        # Display information
        display_sample_info(sample, table_info, args.index, args.split, args.level, args.show_sql_structure)
        
        print(f"✅ Successfully loaded sample {args.index} from {args.split} split ({args.level}-level)")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
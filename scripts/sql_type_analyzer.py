#!/usr/bin/env python3
"""
SQL Type Analyzer and Classifier

Analyzes SQL queries from the training dataset and classifies them into
different types based on their structure and complexity.

SQL Type Categories (in priority order):
1. SET_OP: Contains UNION, INTERSECT, EXCEPT
2. SUBQUERY: Contains subqueries in any form
3. JOIN: Contains JOIN operations (2+ tables)
4. GROUP: Contains GROUP BY
5. AGG: Contains aggregation functions (no JOIN/GROUP/SUBQUERY)
6. ORDER: Contains ORDER BY (no AGG/JOIN/GROUP/SUBQUERY)
7. SELECT_WHERE: Basic SELECT with WHERE
8. SELECT_ONLY: Simple SELECT without WHERE
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, Name


class SQLTypeClassifier:
    """Classifies SQL queries into different types based on structure."""

    def __init__(self):
        self.set_operators = ['UNION', 'INTERSECT', 'EXCEPT']
        self.join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN']
        self.aggregation_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']

    def normalize_sql(self, sql: str) -> str:
        """Normalize SQL query for analysis."""
        if not sql:
            return ""

        # Remove extra whitespace and normalize
        sql = re.sub(r'\s+', ' ', sql.strip())

        # Convert to uppercase for keyword matching
        return sql.upper()

    def has_set_operations(self, sql: str) -> bool:
        """Check if SQL contains set operations."""
        for op in self.set_operators:
            if re.search(rf'\b{op}\b', sql, re.IGNORECASE):
                return True
        return False

    def has_subquery(self, sql: str) -> bool:
        """Check if SQL contains subqueries."""
        # Parse SQL to find nested SELECT statements
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False

            statement = parsed[0]
            return self._find_subquery_in_tokens(statement.tokens)
        except:
            # Fallback to regex if parsing fails
            return self._has_subquery_regex(sql)

    def _find_subquery_in_tokens(self, tokens) -> bool:
        """Recursively find subqueries in parsed tokens."""
        select_count = 0

        for token in tokens:
            if hasattr(token, 'tokens'):
                # Recursive check for nested tokens
                if self._find_subquery_in_tokens(token.tokens):
                    return True

            # Count SELECT keywords
            if token.ttype is Keyword and token.value.upper() == 'SELECT':
                select_count += 1
                if select_count > 1:  # More than one SELECT = subquery
                    return True

            # Check for parenthesized subqueries
            if str(token).strip().startswith('(') and 'SELECT' in str(token).upper():
                return True

        return False

    def _has_subquery_regex(self, sql: str) -> bool:
        """Fallback regex method to detect subqueries."""
        # Look for SELECT inside parentheses
        subquery_pattern = r'\(\s*SELECT\b'
        if re.search(subquery_pattern, sql, re.IGNORECASE):
            return True

        # Count SELECT keywords
        select_count = len(re.findall(r'\bSELECT\b', sql, re.IGNORECASE))
        return select_count > 1

    def has_join(self, sql: str) -> bool:
        """Check if SQL contains JOIN operations."""
        for join_type in self.join_keywords:
            if re.search(rf'\b{join_type}\b', sql, re.IGNORECASE):
                return True

        # Also check for implicit joins (comma-separated tables in FROM)
        # FROM table1, table2 pattern
        from_match = re.search(r'\bFROM\s+([^WHERE^GROUP^ORDER^HAVING^LIMIT^;]+)', sql, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1).strip()
            # Remove subqueries in parentheses before checking
            from_clause = re.sub(r'\([^)]+\)', '', from_clause)
            # Count commas (indicating multiple tables)
            if ',' in from_clause:
                return True

        return False

    def has_group_by(self, sql: str) -> bool:
        """Check if SQL contains GROUP BY."""
        return bool(re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE))

    def has_aggregation(self, sql: str) -> bool:
        """Check if SQL contains aggregation functions."""
        for func in self.aggregation_functions:
            if re.search(rf'\b{func}\s*\(', sql, re.IGNORECASE):
                return True
        return False

    def has_order_by(self, sql: str) -> bool:
        """Check if SQL contains ORDER BY."""
        return bool(re.search(r'\bORDER\s+BY\b', sql, re.IGNORECASE))

    def has_where(self, sql: str) -> bool:
        """Check if SQL contains WHERE clause."""
        return bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))

    def classify_sql(self, sql: str) -> str:
        """
        Classify SQL query into one of the predefined types.

        Classification follows priority order:
        1. SET_OP (highest priority)
        2. SUBQUERY
        3. JOIN
        4. GROUP
        5. AGG
        6. ORDER
        7. SELECT_WHERE
        8. SELECT_ONLY (lowest priority)
        """
        if not sql or not sql.strip():
            return "UNKNOWN"

        sql_normalized = self.normalize_sql(sql)

        # 1. SET_OP: Highest priority
        if self.has_set_operations(sql_normalized):
            return "SET_OP"

        # 2. SUBQUERY
        if self.has_subquery(sql_normalized):
            return "SUBQUERY"

        # 3. JOIN
        if self.has_join(sql_normalized):
            return "JOIN"

        # 4. GROUP
        if self.has_group_by(sql_normalized):
            return "GROUP"

        # 5. AGG (only if no JOIN/GROUP/SUBQUERY)
        if self.has_aggregation(sql_normalized):
            return "AGG"

        # 6. ORDER (only if no AGG/JOIN/GROUP/SUBQUERY)
        if self.has_order_by(sql_normalized):
            return "ORDER"

        # 7. SELECT_WHERE
        if self.has_where(sql_normalized):
            return "SELECT_WHERE"

        # 8. SELECT_ONLY (default)
        return "SELECT_ONLY"


def analyze_training_data(input_path: str, output_path: str, level: str = "std"):
    """
    Analyze training data and add sql_type classification.

    Args:
        input_path: Path to the dataset directory
        output_path: Path to save the enhanced dataset
        level: Level of the dataset (std, syllable, word)
    """
    classifier = SQLTypeClassifier()

    # Construct paths
    input_file = Path(input_path) / f"{level}-level" / "train.json"
    # Output to the same level directory with descriptive name
    output_file = Path(output_path) / f"{level}-level" / "train_with_sql_labels.json"

    if not input_file.exists():
        raise FileNotFoundError(f"Training file not found: {input_file}")

    print(f"📂 Loading training data from: {input_file}")

    # Load training data
    with open(input_file, 'r', encoding='utf-8') as f:
        train_data = json.load(f)

    print(f"📊 Loaded {len(train_data)} training samples")

    # Initialize counters
    type_counts = {
        "SET_OP": 0,
        "SUBQUERY": 0,
        "JOIN": 0,
        "GROUP": 0,
        "AGG": 0,
        "ORDER": 0,
        "SELECT_WHERE": 0,
        "SELECT_ONLY": 0,
        "UNKNOWN": 0
    }

    # Process each sample
    enhanced_data = []

    for i, sample in enumerate(train_data):
        if i % 1000 == 0:
            print(f"🔄 Processing sample {i+1}/{len(train_data)}...")

        # Extract required fields
        enhanced_sample = {
            "db_id": sample.get("db_id", ""),
            "question": sample.get("question", ""),
            "query": sample.get("query", ""),
        }

        # Classify SQL type
        sql_type = classifier.classify_sql(enhanced_sample["query"])
        enhanced_sample["sql_type"] = sql_type

        # Update counters
        type_counts[sql_type] += 1

        enhanced_data.append(enhanced_sample)

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save enhanced dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Enhanced dataset saved to: {output_file}")

    # Print statistics
    print(f"\n📈 SQL Type Distribution:")
    print("=" * 50)
    total_samples = len(enhanced_data)

    for sql_type, count in type_counts.items():
        percentage = (count / total_samples) * 100 if total_samples > 0 else 0
        print(f"{sql_type:12}: {count:5d} samples ({percentage:5.1f}%)")

    print("=" * 50)
    print(f"{'TOTAL':12}: {total_samples:5d} samples (100.0%)")

    return enhanced_data, type_counts


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Analyze SQL queries and classify them by type"
    )
    parser.add_argument(
        '--input',
        default='dataset/ViText2SQL',
        help='Input dataset directory path'
    )
    parser.add_argument(
        '--output',
        default='dataset/ViText2SQL',
        help='Output directory path'
    )
    parser.add_argument(
        '--level',
        choices=['std', 'syllable', 'word'],
        default='std',
        help='Dataset level to process'
    )

    args = parser.parse_args()

    print("🚀 Starting SQL Type Analysis")
    print("=" * 60)
    print(f"📂 Input: {args.input}")
    print(f"📁 Output: {args.output}")
    print(f"🔤 Level: {args.level}")
    print("=" * 60)

    try:
        enhanced_data, type_counts = analyze_training_data(
            args.input,
            args.output,
            args.level
        )

        print("\n🎉 Analysis completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

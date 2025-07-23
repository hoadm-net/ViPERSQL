# ViText2SQL Dataset

The Vietnamese Text-to-SQL dataset used in ViPERSQL for natural language to SQL conversion research.

## Dataset Overview

ViText2SQL is a comprehensive Vietnamese Text-to-SQL dataset designed for evaluating natural language to SQL conversion systems. The dataset provides Vietnamese natural language questions paired with corresponding SQL queries across multiple database schemas.

## Dataset Structure

```
dataset/ViText2SQL/
├── std-level/                      # Standard Vietnamese text (recommended)
│   ├── train.json                  # Training set
│   ├── train_with_sql_labels.json  # Training set with SQL type labels (NEW)
│   ├── dev.json                    # Development/validation set
│   ├── test.json                   # Test set
│   └── tables.json                 # Database schemas
├── syllable-level/                 # Syllable-segmented text
│   ├── train.json
│   ├── dev.json
│   ├── test.json
│   ├── test_gold.sql
│   └── tables.json
└── word-level/                     # Word-segmented text
    ├── train.json
    ├── dev.json
    ├── test.json
    ├── test_gold.sql
    └── tables.json
```

## Data Format

### Standard Question-SQL Pairs
Each data file contains JSON objects with the following structure:
```json
{
  "db_id": "database_identifier",
  "question": "Vietnamese natural language question",
  "query": "Corresponding SQL query"
}
```

### Enhanced Training Data with SQL Labels (NEW)
The `train_with_sql_labels.json` file provides additional SQL type classification:
```json
{
  "db_id": "database_identifier", 
  "question": "Vietnamese natural language question",
  "query": "Corresponding SQL query",
  "sql_type": "JOIN"
}
```

#### SQL Type Categories
The dataset includes 8 SQL type categories based on query complexity and structure:

| SQL Type | Description | Examples | Count | Percentage |
|----------|-------------|----------|-------|------------|
| `SET_OP` | Set operations (UNION, INTERSECT, EXCEPT) | Complex queries combining results | 419 | 6.1% |
| `SUBQUERY` | Contains subqueries in any clause | Nested SELECT statements | 764 | 11.2% |
| `JOIN` | Join operations between 2+ tables | Multi-table relationships | 2,582 | 37.8% |
| `GROUP` | Contains GROUP BY clause | Data aggregation and grouping | 666 | 9.7% |
| `AGG` | Aggregation functions (COUNT, SUM, AVG, MIN, MAX) | Statistical calculations | 774 | 11.3% |
| `ORDER` | Contains ORDER BY clause | Data sorting and ranking | 527 | 7.7% |
| `SELECT_WHERE` | Basic SELECT with WHERE conditions | Filtered data retrieval | 860 | 12.6% |
| `SELECT_ONLY` | Simple SELECT without conditions | Basic data retrieval | 239 | 3.5% |

**Classification Priority**: Types are assigned based on priority order (SET_OP → SUBQUERY → JOIN → GROUP → AGG → ORDER → SELECT_WHERE → SELECT_ONLY), ensuring each query gets the most specific applicable label.

### Database Schemas
The `tables.json` file contains database schema information:
```json
{
  "db_id": "database_identifier",
  "table_names": ["table1", "table2", ...],
  "column_names": [
    [table_index, "column_name"],
    ...
  ],
  "column_types": ["text", "number", ...],
  "foreign_keys": [[column1_index, column2_index], ...],
  "primary_keys": [column_index, ...]
}
```

## Text Granularity Levels

### Standard Level (std-level)
- **Recommended for research**: Standard Vietnamese text without segmentation
- **Natural representation**: Closest to real-world Vietnamese text
- **Usage**: Default level for most experiments

### Syllable Level (syllable-level)
- **Fine-grained segmentation**: Text segmented at syllable boundaries
- **Linguistic analysis**: Useful for detailed Vietnamese text processing studies
- **Specialized applications**: Research on Vietnamese morphology

### Word Level (word-level)
- **Word-based segmentation**: Text segmented at word boundaries
- **Intermediate granularity**: Between standard and syllable levels
- **Comparative studies**: Useful for segmentation impact analysis

## Creating Standard-Level Dataset

The standard-level dataset is the normalized version recommended for most research applications. To generate or verify the standard-level dataset:

### Normalization Process

1. **Text Standardization**
   - Remove excessive whitespace
   - Normalize Vietnamese diacritics (NFC normalization)
   - Standardize punctuation

2. **SQL Standardization**
   - Normalize SQL keywords to lowercase
   - Standardize spacing and formatting
   - Remove unnecessary semicolons

3. **Quality Assurance**
   - Validate SQL syntax
   - Check database schema consistency
   - Ensure question-query alignment

### Conversion Script

Use the provided normalization script:
```bash
python scripts/normalize_to_std.py --input syllable-level --output std-level
```

## Dataset Statistics

- **Total Questions**: ~7,000 Vietnamese questions
- **Database Schemas**: Multiple domains (university, music, architecture, etc.)
- **Query Complexity**: Ranges from simple SELECT to complex JOIN operations
- **Split Distribution**: 
  - Training: ~70%
  - Development: ~15%
  - Test: ~15%

## Usage Guidelines

### For Model Training
- Use `train.json` for model training
- Use `dev.json` for hyperparameter tuning and validation
- Reserve `test.json` for final evaluation

### For Evaluation
- Report results on `test.json` for fair comparison
- Use exact match and component-wise F1 metrics
- Include error analysis for comprehensive evaluation

### Best Practices
- Use std-level for general research unless specific segmentation studies
- Ensure consistent evaluation metrics across experiments
- Report dataset version and preprocessing details

## Data Quality

The dataset has been manually reviewed for:
- **Question clarity**: Natural Vietnamese phrasing
- **SQL correctness**: Syntactically and semantically valid queries
- **Schema consistency**: Proper foreign key relationships
- **Answer completeness**: All questions have corresponding SQL queries

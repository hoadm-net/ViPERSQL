# Data Processing Scripts

This directory contains essential scripts for preprocessing data and creating intermediate files required by different sample selection methods in ViPERSQL.

## Overview

The scripts handle various preprocessing tasks including dataset normalization, SQL type classification, embedding generation, and candidate pool creation for different selection strategies.

## Scripts Description

### 1. `normalize_to_std.py`
**Purpose**: Normalizes the ViText2SQL dataset for ViPERSQL evaluation system

**Function**:
- Converts raw ViText2SQL data to standardized format
- Creates the `std-level/` directory structure
- Ensures consistent data formatting across train/dev/test splits

**Usage**:
```bash
python scripts/normalize_to_std.py
```

**Output**: Normalized files in `dataset/ViText2SQL/std-level/`

### 2. `sql_type_analyzer.py`
**Purpose**: Analyzes and classifies SQL queries into different structural types

**SQL Type Categories** (in priority order):
1. **SET_OP**: Contains UNION, INTERSECT, EXCEPT
2. **SUBQUERY**: Contains subqueries in any form
3. **JOIN**: Contains JOIN operations (2+ tables)
4. **GROUP**: Contains GROUP BY
5. **AGG**: Contains aggregation functions (no JOIN/GROUP/SUBQUERY)
6. **ORDER**: Contains ORDER BY (no AGG/JOIN/GROUP/SUBQUERY)
7. **SELECT_WHERE**: Basic SELECT with WHERE
8. **SELECT_ONLY**: Simple SELECT without WHERE

**Usage**:
```bash
python scripts/sql_type_analyzer.py
```

**Output**: Creates `train_with_sql_labels.json` with SQL type annotations

### 3. `build_dicl_candidates.py`
**Purpose**: Creates candidate pools for DICL and ASTRES selection methods

**Function**:
- Samples ~20 examples from each SQL type from training data
- Generates PhoBERT-base-v2 embeddings for Vietnamese questions
- Creates diverse candidate pool for similarity-based selection

**Requirements**: 
- Must run `sql_type_analyzer.py` first to generate `train_with_sql_labels.json`
- Requires PhoBERT-base-v2 model (automatically downloaded)

**Usage**:
```bash
python scripts/build_dicl_candidates.py
```

**Output**: Creates `dataset/ViText2SQL/std-level/dicl_candidates.json`

**Output Format**:
```json
{
  "db_id": "database_id",
  "question": "Vietnamese question",
  "query": "SQL query", 
  "sql_type": "JOIN",
  "question_embedding": [0.1, 0.2, ...]
}
```

### 4. `skill_knn_preprocessing.py`
**Purpose**: Preprocesses training data for Skill-KNN selection method

**Function**:
- Uses LLM (GPT-4o-mini) to analyze SQL queries and extract skills
- Creates BERT embeddings for extracted skills
- Prepares skill-based similarity matching data

**Requirements**:
- Valid OpenAI API key in configuration
- Internet connection for LLM API calls

**Usage**:
```bash
python scripts/skill_knn_preprocessing.py
```

**Output**: Creates `dataset/ViText2SQL/std-level/skill_knn_train.json`

## Processing Pipeline

For a complete setup, run scripts in this order:

1. **Dataset Normalization**:
   ```bash
   python scripts/normalize_to_std.py
   ```

2. **SQL Type Classification**:
   ```bash
   python scripts/sql_type_analyzer.py
   ```

3. **DICL/ASTRES Candidate Pool** (required for DICL and ASTRES):
   ```bash
   python scripts/build_dicl_candidates.py
   ```

4. **Skill-KNN Preprocessing** (optional, for Skill-KNN method):
   ```bash
   python scripts/skill_knn_preprocessing.py
   ```

## Notes

- All scripts should be run from the project root directory
- Some scripts require external dependencies (PhoBERT, OpenAI API)
- Processing time varies depending on dataset size and available hardware
- GPU acceleration is automatically used when available for embedding generation

## Dependencies

- `torch` and `transformers` for PhoBERT embeddings
- `sqlparse` for SQL parsing and analysis
- `openai` for LLM-based skill extraction (Skill-KNN only)
- Standard Python libraries: `json`, `pathlib`, `argparse`, etc.

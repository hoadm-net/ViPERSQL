# 🔍 Sample Viewer Usage Guide - ViText2SQL

## 📋 Overview

The `sample_viewer.py` tool is a comprehensive utility for exploring the ViText2SQL dataset. It displays detailed information about individual samples including Vietnamese questions, SQL queries, database schema, and structural analysis.

## 🚀 Basic Usage

### 1. View First Sample from Training Set
```bash
python sample_viewer.py -s train -i 0
```

### 2. View Sample with Detailed SQL Analysis
```bash
python sample_viewer.py -s train -i 0 --show-sql-structure
```

### 3. View Sample from Dev Set with Word-level Tokenization
```bash
python sample_viewer.py -s dev -i 5 -l word
```

### 4. View Sample from Test Set
```bash
python sample_viewer.py -s test -i 10
```

## 📝 Command Line Arguments

| Argument | Short | Required | Options | Default | Description |
|----------|-------|----------|---------|---------|-------------|
| `--split` | `-s` | Yes | `train`, `dev`, `test` | - | Dataset split to load |
| `--index` | `-i` | Yes | Integer from 0 | - | Sample index to display |
| `--level` | `-l` | No | `syllable`, `word` | `syllable` | Tokenization level |
| `--dataset-path` | - | No | Path string | `dataset/ViText2SQL` | Dataset directory path |
| `--show-sql-structure` | - | No | - | False | Show detailed SQL structure analysis |

## 🎯 Specific Examples

### Example 1: Basic Sample View
```bash
python sample_viewer.py -s train -i 0
```

**Output includes:**
- Metadata: index, split, level, database ID
- Vietnamese question and tokenization
- SQL query and tokenization variants
- Database schema (tables, columns, keys)
- Summary statistics

### Example 2: Detailed SQL Analysis
```bash
python sample_viewer.py -s train -i 5 --show-sql-structure
```

**Additional information:**
- Complexity assessment (Easy/Medium/Hard/Extra Hard)
- SQL component analysis (SELECT, WHERE, GROUP BY, etc.)
- Detailed JSON structure of parsed SQL

### Example 3: Compare Tokenization Levels
```bash
# View same sample with syllable-level tokenization
python sample_viewer.py -s dev -i 0 -l syllable

# View same sample with word-level tokenization
python sample_viewer.py -s dev -i 0 -l word
```

## 📊 Information Display

### 🔢 Basic Information
- **Sample Index**: Position of sample in dataset
- **Split**: Dataset split (TRAIN/DEV/TEST)
- **Level**: Tokenization level (syllable/word)
- **Database ID**: Name of database used

### ❓ Question Information
- **Vietnamese Question**: Original Vietnamese question
- **Tokenized Question**: Question after tokenization
- **Question Length**: Number of tokens in question

### 🗃️ SQL Query Information
- **SQL Query**: Original SQL query
- **Tokenized SQL**: SQL after tokenization
- **SQL Tokens (no values)**: SQL with values replaced by "value"
- **SQL Length**: Number of tokens in SQL

### 🗂️ Database Schema Information
- **Tables**: List of tables with indices
- **Columns**: List of columns in `table.column` format
- **Foreign Keys**: Foreign key relationships
- **Primary Keys**: Primary key columns

### 🔍 SQL Analysis (with --show-sql-structure)
- **Complexity**: Query complexity level
- **Components**: SQL components present in query
- **Detailed Structure**: Complete JSON structure

## 📈 SQL Complexity Levels

The tool automatically categorizes SQL query complexity:

- **Easy**: Simple SELECT with basic WHERE conditions
- **Medium**: Contains GROUP BY, ORDER BY, or simple operations
- **Hard**: Complex queries with multiple tables or advanced operations
- **Extra Hard**: Nested queries, UNION, INTERSECT, or very complex operations

## 🎯 Use Cases

### 1. Dataset Exploration
```bash
# View different samples to understand structure
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 100
python sample_viewer.py -s train -i 500
```

### 2. Complexity Analysis
```bash
# Find simple samples
python sample_viewer.py -s train -i 1 --show-sql-structure

# Find complex samples
python sample_viewer.py -s train -i 50 --show-sql-structure
```

### 3. Tokenization Comparison
```bash
# Compare syllable vs word level
python sample_viewer.py -s dev -i 0 -l syllable
python sample_viewer.py -s dev -i 0 -l word
```

### 4. Database Schema Investigation
```bash
# View different databases
python sample_viewer.py -s train -i 0  # academic database
python sample_viewer.py -s dev -i 0   # architecture database
```

## 🔧 Troubleshooting

### Index Out of Range Error
```bash
❌ Error: Index 10000 out of range. Dataset has 6831 samples (0-6830)
```
**Solution**: Use index from 0 to (total_samples - 1)

### File Not Found Error
```bash
❌ Error: Dataset file not found: dataset/ViText2SQL/syllable-level/train.json
```
**Solution**: Check dataset path or use `--dataset-path` parameter

### Large Dataset Handling
For quick dataset statistics viewing:
```bash
# View first few samples
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 1
python sample_viewer.py -s train -i 2
```

## 💡 Useful Tips

### 1. Find Samples by Database
To view samples from a specific database, run multiple commands:
```bash
# View different samples to find desired database
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 10
python sample_viewer.py -s train -i 20
```

### 2. Analyze Each Dataset Split
```bash
# Train set (6,831 samples)
python sample_viewer.py -s train -i 0

# Dev set (954 samples) 
python sample_viewer.py -s dev -i 0

# Test set (1,908 samples)
python sample_viewer.py -s test -i 0
```

### 3. Compare Complexity Levels
```bash
# Find Easy samples
python sample_viewer.py -s train -i 5 --show-sql-structure

# Find Hard samples (usually higher indices)
python sample_viewer.py -s train -i 1000 --show-sql-structure
```

## 📚 Dataset Statistics

### Overview
- **Train**: 6,831 samples (70.5%)
- **Dev**: 954 samples (9.8%)
- **Test**: 1,908 samples (19.7%)
- **Total**: 9,693 samples
- **Databases**: 166 unique databases

### Complexity Distribution
- **Easy**: 39.5% - Simple SELECT queries
- **Medium**: 13.5% - Contains GROUP BY, ORDER BY
- **Hard**: 36.5% - Complex JOINs
- **Extra**: 10.5% - Nested queries, UNION

## 🔗 Workflow Integration

### For Research
```bash
# Explore dataset before training models
python sample_viewer.py -s train -i 0 --show-sql-structure

# Analyze validation samples
python sample_viewer.py -s dev -i 0 --show-sql-structure

# Check test samples
python sample_viewer.py -s test -i 0 --show-sql-structure
```

### For Development
```bash
# Debug specific samples
python sample_viewer.py -s train -i 123 --show-sql-structure

# Validate preprocessing pipeline
python sample_viewer.py -s train -i 0 -l syllable
python sample_viewer.py -s train -i 0 -l word
```

## 🎉 Conclusion

The `sample_viewer.py` tool is essential for:
- ✅ Understanding ViText2SQL dataset structure
- ✅ Analyzing specific samples
- ✅ Evaluating query complexity
- ✅ Comparing tokenization levels
- ✅ Debugging and validating data pipelines

Try the examples above to get familiar with the tool and explore the ViText2SQL dataset effectively! 
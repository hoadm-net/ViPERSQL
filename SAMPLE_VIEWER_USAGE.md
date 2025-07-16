# Sample Viewer Usage Guide

A tool for exploring the ViText2SQL dataset with detailed sample information, SQL analysis, and database schema visualization.

## Overview

The `sample_viewer.py` tool displays comprehensive information about individual dataset samples including Vietnamese questions, SQL queries, database schema, and structural analysis.

## Quick Start

### Basic Usage
```bash
# View first training sample
python sample_viewer.py -s train -i 0

# View with detailed SQL analysis
python sample_viewer.py -s train -i 0 --show-sql-structure

# View development set sample with word-level tokenization
python sample_viewer.py -s dev -i 5 -l word
```

## Command Line Arguments

| Argument | Short | Required | Options | Default | Description |
|----------|-------|----------|---------|---------|-------------|
| `--split` | `-s` | Yes | `train`, `dev`, `test` | - | Dataset split to load |
| `--index` | `-i` | Yes | Integer from 0 | - | Sample index to display |
| `--level` | `-l` | No | `syllable`, `word` | `syllable` | Tokenization level |
| `--dataset-path` | - | No | Path string | `dataset/ViText2SQL` | Dataset directory path |
| `--show-sql-structure` | - | No | - | False | Show detailed SQL structure analysis |

## Usage Examples

### Example 1: Basic Sample View
```bash
python sample_viewer.py -s train -i 0
```

**Output includes:**
- Sample metadata: index, split, level, database ID
- Vietnamese question with tokenization details
- SQL query with variants and structure
- Database schema (tables, columns, keys)

### Example 2: Detailed SQL Analysis
```bash
python sample_viewer.py -s train -i 0 --show-sql-structure
```

**Additional output:**
- SQL complexity analysis
- Query component breakdown
- Structure scoring and classification
- Detailed SQL parsing information

### Example 3: Word-level Tokenization
```bash
python sample_viewer.py -s dev -i 10 -l word
```

**Shows:**
- Word-level tokenized Vietnamese question
- Comparison with syllable-level version
- Word-based SQL query variants

### Example 4: Test Set Exploration
```bash
python sample_viewer.py -s test -i 25 --show-sql-structure
```

**Displays:**
- Test sample without gold SQL (if applicable)
- Complete schema information
- Detailed structural analysis

## Common Usage Patterns

### Dataset Exploration
```bash
# Explore different complexity levels
python sample_viewer.py -s train -i 0    # Easy query
python sample_viewer.py -s train -i 100  # Different complexity
python sample_viewer.py -s train -i 200  # Another example

# Compare tokenization levels
python sample_viewer.py -s train -i 0 -l syllable
python sample_viewer.py -s train -i 0 -l word
```

### Development and Testing
```bash
# Check specific problematic samples
python sample_viewer.py -s dev -i 50 --show-sql-structure

# Analyze test samples for model development
python sample_viewer.py -s test -i 75
```

### Schema Understanding
```bash
# View samples from different databases
python sample_viewer.py -s train -i 10   # Database A
python sample_viewer.py -s train -i 50   # Database B
python sample_viewer.py -s train -i 100  # Database C
```

## Output Format

### Basic Information
- **Sample Metadata**: Index, split, tokenization level
- **Database Information**: Database ID and type
- **Question**: Original Vietnamese question
- **SQL Query**: Generated SQL with formatting

### Detailed Analysis (with --show-sql-structure)
- **SQL Components**: SELECT, FROM, WHERE, JOIN analysis
- **Complexity Metrics**: Query difficulty scoring
- **Structure Analysis**: Nested queries, aggregations, etc.

### Schema Information
- **Tables**: Table names and descriptions
- **Columns**: Column names, types, and relationships
- **Keys**: Primary keys and foreign key relationships

## Tips and Best Practices

### Finding Specific Samples
```bash
# Start with sample 0 and increment to explore
python sample_viewer.py -s train -i 0
python sample_viewer.py -s train -i 1
python sample_viewer.py -s train -i 2

# Use structured exploration for different databases
# Training set typically has diverse examples
```

### Understanding SQL Complexity
```bash
# Use --show-sql-structure for learning
python sample_viewer.py -s train -i 50 --show-sql-structure

# Compare simple vs complex queries
python sample_viewer.py -s train -i 0 --show-sql-structure   # Often simpler
python sample_viewer.py -s train -i 500 --show-sql-structure # Often complex
```

### Tokenization Comparison
```bash
# Always compare both levels for complete understanding
python sample_viewer.py -s dev -i 10 -l syllable
python sample_viewer.py -s dev -i 10 -l word
```

## Error Handling

### Common Issues

#### Sample Index Out of Range
```bash
# Error: Index 10000 is out of range
python sample_viewer.py -s train -i 10000
```
**Solution**: Use valid index range (0 to dataset_size-1)

#### Dataset Not Found
```bash
# Error: Dataset file not found
```
**Solution**: Ensure dataset path is correct and files exist

#### Invalid Split
```bash
# Error: Invalid split 'invalid'
```
**Solution**: Use 'train', 'dev', or 'test'

### Troubleshooting
```bash
# Check if dataset exists
ls dataset/ViText2SQL/syllable-level/

# Verify file contents
python -c "import json; print(len(json.load(open('dataset/ViText2SQL/syllable-level/train.json'))))"
```

## Integration with Other Tools

### With Zero-shot NL2SQL System
```bash
# Explore samples that will be processed
python sample_viewer.py -s dev -i 5
python config_nl2sql.py --split dev --samples 1 --start-index 5
```

### With MINT Evaluation
```bash
# View sample structure before evaluation
python sample_viewer.py -s test -i 10 --show-sql-structure
# Then run evaluation with understanding of query complexity
```

## Advanced Usage

### Custom Dataset Path
```bash
# Use custom dataset location
python sample_viewer.py -s train -i 0 --dataset-path /path/to/custom/ViText2SQL
```

### Batch Analysis
```bash
# Analyze multiple samples for patterns
for i in {0..10}; do
    echo "=== Sample $i ==="
    python sample_viewer.py -s train -i $i
    echo ""
done
```

## Output Examples

### Basic Output
```
=== ViText2SQL Sample Information ===
Metadata:
- Index: 0
- Split: train
- Level: syllable
- Database ID: academic

Vietnamese Question:
"hiển thị trang chủ của hội nghị PVLDB"

SQL Query:
SELECT trang_chủ FROM tạp_chí WHERE tên = 'PVLDB'
```

### Detailed Output (with --show-sql-structure)
```
=== SQL Structure Analysis ===
Components:
- SELECT: 1 column
- FROM: 1 table
- WHERE: 1 condition
- Complexity: Simple
- Score: 2.5/10
```

This tool is essential for understanding the dataset structure and developing effective Text-to-SQL models for Vietnamese. 
# ViText2SQL Sample Viewer - Usage Guide

## Overview

The `sample_viewer.py` script is a comprehensive tool for exploring the ViText2SQL dataset. It displays detailed information about individual samples including Vietnamese questions, SQL queries, database schema, and structural analysis.

## Quick Start

```bash
# View the first training sample (syllable-level)
python sample_viewer.py -s train -i 0

# View a test sample with detailed SQL structure analysis
python sample_viewer.py -s test -i 10 --show-sql-structure

# View a development sample using word-level tokenization
python sample_viewer.py -s dev -i 5 -l word
```

## Command Line Arguments

| Argument | Short | Required | Options | Default | Description |
|----------|-------|----------|---------|---------|-------------|
| `--split` | `-s` | Yes | `train`, `dev`, `test` | - | Dataset split to load |
| `--index` | `-i` | Yes | 0-based integer | - | Sample index to display |
| `--level` | `-l` | No | `syllable`, `word` | `syllable` | Tokenization level |
| `--dataset-path` | - | No | Path string | `dataset/ViText2SQL` | Dataset directory path |
| `--show-sql-structure` | - | No | - | False | Show detailed SQL structure analysis |

## Example Outputs

### Basic Sample Information
- Sample metadata (index, split, level, database ID)
- Vietnamese question with tokenization
- SQL query with tokenization variations
- Database schema information (tables, columns, keys)
- Summary statistics

### With SQL Structure Analysis
When using `--show-sql-structure`, you also get:
- Query complexity assessment (Easy/Medium/Hard/Extra Hard)
- SQL components analysis (SELECT, WHERE, GROUP BY, etc.)
- Detailed JSON structure of the parsed SQL

## Sample Complexity Levels

The script automatically categorizes SQL query complexity:

- **Easy**: Simple SELECT with basic WHERE conditions
- **Medium**: Queries with GROUP BY, ORDER BY, or simple operations  
- **Hard**: Complex queries with multiple tables or advanced operations
- **Extra Hard**: Nested queries, UNION, INTERSECT, or very complex operations

## Use Cases

1. **Dataset Exploration**: Understand the structure and content of ViText2SQL
2. **Sample Analysis**: Examine specific samples for research or debugging
3. **Schema Understanding**: Learn about database structures in the dataset
4. **Complexity Assessment**: Evaluate query difficulty for model training
5. **Development**: Validate data loading and preprocessing pipelines

## Tips

- Use different indices to explore various sample types
- Compare syllable vs word-level tokenization differences
- Use `--show-sql-structure` for detailed query analysis
- Examine samples from different splits to understand data distribution 
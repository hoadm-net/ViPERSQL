# ViPERSQL: Vietnamese Text-to-SQL Framework

A comprehensive framework and toolkit for Vietnamese Text-to-SQL conversion, featuring zero-shot generation capabilities and evaluation tools.

## Features

- **Zero-shot NL2SQL**: Generate SQL queries from Vietnamese natural language without training
- **Multiple LLM Support**: OpenAI GPT-4, Claude, and other language models
- **MINT Evaluation Toolkit**: Comprehensive evaluation metrics and database management
- **Sample Viewer**: Interactive dataset exploration tool
- **Vietnamese Language Support**: Optimized for Vietnamese text processing

## Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- OpenAI or Anthropic API keys

### Installation

```bash
# Clone the repository
git clone https://github.com/hoadm-net/ViPERSQL.git
cd ViPERSQL

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install langchain langchain-openai langchain-anthropic python-dotenv sqlparse
pip install pandas numpy matplotlib seaborn plotly jupyter
```

### API Configuration
Copy the example file and add your API keys:
```bash
# Copy the template
cp .env.example .env

# Edit .env with your actual API keys
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic API Key  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

## Usage

### 1. Zero-shot NL2SQL Generation

Generate SQL queries from Vietnamese questions:

```bash
# Quick test with 3 samples
python zeroshot_nl2sql.py

# Evaluate with specific model and dataset
python config_nl2sql.py --model gpt-4o-mini --split dev --samples 10

# Full evaluation
python config_nl2sql.py --model gpt-4o --split test --samples 50
```

### 2. Dataset Exploration

View dataset samples and analyze structure:

```bash
# View training sample
python sample_viewer.py -s train -i 0

# View with detailed SQL analysis
python sample_viewer.py -s train -i 0 --show-sql-structure

# View development set sample
python sample_viewer.py -s dev -i 5 -l word
```

### 3. MINT Evaluation Toolkit

Use the evaluation toolkit for comprehensive analysis:

```python
from mint import SQLiteBuilder, SQLExecutor, EvaluationMetrics

# Build databases
builder = SQLiteBuilder()
builder.build_all_databases("dataset/ViText2SQL")

# Execute and evaluate queries
executor = SQLExecutor()
metrics = EvaluationMetrics()

results = metrics.comprehensive_evaluation(predicted_queries, gold_queries)
print(metrics.evaluation_summary(results))
```

## Available Models

### OpenAI Models
- `gpt-4o` - Latest and most capable
- `gpt-4o-mini` - Faster and cost-effective
- `gpt-4-turbo` - High performance

### Anthropic Models
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and efficient

## Dataset Structure

```
dataset/ViText2SQL/
├── syllable-level/
│   ├── train.json         # Training data
│   ├── dev.json           # Development data
│   ├── test.json          # Test questions
│   ├── test_gold.sql      # Test gold SQL queries
│   └── tables.json        # Database schema metadata
└── word-level/
    ├── train.json         # Training data
    ├── dev.json           # Development data
    ├── test.json          # Test questions
    ├── test_gold.sql      # Test gold SQL queries
    └── tables.json        # Database schema metadata
```

## Tools and Components

### Zero-shot NL2SQL System
- **Vietnamese language optimization**: Specialized prompts for Vietnamese
- **Schema-aware generation**: Uses complete database schema information
- **Multiple model support**: Works with OpenAI and Anthropic models
- **Comprehensive logging**: Tracks all requests, responses, and evaluations

### MINT Evaluation Toolkit
- **Database creation**: Generate SQLite databases from metadata
- **Query execution**: Safe SQL execution with timeout protection
- **Evaluation metrics**: Exact match, execution accuracy, component analysis
- **Error analysis**: Detailed error categorization and debugging

### Sample Viewer
- **Interactive exploration**: Browse dataset samples with detailed information
- **SQL structure analysis**: Analyze query complexity and components
- **Schema visualization**: View database structure and relationships
- **Tokenization support**: Both syllable-level and word-level views

## Command Examples

```bash
# Basic NL2SQL generation
python zeroshot_nl2sql.py

# Model comparison
python config_nl2sql.py --model gpt-4o --samples 20
python config_nl2sql.py --model claude-3-sonnet-20240229 --samples 20

# Dataset exploration
python sample_viewer.py -s train -i 100
python sample_viewer.py -s test -i 50 --show-sql-structure

# Different tokenization levels
python config_nl2sql.py --level syllable --samples 10
python config_nl2sql.py --level word --samples 10
```

## Output and Results

### Console Output
Real-time progress and evaluation results:
```
🔄 Running evaluation on dev split with 10 samples
📊 Model: gpt-4o-mini
✅ Loaded 10 samples from dev split
📝 Processing 1/10: architecture
✅ Exact match!
```

### Structured Logs
Detailed logs saved to `logs/nl2sql_logs.json`:
- Request tracking with unique IDs
- LLM response monitoring
- SQL execution results
- Error analysis

### Evaluation Results
Results saved to `results/` directory with:
- Configuration details
- Summary metrics
- Detailed per-sample results
- Component-wise accuracy

## Documentation

- **Setup Guide**: See `ZEROSHOT_NL2SQL_GUIDE.md` for detailed setup and usage
- **MINT Toolkit**: See `mint/README.md` for evaluation toolkit documentation
- **Sample Viewer**: See `SAMPLE_VIEWER_USAGE.md` for dataset exploration guide

## Project Structure

```
ViPERSQL/
├── dataset/               # ViText2SQL dataset
├── sqlite_dbs/           # Generated SQLite databases
├── mint/                 # MINT evaluation toolkit
├── logs/                 # System logs
├── results/              # Evaluation results
├── zeroshot_nl2sql.py    # Main NL2SQL system
├── config_nl2sql.py      # Configuration and batch runner
├── sample_viewer.py      # Dataset exploration tool
├── mint_example.py       # MINT usage examples
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review example usage

---

**ViPERSQL** - Vietnamese Text-to-SQL made simple and effective.
# ViPERSQL: Vietnamese Text-to-SQL Framework

A unified framework for Vietnamese Text-to-SQL conversion supporting multiple strategies: Zero-shot, Few-shot, and Chain-of-Thought (CoT).

> **Note**: This framework is optimized for **syllable-level tokenization** which works best with Large Language Models for Vietnamese text processing. Word-level tokenization is also supported but syllable-level is the default and recommended approach.

## 🚀 Features

- **Multiple Strategies**: Zero-shot, Few-shot, and CoT approaches
- **Unified CLI**: Single command-line tool for all operations
- **Configuration Management**: Environment-based configuration with .env support
- **Multiple LLM Support**: OpenAI GPT-4, Claude, and other language models
- **MINT Evaluation Toolkit**: Comprehensive evaluation metrics and database management
- **Template System**: Flexible prompt template management for each strategy
- **Vietnamese Language Support**: Optimized for Vietnamese text processing
- **Component-wise F1-score**: Detailed analysis of SQL clause accuracy
- **Chain-of-Thought Reasoning**: Step-by-step reasoning for complex queries
- **Batch Processing**: Efficient processing of multiple queries
- **Comprehensive Logging**: Detailed logging and error tracking

## 🏗️ Architecture

```
vipersql.py (Unified CLI)
    ├── Strategy Manager
    │   ├── Zero-shot Strategy
    │   ├── Few-shot Strategy (Random k examples)
    │   └── CoT Strategy (Step-by-step reasoning)
    └── MINT Core
        ├── Configuration Manager
        ├── LLM Interface
        ├── Template Manager
        ├── Evaluation Engine
        └── Unified Logger
```

## 📋 Quick Start

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
```

### Configuration

1. **Copy configuration template:**
```bash
cp config.env .env
```

2. **Edit .env with your API keys:**
```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-key

# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key

# Optional: Customize other settings
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_STRATEGY=zero-shot
DEFAULT_SAMPLES=10
```

## 🎯 Usage

### Basic Commands

```bash
# List available strategies
python vipersql.py --list-strategies

# Zero-shot evaluation (default)
python vipersql.py --samples 10

# Few-shot with examples  
python vipersql.py --strategy few-shot --samples 20

# Chain-of-Thought reasoning
python vipersql.py --strategy cot --samples 5


```

### Advanced Usage

```bash
# Different models
python vipersql.py --model gpt-4o --samples 50
python vipersql.py --model claude-3-sonnet-20240229 --samples 20

# Different datasets (syllable-level is default)
python vipersql.py --split train --samples 100
python vipersql.py --split test --samples -1  # All samples
python vipersql.py --split dev --level word --samples 50  # Use word-level if needed

# Custom configuration
python vipersql.py --config custom.env --strategy few-shot

# Custom template
python vipersql.py --template templates/custom_template.txt
```

## 🔧 Configuration Options

All configuration can be set via environment variables or .env files:

### API & Model Settings
```bash
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.1
DEFAULT_MAX_TOKENS=2000
```

### Strategy Settings
```bash
DEFAULT_STRATEGY=zero-shot
FEW_SHOT_EXAMPLES=3
COT_REASONING_STEPS=true
```

### Dataset Settings
```bash
DATASET_PATH=dataset/ViText2SQL
DEFAULT_SPLIT=dev
DEFAULT_LEVEL=syllable
DEFAULT_SAMPLES=10
```

### Output Settings
```bash
RESULTS_DIR=results
LOGS_DIR=logs
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
```

## 📊 Available Strategies

### 1. Zero-shot Strategy
Direct conversion without examples, relying on LLM's pre-trained knowledge.

```bash
python vipersql.py --strategy zero-shot --samples 10
```

**Template**: `templates/vietnamese_nl2sql.txt`

### 2. Few-shot Strategy  
Uses k examples from training set to guide the conversion process.

```bash
python vipersql.py --strategy few-shot --samples 10
```

**Features:**
- Random selection of k examples (default: k=3)
- Framework for future selection strategies
- Automatic loading from training dataset
- Template-based example formatting

**Template**: `templates/few_shot_vietnamese_nl2sql.txt`

### 3. Chain-of-Thought (CoT) Strategy
Step-by-step reasoning approach for complex queries.

```bash
python vipersql.py --strategy cot --samples 10
```

**Features:**
- Step-by-step reasoning before SQL generation
- Automatic extraction of reasoning and SQL from response
- Support for SQL code blocks in markdown format
- Optional integration with few-shot examples

**Template**: `templates/cot_vietnamese_nl2sql.txt`



## 🎨 Template System

### Template Structure
Templates use LangChain format with variables:

```
You are an expert in converting Vietnamese natural language questions to SQL queries.

Database Schema:
Tables: {tables}
Columns: {columns}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Vietnamese Question: {question}

SQL Query:
```

### Template Variables
- `{tables}`: Comma-separated table names
- `{columns}`: Comma-separated column names
- `{foreign_keys}`: Foreign key relationships
- `{primary_keys}`: Primary key columns
- `{question}`: Vietnamese natural language question
- `{examples}`: Few-shot examples (for few-shot, CoT)

### Custom Templates
Create custom templates and use them:

```bash
python vipersql.py --template my_custom_template.txt --strategy zero-shot
```

## 📈 Evaluation System

### Evaluation Metrics
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

### Results Structure
Results are saved to `results/` directory with comprehensive evaluation data:

```json
{
  "config": {
    "strategy": "zero-shot",
    "model": "gpt-4o-mini",
    "split": "dev",
    "num_samples": 10
  },
  "summary": {
    "exact_match_accuracy": 0.0,
    "syntax_validity": 100.0,
    "component_f1_scores": {
      "SELECT": 0.0,
      "FROM": 0.0,
      "WHERE": 0.0,
      "GROUP BY": 0.0,
      "ORDER BY": 0.0,
      "HAVING": 0.0,
      "KEYWORDS": 100.0
    }
  },
  "detailed_results": [...]
}
```

### Logging System
Comprehensive logging to `logs/vipersql_logs.json` with request tracking, strategy execution, and performance metrics.

## 🛠️ Development

### Adding New Strategies

1. **Create strategy class:**
```python
# mint/strategies/my_strategy.py
from .base import BaseStrategy, StrategyResult

class MyStrategy(BaseStrategy):
    def _get_strategy_name(self) -> str:
        return "my-strategy"
    
    def generate_sql(self, question, schema_info, db_id, examples=None):
        # Implementation here
        pass
```

2. **Add to strategy manager:**
```python
# mint/strategies/__init__.py
from .my_strategy import MyStrategy
```

3. **Create template:**
```
# templates/my_strategy_template.txt
Your custom prompt template here...
```

### Adding New Example Selection Strategies

For few-shot strategy, implement new selection methods:

```python
def _select_similarity_based_examples(self, question: str, k: int) -> List[Dict]:
    # Implement similarity-based selection
    pass

def _select_difficulty_based_examples(self, question: str, k: int) -> List[Dict]:
    # Implement difficulty-based selection
    pass
```

### Using as Library

```python
from mint import create_strategy, ViPERConfig

# Create configuration
config = ViPERConfig(
    strategy="zero-shot",
    model_name="gpt-4o-mini",
    samples=10
)

# Create strategy instance
strategy = create_strategy("zero-shot", **config.to_dict())

# Generate SQL
result = strategy.generate_sql(
    question="Có bao nhiêu học sinh?",
    schema_info=schema_info,
    db_id="school"
)

print(f"Generated SQL: {result.sql_query}")
```

## 📚 Documentation

- **Setup Guide**: Detailed installation and configuration
- **Strategy Guide**: In-depth explanation of each strategy
- **Template Guide**: How to create and customize templates
- **API Reference**: Complete API documentation for library usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new strategies
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check documentation in `docs/` folder
- Review example usage in README

---

**ViPERSQL v2** - Vietnamese Text-to-SQL made unified and extensible.
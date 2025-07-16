# Zero-shot NL2SQL System Setup Guide

A comprehensive guide for setting up and using the Zero-shot Natural Language to SQL generation system for Vietnamese text.

## Features

- **Multiple LLM Support**: OpenAI GPT-4, GPT-4o, Anthropic Claude models
- **Comprehensive Logging**: Full request/response tracking with structured JSON logs
- **Detailed Evaluation**: Exact match, execution accuracy, component analysis
- **Vietnamese Language Support**: Optimized for Vietnamese NL2SQL tasks
- **Schema-aware Generation**: Utilizes complete database schema information

## Prerequisites

1. **Python Environment**: Python 3.8+ with virtual environment
2. **API Keys**: OpenAI and/or Anthropic API keys
3. **Dataset**: ViText2SQL dataset with SQLite databases

## Setup

### 1. Environment Setup
```bash
# Virtual environment is already created
source venv/bin/activate

# Required packages are already installed:
# langchain, langchain-openai, langchain-anthropic, python-dotenv, sqlparse
```

### 2. API Key Configuration
Create/edit the `.env` file with your API keys:
```bash
# OpenAI API Key (for GPT models)
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic API Key (for Claude models)  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional: LangChain tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langchain-key-here
```

### 3. Available Models
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- **Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

## Usage

### Quick Start
```bash
# Test with 3 samples using GPT-4o-mini (default)
python zeroshot_nl2sql.py

# Run evaluation with specific model
python config_nl2sql.py --model gpt-4o-mini --split dev --samples 10
```

### Command Line Options

#### Basic Evaluation
```bash
# Evaluate specific number of samples
python config_nl2sql.py --model gpt-4o --split dev --samples 20

# Evaluate test set with Claude
python config_nl2sql.py --model claude-3-haiku-20240307 --split test --samples 50

# Full evaluation (all samples)
python config_nl2sql.py --model gpt-4o-mini --split train --samples -1
```

#### Tokenization Levels
```bash
# Syllable-level tokenization (default)
python config_nl2sql.py --level syllable --samples 20

# Word-level tokenization
python config_nl2sql.py --level word --samples 20
```

#### Custom Dataset Path
```bash
python config_nl2sql.py --dataset-path /path/to/your/ViText2SQL --samples 10
```

## Output and Logging

### Console Output
The system provides real-time feedback:
```
🔄 Running evaluation on dev split with 10 samples
📊 Model: gpt-4o-mini
📁 Dataset: dataset/ViText2SQL/syllable-level
============================================================
✅ Loaded 10 samples from dev split

📝 Processing 1/10: architecture
✅ Exact match!

📝 Processing 2/10: academic  
🟡 Execution accurate but different syntax
```

### Structured Logs
All operations are logged to `logs/nl2sql_logs.json`:
```json
{
  "request_id": "req_1234567890",
  "timestamp": "2024-01-15T10:30:45",
  "type": "REQUEST",
  "question": "Có tất cả bao nhiêu kiến trúc sư nữ?",
  "db_id": "architecture"
}
```

### Results Files
Evaluation results are saved to `results/` directory:
```json
{
  "config": {
    "model": "gpt-4o-mini",
    "split": "dev", 
    "level": "syllable",
    "num_samples": 10
  },
  "summary": {
    "exact_match_accuracy": 85.0,
    "execution_accuracy": 92.0,
    "syntax_validity": 98.0
  },
  "detailed_results": [...]
}
```

## Evaluation Metrics

### Primary Metrics
- **Exact Match**: Perfect string match after normalization
- **Execution Accuracy**: Same query results as gold standard
- **Syntax Validity**: Valid SQL syntax using sqlparse

### Component Analysis
- **SELECT accuracy**: Correct column selection
- **FROM accuracy**: Correct table selection
- **WHERE accuracy**: Correct filtering conditions
- **JOIN accuracy**: Correct table relationships
- **GROUP BY/ORDER BY accuracy**: Correct aggregation/sorting

### Error Analysis
- **Missing keywords**: Required SQL components not generated
- **Extra keywords**: Unnecessary SQL components added
- **Structural differences**: Major query structure changes
- **Length differences**: Token count variations

## System Components

### Core Classes

#### `VietnameseNL2SQL` Class
- LLM Integration for OpenAI and Anthropic models
- Vietnamese-optimized prompt engineering
- Schema formatting for LLM consumption
- SQL response cleaning and formatting

#### `NL2SQLLogger` Class  
- Request tracking with unique IDs
- LLM response monitoring (times, tokens, performance)
- SQL execution result logging
- Comprehensive error tracking

#### `NL2SQLEvaluator` Class
- Multi-metric evaluation system
- Component-wise SQL analysis
- Error categorization and analysis
- Performance and resource tracking

## Usage Examples

### Example 1: Architecture Database
```
Vietnamese Question: "Có tất cả bao nhiêu kiến trúc sư nữ?"
Generated SQL: "SELECT COUNT(*) FROM kiến_trúc_sư WHERE giới_tính = 'female'"
Gold SQL: "SELECT COUNT(*) FROM kiến_trúc_sư WHERE giới_tính = 'female'"
Result: ✅ Exact Match
```

### Example 2: Academic Database
```
Vietnamese Question: "hiển thị trang chủ của hội nghị PVLDB"
Generated SQL: "SELECT trang_chủ FROM tạp_chí WHERE tên = 'PVLDB'"
Gold SQL: "SELECT trang_chủ FROM tạp_chí WHERE tên = 'PVLDB'"
Result: ✅ Exact Match
```

## Troubleshooting

### Common Issues

#### API Key Errors
```bash
❌ Error: No API keys found in environment!
```
**Solution**: Set API keys in `.env` file

#### Dataset Not Found
```bash
❌ Dataset not found: dataset/ViText2SQL/syllable-level/dev.json
```
**Solution**: Ensure dataset is properly loaded and paths are correct

#### Database Connection Issues
```bash
❌ Database execution error: no such table
```
**Solution**: Check if SQLite databases exist in `sqlite_dbs/` directory

#### Model Not Supported
```bash
❌ Unsupported model: custom-model
```
**Solution**: Use supported OpenAI or Anthropic models

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python config_nl2sql.py --samples 1
```

## Best Practices

### Model Selection
- **GPT-4o**: Best accuracy, higher cost
- **GPT-4o-mini**: Good balance of accuracy and cost
- **Claude-3-Haiku**: Fast responses, lower cost
- **Claude-3-Sonnet**: Better reasoning, moderate cost

### Evaluation Strategy
```bash
# Start with small samples for quick testing
python config_nl2sql.py --samples 5

# Increase gradually for comprehensive evaluation  
python config_nl2sql.py --samples 50

# Full evaluation for final results
python config_nl2sql.py --samples -1
```

### Performance Optimization

#### Batch Processing
Process multiple samples efficiently with proper API rate limiting

#### Caching
Schema information is cached to reduce processing time

#### Memory Management
Use appropriate batch sizes for large evaluations

## Advanced Configuration

### Custom Prompt Engineering
The system uses optimized prompts for Vietnamese NL2SQL:

```
You are an expert in converting Vietnamese natural language questions to SQL queries.

Database Schema:
Tables: {tables}
Columns: {columns} 
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Important Guidelines:
1. Generate ONLY the SQL query without explanation
2. Use exact table and column names from schema
3. Handle Vietnamese text carefully
4. Use proper SQL syntax and formatting
5. Consider table relationships for JOINs

Vietnamese Question: {question}

SQL Query:
```

### Error Recovery
The system handles various error conditions gracefully:
- API timeouts and rate limits
- Invalid SQL syntax
- Database connection issues
- Model response errors

## Next Steps

1. **Start Small**: Begin with 5-10 samples to test setup
2. **Model Comparison**: Try different models to find the best fit
3. **Analyze Results**: Review logs and results for improvement opportunities
4. **Scale Up**: Gradually increase sample sizes for comprehensive evaluation
5. **Optimize**: Refine prompts and parameters based on results

## Support

For issues and questions:
- Check existing documentation
- Review console output and logs
- Create GitHub issues with error details
- Provide complete context for troubleshooting 
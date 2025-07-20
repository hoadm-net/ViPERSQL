# ViPERSQL: Vietnamese Text-to-SQL System

A comprehensive toolkit for Vietnamese Natural Language to SQL conversion with advanced prompting strategies and enhanced evaluation metrics.

## Overview

ViPERSQL provides a unified framework for Vietnamese Text-to-SQL conversion, supporting multiple prompting strategies and comprehensive evaluation. The system is designed for research and practical applications in Vietnamese database query generation using large language models.

## Key Features

- **Multiple Strategies**: Zero-shot, Few-shot, and Chain-of-Thought (CoT) prompting
- **Enhanced Evaluation**: Component-wise F1 scores, exact match accuracy, error analysis
- **Multi-LLM Support**: OpenAI GPT models and Anthropic Claude
- **Vietnamese Text Processing**: Support for std, syllable, and word-level granularity
- **Comprehensive Metrics**: Detailed performance analysis with precision and recall

## Architecture

```
ViPERSQL/
├── vipersql.py             # Main CLI interface
├── mint/                   # Core framework
│   ├── strategies/         # Prompting strategies
│   ├── enhanced_metrics.py # Evaluation metrics
│   ├── evaluator.py        # Unified evaluator
│   ├── llm_interface.py    # LLM abstraction
│   └── config.py          # System configuration
├── dataset/ViText2SQL/     # Vietnamese Text-to-SQL dataset
├── templates/              # Prompt templates
└── results/                # Evaluation outputs
```

## Quick Start

### Installation

```bash
git clone <repository-url>
cd ViPERSQL
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Usage

```bash
# Few-shot strategy with GPT-4o-mini
python vipersql.py --strategy few-shot --model gpt-4o-mini --samples 10

# Zero-shot with Claude
python vipersql.py --strategy zero-shot --model claude-3-5-sonnet-20241022 --samples 20

# Chain-of-Thought reasoning
python vipersql.py --strategy cot --samples 5
```

### Command Options

- `--strategy`: Prompting strategy (zero-shot, few-shot, cot)
- `--model`: LLM model name
- `--level`: Text granularity (std, syllable, word)
- `--split`: Dataset split (train, dev, test)
- `--samples`: Number of samples to process

## Output

The system generates:
- **Predictions**: SQL queries with metadata (`predictions.json`)
- **Evaluation metrics**: Detailed performance analysis (`eval_results_*.json`)
- **Reports**: Human-readable evaluation summaries (`eval_report_*.txt`)

## Research Applications

ViPERSQL is designed for:
- Vietnamese NL2SQL model evaluation and comparison
- Prompting strategy research and development
- Cross-lingual Text-to-SQL studies
- LLM performance analysis on structured query generation

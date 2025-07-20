# ViPERSQL: Vietnamese Text-to-SQL System

A comprehensive toolkit for Vietnamese Natural Language to SQL conversion with advanced prompting strategies, intelligent example selection, and enhanced evaluation metrics.

## Overview

ViPERSQL provides a unified framework for Vietnamese Text-to-SQL conversion, supporting multiple prompting strategies with intelligent example selection and comprehensive evaluation. The system is designed for research and practical applications in Vietnamese database query generation using large language models.

## Key Features

- **Multiple Strategies**: Zero-shot, Few-shot, and Chain-of-Thought (CoT) prompting
- **Intelligent Example Selection**: 
  - Random selection (baseline)
  - **Skill-KNN**: Similarity-based selection using SQL skills analysis
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
│   ├── skill_knn_selector.py # Intelligent example selection
│   ├── enhanced_metrics.py # Evaluation metrics
│   ├── evaluator.py        # Unified evaluator
│   ├── llm_interface.py    # LLM abstraction
│   └── config.py          # System configuration
├── dataset/ViText2SQL/     # Vietnamese Text-to-SQL dataset
├── templates/              # Prompt templates
├── scripts/                # Preprocessing utilities
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
# Few-shot strategy with random example selection (baseline)
python vipersql.py --strategy few-shot --model gpt-4o-mini --samples 10

# Few-shot strategy with Skill-KNN intelligent selection
python vipersql.py --strategy few-shot --example-selection-strategy skill_knn --samples 10

# Zero-shot with Claude
python vipersql.py --strategy zero-shot --model claude-3-5-sonnet-20241022 --samples 20

# Chain-of-Thought reasoning
python vipersql.py --strategy cot --samples 5
```

### Command Options

- `--strategy`: Prompting strategy (zero-shot, few-shot, cot)
- `--example-selection-strategy`: Example selection method (random, skill_knn) - for few-shot only
- `--model`: LLM model name
- `--level`: Text granularity (std, syllable, word)
- `--split`: Dataset split (train, dev, test)
- `--samples`: Number of samples to process

## Skill-KNN Example Selection

ViPERSQL introduces an intelligent example selection method for few-shot learning:

### How it works:
1. **Preprocessing**: Extract SQL skills from training data using LLM analysis of question + SQL pairs
2. **Skill Embedding**: Create embeddings using google-bert/bert-base-uncased
3. **Runtime Selection**: For each test question, predict required skills and find most similar training examples

### Setup Skill-KNN:
```bash
# First, preprocess training data (run once)
python scripts/skill_knn_preprocessing.py --num_samples 50  # for testing
python scripts/skill_knn_preprocessing.py                  # for full dataset

# Then use skill_knn selection
python vipersql.py --strategy few-shot --example-selection-strategy skill_knn --samples 10
```

### Benefits:
- **Smarter selection**: Choose examples with similar SQL complexity and patterns
- **Better context**: Provide more relevant examples to guide LLM reasoning
- **Improved accuracy**: Potentially better performance than random selection

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

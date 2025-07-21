# ViPERSQL - Vietnamese Text-to-SQL System

A comprehensive Vietnamese Text-to-SQL system that converts natural language questions in Vietnamese to SQL queries using Large Language Models (LLMs).

## 🚀 Features

- **Multiple Strategies**: Zero-shot, Few-shot, and Chain-of-Thought approaches
- **Advanced Example Selection**: Random and Skill-based KNN selection for few-shot learning
- **Multi-level Vietnamese Support**: Standard, syllable, and word-level text segmentation
- **Comprehensive Evaluation**: Enhanced metrics with component-wise analysis
- **Multiple LLM Support**: OpenAI GPT and Anthropic Claude models
- **Modular Architecture**: Clean, extensible codebase with strategy pattern

## 📁 Project Structure

```
ViPERSQL/
├── mint/                     # Core system package
│   ├── strategies/          # SQL generation strategies
│   │   ├── zero_shot.py    # Zero-shot strategy
│   │   ├── few_shot.py     # Few-shot strategy
│   │   └── cot.py          # Chain-of-thought strategy
│   ├── selectors/          # Example selection strategies
│   │   ├── random_selector.py     # Random selection
│   │   └── skill_knn_selector.py  # Skill-based KNN selection
│   ├── config.py           # Configuration management
│   ├── llm_interface.py    # LLM provider interface
│   ├── evaluator.py        # Evaluation engine
│   └── utils.py            # Utility functions
├── dataset/                 # Vietnamese Text-to-SQL dataset
│   └── ViText2SQL/
│       ├── std-level/       # Standard Vietnamese
│       ├── syllable-level/  # Syllable-segmented
│       └── word-level/      # Word-segmented
├── templates/               # Prompt templates
├── scripts/                 # Utility scripts
├── results/                 # Evaluation results
└── vipersql.py             # Main entry point
```

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/ViPERSQL.git
cd ViPERSQL
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 🎯 Usage

### Basic Usage

```bash
# Zero-shot generation
python vipersql.py --strategy zero-shot --samples 10

# Few-shot with random selection
python vipersql.py --strategy few-shot --example-selection-strategy random --samples 10

# Few-shot with skill-based selection
python vipersql.py --strategy few-shot --example-selection-strategy skill_knn --samples 10

# Chain-of-thought reasoning
python vipersql.py --strategy cot --samples 10
```

### Advanced Options

```bash
# Different text segmentation levels
python vipersql.py --level syllable --samples 10
python vipersql.py --level word --samples 10

# Different dataset splits
python vipersql.py --split dev --samples 10
python vipersql.py --split test --samples 10

# Different models
python vipersql.py --model gpt-4-turbo --samples 10
python vipersql.py --model claude-3-sonnet --samples 10
```

## 🧠 Strategies

### 1. Zero-shot
Direct translation from Vietnamese question to SQL without examples.

### 2. Few-shot
Uses training examples to guide SQL generation with two selection strategies:

#### Random Selection
- Randomly selects k examples from training data
- Fast and simple baseline approach

#### Skill-based KNN Selection
- Extracts SQL skills from questions using LLM
- Uses BERT embeddings for skill similarity
- Selects examples with highest skill similarity

### 3. Chain-of-Thought (CoT)
Step-by-step reasoning approach that breaks down the problem.

## 📊 Evaluation

The system provides comprehensive evaluation with:

- **Exact Match Accuracy**: Perfect SQL query matches
- **Component-wise F1 Scores**: SELECT, FROM, WHERE, GROUP BY, etc.
- **Enhanced Metrics**: Detailed precision and recall analysis
- **Error Analysis**: Categorized error types and patterns

## 🔧 Configuration

Key configuration options in `.env`:

```env
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Model Settings
DEFAULT_MODEL=gpt-4-turbo
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=1000

# Strategy Settings
DEFAULT_STRATEGY=zero-shot
FEW_SHOT_EXAMPLES=3
EXAMPLE_SELECTION_STRATEGY=random
```

## 🏗 Architecture

The system follows a clean, modular architecture:

- **Strategy Pattern**: Different SQL generation approaches
- **Selector Pattern**: Pluggable example selection methods
- **Template System**: Flexible prompt engineering
- **Unified LLM Interface**: Support for multiple providers
- **Comprehensive Evaluation**: Detailed metrics and analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📚 Citation

If you use this work in your research, please cite:

```bibtex
@article{vipersql2025,
  title={ViPERSQL: Vietnamese Text-to-SQL with Advanced Example Selection},
  author={Your Name},
  year={2025}
}
```

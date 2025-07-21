# ViPERSQL - Vietnamese Text-to-SQL System

A comprehensive Vietnamese Text-to-SQL system that converts natural language questions in Vietnamese to SQL queries using Large Language Models (LLMs) with multiple advanced strategies and enhanced evaluation metrics.

## 🚀 Features

### Core Capabilities
- **Multiple Strategies**: Zero-shot, Few-shot, and Chain-of-Thought (CoT) approaches
- **Advanced Example Selection**: Random, Skill-based KNN, and DICL (Domain-Independent Context Learning) selection for few-shot learning
- **Multi-level Vietnamese Support**: Standard, syllable, and word-level text segmentation
- **Enhanced Evaluation**: Component-wise F1 scores with precision/recall analysis
- **Multiple LLM Support**: OpenAI GPT and Anthropic Claude models
- **Unified CLI Interface**: Single entry point for all operations

### Advanced Features
- **Template Management**: Flexible prompt engineering system
- **Intermediate Results**: Automatic saving during long runs
- **Comprehensive Reports**: Detailed evaluation with error analysis
- **Modular Architecture**: Clean, extensible codebase with strategy pattern
- **Configuration Management**: Environment-based configuration with overrides

## 📁 Project Structure

```
ViPERSQL/
├── mint/                           # Core system package
│   ├── strategies/                 # SQL generation strategies
│   │   ├── zero_shot.py           # Zero-shot strategy
│   │   ├── few_shot.py            # Few-shot strategy
│   │   └── cot.py                 # Chain-of-thought strategy
│   ├── selectors/                 # Example selection strategies
│   │   ├── random_selector.py     # Random selection
│   │   ├── skill_knn_selector.py  # Skill-based KNN selection
│   │   └── dicl_selector.py       # DICL selection
│   ├── config.py                  # Configuration management
│   ├── llm_interface.py           # Unified LLM provider interface
│   ├── template_manager.py        # Prompt template system
│   ├── evaluator.py               # Enhanced evaluation engine
│   ├── enhanced_metrics.py        # Advanced metrics calculation
│   └── utils.py                   # Utility functions
├── dataset/                       # Vietnamese Text-to-SQL dataset
│   └── ViText2SQL/
│       ├── std-level/             # Standard Vietnamese
│       ├── syllable-level/        # Syllable-segmented
│       └── word-level/            # Word-segmented
├── templates/                     # Prompt templates
│   ├── vietnamese_nl2sql.txt      # Zero-shot template
│   ├── few_shot_vietnamese_nl2sql.txt  # Few-shot template
│   ├── cot_vietnamese_nl2sql.txt  # Chain-of-thought template
│   └── skill_extraction_vietnamese.txt # Skill extraction template
├── scripts/                       # Utility scripts
│   ├── skill_knn_preprocessing.py # Skill extraction preprocessing
│   ├── build_dicl_candidates.py   # DICL candidate building
│   └── sql_type_analyzer.py       # SQL complexity analysis
├── results/                       # Evaluation results
└── vipersql.py                    # Main CLI entry point
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

### Quick Start

```bash
# Zero-shot generation (default)
python vipersql.py --samples 10

# Few-shot with random selection
python vipersql.py --strategy few-shot --samples 10

# Few-shot with skill-based selection  
python vipersql.py --strategy few-shot --example-selection-strategy skill_knn --samples 10

# Chain-of-thought reasoning
python vipersql.py --strategy cot --samples 10
```

### Advanced Usage

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

# DICL example selection
python vipersql.py --strategy few-shot --example-selection-strategy dicl --samples 10
```

## 🧠 Strategies

### 1. Zero-shot
Direct translation from Vietnamese question to SQL without examples using carefully crafted prompts.

**Key Features:**
- Optimized Vietnamese prompts
- Schema-aware generation
- Robust error handling

### 2. Few-shot
Uses training examples to guide SQL generation with multiple selection strategies:

#### Random Selection
- Randomly selects k examples from training data
- Fast and simple baseline approach
- Consistent performance across different domains

#### Skill-based KNN Selection
- Extracts SQL skills from questions using LLM
- Uses BERT embeddings for skill similarity matching
- Selects examples with highest skill relevance
- Improved performance on complex queries

#### DICL (Domain-Independent Context Learning) Selection
- **Advanced Cross-Domain Learning**: Selects examples that demonstrate transferable reasoning patterns across different database domains
- **Contextual Similarity Matching**: Uses semantic understanding to find examples with similar logical structures regardless of domain
- **Enhanced Generalization**: Improves model performance on unseen domains by learning domain-agnostic SQL patterns
- **Intelligent Candidate Building**: Pre-processes training data to identify high-quality cross-domain examples
- **Robust Performance**: Maintains consistency across diverse database schemas and question types

### 3. Chain-of-Thought (CoT)
Step-by-step reasoning approach that breaks down complex problems:

**Process:**
1. Question understanding and decomposition
2. Schema analysis and table identification
3. Step-by-step SQL construction
4. Final query synthesis

## 📊 Enhanced Evaluation

The system provides comprehensive evaluation metrics:

### Core Metrics
- **Exact Match Accuracy**: Perfect SQL query matches
- **Component-wise F1 Scores**: SELECT, FROM, WHERE, GROUP BY, ORDER BY, etc.
- **Precision & Recall**: Detailed component analysis

### Advanced Analysis
- **Error Categorization**: Systematic error pattern analysis
- **Complexity-based Evaluation**: Performance across different SQL complexity levels
- **Cross-domain Analysis**: Evaluation across different database domains

### Report Generation
- **JSON Reports**: Machine-readable detailed results
- **Text Summaries**: Human-readable evaluation summaries
- **Intermediate Saves**: Progress tracking during long evaluations

## 🔧 Configuration

### Environment Variables (.env)

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

# Evaluation Settings
BATCH_SIZE=10
SAVE_INTERMEDIATE=true
```

### Runtime Configuration
All environment settings can be overridden via command-line arguments:

```bash
python vipersql.py --model claude-3-sonnet --strategy cot --samples 20
```

## 🏗 Architecture

### Design Principles
- **Strategy Pattern**: Pluggable SQL generation strategies
- **Factory Pattern**: Dynamic strategy and selector creation
- **Template System**: Flexible prompt engineering
- **Unified Interface**: Consistent API across all components
- **Comprehensive Logging**: Detailed execution tracking

### Core Components

#### Configuration Management
- Environment-based configuration with validation
- Runtime parameter override capabilities
- Type-safe configuration handling

#### LLM Interface
- Unified interface for multiple LLM providers
- Automatic retry and error handling
- Token usage tracking and optimization

#### Template System
- Jinja2-based template rendering
- Modular prompt components
- Multi-language template support

#### Enhanced Evaluation
- Component-wise SQL analysis
- Statistical significance testing
- Comprehensive error categorization

## 📈 Performance Optimization

### Efficient Processing
- Sequential processing with intermediate saves
- Memory-optimized batch handling
- Automatic error recovery

### Scalability Features
- Configurable batch sizes
- Intermediate result caching
- Progress tracking and resumption

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:

- Code style and standards
- Testing requirements
- Documentation expectations
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

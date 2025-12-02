# ViPERSQL

**Vietnamese/English Text-to-SQL System with ViR2 Example Selection Method**

A research system for converting natural language questions to SQL queries, featuring **ViR2** - a novel two-stage example selection method combining semantic retrieval with syntactic matching and diversity optimization.

---

## 🎯 Overview

ViPERSQL addresses the challenge of selecting optimal few-shot examples for Text-to-SQL tasks through:

- **ViR2 Method**: Two-stage selection (PhoBERT retrieval → POS-based re-ranking with diversity)
- **Multi-Language Support**: Vietnamese (PhoBERT + underthesea) and English (BERT + spaCy)
- **Enhanced Evaluation**: Component-wise F1 metrics beyond Exact Match
- **Modular Architecture**: Extensible framework with multiple strategies and selectors

**Key Innovation:**

$$\text{Score}(E, q) = \text{POS\_Score}(E, q) + \lambda \cdot \text{Diversity}(E)$$

where $\lambda = 0.3$ balances syntactic similarity and example diversity.

---

## 📚 Documentation

### Core Concepts

- **[Architecture](docs/ARCHITECTURE.md)** - System design and module organization
- **[ViR2 Method](docs/VIR2_METHOD.md)** - Two-stage selection algorithm
- **[Strategies](docs/STRATEGIES.md)** - Zero-shot, Few-shot, Chain-of-Thought
- **[Selectors](docs/SELECTORS.md)** - Random, DICL, ASTRES, Skill-KNN, ViR2
- **[Evaluation](docs/EVALUATION_METRICS.md)** - Component-wise metrics and analysis

### Usage Guides

- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration](docs/CONFIGURATION.md)** - All parameters and settings
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Common scenarios
- **[Multi-Language](docs/MULTILANG_SUPPORT.md)** - Vietnamese and English support

### Advanced

- **[Ablation Studies](docs/ABLATION_EXPERIMENTS.md)** - Testing ViR2 components
- **[Extending System](docs/EXTENDING_SYSTEM.md)** - Add new strategies/selectors
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation

---

## ⚡ Quick Start

### Installation

```bash
git clone https://github.com/hoadm-net/ViPERSQL.git
cd ViPERSQL
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### Basic Usage

```bash
# Zero-shot (baseline)
python vipersql.py --samples 10

# Few-shot with ViR2 (recommended)
python vipersql.py --strategy few-shot --example-selection-strategy vir2 --samples 10

# Chain-of-thought reasoning
python vipersql.py --strategy cot --samples 10
```

See **[Usage Examples](docs/USAGE_EXAMPLES.md)** for more scenarios.

---

## 🏗️ System Architecture

```
Input Question
      ↓
┌─────────────┐
│  Strategy   │  Zero-shot / Few-shot / CoT
└─────┬───────┘
      ↓
┌─────────────┐
│  Selector   │  Random / DICL / ASTRES / Skill-KNN / ViR2
└─────┬───────┘  (if Few-shot)
      ↓
┌─────────────┐
│ LLM Interface│  OpenAI GPT / Anthropic Claude
└─────┬───────┘
      ↓
┌─────────────┐
│  Evaluator  │  Component F1 + Error Analysis
└─────┬───────┘
      ↓
  SQL Query + Metrics
```

See **[Architecture](docs/ARCHITECTURE.md)** for details.

---

## 🎓 Research Contributions

1. **ViR2 Method**: Novel two-stage example selection combining semantic + syntactic + diversity
2. **Multi-Language Framework**: Unified architecture for Vietnamese and English
3. **Enhanced Metrics**: Component-wise evaluation beyond Exact Match
4. **Ablation Framework**: Systematic testing of individual components

---

## 📊 Supported Methods

| Method | Type | Speed | Complexity | Notes |
|--------|------|-------|------------|-------|
| Zero-shot | Baseline | ⚡⚡⚡ | Low | No training examples |
| Random | Few-shot | ⚡⚡⚡ | Low | Random selection baseline |
| DICL | Few-shot | ⚡⚡ | Medium | Semantic similarity only |
| ASTRES | Few-shot | ⚡ | High | AST-based structural matching |
| Skill-KNN | Few-shot | ⚡⚡ | Medium | SQL skill extraction + matching |
| **ViR2** | Few-shot | ⚡⚡ | Medium | **Two-stage: Semantic + POS + Diversity** |
| CoT | Reasoning | ⚡ | High | Step-by-step reasoning |

---

## 📁 Project Structure

```
ViPERSQL/
├── vipersql.py              # Main CLI entry point
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── VIR2_METHOD.md
│   ├── STRATEGIES.md
│   └── ...
├── mint/                   # Core package
│   ├── core/              # Evaluator, LLM, Templates
│   ├── strategies/        # Zero-shot, Few-shot, CoT
│   ├── selectors/         # Random, DICL, ASTRES, ViR2
│   ├── metrics/           # Enhanced metrics
│   └── utils/             # Utilities
├── dataset/               # ViText2SQL dataset
├── templates/             # Prompt templates
├── scripts/               # Preprocessing scripts
└── results/               # Evaluation outputs
```

---

## 🛠️ Configuration

All settings configurable via `.env` or command-line:

```bash
# Model selection
--model gpt-4o              # or claude-3-5-sonnet-20241022

# Strategy selection  
--strategy few-shot         # or zero-shot, cot

# Selector for few-shot
--example-selection-strategy vir2  # or random, dicl, astres, skill_knn

# ViR2 parameters
--vir2-candidate-pool-size 50      # Stage 1 pool size (M)
--vir2-beam-size 5                 # Beam search width (B)
--vir2-diversity-weight 0.3        # Diversity weight (λ)

# Dataset options
--level std                 # or syllable, word
--split dev                 # or test
--samples 100               # Number of samples
```

See **[Configuration Guide](docs/CONFIGURATION.md)** for all options.

---

## 🔬 Example: Running ViR2

```bash
# Basic ViR2 with default parameters (M=50, B=5, λ=0.3)
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 100

# Custom ViR2 parameters
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --vir2-diversity-weight 0.5 \
  --samples 100

# Ablation: ViR2 without POS matching
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-pos \
  --samples 100
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

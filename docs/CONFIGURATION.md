# Configuration Guide

## Overview

ViPERSQL configuration can be set via 3 methods (priority high → low):

1. **Command-line arguments** (highest priority)
2. **Environment variables** (.env file)
3. **Default values** (in code)

---

## Configuration Sources

### 1. Command-Line Arguments

Override mọi settings khác.

```bash
python vipersql.py \
  --model gpt-4o \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 100 \
  --temperature 0.5
```

### 2. Environment Variables (.env)

```env
# .env file
DEFAULT_MODEL=gpt-4o
DEFAULT_STRATEGY=few-shot
EXAMPLE_SELECTION_STRATEGY=vir2
DEFAULT_TEMPERATURE=0.3
```

### 3. Default Values

Defined in `mint/constants.py` - used when no override present.

---

## Complete Parameter Reference

### API Keys

| Parameter | Environment Variable | Required | Description |
|-----------|---------------------|----------|-------------|
| N/A | `OPENAI_API_KEY` | ✅ (if using OpenAI) | OpenAI API key |
| N/A | `ANTHROPIC_API_KEY` | ✅ (if using Anthropic) | Anthropic API key |
| N/A | `LANGCHAIN_API_KEY` | ❌ | LangChain tracing (optional) |
| N/A | `LANGCHAIN_TRACING_V2` | ❌ | Enable tracing (true/false) |

### Model Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Model | `--model` | `DEFAULT_MODEL` | `gpt-4o` | LLM model name |
| Temperature | `--temperature` | `DEFAULT_TEMPERATURE` | `0.3` | Sampling temperature (0-1) |
| Max tokens | `--max-tokens` | `DEFAULT_MAX_TOKENS` | `1000` | Maximum response tokens |
| Timeout | `--timeout` | `DEFAULT_TIMEOUT` | `60` | API timeout (seconds) |

**Available Models:**
- `gpt-4o` - OpenAI GPT-4 Optimized
- `gpt-4o-mini` - OpenAI GPT-4 Mini (cheaper)
- `claude-3-5-sonnet-20241022` - Anthropic Claude 3.5 Sonnet

### Strategy Settings

| Parameter | CLI | Environment | Default | Values |
|-----------|-----|-------------|---------|--------|
| Strategy | `--strategy` | `DEFAULT_STRATEGY` | `zero-shot` | `zero-shot`, `few-shot`, `cot` |
| Template dir | `--template-dir` | `DEFAULT_TEMPLATE_DIR` | `templates` | Path to templates |

### Few-shot Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Selector | `--example-selection-strategy` | `EXAMPLE_SELECTION_STRATEGY` | `random` | Selection method |
| Examples (k) | `--few-shot-examples` | `FEW_SHOT_EXAMPLES` | `3` | Number of examples |

**Available Selectors:**
- `random` - Random selection
- `dicl` - Semantic similarity (DICL)
- `astres` - AST-based matching
- `skill_knn` - Skill-based KNN
- `vir2` - Two-stage ViR2 (recommended)
- `vir2-no-pos` - ViR2 without POS matching
- `vir2-no-diversity` - ViR2 without diversity
- `vir2-no-beam-search` - ViR2 without beam search
- `multilang-vir2` - Multi-language ViR2

### ViR2 Settings

| Parameter | CLI | Environment | Default | Range | Description |
|-----------|-----|-------------|---------|-------|-------------|
| Pool size (M) | `--vir2-candidate-pool-size` | `VIR2_CANDIDATE_POOL_SIZE` | `50` | [10, 200] | Stage 1 candidates |
| Beam size (B) | `--vir2-beam-size` | `VIR2_BEAM_SIZE` | `5` | [1, 20] | Beam search width |
| Diversity (λ) | `--vir2-diversity-weight` | `VIR2_DIVERSITY_WEIGHT` | `0.3` | [0, 1] | Diversity weight |

### CoT Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Reasoning steps | `--cot-reasoning-steps` | `COT_REASONING_STEPS` | `true` | Enable step-by-step |

### Dataset Settings

| Parameter | CLI | Environment | Default | Values |
|-----------|-----|-------------|---------|--------|
| Path | `--dataset-path` | `DATASET_PATH` | `dataset/ViText2SQL` | Dataset directory |
| Split | `--split` | `DEFAULT_SPLIT` | `dev` | `dev`, `test` |
| Level | `--level` | `DEFAULT_LEVEL` | `std` | `std`, `syllable`, `word` |
| Samples | `--samples` | `DEFAULT_SAMPLES` | `None` (all) | Number to process |

### Multi-Language Settings

| Parameter | CLI | Environment | Default | Values |
|-----------|-----|-------------|---------|--------|
| Language | `--language` | `LANGUAGE` | `auto` | `auto`, `vi`, `en` |
| Cross-lingual | `--cross-lingual` | `CROSS_LINGUAL` | `false` | Enable cross-lingual |

### Output Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Results dir | `--results-dir` | `RESULTS_DIR` | `results` | Output directory |

### Evaluation Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Execution accuracy | N/A | `ENABLE_EXECUTION_ACCURACY` | `true` | Enable EX metric |
| Component analysis | N/A | `ENABLE_COMPONENT_ANALYSIS` | `true` | Enable F1 metrics |
| Error analysis | N/A | `ENABLE_ERROR_ANALYSIS` | `true` | Enable error analysis |
| Eval timeout | N/A | `EVALUATION_TIMEOUT` | `60` | Timeout (seconds) |

### Logging Settings

| Parameter | CLI | Environment | Default | Values |
|-----------|-----|-------------|---------|--------|
| Log level | N/A | `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| Log format | N/A | `LOG_FORMAT` | Standard | Log format string |

### Performance Settings

| Parameter | CLI | Environment | Default | Description |
|-----------|-----|-------------|---------|-------------|
| Batch size | N/A | `BATCH_SIZE` | `10` | Processing batch size |
| Max concurrent | N/A | `MAX_CONCURRENT_REQUESTS` | `5` | Concurrent API calls |
| Retry attempts | N/A | `RETRY_ATTEMPTS` | `3` | API retry count |
| Retry delay | N/A | `RETRY_DELAY` | `5` | Retry delay (seconds) |

---

## Configuration Examples

### Example 1: .env File

```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Settings
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=1000

# Strategy
DEFAULT_STRATEGY=few-shot
EXAMPLE_SELECTION_STRATEGY=vir2
FEW_SHOT_EXAMPLES=3

# ViR2 Parameters
VIR2_CANDIDATE_POOL_SIZE=50
VIR2_BEAM_SIZE=5
VIR2_DIVERSITY_WEIGHT=0.3

# Dataset
DATASET_PATH=dataset/ViText2SQL
DEFAULT_SPLIT=dev
DEFAULT_LEVEL=std

# Output
RESULTS_DIR=results

# Logging
LOG_LEVEL=INFO
```

### Example 2: Command-Line Override

```bash
# Override .env settings via CLI
python vipersql.py \
  --model claude-3-5-sonnet-20241022 \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 5 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --vir2-diversity-weight 0.5 \
  --level syllable \
  --split test \
  --samples 200 \
  --temperature 0.5
```

### Example 3: Multiple Configurations

**Production (.env.prod):**
```env
DEFAULT_MODEL=gpt-4o
DEFAULT_STRATEGY=few-shot
EXAMPLE_SELECTION_STRATEGY=vir2
FEW_SHOT_EXAMPLES=5
LOG_LEVEL=WARNING
```

**Development (.env.dev):**
```env
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_STRATEGY=zero-shot
LOG_LEVEL=DEBUG
```

**Usage:**
```bash
# Production
cp .env.prod .env
python vipersql.py --samples 1000

# Development
cp .env.dev .env
python vipersql.py --samples 10
```

---

## Configuration Scenarios

### Scenario 1: Quick Test

**Goal:** Fast feedback, low cost

```bash
python vipersql.py \
  --model gpt-4o-mini \
  --strategy zero-shot \
  --samples 10
```

### Scenario 2: Best Accuracy

**Goal:** Highest quality predictions

```bash
python vipersql.py \
  --model gpt-4o \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 5 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --samples 1000
```

### Scenario 3: Budget-Conscious

**Goal:** Balance cost and accuracy

```bash
python vipersql.py \
  --model gpt-4o-mini \
  --strategy few-shot \
  --example-selection-strategy dicl \
  --few-shot-examples 3 \
  --samples 1000
```

### Scenario 4: Interpretable

**Goal:** Understand model reasoning

```bash
python vipersql.py \
  --model claude-3-5-sonnet-20241022 \
  --strategy cot \
  --temperature 0.5 \
  --max-tokens 2000 \
  --samples 100
```

### Scenario 5: Multi-Language

**Goal:** Process Vietnamese and English

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language auto \
  --samples 500
```

### Scenario 6: Ablation Study

**Goal:** Test ViR2 components

```bash
# Full ViR2
python vipersql.py --example-selection-strategy vir2 --samples 100

# Without POS
python vipersql.py --example-selection-strategy vir2-no-pos --samples 100

# Without diversity
python vipersql.py --example-selection-strategy vir2-no-diversity --samples 100

# Without beam search
python vipersql.py --example-selection-strategy vir2-no-beam-search --samples 100
```

---

## Tuning Guidelines

### Temperature

**Low (0.1-0.3):**
- ✅ Deterministic outputs
- ✅ SQL generation (structured task)
- ❌ Creative tasks

**Medium (0.4-0.6):**
- ✅ Chain-of-thought reasoning
- ✅ Balanced exploration
- ⚠️ May vary slightly

**High (0.7-1.0):**
- ✅ Creative text generation
- ❌ SQL generation (too random)

**Recommendation:** 0.3 for SQL, 0.5 for CoT

### Max Tokens

**Low (500-1000):**
- ✅ Zero-shot, Few-shot
- ✅ Simple queries
- ❌ Complex queries, CoT

**Medium (1000-2000):**
- ✅ Most use cases
- ✅ Chain-of-thought
- ⚠️ May truncate long reasoning

**High (2000+):**
- ✅ Complex CoT
- ✅ Multiple nested queries
- ⚠️ Higher cost

**Recommendation:** 1000 for normal, 2000 for CoT

### ViR2 Hyperparameters

**Candidate Pool Size (M):**
- **Small (10-30):** Fast, may miss good examples
- **Medium (50-100):** Balanced (recommended)
- **Large (100-200):** Better coverage, slower

**Beam Size (B):**
- **Small (1-3):** Fast, greedy selection
- **Medium (5-10):** Good optimization (recommended)
- **Large (10-20):** Better optimization, diminishing returns

**Diversity Weight (λ):**
- **Low (0-0.2):** Prefer similar structure
- **Medium (0.3-0.5):** Balanced (recommended)
- **High (0.6-1.0):** Prefer diverse examples

---

## Environment Variable Template

Copy this to `.env`:

```env
# ============================================================
# ViPERSQL Configuration
# ============================================================

# ------------------------------------------------------------
# API Keys (Required)
# ------------------------------------------------------------
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Optional: LangChain Tracing
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false

# ------------------------------------------------------------
# Model Settings
# ------------------------------------------------------------
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=1000
DEFAULT_TIMEOUT=60

# ------------------------------------------------------------
# Strategy Settings
# ------------------------------------------------------------
DEFAULT_STRATEGY=few-shot
DEFAULT_TEMPLATE_DIR=templates

# ------------------------------------------------------------
# Few-shot Settings
# ------------------------------------------------------------
EXAMPLE_SELECTION_STRATEGY=vir2
FEW_SHOT_EXAMPLES=3

# ------------------------------------------------------------
# ViR2 Settings
# ------------------------------------------------------------
VIR2_CANDIDATE_POOL_SIZE=50
VIR2_BEAM_SIZE=5
VIR2_DIVERSITY_WEIGHT=0.3

# ------------------------------------------------------------
# CoT Settings
# ------------------------------------------------------------
COT_REASONING_STEPS=true

# ------------------------------------------------------------
# Dataset Settings
# ------------------------------------------------------------
DATASET_PATH=dataset/ViText2SQL
DEFAULT_SPLIT=dev
DEFAULT_LEVEL=std
DEFAULT_SAMPLES=

# ------------------------------------------------------------
# Multi-Language Settings
# ------------------------------------------------------------
LANGUAGE=auto
CROSS_LINGUAL=false

# ------------------------------------------------------------
# Output Settings
# ------------------------------------------------------------
RESULTS_DIR=results

# ------------------------------------------------------------
# Evaluation Settings
# ------------------------------------------------------------
ENABLE_EXECUTION_ACCURACY=true
ENABLE_COMPONENT_ANALYSIS=true
ENABLE_ERROR_ANALYSIS=true
EVALUATION_TIMEOUT=60

# ------------------------------------------------------------
# Logging Settings
# ------------------------------------------------------------
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# ------------------------------------------------------------
# Performance Settings
# ------------------------------------------------------------
BATCH_SIZE=10
MAX_CONCURRENT_REQUESTS=5
RETRY_ATTEMPTS=3
RETRY_DELAY=5
```

---

## Validation

### Check Configuration

```bash
# Dry run to see loaded config (if supported)
python vipersql.py --samples 0 --dry-run

# Or check programmatically
python -c "from mint.config import ViPERConfig; print(ViPERConfig())"
```

### Common Issues

**Issue: API key not loaded**
```bash
# Check .env exists
ls -la .env

# Verify syntax
cat .env | grep API_KEY
```

**Issue: Parameter not taking effect**
- Check priority: CLI > ENV > Default
- Verify environment variable name matches
- Restart if .env changed

---

## Related Documentation

- **[Quick Start](QUICKSTART.md)** - Get started quickly
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world scenarios
- **[ViR2 Method](VIR2_METHOD.md)** - ViR2 hyperparameters explained
- **[Strategies](STRATEGIES.md)** - Strategy-specific settings

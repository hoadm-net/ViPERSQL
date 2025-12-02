# Quick Start Guide

## Get Started in 5 Minutes

### Prerequisites

- Python 3.8+
- pip
- API key (OpenAI or Anthropic)

---

## Step 1: Clone & Install

```bash
# Clone repository
git clone https://github.com/hoadm-net/ViPERSQL.git
cd ViPERSQL

# Install dependencies
pip install -r requirements.txt

# Install spaCy models (for POS tagging)
python -m spacy download en_core_web_sm
```

---

## Step 2: Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add API keys
nano .env
```

**Minimum configuration in .env:**

```env
# Choose one (or both)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Choose default model
DEFAULT_MODEL=gpt-4o
```

---

## Step 3: Run First Evaluation

### Option A: Zero-shot (Simplest)

```bash
python vipersql.py --samples 10
```

**Expected output:**
```
🚀 ViPERSQL - Vietnamese Text-to-SQL System
Strategy: ZERO-SHOT
Model: gpt-4o
Samples: 10

Processing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✅ Evaluation Complete!
Exact Match: 70.0%
Avg F1: 82.5%

Results saved to: results/zero-shot_10_20251201_103045/
```

### Option B: Few-shot with ViR2 (Recommended)

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 10
```

**Expected output:**
```
🚀 ViPERSQL - Vietnamese Text-to-SQL System
Strategy: FEW-SHOT
Selector: ViR2 (Two-Stage)
Model: gpt-4o
Samples: 10

[ViR2] Loading meaning pool... ✓
[ViR2] Loaded 1000 training examples

Processing sample 1/10...
[ViR2] Stage 1: Retrieved 50 candidates
[ViR2] Stage 2: Selected 3 examples
Generated SQL: SELECT...

...

✅ Evaluation Complete!
Exact Match: 85.0%
Avg F1: 91.2%

Results saved to: results/few-shot-vir2_10_20251201_103112/
```

---

## Step 4: View Results

```bash
cd results/few-shot-vir2_10_20251201_103112/

# View human-readable report
cat eval_report.txt

# View detailed metrics (JSON)
cat eval_results.json

# View all predictions
cat predictions.json
```

---

## Common Use Cases

### 1. Quick Test (10 samples)

```bash
python vipersql.py --samples 10
```

### 2. Full Evaluation (100+ samples)

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 100
```

### 3. Different Models

```bash
# OpenAI GPT-4o
python vipersql.py --model gpt-4o --samples 10

# OpenAI GPT-4o-mini (cheaper)
python vipersql.py --model gpt-4o-mini --samples 10

# Anthropic Claude
python vipersql.py --model claude-3-5-sonnet-20241022 --samples 10
```

### 4. Different Dataset Levels

```bash
# Standard level (default)
python vipersql.py --level std --samples 10

# Syllable level
python vipersql.py --level syllable --samples 10

# Word level
python vipersql.py --level word --samples 10
```

### 5. Different Splits

```bash
# Dev split (default)
python vipersql.py --split dev --samples 10

# Test split
python vipersql.py --split test --samples 10
```

---

## Parameter Reference

### Essential Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--samples` | Integer | all | Number of samples to process |
| `--strategy` | `zero-shot`, `few-shot`, `cot` | `zero-shot` | Generation strategy |
| `--model` | `gpt-4o`, `gpt-4o-mini`, `claude-3-5-sonnet-20241022` | `gpt-4o` | LLM model |

### Few-shot Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--example-selection-strategy` | `random`, `dicl`, `astres`, `skill_knn`, `vir2` | `random` | Selector method |
| `--few-shot-examples` | Integer | 3 | Number of examples |

### ViR2 Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--vir2-candidate-pool-size` | Integer | 50 | Stage 1 pool size (M) |
| `--vir2-beam-size` | Integer | 5 | Beam search width (B) |
| `--vir2-diversity-weight` | Float [0-1] | 0.3 | Diversity weight (λ) |

### Dataset Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--level` | `std`, `syllable`, `word` | `std` | Text segmentation level |
| `--split` | `dev`, `test` | `dev` | Dataset split |

---

## Troubleshooting

### Error: API key not found

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
cat .env | grep API_KEY
```

### Error: Module not found

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
```

### Error: Pre-computed embeddings not found

**Solution:**
```bash
# Build DICL candidates (for ViR2)
python scripts/build_dicl_candidates.py \
  --dataset-path dataset/ViText2SQL \
  --level std
```

### Slow performance

**Solutions:**
- Use fewer samples: `--samples 10`
- Use faster model: `--model gpt-4o-mini`
- Use simpler strategy: `--strategy zero-shot`
- Use simpler selector: `--example-selection-strategy dicl`

### High API costs

**Solutions:**
- Use `gpt-4o-mini` instead of `gpt-4o`
- Use `zero-shot` instead of `few-shot`
- Reduce `--samples`
- Lower `--few-shot-examples`

---

## Next Steps

### Learn More

- **[Architecture](ARCHITECTURE.md)** - Understand system design
- **[ViR2 Method](VIR2_METHOD.md)** - Deep dive into ViR2
- **[Strategies](STRATEGIES.md)** - Compare strategies
- **[Configuration](CONFIGURATION.md)** - All parameters

### Advanced Usage

- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world scenarios
- **[Ablation Experiments](ABLATION_EXPERIMENTS.md)** - Test components
- **[Extending System](EXTENDING_SYSTEM.md)** - Add new features

### Development

- **[API Reference](API_REFERENCE.md)** - Complete API docs
- **[Multi-Language Support](MULTILANG_SUPPORT.md)** - Vietnamese & English

---

## Common Commands Cheat Sheet

```bash
# Quick test
python vipersql.py --samples 10

# Full ViR2 evaluation
python vipersql.py --strategy few-shot --example-selection-strategy vir2 --samples 100

# Budget-friendly
python vipersql.py --model gpt-4o-mini --samples 100

# Chain-of-thought
python vipersql.py --strategy cot --samples 50

# Custom ViR2 parameters
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --samples 100

# Ablation: ViR2 without POS
python vipersql.py --strategy few-shot --example-selection-strategy vir2-no-pos --samples 100

# BIRD dataset (if available)
python bird_vi_vir2_fewshot.py --samples 100
```

---

## Need Help?

- Check **[Configuration](CONFIGURATION.md)** for all options
- See **[Usage Examples](USAGE_EXAMPLES.md)** for scenarios
- Read **[Troubleshooting](#troubleshooting)** section above

---

**You're ready to go! 🚀**

# Ablation Studies for ViPERSQL

This document describes the ablation experiment variants available in ViPERSQL and how to run them using the main script.

## Overview

Ablation studies help understand which components of the ViR2 strategy are most important by systematically removing or modifying individual parts. We provide several pre-built variants for testing different aspects of the system.

## Available Ablation Variants

### 1. ViR2 (Full Implementation)
**Description**: Complete ViR2 strategy with all components enabled
- Stage 1: PhoBERT semantic retrieval (M=50 candidates)
- Stage 2: Beam search re-ranking with POS matching + diversity scoring

**Usage**:
```bash
python vipersql.py --strategy few-shot --selector vir2 --samples 300
```

### 2. ViR2 No Diversity
**Description**: Removes diversity constraint from the scoring function
- Keeps: PhoBERT retrieval + Beam search + POS matching  
- Removes: Diversity penalty in scoring

**Usage**:
```bash
python vipersql.py --strategy few-shot --selector vir2-no-diversity --samples 300
```

### 3. ViR2 No Beam Search  
**Description**: Replaces beam search with simple greedy selection
- Keeps: PhoBERT retrieval + POS matching + diversity scoring
- Removes: Beam search optimization (uses top-k selection instead)

**Usage**:
```bash
python vipersql.py --strategy few-shot --selector vir2-no-beam-search --samples 300
```

### 4. ViR2 No POS
**Description**: Removes POS matching component entirely
- Keeps: PhoBERT retrieval + beam search + diversity scoring
- Removes: POS matching (uses only semantic similarity)

**Usage**:
```bash
python vipersql.py --strategy few-shot --selector vir2-no-pos --samples 300
```

## Running Ablation Experiments

### Basic Usage
```bash
# Run specific ablation variant
python vipersql.py --strategy few-shot --selector [VARIANT_NAME] --samples [N]
```

### Complete Ablation Suite
Run all variants in sequence:

```bash
# Full ViR2
python vipersql.py --strategy few-shot --selector vir2 --samples 300

# No Diversity variant  
python vipersql.py --strategy few-shot --selector vir2-no-diversity --samples 300

# No Beam Search variant
python vipersql.py --strategy few-shot --selector vir2-no-beam-search --samples 300

# No POS variant
python vipersql.py --strategy few-shot --selector vir2-no-pos --samples 300
```

### Sample Sizes
You can test with different sample sizes:

```bash
# Quick test with 3 samples
python vipersql.py --strategy few-shot --selector vir2 --samples 3

# Medium test with 30 samples  
python vipersql.py --strategy few-shot --selector vir2 --samples 30

# Full evaluation with 300 samples
python vipersql.py --strategy few-shot --selector vir2 --samples 300
```

### Output
Results are automatically saved to the `results/` directory with timestamps:
- `results/few-shot-vir2300_[timestamp]/` - Full ViR2 results
- `results/few-shot-vir2-no-diversity300_[timestamp]/` - No diversity results  
- `results/few-shot-vir2-no-beam-search300_[timestamp]/` - No beam search results
- `results/few-shot-vir2-no-pos300_[timestamp]/` - No POS results

Each folder contains:
- `eval_report_[timestamp].txt` - Human-readable summary
- `eval_results_[timestamp].json` - Detailed metrics
- `predictions.json` - Generated SQL queries

---

*Use these commands to systematically evaluate different components of the ViR2 strategy and understand their individual contributions.*

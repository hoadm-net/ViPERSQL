# Usage Examples

## Real-World Scenarios

Real-world examples of using ViPERSQL for various scenarios.

---

## Basic Usage

### 1. Quick Baseline

**Scenario:** Need quick baseline for comparison

```bash
python vipersql.py \
  --strategy zero-shot \
  --model gpt-4o-mini \
  --samples 50
```

**Output:** `results/zero-shot_50_TIMESTAMP/`

---

### 2. Best Accuracy Run

**Scenario:** Want highest accuracy, not concerned about cost

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --model gpt-4o \
  --few-shot-examples 5 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --samples 1000
```

**Expected:**
- Highest EM and F1 scores
- Longer processing time
- Higher API costs

---

### 3. Budget-Conscious Evaluation

**Scenario:** Limited budget, need to balance accuracy and cost

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy dicl \
  --model gpt-4o-mini \
  --few-shot-examples 3 \
  --samples 1000
```

**Benefits:**
- Lower cost (gpt-4o-mini)
- Good accuracy (DICL selector)
- Fast selection

---

## Comparison Studies

### 4. Compare Strategies

**Goal:** Compare Zero-shot vs Few-shot vs CoT

```bash
# Zero-shot
python vipersql.py \
  --strategy zero-shot \
  --model gpt-4o \
  --samples 200

# Few-shot
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --model gpt-4o \
  --samples 200

# Chain-of-thought
python vipersql.py \
  --strategy cot \
  --model gpt-4o \
  --samples 200
```

**Analysis:** Compare results từ 3 output folders

---

### 5. Compare Selectors

**Goal:** Compare example selectors

```bash
# Random baseline
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy random \
  --samples 300

# DICL
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy dicl \
  --samples 300

# ViR2
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300
```

---

### 6. Compare Models

**Goal:** Compare LLM models

```bash
# GPT-4o
python vipersql.py \
  --model gpt-4o \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 200

# GPT-4o-mini
python vipersql.py \
  --model gpt-4o-mini \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 200

# Claude-3.5-Sonnet
python vipersql.py \
  --model claude-3-5-sonnet-20241022 \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 200
```

---

## Ablation Studies

### 7. ViR2 Component Analysis

**Goal:** Test contribution of each ViR2 component

```bash
# Full ViR2 (baseline)
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300

# Without POS matching
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-pos \
  --samples 300

# Without diversity
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-diversity \
  --samples 300

# Without beam search
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-beam-search \
  --samples 300
```

**Analysis:**
- Compare EM and F1 scores
- Identify most important component
- Quantify contribution of each component

---

### 8. ViR2 Hyperparameter Tuning

**Goal:** Find optimal hyperparameters for ViR2

```bash
# Vary M (candidate pool size)
for M in 20 50 100 150; do
  python vipersql.py \
    --strategy few-shot \
    --example-selection-strategy vir2 \
    --vir2-candidate-pool-size $M \
    --samples 200
done

# Vary B (beam size)
for B in 1 3 5 10 15; do
  python vipersql.py \
    --strategy few-shot \
    --example-selection-strategy vir2 \
    --vir2-beam-size $B \
    --samples 200
done

# Vary λ (diversity weight)
for lambda in 0.0 0.2 0.3 0.5 0.7 1.0; do
  python vipersql.py \
    --strategy few-shot \
    --example-selection-strategy vir2 \
    --vir2-diversity-weight $lambda \
    --samples 200
done
```

---

## Dataset Variations

### 9. Different Text Levels

**Goal:** Test across text segmentation levels

```bash
# Standard level
python vipersql.py \
  --level std \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300

# Syllable level
python vipersql.py \
  --level syllable \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300

# Word level
python vipersql.py \
  --level word \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300
```

---

### 10. Different Dataset Splits

**Goal:** Evaluate on different splits

```bash
# Dev split (validation)
python vipersql.py \
  --split dev \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300

# Test split (final evaluation)
python vipersql.py \
  --split test \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 300
```

---

## Multi-Language

### 11. Vietnamese-English Comparison

**Goal:** Test multi-language support

```bash
# Vietnamese (ViText2SQL)
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language vi \
  --samples 300

# English (BIRD)
python bird_en_vir2_fewshot.py \
  --samples 300

# Or with multilang-vir2
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language en \
  --samples 300
```

---

### 12. Auto Language Detection

**Goal:** Mixed Vietnamese-English dataset

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language auto \
  --samples 500
```

**System will:**
- Auto-detect each question's language
- Use PhoBERT for Vietnamese
- Use BERT for English
- Apply language-specific POS matching

---

## Production Scenarios

### 13. Full Evaluation Run

**Goal:** Complete evaluation for paper/report

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --model gpt-4o \
  --few-shot-examples 3 \
  --vir2-candidate-pool-size 50 \
  --vir2-beam-size 5 \
  --vir2-diversity-weight 0.3 \
  --level std \
  --split test \
  --samples 1000 \
  --temperature 0.3 \
  --max-tokens 1000
```

**Generates:**
- Full predictions
- Component F1 scores
- Error analysis
- Complexity breakdown

---

### 14. Incremental Processing

**Goal:** Process large dataset in batches

```bash
# Batch 1
python vipersql.py --samples 100 --split dev

# Batch 2
python vipersql.py --samples 100 --split dev --offset 100

# Batch 3
python vipersql.py --samples 100 --split dev --offset 200

# ... combine results later
```

---

## Debugging & Analysis

### 15. Error Analysis

**Goal:** Understand failure cases

```bash
# Run evaluation
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --samples 100

# Check results
cd results/few-shot-vir2_100_TIMESTAMP/

# View errors in eval_results.json
cat eval_results.json | jq '.error_statistics'

# Find failed examples
cat predictions.json | jq '.predictions[] | select(.exact_match == false)'
```

---

### 16. Component Performance

**Goal:** See which components model performs well/poorly on

```bash
# Run evaluation
python vipersql.py --samples 200

# Check component F1
cat results/*/eval_results.json | jq '.component_f1'
```

**Typical output:**
```json
{
  "SELECT": 0.92,
  "FROM": 0.91,
  "WHERE": 0.76,   // Low - model struggles with conditions
  "GROUP BY": 0.68, // Low - aggregations difficult
  "ORDER BY": 0.85,
  "HAVING": 0.54,   // Lowest - complex logic
  "KEYWORDS": 0.88
}
```

**Action:** Add more GROUP BY/HAVING examples

---

## Scripted Workflows

### 17. Full Comparison Suite

```bash
#!/bin/bash
# compare_all.sh

SAMPLES=300

# Strategies
for strategy in zero-shot few-shot cot; do
  python vipersql.py \
    --strategy $strategy \
    --samples $SAMPLES
done

# Selectors (for few-shot)
for selector in random dicl astres skill_knn vir2; do
  python vipersql.py \
    --strategy few-shot \
    --example-selection-strategy $selector \
    --samples $SAMPLES
done

echo "✅ All comparisons complete! Check results/ folder"
```

**Run:**
```bash
chmod +x compare_all.sh
./compare_all.sh
```

---

### 18. Hyperparameter Grid Search

```bash
#!/bin/bash
# grid_search.sh

SAMPLES=200

for M in 30 50 100; do
  for B in 3 5 10; do
    for lambda in 0.2 0.3 0.5; do
      echo "Testing M=$M, B=$B, λ=$lambda"
      python vipersql.py \
        --strategy few-shot \
        --example-selection-strategy vir2 \
        --vir2-candidate-pool-size $M \
        --vir2-beam-size $B \
        --vir2-diversity-weight $lambda \
        --samples $SAMPLES
    done
  done
done

echo "✅ Grid search complete!"
```

---

## BIRD Dataset

### 19. BIRD Vietnamese Evaluation

```bash
python bird_vi_vir2_fewshot.py \
  --samples 300 \
  --k-examples 3
```

---

### 20. BIRD English Evaluation

```bash
python bird_en_vir2_fewshot.py \
  --samples 300 \
  --k-examples 3
```

---

### 21. BIRD Random Baseline

```bash
python bird_vi_random_fewshot.py \
  --samples 300 \
  --k-examples 3
```

---

## Custom Scenarios

### 22. High-Temperature Exploration

**Goal:** Test creative SQL generation

```bash
python vipersql.py \
  --strategy cot \
  --temperature 0.8 \
  --max-tokens 2000 \
  --samples 50
```

**Note:** Higher temperature may produce varied but less accurate SQL

---

### 23. Minimal Token Usage

**Goal:** Minimize API costs

```bash
python vipersql.py \
  --strategy zero-shot \
  --model gpt-4o-mini \
  --temperature 0.1 \
  --max-tokens 500 \
  --samples 1000
```

---

### 24. Maximum Accuracy

**Goal:** Best possible results

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --model gpt-4o \
  --few-shot-examples 7 \
  --vir2-candidate-pool-size 150 \
  --vir2-beam-size 15 \
  --vir2-diversity-weight 0.4 \
  --temperature 0.2 \
  --max-tokens 1500 \
  --samples 1000
```

---

## Tips & Best Practices

### Sample Size Selection

- **10-50:** Quick tests, debugging
- **100-300:** Method comparison
- **300-1000:** Full evaluation
- **1000+:** Final results for publication

### Model Selection

- **gpt-4o-mini:** Development, testing, budget-conscious
- **gpt-4o:** Production, best accuracy
- **claude-3-5-sonnet:** Alternative, good reasoning

### Selector Selection

- **random:** Baseline only
- **dicl:** Fast, good accuracy
- **vir2:** Best accuracy (recommended)
- **multilang-vir2:** Multi-language datasets

### Strategy Selection

- **zero-shot:** Simple queries, baseline
- **few-shot:** Most use cases (recommended)
- **cot:** Complex reasoning, interpretability

---

## Analyzing Results

### Compare Two Runs

```bash
# Run 1: Random selector
python vipersql.py \
  --example-selection-strategy random \
  --samples 300
# → results/few-shot-random_300_20251201_100000/

# Run 2: ViR2 selector
python vipersql.py \
  --example-selection-strategy vir2 \
  --samples 300
# → results/few-shot-vir2_300_20251201_101500/

# Compare
diff \
  results/few-shot-random_300_*/eval_results.json \
  results/few-shot-vir2_300_*/eval_results.json
```

### Extract Key Metrics

```bash
# Exact Match
cat results/*/eval_results.json | jq '.overall_metrics.exact_match_accuracy'

# Avg F1
cat results/*/eval_results.json | jq '.overall_metrics.avg_f1'

# Component F1
cat results/*/eval_results.json | jq '.component_f1'
```

---

## Related Documentation

- **[Quick Start](QUICKSTART.md)** - Get started
- **[Configuration](CONFIGURATION.md)** - All parameters
- **[Strategies](STRATEGIES.md)** - Strategy details
- **[Selectors](SELECTORS.md)** - Selector details
- **[Evaluation Metrics](EVALUATION_METRICS.md)** - Understanding results

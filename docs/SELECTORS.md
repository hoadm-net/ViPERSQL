# Example Selection Methods

## Overview

Example selectors choose k best training examples to guide LLM in **Few-shot Strategy**.

---

## Selector Interface

```python
class BaseSelector(ABC):
    @abstractmethod
    def select_examples(
        self,
        question: str,
        k: int,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]
```

**Input:**
- `question`: New question for SQL generation
- `k`: Number of examples to select
- `db_id`: Optional - filter by database

**Output:**
- List of k examples, each containing: `{question, query, db_id, ...}`

---

## Comparison Table

| Selector | Complexity | Speed | Requires | Best For |
|----------|------------|-------|----------|----------|
| Random | $O(1)$ | ⚡⚡⚡ | Nothing | Baseline |
| DICL | $O(n)$ | ⚡⚡ | Pre-computed embeddings | Semantic similarity |
| ASTRES | $O(n^2)$ | ⚡ | SQL parsing | Structural matching |
| Skill-KNN | $O(n)$ + LLM | ⚡⚡ | LLM calls | Task-aware |
| **ViR2** | $O(k \cdot B \cdot M)$ | **⚡⚡** | **Pre-computed embeddings** | **Best overall** |

---

## 1. Random Selector

### Method

Randomly selects k examples from training pool.

### Algorithm

```
Input: Training pool P, k examples
Output: k random examples

1. If db_id specified:
     P' = filter P by db_id
   Else:
     P' = P

2. Return random.sample(P', k)
```

### When to Use

- ✅ Quick baseline
- ✅ Sanity check
- ✅ No preprocessing available
- ❌ Production use

### Parameters

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy random \
  --few-shot-examples 3
```

### Advantages

- ⚡ Fastest
- 🎯 Simple
- 📦 No preprocessing

### Limitations

- ❌ No relevance
- ❌ Poor accuracy
- ❌ Inconsistent results

---

## 2. DICL Selector

**DICL = Domain-Independent Context Learning**

### Method

Selects examples based on **semantic similarity** (PhoBERT/BERT embeddings).

### Algorithm

```
Input: Question q, Candidate pool C, k examples
Output: k most similar examples

1. Encode q → embedding e_q using PhoBERT/BERT

2. For each candidate c in C:
     Compute similarity: sim(e_q, e_c)

3. Sort candidates by similarity descending

4. Return top-k candidates
```

### Similarity Metric

$$\text{sim}(q_1, q_2) = \frac{\mathbf{e}_{q_1} \cdot \mathbf{e}_{q_2}}{\|\mathbf{e}_{q_1}\| \|\mathbf{e}_{q_2}\|}$$

Cosine similarity in embedding space.

### When to Use

- ✅ Semantic relevance needed
- ✅ Have pre-computed embeddings
- ✅ Fast selection required
- ❌ Need syntactic matching
- ❌ Need diversity

### Parameters

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy dicl \
  --few-shot-examples 3
```

### Preprocessing

```bash
# Build DICL candidates with pre-computed embeddings
python scripts/build_dicl_candidates.py \
  --dataset-path dataset/ViText2SQL \
  --level std
```

Generates: `dataset/ViText2SQL/std-level/dicl_candidates.json`

### Advantages

- 🎯 Semantic relevance
- ⚡ Fast (pre-computed embeddings)
- 📊 Better than random

### Limitations

- ❌ Only semantic (ignores structure)
- ❌ No diversity
- ❌ May select redundant examples

---

## 3. ASTRES Selector

**ASTRES = AST-based Retrieval and Example Selection**

### Method

Selects examples based on **SQL structure similarity** via Abstract Syntax Trees.

### Algorithm

```
Input: Question q, Candidate pool C, k examples, Schema
Output: k structurally similar examples

1. Generate zero-shot SQL for q → sql_q

2. Parse sql_q to AST → ast_q

3. For each candidate c in C:
     Parse c.query to AST → ast_c
     Compute AST similarity: sim(ast_q, ast_c)

4. Sort by AST similarity

5. Return top-k
```

### AST Similarity

Based on **tree edit distance**:

$$\text{sim}_{\text{AST}}(t_1, t_2) = 1 - \frac{\text{EditDist}(t_1, t_2)}{\max(|t_1|, |t_2|)}$$

### When to Use

- ✅ Structural similarity important
- ✅ Have SQL parser
- ✅ English queries (designed for English)
- ❌ Vietnamese (not optimized)
- ❌ Speed critical

### Parameters

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy astres \
  --few-shot-examples 3
```

### Advantages

- 🌳 Structure-aware
- 📐 Good for similar query patterns
- 🎯 Matches SQL complexity

### Limitations

- ⏱️ Slow (parsing overhead)
- 🇬🇧 English-centric
- 🔧 Requires zero-shot generation first
- ❌ Not optimized for Vietnamese

---

## 4. Skill-KNN Selector

### Method

Extract "SQL skills" from queries using LLM, then match by skill similarity.

### Algorithm

```
Input: Question q, Candidate pool C (with skills), k examples
Output: k skill-matched examples

1. Extract skills from q using LLM:
   Prompt: "What SQL skills are needed for: {q}?"
   → skills_q = "JOIN, aggregation, GROUP BY"

2. Encode skills_q → embedding e_skills

3. For each candidate c in C:
     Compute similarity: sim(e_skills, e_skills_c)

4. Sort by skill similarity

5. Return top-k
```

### SQL Skills Examples

- "Simple SELECT"
- "JOIN two tables"
- "Aggregation (COUNT/SUM/AVG)"
- "GROUP BY"
- "Nested SELECT"
- "HAVING clause"
- "ORDER BY"

### When to Use

- ✅ Task-aware selection
- ✅ Good accuracy
- ✅ Interpretable (can see skills)
- ❌ Budget tight (requires LLM calls)
- ❌ Speed critical

### Parameters

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy skill_knn \
  --few-shot-examples 3
```

### Preprocessing

```bash
# Extract skills for training data using LLM
python scripts/skill_knn_preprocessing.py \
  --num_samples 1000 \
  --delay 1.0
```

Generates: `dataset/ViText2SQL/std-level/skill_knn_train.json`

**Warning:** Expensive! Calls LLM for every training example.

### Advantages

- 🧠 Task-aware
- 📊 Good accuracy
- 🔍 Interpretable skills
- 🎯 Matches query complexity

### Limitations

- 💰 Expensive preprocessing
- ⏱️ Slow selection
- 🎲 Depends on skill extraction quality
- 🔧 Requires LLM for new questions

---

## 5. ViR2 Selector (Main Contribution)

**ViR2 = Vietnamese Retrieval and Re-ranking**

### Method

**Two-stage selection:**
1. **Stage 1:** PhoBERT semantic retrieval → top-M candidates
2. **Stage 2:** Beam search re-ranking with POS + diversity → k examples

### Algorithm Overview

```
Input: Question q, Meaning Pool P, Parameters (M, B, k, λ)
Output: k optimal examples

Stage 1: Semantic Retrieval
├─ Encode q using PhoBERT
├─ Compute similarity with all examples in P
└─ Select top-M candidates → C

Stage 2: Beam Search Re-ranking
├─ Initialize beams = [[]]
├─ For i in [1, k]:
│   ├─ For each beam:
│   │   ├─ Try adding each candidate from C
│   │   └─ Score = POS_match + λ * diversity
│   └─ Keep top-B beams
└─ Return best beam
```

### Scoring Function

$$\text{Score}(E, q) = \text{POS_Score}(E, q) + \lambda \cdot \text{Diversity}(E)$$

where:

$$\text{POS_Score}(E, q) = \frac{1}{k} \sum_{i=1}^{k} \text{POS_match}(q, q_{e_i})$$

$$\text{Diversity}(E) = 1 - \frac{2}{k(k-1)} \sum_{i<j} \text{sim}(e_i, e_j)$$

### When to Use

- ✅ **Best accuracy** (recommended)
- ✅ Vietnamese Text-to-SQL
- ✅ Have pre-computed embeddings
- ✅ Can afford medium complexity
- ❌ Extremely simple queries (use random)

### Parameters

**Default:**
```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 3
```

**Custom:**
```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 5 \
  --vir2-candidate-pool-size 100 \
  --vir2-beam-size 10 \
  --vir2-diversity-weight 0.5
```

### Hyperparameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `M` (pool size) | 50 | [10, 200] | Stage 1 candidates |
| `B` (beam size) | 5 | [1, 20] | Beam search width |
| `λ` (diversity) | 0.3 | [0, 1] | Diversity weight |
| `k` (examples) | 3 | [1, 10] | Final examples |

### Preprocessing

```bash
# Use DICL candidates as meaning pool
python scripts/build_dicl_candidates.py \
  --dataset-path dataset/ViText2SQL \
  --level std
```

Generates: `dataset/ViText2SQL/std-level/dicl_candidates.json`

ViR2 loads this file automatically.

### Advantages

- 🏆 **Best accuracy**
- 🇻🇳 **Vietnamese-optimized** (PhoBERT + underthesea)
- 🎯 Combines semantic + syntactic
- 📊 Diversity optimization
- ⚡ Fast (pre-computed embeddings)

### Limitations

- 🔧 More complex than DICL
- ⚙️ Hyperparameters to tune
- 📦 Requires preprocessing

---

## 6. Multi-Language ViR2

### Method

Extension of ViR2 with **automatic language detection** and language-specific models.

### Supported Languages

- **Vietnamese:** PhoBERT + underthesea POS
- **English:** BERT + spaCy POS

### Algorithm

```
Input: Question q (any language)
Output: k examples

1. Detect language: lang = detect_language(q)
   → "vi" or "en"

2. Stage 1: Semantic retrieval
   - If lang == "vi": Use PhoBERT
   - If lang == "en": Use BERT
   → Top-M candidates

3. Stage 2: Beam search
   - If lang == "vi": Use underthesea POS
   - If lang == "en": Use spaCy POS
   → k examples
```

### When to Use

- ✅ Multi-language datasets (Vietnamese + English)
- ✅ BIRD dataset (has both languages)
- ✅ Want single unified system
- ❌ Single language only (use regular ViR2)

### Parameters

```bash
# Auto-detect language
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --samples 100

# Force Vietnamese
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language vi \
  --samples 100

# Force English
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy multilang-vir2 \
  --language en \
  --samples 100
```

### Advantages

- 🌍 Multi-language support
- 🔄 Unified architecture
- 🎯 Language-specific optimization

### Limitations

- 🔧 More complex
- 📦 Requires both language models
- 💾 More memory (2 models loaded)

---

## Ablation Variants (ViR2)

To test contribution of each component in ViR2:

### ViR2-No-POS

**Remove:** POS matching component

**Scoring:** Only semantic similarity + diversity

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-pos
```

### ViR2-No-Diversity

**Remove:** Diversity optimization

**Scoring:** Only POS matching

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-diversity
```

### ViR2-No-Beam-Search

**Remove:** Beam search

**Method:** Greedy top-k selection

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2-no-beam-search
```

See **[Ablation Experiments](ABLATION_EXPERIMENTS.md)** for details.

---

## Performance Comparison

### Computational Complexity

| Selector | Time Complexity | Space Complexity |
|----------|-----------------|------------------|
| Random | $O(1)$ | $O(1)$ |
| DICL | $O(n)$ | $O(n \cdot d)$ |
| ASTRES | $O(n \cdot m^2)$ | $O(n \cdot m)$ |
| Skill-KNN | $O(n + \text{LLM})$ | $O(n \cdot d)$ |
| ViR2 | $O(M + k \cdot B \cdot M)$ | $O(n \cdot d)$ |

where:
- $n$ = training pool size
- $d$ = embedding dimension (768)
- $m$ = average SQL length
- $M$ = candidate pool size (50)
- $B$ = beam size (5)
- $k$ = final examples (3)

### Speed Benchmark (typical)

| Selector | Selection Time |
|----------|----------------|
| Random | ~0.001s |
| DICL | ~0.05s |
| ASTRES | ~2.0s |
| Skill-KNN | ~0.1s + LLM call |
| ViR2 | ~0.2s |

### Accuracy (typical - depends on dataset)

Results are illustrative:

| Selector | Exact Match | Component F1 |
|----------|-------------|--------------|
| Random | Baseline | Baseline |
| DICL | +5-10% | +5-10% |
| ASTRES | +3-7% | +3-7% |
| Skill-KNN | +6-12% | +6-12% |
| **ViR2** | **+10-15%** | **+10-15%** |

---

## Usage Recommendations

### For Quick Experiments

```bash
# Random baseline
python vipersql.py --strategy few-shot --example-selection-strategy random --samples 10
```

### For Production

```bash
# ViR2 (best accuracy)
python vipersql.py --strategy few-shot --example-selection-strategy vir2 --samples 1000
```

### For Budget-Conscious

```bash
# DICL (good accuracy, fast)
python vipersql.py --strategy few-shot --example-selection-strategy dicl --samples 1000
```

### For Multi-Language

```bash
# Multi-language ViR2
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --samples 1000
```

---

## Environment Configuration

```env
# Selector defaults
EXAMPLE_SELECTION_STRATEGY=vir2
FEW_SHOT_EXAMPLES=3

# ViR2 parameters
VIR2_CANDIDATE_POOL_SIZE=50
VIR2_BEAM_SIZE=5
VIR2_DIVERSITY_WEIGHT=0.3
```

---

## Troubleshooting

### Low accuracy with Random

**Solution:** Use semantic selector (DICL or ViR2)

### DICL selects redundant examples

**Solution:** Use ViR2 (has diversity optimization)

### ViR2 too slow

**Solutions:**
- Reduce `M` (candidate pool size)
- Reduce `B` (beam size)
- Use DICL instead

### Pre-computed embeddings missing

**Solution:**
```bash
python scripts/build_dicl_candidates.py \
  --dataset-path dataset/ViText2SQL \
  --level std
```

---

## Related Documentation

- **[ViR2 Method](VIR2_METHOD.md)** - Detailed ViR2 algorithm and math
- **[Strategies](STRATEGIES.md)** - Few-shot strategy usage
- **[Ablation Experiments](ABLATION_EXPERIMENTS.md)** - Testing framework
- **[Configuration](CONFIGURATION.md)** - All parameters

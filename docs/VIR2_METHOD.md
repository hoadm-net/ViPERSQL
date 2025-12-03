# ViR2: Two-Stage Example Selection Method

## Overview

**ViR2 (Vietnamese Retrieval and Re-ranking)** is a few-shot example selection method for Text-to-SQL that combines semantic retrieval with syntactic matching and diversity optimization.

## Motivation

### Limitations of Current Methods

| Method | Limitations |
|--------|-------------|
| Random | No semantic understanding |
| DICL | Relies solely on semantic similarity, ignores grammatical structure |
| ASTRES | AST matching not suitable for Vietnamese |
| Skill-KNN | Requires LLM for skill extraction → expensive |

### Solution: ViR2

ViR2 combines three components:

1. **Semantic Similarity** - PhoBERT embeddings
2. **Syntactic Matching** - POS tagging (Vietnamese-aware)
3. **Diversity** - Avoids redundant examples

---

## Method Architecture

### Two-Stage Pipeline

```
Input: Question q, Training Pool P, Parameters (M, B, k, λ)

Stage 1: Semantic Retrieval
│
├─ Encode q using PhoBERT → embedding e_q
├─ Compute cosine similarity with all examples in P
└─ Select top-M candidates → C
│
↓
│
Stage 2: Beam Search Re-ranking
│
├─ Initialize beams = [[]]
├─ For each position i ∈ [1, k]:
│   ├─ For each beam:
│   │   ├─ For each candidate c ∈ C:
│   │   │   ├─ Create new_beam = beam + [c]
│   │   │   └─ Compute score(new_beam, q)
│   │   └─ Collect all candidate beams
│   └─ Keep top-B beams by score
└─ Return best beam (k examples)
```

---

## Stage 1: Semantic Retrieval

### Objective

Filter top-M candidates with high semantic similarity to the new question.

### Algorithm

**Input:**
- Question $q$ (new question)
- Meaning Pool $P = \{(q_1, s_1), (q_2, s_2), \ldots, (q_n, s_n)\}$
- Pool size $M$ (default: 50)

**Process:**

1. **Encode question:**
   $$\mathbf{e}_q = \text{PhoBERT}(q)$$

2. **Compute similarities:**
   $$\text{sim}(q, q_i) = \frac{\mathbf{e}_q \cdot \mathbf{e}_{q_i}}{\|\mathbf{e}_q\| \|\mathbf{e}_{q_i}\|}$$

3. **Select top-M:**
   $$C = \text{TopK}(P, M, \text{by}=\text{sim})$$

**Output:** Candidate set $C = \{c_1, c_2, \ldots, c_M\}$

### Implementation Details

**PhoBERT Encoding:**
- Model: `vinai/phobert-base-v2`
- Embedding dimension: 768
- Pooling: Mean pooling over all token embeddings

**Optimization:**
- Pre-compute embeddings for training pool → Saved in `dicl_candidates.json`
- Only encode new question at runtime
- Complexity: $O(M)$ similarity computations

---

## Stage 2: Beam Search Re-ranking

### Objective

From M candidates, select k optimal examples using beam search with a scoring function that combines POS matching and diversity.

### Beam Search Algorithm

**Input:**
- Candidates $C = \{c_1, \ldots, c_M\}$
- Question $q$
- Beam size $B$ (default: 5)
- Number of examples $k$ (default: 3)

**Process:**

**Initialize:**
$$\text{beams} = [\emptyset]$$

**For** $i = 1$ to $k$:
1. $\text{candidates} = \emptyset$
2. **For each** beam $\in \text{beams}$:
   - **For each** $c \in C$:
     - $\text{new_beam} = \text{beam} \cup \{c\}$
     - $\text{score} = f(\text{new_beam}, q)$
     - $\text{candidates} = \text{candidates} \cup \{(\text{new_beam}, \text{score})\}$
3. $\text{beams} = \text{TopB}(\text{candidates}, B)$

**Return:** Best beam (highest score)

### Scoring Function

$$f(E, q) = \text{POS}_{\text{Score}}(E, q) + \lambda \cdot \text{Diversity}(E)$$

where:
- $E = \{e_1, e_2, \ldots, e_k\}$ is the set of selected examples
- $\lambda$ is diversity weight (default: 0.3)

---

## Component 1: POS Matching

### Definition

POS matching measures **grammatical structure** similarity between new question and example questions.

### Algorithm

**Input:** Two questions $q_1$, $q_2$

**Step 1: POS Tagging**

Using **underthesea** (Vietnamese-specific):

```
q_1 = "Có bao nhiêu học sinh trong lớp 10A?"
POS tags: [('Có', 'V'), ('bao nhiêu', 'M'), ('học sinh', 'N'), ('trong', 'E'), ('lớp', 'N'), ('10A', 'M')]
```

**Step 2: Extract POS Distribution**

$$D_1 = \{(\text{V}, 1), (\text{M}, 2), (\text{N}, 2), (\text{E}, 1)\}$$

Normalize:
$$P_1(t) = \frac{\text{count}(t)}{\sum_{\text{all tags}} \text{count}}$$

**Step 3: Compute Jensen-Shannon Divergence**

$$\text{JSD}(P_1, P_2) = \frac{1}{2} D_{\text{KL}}(P_1 \| M) + \frac{1}{2} D_{\text{KL}}(P_2 \| M)$$

where $M = \frac{P_1 + P_2}{2}$

**Step 4: POS Match Score**

$$\text{POS}_{\text{match}}(q_1, q_2) = 1 - \text{JSD}(P_1, P_2)$$

Range: $[0, 1]$ (1 = identical POS distribution)

### Average POS Score

For a set of examples $E = \{e_1, \ldots, e_k\}$ and question $q$:

$$\text{POS}_{\text{Score}}(E, q) = \frac{1}{k} \sum_{i=1}^{k} \text{POS}_{\text{match}}(q, q_{e_i})$$

### Why POS Matching is Important for Vietnamese?

- Vietnamese has different word order from English
- Complex grammatical structure (isolating language)
- **underthesea** understands Vietnamese-specific patterns
- POS tags: N (noun), V (verb), M (number), E (preposition), A (adjective), etc.

---

## Component 2: Diversity Optimization

### Definition

Diversity ensures k examples are not too similar, covering multiple SQL patterns.

### Algorithm

**Input:** Set of examples $E = \{e_1, e_2, \ldots, e_k\}$

**Step 1: Compute Pairwise Similarities**

Using embeddings from Stage 1:

$$\text{sim}(e_i, e_j) = \frac{\mathbf{e}_{e_i} \cdot \mathbf{e}_{e_j}}{\|\mathbf{e}_{e_i}\| \|\mathbf{e}_{e_j}\|}$$

**Step 2: Average Pairwise Similarity**

$$\text{AvgSim}(E) = \frac{2}{k(k-1)} \sum_{i=1}^{k-1} \sum_{j=i+1}^{k} \text{sim}(e_i, e_j)$$

**Step 3: Diversity Score**

$$\text{Diversity}(E) = 1 - \text{AvgSim}(E)$$

Range: $[0, 1]$ (1 = completely diverse, 0 = identical)

### Intuition

- High diversity = Semantically different examples
- Low diversity = Overly similar examples (redundant)
- Balanced with POS matching via $\lambda$

---

## Hyperparameters

### Configurable Parameters

| Parameter | Symbol | Default | Range | Description |
|-----------|--------|---------|-------|-------------|
| Candidate pool size | $M$ | 50 | [10, 200] | Stage 1 retrieval size |
| Beam size | $B$ | 5 | [1, 20] | Beam search width |
| Diversity weight | $\lambda$ | 0.3 | [0, 1] | Balance POS vs diversity |
| Examples | $k$ | 3 | [1, 10] | Final selection count |

### Tuning Guidelines

**$M$ (Candidate pool size):**
- Large → Better coverage but slower Stage 2
- Small → Faster but may miss good examples
- Recommended: 50-100 for typical datasets

**$B$ (Beam size):**
- Large → Better optimization but slower
- Small → Faster but sub-optimal
- Recommended: 5-10

**$\lambda$ (Diversity weight):**
- High → Prefer diverse examples (multiple patterns)
- Low → Prefer similar structure (consistent style)
- Recommended: 0.2-0.5

**$k$ (Number of examples):**
- Many → Better guidance but longer prompts, more tokens
- Few → Shorter prompts but less guidance
- Recommended: 3-5

---

## Computational Complexity

### Stage 1: Semantic Retrieval

**Time Complexity:**
- Encoding question: $O(L)$ where $L$ = question length
- Similarity computation: $O(|P|)$ where $|P|$ = pool size
- **Total:** $O(L + |P|)$

**Space Complexity:**
- Store embeddings: $O(|P| \times D)$ where $D$ = 768

**Optimization:**
- Pre-compute pool embeddings → Save $O(|P| \times L)$

### Stage 2: Beam Search

**Time Complexity:**
- For each position $i \in [1, k]$:
  - Expand $B$ beams with $M$ candidates → $B \times M$ new beams
  - Score computation per beam:
    - POS matching: $O(k \times L_{\text{avg}})$
    - Diversity: $O(k^2)$
  - Keep top-$B$: $O(B \times M \times \log B)$

**Total:** $O(k \times B \times M \times (k \times L_{\text{avg}} + k^2))$

**Practical:** With $k=3, B=5, M=50, L_{\text{avg}}=20$:
- Iterations: $3 \times 5 \times 50 = 750$ beam evaluations
- Fast on modern CPUs (~1-2 seconds)

---

## Ablation Variants

To test contribution of each component:

### ViR2-No-POS

**Modification:** Remove POS matching component

$$f(E, q) = \text{Semantic}_{\text{Score}}(E, q) + \lambda \cdot \text{Diversity}(E)$$

**Usage:**
```bash
python vipersql.py --strategy few-shot --example-selection-strategy vir2-no-pos
```

### ViR2-No-Diversity

**Modification:** Remove diversity optimization

$$f(E, q) = \text{POS}_{\text{Score}}(E, q)$$

Set $\lambda = 0$

**Usage:**
```bash
python vipersql.py --strategy few-shot --example-selection-strategy vir2-no-diversity
```

### ViR2-No-Beam-Search

**Modification:** Replace beam search with greedy top-$k$ selection

**Algorithm:**
1. Score all $M$ candidates individually
2. Select top-$k$ by score

**Usage:**
```bash
python vipersql.py --strategy few-shot --example-selection-strategy vir2-no-beam-search
```

---

## Comparison with Baselines

### vs Random

**ViR2 advantages:**
- Semantic relevance (Stage 1)
- Syntactic similarity (POS matching)
- Diversity optimization

**Random:** Completely random → no relevance

### vs DICL

**ViR2 advantages:**
- POS matching (syntactic structure)
- Diversity (avoid redundancy)

**DICL:** Only semantic similarity

### vs ASTRES

**ViR2 advantages:**
- Vietnamese-specific (PhoBERT + underthesea)
- POS matching suitable for Vietnamese
- No need for SQL parsing

**ASTRES:** AST matching designed for English, requires SQL parsing

### vs Skill-KNN

**ViR2 advantages:**
- No LLM calls for preprocessing → faster, cheaper
- Direct POS matching (no intermediate skill extraction)

**Skill-KNN:** Requires LLM to extract skills → expensive

---

## Example Walkthrough

### Input

**Question:** "Có bao nhiêu học sinh trong lớp 10A?"

**Meaning Pool:** 1000 training examples

**Parameters:** $M=50, B=5, k=3, \lambda=0.3$

### Stage 1: Semantic Retrieval

1. Encode question with PhoBERT → $\mathbf{e}_q \in \mathbb{R}^{768}$
2. Compute similarity with 1000 examples
3. Select top-50 candidates:
   - "Có bao nhiêu giáo viên?" (sim=0.92)
   - "Liệt kê học sinh lớp 10B" (sim=0.88)
   - "Số lượng học sinh toàn trường" (sim=0.85)
   - ...

### Stage 2: Beam Search

**Iteration 1** (select 1st example):
- Try all 50 candidates as 1st example
- Compute score (only POS since no diversity yet)
- Keep top-5 beams:
  - Beam 1: ["Có bao nhiêu giáo viên?"] score=0.94
  - Beam 2: ["Số lượng học sinh toàn trường"] score=0.89
  - ...

**Iteration 2** (select 2nd example):
- For each beam, try adding each of 50 candidates
- Total: 5 × 50 = 250 combinations
- Compute score (POS + diversity now)
- Keep top-5 beams:
  - Beam 1: [ex1, ex7] score=0.91
  - Beam 2: [ex1, ex12] score=0.88
  - ...

**Iteration 3** (select 3rd example):
- Similar process → 250 combinations
- Keep top-5 beams
- Final best beam: [ex1, ex7, ex23] score=0.87

**Output:** 3 selected examples

---

## Configuration

### Via Command Line

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --vir2-candidate-pool-size 50 \
  --vir2-beam-size 5 \
  --vir2-diversity-weight 0.3 \
  --few-shot-examples 3
```

### Via .env File

```env
# ViR2 Parameters
VIR2_CANDIDATE_POOL_SIZE=50
VIR2_BEAM_SIZE=5
VIR2_DIVERSITY_WEIGHT=0.3
FEW_SHOT_EXAMPLES=3
```

---

## References

**PhoBERT:**
- Nguyen, D. Q., & Nguyen, A. T. (2020). PhoBERT: Pre-trained language models for Vietnamese.

**underthesea:**
- Vietnamese NLP toolkit: https://github.com/undertheseanlp/underthesea

**Beam Search:**
- Freitag, M., & Al-Onaizan, Y. (2017). Beam search strategies for neural machine translation.

**Jensen-Shannon Divergence:**
- Lin, J. (1991). Divergence measures based on the Shannon entropy.


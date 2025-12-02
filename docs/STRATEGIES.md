# SQL Generation Strategies

## Overview

ViPERSQL supports 3 main strategies for Text-to-SQL generation, each suitable for different use cases.

---

## Strategy Interface

All strategies implement `BaseStrategy`:

```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        db_id: str,
        **kwargs
    ) -> StrategyResult
```

---

## 1. Zero-Shot Strategy

### Concept

Direct translation from natural language to SQL **without using examples**.

### When to Use

- ✅ Simple queries
- ✅ Well-structured schemas
- ✅ Limited budget (ít tokens)
- ✅ Fast response needed
- ❌ Complex multi-table joins
- ❌ Ambiguous questions

### Prompt Structure

```
You are an expert in converting Vietnamese/English natural language to SQL.

Database Schema:
Tables: {table_list}
Columns: {column_list}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Question: {question}

Generate the SQL query:
```

### Parameters

```bash
python vipersql.py --strategy zero-shot --samples 100
```

**Configurable:**
- `--model` - LLM model choice
- `--temperature` - Creativity (default: 0.3)
- `--max-tokens` - Response length (default: 1000)

### Advantages

- ⚡ Fast - No example selection overhead
- 💰 Cheap - Fewer tokens
- 🎯 Simple - No training data needed

### Limitations

- ❌ Lower accuracy on complex queries
- ❌ No guidance from similar examples
- ❌ May miss domain-specific patterns

---

## 2. Few-Shot Strategy

### Concept

Provides **k examples** from training data to guide the LLM.

### When to Use

- ✅ Training data available
- ✅ Best accuracy needed
- ✅ Complex queries
- ✅ Domain-specific patterns
- ❌ Extremely simple queries
- ❌ Very tight token budget

### Prompt Structure

```
You are an expert in converting Vietnamese/English natural language to SQL.

Database Schema:
Tables: {table_list}
Columns: {column_list}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Here are some examples:

Example 1:
Question: {example_q1}
SQL: {example_sql1}

Example 2:
Question: {example_q2}
SQL: {example_sql2}

Example 3:
Question: {example_q3}
SQL: {example_sql3}

Now, generate SQL for this question:
Question: {question}

SQL Query:
```

### Example Selection Methods

Few-shot strategy relies on **Selectors** to choose examples:

| Selector | Method | Speed | Quality |
|----------|--------|-------|---------|
| Random | Random sampling | ⚡⚡⚡ | Baseline |
| DICL | Semantic similarity | ⚡⚡ | Good |
| ASTRES | AST matching | ⚡ | Medium |
| Skill-KNN | Skill extraction | ⚡⚡ | Good |
| **ViR2** | **Two-stage** | **⚡⚡** | **Best** |

### Parameters

**Basic:**
```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 3 \
  --samples 100
```

**With ViR2 tuning:**
```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 3 \
  --vir2-candidate-pool-size 50 \
  --vir2-beam-size 5 \
  --vir2-diversity-weight 0.3 \
  --samples 100
```

**Configurable:**
- `--example-selection-strategy` - Selector method
- `--few-shot-examples` - Number of examples (k)
- ViR2-specific: `--vir2-candidate-pool-size`, `--vir2-beam-size`, `--vir2-diversity-weight`

### Advantages

- 🎯 Best accuracy
- 📚 Learn from similar examples
- 🔄 Adaptable to domain patterns
- 🧠 Capture complex SQL structures

### Limitations

- ⏱️ Slower - Example selection overhead
- 💰 More expensive - More tokens
- 📦 Requires training data
- 🔧 Selector tuning needed

### Example Selection Comparison

**Scenario:** "Có bao nhiêu học sinh trong lớp 10A?"

**Random Selection:**
```
Examples may include:
- "List all teachers"
- "Count total schools"  
- "Find student by ID"
→ Not very relevant
```

**DICL Selection:**
```
Examples include:
- "Có bao nhiêu giáo viên?" (semantic similarity)
- "Số lượng học sinh toàn trường"
- "Liệt kê học sinh lớp 10B"
→ Semantically similar
```

**ViR2 Selection:**
```
Examples include:
- "Có bao nhiêu giáo viên?" (POS match: pattern "How many X")
- "Đếm số học sinh lớp 11A" (similar structure)
- "Liệt kê tên môn học" (diverse, covers different SQL pattern)
→ Syntactically similar + diverse
```

---

## 3. Chain-of-Thought (CoT) Strategy

### Concept

Encourage LLM to **reason step-by-step** before generating SQL.

### When to Use

- ✅ Complex multi-step reasoning
- ✅ Multi-table joins
- ✅ Nested queries
- ✅ Interpretability important
- ✅ Debug model thinking
- ❌ Simple queries
- ❌ Tight latency requirements

### Prompt Structure

```
You are an expert in converting Vietnamese/English natural language to SQL.

Database Schema:
Tables: {table_list}
Columns: {column_list}
Foreign Keys: {foreign_keys}
Primary Keys: {primary_keys}

Question: {question}

Let's think step by step:

Step 1: Identify the tables needed
- Which tables contain relevant information?

Step 2: Identify the columns needed
- Which columns should we SELECT?
- Which columns are used in conditions?

Step 3: Identify JOIN conditions
- How are the tables related?
- What are the foreign key relationships?

Step 4: Identify WHERE conditions
- What filters should we apply?
- What comparisons are needed?

Step 5: Identify aggregations and GROUP BY
- Are there any COUNT, SUM, AVG operations?
- Do we need GROUP BY?

Step 6: Construct the final SQL query

SQL Query:
```

### Parameters

```bash
python vipersql.py \
  --strategy cot \
  --cot-reasoning-steps \
  --samples 100
```

**Configurable:**
- `--cot-reasoning-steps` - Enable/disable explicit steps
- `--model` - LLM (better with GPT-4o or Claude-3.5-Sonnet)
- `--temperature` - Can be slightly higher (0.5) for reasoning
- `--max-tokens` - Higher limit (2000+) for reasoning + SQL

### Example Output

**Question:** "Có bao nhiêu học sinh trong lớp 10A có điểm trung bình trên 8.0?"

**CoT Reasoning:**

```
Step 1: Tables needed
- Table `students` (student information)
- Table `classes` (class information)
- Table `grades` (student grades)

Step 2: Columns needed
- COUNT(*) for counting students
- students.class_id to filter by class
- classes.name to identify class "10A"
- AVG(grades.score) for average grade
- grades.student_id to group by student

Step 3: JOIN conditions
- students.id = grades.student_id
- students.class_id = classes.id

Step 4: WHERE conditions
- classes.name = "10A"
- AVG(grades.score) > 8.0

Step 5: Aggregations
- COUNT(DISTINCT students.id)
- GROUP BY students.id
- HAVING AVG(grades.score) > 8.0

Step 6: Final SQL
```

**Generated SQL:**
```sql
SELECT COUNT(DISTINCT s.id)
FROM students s
JOIN classes c ON s.class_id = c.id
JOIN grades g ON s.id = g.student_id
WHERE c.name = "10A"
GROUP BY s.id
HAVING AVG(g.score) > 8.0
```

### Advantages

- 🧠 Better reasoning for complex queries
- 🔍 Interpretable - Can see thinking process
- 🐛 Easier debugging - Know where model fails
- 🎯 Handles multi-step logic well

### Limitations

- ⏱️ Slowest - Extra reasoning tokens
- 💰 Most expensive - 2-3x more tokens
- 🎲 May overthink simple queries
- 📝 Longer prompts

---

## Strategy Comparison

### Token Usage

| Strategy | Prompt Tokens | Response Tokens | Total |
|----------|---------------|-----------------|-------|
| Zero-shot | ~500 | ~100 | ~600 |
| Few-shot (k=3) | ~2000 | ~100 | ~2100 |
| CoT | ~1000 | ~500 | ~1500 |

### Performance Characteristics

| Strategy | Latency | Cost | Accuracy | Complexity |
|----------|---------|------|----------|------------|
| Zero-shot | 1x | 1x | Baseline | Low |
| Few-shot | 2x | 3.5x | Best | Medium |
| CoT | 1.5x | 2.5x | Good | High |

### Use Case Matrix

| Query Type | Zero-shot | Few-shot | CoT |
|------------|-----------|----------|-----|
| Simple SELECT | ✅ Best | ✅ | ⚠️ Overkill |
| Single JOIN | ✅ | ✅ Best | ✅ |
| Multiple JOINs | ⚠️ | ✅ Best | ✅ Best |
| Aggregations | ✅ | ✅ Best | ✅ |
| Nested queries | ❌ | ✅ | ✅ Best |
| Complex logic | ❌ | ✅ | ✅ Best |

---

## Combining Strategies

### Few-shot + CoT (Hybrid)

**Concept:** Use few-shot examples WITH chain-of-thought reasoning

**Prompt:**
```
Examples:
[3 examples with reasoning steps shown]

Now for your question, let's think step by step:
...
```

**Benefits:**
- Best of both worlds
- Examples guide + explicit reasoning
- Highest accuracy

**Drawbacks:**
- Most expensive (5000+ tokens)
- Slowest

**Usage:**
```bash
# Not directly supported, but can customize templates
# See EXTENDING_SYSTEM.md for custom strategies
```

---

## Configuration Examples

### Quick Baseline (Zero-shot)

```bash
python vipersql.py \
  --strategy zero-shot \
  --model gpt-4o-mini \
  --samples 100
```

### Best Accuracy (Few-shot + ViR2)

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy vir2 \
  --few-shot-examples 5 \
  --model gpt-4o \
  --samples 100
```

### Interpretable (CoT)

```bash
python vipersql.py \
  --strategy cot \
  --model claude-3-5-sonnet-20241022 \
  --temperature 0.5 \
  --max-tokens 2000 \
  --samples 100
```

### Budget-Conscious (Zero-shot + GPT-4o-mini)

```bash
python vipersql.py \
  --strategy zero-shot \
  --model gpt-4o-mini \
  --temperature 0.1 \
  --samples 1000
```

---

## Environment Configuration

### Via .env

```env
# Strategy defaults
DEFAULT_STRATEGY=few-shot
EXAMPLE_SELECTION_STRATEGY=vir2
FEW_SHOT_EXAMPLES=3

# CoT settings
COT_REASONING_STEPS=true

# Model settings
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=1000
```

### Via Command Line (Override .env)

```bash
python vipersql.py \
  --strategy few-shot \
  --model claude-3-5-sonnet-20241022 \
  --temperature 0.7
```

---

## Template Customization

Templates are stored in `templates/`:

```
templates/
├── vietnamese_nl2sql.txt              # Zero-shot
├── few_shot_vietnamese_nl2sql.txt     # Few-shot
├── cot_vietnamese_nl2sql.txt          # Chain-of-thought
└── skill_extraction_vietnamese.txt    # Skill extraction (Skill-KNN)
```

**To customize:**

1. Edit template file
2. Modify variable placeholders: `{question}`, `{schema}`, `{examples}`
3. Restart system (templates loaded at init)

See **[Extending System](EXTENDING_SYSTEM.md)** for custom templates.

---

## Performance Tips

### For Zero-shot

- ✅ Use lower temperature (0.1-0.3)
- ✅ Clear, specific prompts
- ✅ Good schema descriptions

### For Few-shot

- ✅ Use ViR2 selector
- ✅ k=3-5 examples optimal
- ✅ Ensure diverse examples
- ✅ Pre-compute embeddings

### For CoT

- ✅ Use better models (GPT-4o, Claude-3.5)
- ✅ Higher temperature okay (0.5)
- ✅ More max_tokens (2000+)
- ✅ Save reasoning traces for analysis

---

## Troubleshooting

### Zero-shot generates wrong SQL

**Solutions:**
- Improve schema descriptions
- Try few-shot instead
- Lower temperature
- Add schema examples in prompt

### Few-shot not improving accuracy

**Solutions:**
- Check selector quality (try ViR2 if using random)
- Increase k (more examples)
- Ensure training data quality
- Try different selector

### CoT reasoning is incorrect

**Solutions:**
- Use better model (GPT-4o > GPT-4o-mini)
- Adjust prompt to guide reasoning
- Provide reasoning examples
- Check if query is too simple (use few-shot instead)

---

## Related Documentation

- **[Selectors](SELECTORS.md)** - Example selection methods for Few-shot
- **[ViR2 Method](VIR2_METHOD.md)** - Detailed ViR2 algorithm
- **[Configuration](CONFIGURATION.md)** - All configuration parameters
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world usage scenarios

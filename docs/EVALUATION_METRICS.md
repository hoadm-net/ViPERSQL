# Enhanced Evaluation Metrics

## Overview

ViPERSQL goes beyond simple **Exact Match (EM)**, providing **component-wise analysis** and **error categorization** for deeper understanding of model performance.

---

## Metrics Hierarchy

```
Enhanced Evaluation Metrics
│
├── Exact Match (EM)
│   └── Binary: SQL query khớp 100%
│
├── Component-wise F1
│   ├── SELECT clause F1
│   ├── FROM clause F1
│   ├── WHERE clause F1
│   ├── GROUP BY clause F1
│   ├── ORDER BY clause F1
│   ├── HAVING clause F1
│   └── KEYWORDS F1
│
├── Error Analysis
│   ├── Missing clauses
│   ├── Extra clauses
│   ├── Wrong predicates
│   └── Schema errors
│
└── Query Complexity
    ├── Simple
    ├── Moderate
    └── Challenging
```

---

## 1. Exact Match (EM)

### Definition

SQL query prediction matches **exactly 100%** with gold query (after normalization).

### Formula

$$\text{EM} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1}[\text{normalize}(pred_i) = \text{normalize}(gold_i)]$$

where $\mathbb{1}[\cdot]$ is indicator function.

### Normalization Steps

1. **Lowercase:** `SELECT` → `select`
2. **Remove extra whitespace:** `select  *` → `select *`
3. **Standardize quotes:** `"table"` → `'table'`
4. **Sort clauses:** Đảm bảo thứ tự consistent
5. **Remove trailing semicolon:** `select * from t;` → `select * from t`

### Limitations

- ❌ Binary (all-or-nothing)
- ❌ Does not show WHERE model fails
- ❌ Does not distinguish minor vs major errors
- ❌ Semantically equivalent queries scored as wrong

**Example:**
```sql
Predicted: SELECT name FROM students WHERE age > 18
Gold:      SELECT name FROM students WHERE 18 < age
```
→ EM = 0 (mặc dù semantically equivalent)

---

## 2. Component-wise F1 Scores

### Concept

Evaluates **each component** of SQL query separately.

### SQL Components

1. **SELECT** - Columns to retrieve
2. **FROM** - Tables involved
3. **WHERE** - Filter conditions
4. **GROUP BY** - Grouping columns
5. **ORDER BY** - Sorting columns
6. **HAVING** - Group filters
7. **KEYWORDS** - SQL operations (DISTINCT, JOIN, etc.)

### Extraction Method

**Example Query:**
```sql
SELECT DISTINCT s.name, AVG(g.score) 
FROM students s 
JOIN grades g ON s.id = g.student_id 
WHERE s.class = '10A' 
GROUP BY s.name 
HAVING AVG(g.score) > 8.0
```

**Extracted Components:**

```python
{
  "SELECT": {"s.name", "AVG(g.score)"},
  "FROM": {"students", "grades"},
  "WHERE": {"s.class = '10A'"},
  "GROUP BY": {"s.name"},
  "HAVING": {"AVG(g.score) > 8.0"},
  "KEYWORDS": {"DISTINCT", "JOIN", "AVG"}
}
```

### F1 Calculation

For each component:

$$\text{Precision} = \frac{|pred \cap gold|}{|pred|}$$

$$\text{Recall} = \frac{|pred \cap gold|}{|gold|}$$

$$F1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### Example

**Predicted SELECT:** `{s.name, s.age}`  
**Gold SELECT:** `{s.name, AVG(g.score)}`

$$\text{Precision} = \frac{1}{2} = 0.5$$

$$\text{Recall} = \frac{1}{2} = 0.5$$

$$F1_{\text{SELECT}} = 2 \cdot \frac{0.5 \cdot 0.5}{0.5 + 0.5} = 0.5$$

### Aggregate F1

$$\text{Avg-F1} = \frac{1}{C} \sum_{c \in \text{components}} F1_c$$

where $C$ = number of components with at least one element.

---

## 3. Error Analysis

### Error Categories

#### Missing Clauses

**Definition:** Gold query has clause but predicted does not.

**Example:**
```sql
Predicted: SELECT name FROM students
Gold:      SELECT name FROM students WHERE age > 18
```
→ Missing WHERE clause

#### Extra Clauses

**Definition:** Predicted has unnecessary clause.

**Example:**
```sql
Predicted: SELECT name FROM students ORDER BY name
Gold:      SELECT name FROM students
```
→ Extra ORDER BY clause

#### Wrong Predicates

**Definition:** Clause present but conditions are incorrect.

**Example:**
```sql
Predicted: WHERE age > 20
Gold:      WHERE age > 18
```
→ Wrong predicate value

#### Schema Errors

**Definition:** Incorrect table or column names used.

**Example:**
```sql
Predicted: SELECT student_name FROM pupils
Gold:      SELECT name FROM students
```
→ Wrong table name, wrong column name

### Error Statistics

```python
{
  "missing_clauses": {
    "WHERE": 15,
    "GROUP BY": 8,
    "HAVING": 3
  },
  "extra_clauses": {
    "ORDER BY": 5
  },
  "wrong_predicates": 22,
  "schema_errors": 10
}
```

---

## 4. Query Complexity Classification

### Complexity Levels

#### Simple Queries

**Characteristics:**
- Single table
- Basic SELECT
- Simple WHERE (0-2 conditions)
- No JOINs, no aggregations

**Example:**
```sql
SELECT name FROM students WHERE class = '10A'
```

#### Moderate Queries

**Characteristics:**
- 2-3 tables
- Simple JOINs
- Basic aggregations (COUNT, SUM, AVG)
- GROUP BY without HAVING

**Example:**
```sql
SELECT s.class, COUNT(*) 
FROM students s 
JOIN grades g ON s.id = g.student_id 
GROUP BY s.class
```

#### Challenging Queries

**Characteristics:**
- 3+ tables
- Multiple JOINs
- Complex aggregations
- Nested queries
- HAVING clauses

**Example:**
```sql
SELECT s.name, AVG(g.score)
FROM students s
JOIN grades g ON s.id = g.student_id
JOIN courses c ON g.course_id = c.id
WHERE c.department = 'Math'
GROUP BY s.name
HAVING AVG(g.score) > (SELECT AVG(score) FROM grades)
```

### Performance by Complexity

```python
{
  "simple": {
    "count": 100,
    "em_accuracy": 0.85,
    "avg_f1": 0.92
  },
  "moderate": {
    "count": 80,
    "em_accuracy": 0.65,
    "avg_f1": 0.78
  },
  "challenging": {
    "count": 20,
    "em_accuracy": 0.30,
    "avg_f1": 0.55
  }
}
```

---

## Evaluation Pipeline

### Single Query Evaluation

```
Input: predicted_sql, gold_sql, db_id, schema_path

1. Normalize both queries
2. Check Exact Match
3. Extract components from both
4. Compute component-wise F1
5. Analyze errors
6. Classify complexity
7. Return metrics dict
```

### Batch Evaluation

```
Input: List of predictions, schema_path

1. For each prediction:
     Evaluate single query
2. Aggregate metrics:
   - Overall EM accuracy
   - Average component F1
   - Error statistics
   - Complexity breakdown
3. Generate report
```

---

## Output Format

### Single Query Result

```json
{
  "request_id": "q_001",
  "db_id": "academic",
  "predicted_sql": "SELECT name FROM students WHERE age > 18",
  "gold_sql": "SELECT name FROM students WHERE age >= 18",
  "exact_match": false,
  "syntax_valid": true,
  "avg_f1": 0.92,
  "f1_scores": {
    "SELECT": 1.0,
    "FROM": 1.0,
    "WHERE": 0.67,
    "GROUP BY": null,
    "ORDER BY": null,
    "HAVING": null,
    "KEYWORDS": 1.0
  },
  "details": {
    "error_analysis": {
      "missing_clauses": [],
      "extra_clauses": [],
      "wrong_predicates": ["age > 18 vs age >= 18"]
    },
    "query_complexity": "simple"
  }
}
```

### Batch Result

```json
{
  "metadata": {
    "total_queries": 200,
    "timestamp": "2025-12-01T10:30:00",
    "dataset": "ViText2SQL std-level dev"
  },
  "overall_metrics": {
    "exact_match_accuracy": 0.72,
    "avg_f1": 0.84,
    "syntax_valid_rate": 0.98
  },
  "component_f1": {
    "SELECT": 0.91,
    "FROM": 0.93,
    "WHERE": 0.78,
    "GROUP BY": 0.71,
    "ORDER BY": 0.85,
    "HAVING": 0.62,
    "KEYWORDS": 0.88
  },
  "error_statistics": {
    "missing_clauses": 45,
    "extra_clauses": 12,
    "wrong_predicates": 38,
    "schema_errors": 18
  },
  "complexity_breakdown": {
    "simple": {"count": 120, "em": 0.85, "f1": 0.92},
    "moderate": {"count": 60, "em": 0.65, "f1": 0.78},
    "challenging": {"count": 20, "em": 0.30, "f1": 0.55}
  }
}
```

---

## Usage

### Command Line

```bash
# Basic evaluation (automatic)
python vipersql.py --strategy few-shot --samples 100

# Results saved to: results/few-shot-vir2_100_TIMESTAMP/
```

### Results Structure

```
results/few-shot-vir2_100_20251201_103000/
├── predictions.json          # All predictions
├── eval_results.json         # Detailed metrics
└── eval_report.txt          # Human-readable summary
```

### Reading Results

**predictions.json:**
```json
{
  "predictions": [
    {
      "db_id": "academic",
      "question": "...",
      "predicted": "SELECT ...",
      "gold": "SELECT ..."
    }
  ]
}
```

**eval_results.json:**
- Full metrics (as shown in Batch Result above)

**eval_report.txt:**
```
=== Evaluation Report ===
Total Queries: 200
Exact Match Accuracy: 72.0%
Average F1 Score: 84.0%

Component F1 Scores:
- SELECT: 91.0%
- FROM: 93.0%
- WHERE: 78.0%
...

Error Analysis:
- Missing clauses: 45
- Extra clauses: 12
...
```

---

## Interpreting Results

### High EM, High F1

✅ **Excellent** - Model performs well

### Low EM, High F1

⚠️ **Minor errors** - Model gets structure right, small mistakes

**Action:** Check error analysis for patterns

### Low EM, Low F1

❌ **Poor performance** - Fundamental issues

**Actions:**
- Check training data quality
- Try different selector
- Improve prompts
- Use better model

### Component-wise Analysis

**High SELECT F1, Low WHERE F1:**
- Model good at identifying columns
- Struggles with conditions

**Low FROM F1:**
- Schema understanding issues
- Need better schema descriptions

**Low GROUP BY/HAVING F1:**
- Complexity too high
- Need more aggregation examples

---

## Comparison with Baselines

### Standard Metrics

- **Exact Match (EM)** - Standard
- **Execution Accuracy (EX)** - Run query, compare results (requires DB)

### ViPERSQL Enhanced Metrics

- ✅ Component F1 - **Detailed breakdown**
- ✅ Error analysis - **Understand failures**
- ✅ Complexity analysis - **Performance by difficulty**
- ✅ Syntax validation - **Catch parse errors**

---

## Configuration

### Enable/Disable Components

```env
# .env configuration
ENABLE_COMPONENT_ANALYSIS=true
ENABLE_ERROR_ANALYSIS=true
EVALUATION_TIMEOUT=30
```

### Schema Path

```bash
# Specify schema for evaluation
python vipersql.py \
  --schema-path dataset/ViText2SQL/std-level/tables.json \
  --samples 100
```

---

## Advanced Features

### Per-Database Analysis

```json
{
  "database_breakdown": {
    "academic": {"em": 0.75, "f1": 0.85},
    "scholar": {"em": 0.68, "f1": 0.80},
    "world_1": {"em": 0.72, "f1": 0.83}
  }
}
```

### SQL Type Analysis

```json
{
  "sql_type_breakdown": {
    "SELECT_only": {"count": 50, "em": 0.90},
    "SELECT_WHERE": {"count": 80, "em": 0.75},
    "JOIN": {"count": 40, "em": 0.60},
    "AGGREGATION": {"count": 30, "em": 0.55}
  }
}
```

---

## Troubleshooting

### Evaluation too slow

**Solutions:**
- Reduce samples
- Disable detailed error analysis
- Increase evaluation timeout

### Inconsistent F1 scores

**Causes:**
- Component extraction issues
- Normalization differences

**Solutions:**
- Check SQL parsing
- Verify schema paths
- Review normalization logic

### Schema errors high

**Solutions:**
- Improve schema descriptions
- Add schema examples in prompts
- Check database coverage in training

---

## Related Documentation

- **[Strategies](STRATEGIES.md)** - Different generation approaches
- **[Selectors](SELECTORS.md)** - Example selection impact on accuracy
- **[Configuration](CONFIGURATION.md)** - Evaluation parameters
- **[Quick Start](QUICKSTART.md)** - Running evaluations

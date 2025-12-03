# API Reference

## Core Modules

Complete API documentation for ViPERSQL core modules.

---

## mint.core.llm_interface

### Class: LLMInterface

Interface for LLM models (OpenAI, Anthropic).

```python
class LLMInterface:
    """Interface for language model interactions."""
```

#### Constructor

```python
def __init__(
    self,
    model_name: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 1000,
    timeout: int = 60,
    **kwargs
) -> None
```

**Parameters:**
- `model_name` (str): Model identifier
  - OpenAI: `gpt-4o`, `gpt-4o-mini`
  - Anthropic: `claude-3-5-sonnet-20241022`
- `temperature` (float): Sampling temperature ∈ [0, 1]
- `max_tokens` (int): Maximum response tokens
- `timeout` (int): Request timeout (seconds)

**Example:**

```python
from mint.core.llm_interface import LLMInterface

llm = LLMInterface(
    model_name="gpt-4o",
    temperature=0.3,
    max_tokens=1000
)
```

#### Methods

##### generate()

```python
def generate(
    self,
    messages: List[Dict[str, str]],
    **kwargs
) -> str
```

Generate response from LLM.

**Parameters:**
- `messages` (List[Dict]): Message list
  ```python
  [
      {"role": "system", "content": "You are..."},
      {"role": "user", "content": "Question..."}
  ]
  ```

**Returns:**
- `str`: Model response

**Raises:**
- `APIError`: API request failed
- `TimeoutError`: Request timeout

**Example:**

```python
messages = [
    {"role": "system", "content": "You are an SQL expert."},
    {"role": "user", "content": "Generate SQL for: How many users?"}
]

response = llm.generate(messages)
print(response)  # "SELECT COUNT(*) FROM users"
```

##### generate_with_retry()

```python
def generate_with_retry(
    self,
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    retry_delay: int = 5,
    **kwargs
) -> str
```

Generate with automatic retry on failure.

**Parameters:**
- `messages`: Same as `generate()`
- `max_retries` (int): Maximum retry attempts
- `retry_delay` (int): Delay between retries (seconds)

**Returns:**
- `str`: Model response

**Example:**

```python
response = llm.generate_with_retry(
    messages=messages,
    max_retries=5,
    retry_delay=10
)
```

---

## mint.strategies

### Base Class: BaseStrategy

```python
class BaseStrategy(ABC):
    """Abstract base class for SQL generation strategies."""
```

#### Constructor

```python
def __init__(
    self,
    llm_interface: LLMInterface,
    template_manager: TemplateManager,
    **kwargs
) -> None
```

#### Abstract Methods

##### generate_sql()

```python
@abstractmethod
def generate_sql(
    self,
    question: str,
    db_id: str,
    schema: str,
    **kwargs
) -> Dict[str, Any]
```

Generate SQL from natural language.

**Parameters:**
- `question` (str): Natural language question
- `db_id` (str): Database identifier
- `schema` (str): Database schema (DDL)
- `**kwargs`: Additional context (examples, hints, etc.)

**Returns:**
```python
{
    'sql': str,           # Generated SQL
    'reasoning': str,     # Optional reasoning steps
    'metadata': dict      # Strategy-specific metadata
}
```

---

### Class: ZeroShotStrategy

```python
class ZeroShotStrategy(BaseStrategy):
    """Direct translation without examples."""
```

**Usage:**

```python
from mint.strategies import get_strategy

strategy = get_strategy('zero-shot', llm_interface=llm, template_manager=tm)

result = strategy.generate_sql(
    question="How many employees?",
    db_id="company",
    schema="CREATE TABLE employees (id INT, name TEXT)"
)

print(result['sql'])
```

---

### Class: FewShotStrategy

```python
class FewShotStrategy(BaseStrategy):
    """SQL generation with in-context examples."""
```

#### Constructor

```python
def __init__(
    self,
    llm_interface: LLMInterface,
    template_manager: TemplateManager,
    example_selector: BaseSelector,
    k: int = 3,
    **kwargs
) -> None
```

**Parameters:**
- `example_selector` (BaseSelector): Example selector
- `k` (int): Number of examples to use

#### Methods

##### generate_sql()

```python
def generate_sql(
    self,
    question: str,
    db_id: str,
    schema: str,
    **kwargs
) -> Dict[str, Any]
```

**Example:**

```python
from mint.strategies import get_strategy
from mint.selectors import get_selector

selector = get_selector('vir2', training_data=train_data)

strategy = get_strategy(
    'few-shot',
    llm_interface=llm,
    template_manager=tm,
    example_selector=selector,
    k=3
)

result = strategy.generate_sql(
    question="What is the average salary?",
    db_id="company",
    schema="CREATE TABLE employees ..."
)
```

---

### Class: CoTStrategy

```python
class CoTStrategy(BaseStrategy):
    """Chain-of-Thought reasoning strategy."""
```

**Usage:**

```python
strategy = get_strategy('cot', llm_interface=llm, template_manager=tm)

result = strategy.generate_sql(
    question="Find employees earning above company average",
    db_id="company",
    schema="CREATE TABLE employees (id INT, salary FLOAT)"
)

print(result['reasoning'])  # Step-by-step reasoning
print(result['sql'])
```

---

## mint.selectors

### Base Class: BaseSelector

```python
class BaseSelector(ABC):
    """Abstract base class for example selectors."""
```

#### Constructor

```python
def __init__(
    self,
    training_data: List[Dict[str, Any]],
    **kwargs
) -> None
```

**Parameters:**
- `training_data`: List of training examples
  ```python
  [
      {
          'question': str,
          'sql': str,
          'db_id': str,
          'schema': str  # optional
      },
      ...
  ]
  ```

#### Abstract Methods

##### select_examples()

```python
@abstractmethod
def select_examples(
    self,
    query: str,
    db_id: str,
    k: int = 3,
    **kwargs
) -> List[Dict[str, Any]]
```

Select k most relevant examples.

**Parameters:**
- `query` (str): Natural language question
- `db_id` (str): Database identifier
- `k` (int): Number of examples to select

**Returns:**
- `List[Dict]`: Selected examples (same format as training_data)

---

### Class: RandomSelector

```python
class RandomSelector(BaseSelector):
    """Random example selection."""
```

**Complexity:** $O(k)$

**Usage:**

```python
from mint.selectors import get_selector

selector = get_selector('random', training_data=train_data)

examples = selector.select_examples(
    query="How many users?",
    db_id="app",
    k=3
)
```

---

### Class: DICLSelector

```python
class DICLSelector(BaseSelector):
    """Semantic similarity-based selection using BERT."""
```

**Complexity:** $O(n)$ where $n$ = training set size

#### Constructor

```python
def __init__(
    self,
    training_data: List[Dict[str, Any]],
    model_name: str = "google-bert/bert-base-uncased",
    **kwargs
) -> None
```

**Parameters:**
- `model_name` (str): BERT model identifier

**Usage:**

```python
selector = get_selector(
    'dicl',
    training_data=train_data,
    model_name="google-bert/bert-base-uncased"
)

examples = selector.select_examples(query, db_id, k=3)
```

---

### Class: ViR2Selector

```python
class ViR2Selector(BaseSelector):
    """
    Two-stage ViR2 selection:
    1. Semantic retrieval (PhoBERT/BERT)
    2. Beam search (POS + diversity)
    """
```

**Complexity:** $O(n + M \cdot B \cdot k)$ where:
- $n$ = training set size
- $M$ = candidate pool size
- $B$ = beam size
- $k$ = final examples

#### Constructor

```python
def __init__(
    self,
    training_data: List[Dict[str, Any]],
    language: str = "vi",
    candidate_pool_size: int = 50,
    beam_size: int = 5,
    diversity_weight: float = 0.3,
    **kwargs
) -> None
```

**Parameters:**
- `language` (str): `'vi'` (PhoBERT) or `'en'` (BERT)
- `candidate_pool_size` (int): Stage 1 pool size $M$
- `beam_size` (int): Beam search width $B$
- `diversity_weight` (float): Diversity weight $\lambda \in [0, 1]$

**Scoring Formula:**

$$
\text{Score}(E, q) = \text{POS_Score}(E, q) + \lambda \cdot \text{Diversity}(E)
$$

where:

$$
\text{POS_Score}(E, q) = \frac{1}{|E|} \sum_{e \in E} \frac{|\text{POS}(e) \cap \text{POS}(q)|}{|\text{POS}(q)|}
$$

$$
\text{Diversity}(E) = \frac{2}{|E|(|E|-1)} \sum_{i<j} (1 - \text{sim}(e_i, e_j))
$$

**Usage:**

```python
selector = get_selector(
    'vir2',
    training_data=train_data,
    language='vi',
    candidate_pool_size=50,
    beam_size=5,
    diversity_weight=0.3
)

examples = selector.select_examples(
    query="Có bao nhiêu nhân viên?",
    db_id="company",
    k=3
)
```

---

### Class: MultiLangViR2Selector

```python
class MultiLangViR2Selector(ViR2Selector):
    """Multi-language ViR2 with auto language detection."""
```

#### Constructor

```python
def __init__(
    self,
    training_data: List[Dict[str, Any]],
    auto_detect_language: bool = True,
    **kwargs
) -> None
```

**Parameters:**
- `auto_detect_language` (bool): Auto-detect query language

**Usage:**

```python
selector = get_selector(
    'multilang-vir2',
    training_data=train_data,
    auto_detect_language=True
)

# Vietnamese query
examples_vi = selector.select_examples("Có bao nhiêu nhân viên?", "company", k=3)

# English query
examples_en = selector.select_examples("How many employees?", "company", k=3)
```

---

## mint.core.evaluator

### Class: Evaluator

```python
class Evaluator:
    """Comprehensive SQL evaluation."""
```

#### Constructor

```python
def __init__(
    self,
    db_path: Optional[str] = None,
    enable_execution: bool = True,
    enable_component_analysis: bool = True,
    enable_error_analysis: bool = True,
    **kwargs
) -> None
```

**Parameters:**
- `db_path` (str): Path to database for execution accuracy
- `enable_execution` (bool): Enable execution accuracy (EX)
- `enable_component_analysis` (bool): Enable component F1
- `enable_error_analysis` (bool): Enable error categorization

#### Methods

##### evaluate_single()

```python
def evaluate_single(
    self,
    pred_sql: str,
    gold_sql: str,
    db_id: str,
    **kwargs
) -> Dict[str, Any]
```

Evaluate single prediction.

**Parameters:**
- `pred_sql` (str): Predicted SQL
- `gold_sql` (str): Ground truth SQL
- `db_id` (str): Database identifier

**Returns:**

```python
{
    'exact_match': bool,
    'avg_f1': float,
    'component_f1': {
        'SELECT': float,
        'FROM': float,
        'WHERE': float,
        'GROUP BY': float,
        'ORDER BY': float,
        'HAVING': float,
        'KEYWORDS': float
    },
    'execution_accuracy': bool,  # if enabled
    'error_type': str,           # if error occurred
    'query_complexity': str      # 'simple', 'medium', 'complex'
}
```

**Example:**

```python
from mint.core.evaluator import Evaluator

evaluator = Evaluator(
    db_path="databases/",
    enable_execution=True,
    enable_component_analysis=True
)

result = evaluator.evaluate_single(
    pred_sql="SELECT COUNT(*) FROM employees WHERE dept='IT'",
    gold_sql="SELECT COUNT(*) FROM employees WHERE dept='IT'",
    db_id="company"
)

print(f"Exact Match: {result['exact_match']}")
print(f"Avg F1: {result['avg_f1']:.3f}")
print(f"Component F1: {result['component_f1']}")
```

##### evaluate_batch()

```python
def evaluate_batch(
    self,
    predictions: List[Dict[str, Any]],
    **kwargs
) -> Dict[str, Any]
```

Evaluate batch of predictions.

**Parameters:**
- `predictions`: List of predictions
  ```python
  [
      {
          'pred_sql': str,
          'gold_sql': str,
          'db_id': str
      },
      ...
  ]
  ```

**Returns:**

```python
{
    'overall_metrics': {
        'exact_match_accuracy': float,
        'avg_f1': float,
        'execution_accuracy': float
    },
    'component_f1': {
        'SELECT': float,
        'FROM': float,
        ...
    },
    'error_statistics': {
        'syntax_error': int,
        'logical_error': int,
        'schema_error': int,
        'join_error': int,
        'aggregation_error': int
    },
    'complexity_breakdown': {
        'simple': {'count': int, 'em': float, 'f1': float},
        'medium': {...},
        'complex': {...}
    }
}
```

**Example:**

```python
predictions = [
    {
        'pred_sql': "SELECT * FROM users",
        'gold_sql': "SELECT * FROM users WHERE active=1",
        'db_id': "app"
    },
    # ... more predictions
]

results = evaluator.evaluate_batch(predictions)

print(f"Overall EM: {results['overall_metrics']['exact_match_accuracy']:.3f}")
print(f"Overall F1: {results['overall_metrics']['avg_f1']:.3f}")
```

---

## mint.metrics.enhanced_metrics

### Functions

#### compute_exact_match()

```python
def compute_exact_match(
    pred_sql: str,
    gold_sql: str,
    normalize: bool = True
) -> bool
```

Compute exact match between SQL queries.

**Parameters:**
- `pred_sql` (str): Predicted SQL
- `gold_sql` (str): Ground truth SQL
- `normalize` (bool): Apply normalization (lowercase, whitespace)

**Returns:**
- `bool`: True if exact match

**Example:**

```python
from mint.metrics.enhanced_metrics import compute_exact_match

em = compute_exact_match(
    pred_sql="SELECT * FROM users",
    gold_sql="SELECT * FROM users"
)
print(em)  # True
```

#### compute_component_f1()

```python
def compute_component_f1(
    pred_sql: str,
    gold_sql: str
) -> Dict[str, Any]
```

Compute component-wise F1 scores.

**Parameters:**
- `pred_sql` (str): Predicted SQL
- `gold_sql` (str): Ground truth SQL

**Returns:**

```python
{
    'avg_f1': float,          # Average F1 across components
    'component_f1': {
        'SELECT': float,      # F1 for SELECT clause
        'FROM': float,        # F1 for FROM clause
        'WHERE': float,       # F1 for WHERE clause
        'GROUP BY': float,    # F1 for GROUP BY
        'ORDER BY': float,    # F1 for ORDER BY
        'HAVING': float,      # F1 for HAVING
        'KEYWORDS': float     # F1 for SQL keywords
    }
}
```

**Formula:**

$$
F1 = \frac{2 \cdot P \cdot R}{P + R}
$$

where:

$$
P = \frac{|\text{Pred} \cap \text{Gold}|}{|\text{Pred}|}
$$

$$
R = \frac{|\text{Pred} \cap \text{Gold}|}{|\text{Gold}|}
$$

**Example:**

```python
from mint.metrics.enhanced_metrics import compute_component_f1

f1 = compute_component_f1(
    pred_sql="SELECT name FROM employees WHERE dept='IT'",
    gold_sql="SELECT name, age FROM employees WHERE dept='IT'"
)

print(f"Avg F1: {f1['avg_f1']:.3f}")
print(f"SELECT F1: {f1['component_f1']['SELECT']:.3f}")
print(f"WHERE F1: {f1['component_f1']['WHERE']:.3f}")
```

#### compute_execution_accuracy()

```python
def compute_execution_accuracy(
    pred_sql: str,
    gold_sql: str,
    db_path: str,
    db_id: str
) -> bool
```

Execute both queries and compare results.

**Parameters:**
- `pred_sql` (str): Predicted SQL
- `gold_sql` (str): Ground truth SQL
- `db_path` (str): Path to database directory
- `db_id` (str): Database identifier

**Returns:**
- `bool`: True if execution results match

**Example:**

```python
from mint.metrics.enhanced_metrics import compute_execution_accuracy

ex = compute_execution_accuracy(
    pred_sql="SELECT COUNT(*) FROM users",
    gold_sql="SELECT COUNT(*) FROM users WHERE active=1",
    db_path="databases/",
    db_id="app"
)
print(ex)  # False (different results)
```

---

## mint.core.template_manager

### Class: TemplateManager

```python
class TemplateManager:
    """Manage prompt templates."""
```

#### Constructor

```python
def __init__(self, template_dir: str = "templates") -> None
```

**Parameters:**
- `template_dir` (str): Directory containing templates

#### Methods

##### load_template()

```python
def load_template(self, template_name: str) -> str
```

Load template from file.

**Parameters:**
- `template_name` (str): Template name (without .txt extension)

**Returns:**
- `str`: Template content

**Example:**

```python
from mint.core.template_manager import TemplateManager

tm = TemplateManager(template_dir="templates")

template = tm.load_template("few_shot_vietnamese_nl2sql")
print(template)
```

##### format_template()

```python
def format_template(
    self,
    template: str,
    **kwargs
) -> str
```

Fill template with variables.

**Parameters:**
- `template` (str): Template string
- `**kwargs`: Template variables

**Returns:**
- `str`: Filled template

**Example:**

```python
filled = tm.format_template(
    template="{question}\n{schema}",
    question="How many users?",
    schema="CREATE TABLE users (id INT)"
)
```

---

## mint.config

### Class: ViPERConfig

```python
class ViPERConfig:
    """Global configuration."""
```

**Attributes:**

```python
# Model settings
DEFAULT_MODEL: str = "gpt-4o"
DEFAULT_TEMPERATURE: float = 0.3
DEFAULT_MAX_TOKENS: int = 1000

# Strategy settings
DEFAULT_STRATEGY: str = "zero-shot"
EXAMPLE_SELECTION_STRATEGY: str = "random"
FEW_SHOT_EXAMPLES: int = 3

# ViR2 settings
VIR2_CANDIDATE_POOL_SIZE: int = 50
VIR2_BEAM_SIZE: int = 5
VIR2_DIVERSITY_WEIGHT: float = 0.3

# Dataset settings
DATASET_PATH: str = "dataset/ViText2SQL"
DEFAULT_SPLIT: str = "dev"
DEFAULT_LEVEL: str = "std"

# Output settings
RESULTS_DIR: str = "results"
```

**Usage:**

```python
from mint.config import ViPERConfig

config = ViPERConfig()

print(config.DEFAULT_MODEL)  # "gpt-4o"
print(config.VIR2_BEAM_SIZE)  # 5
```

---

## Utility Functions

### mint.utils.language_detection

#### detect_language()

```python
def detect_language(text: str) -> str
```

Detect language from text.

**Parameters:**
- `text` (str): Input text

**Returns:**
- `str`: Language code (`'vi'`, `'en'`, etc.)

**Example:**

```python
from mint.utils.language_detection import detect_language

lang = detect_language("Có bao nhiêu nhân viên?")
print(lang)  # "vi"

lang = detect_language("How many employees?")
print(lang)  # "en"
```

---

### mint.utils.sql_parser

#### normalize_sql()

```python
def normalize_sql(sql: str) -> str
```

Normalize SQL query.

**Parameters:**
- `sql` (str): SQL query

**Returns:**
- `str`: Normalized SQL (lowercase, whitespace removed)

**Example:**

```python
from mint.utils.sql_parser import normalize_sql

normalized = normalize_sql("SELECT   * FROM   users")
print(normalized)  # "select * from users"
```

#### parse_sql_components()

```python
def parse_sql_components(sql: str) -> Dict[str, List[str]]
```

Parse SQL into components.

**Parameters:**
- `sql` (str): SQL query

**Returns:**

```python
{
    'SELECT': [...],
    'FROM': [...],
    'WHERE': [...],
    'GROUP BY': [...],
    'ORDER BY': [...],
    'HAVING': [...]
}
```

**Example:**

```python
from mint.utils.sql_parser import parse_sql_components

components = parse_sql_components(
    "SELECT name FROM users WHERE age > 30"
)

print(components['SELECT'])  # ['name']
print(components['FROM'])    # ['users']
print(components['WHERE'])   # ['age > 30']
```

---

## Error Handling

All modules raise standard exceptions:

- `ValueError`: Invalid parameters
- `FileNotFoundError`: Missing files (datasets, templates)
- `APIError`: LLM API errors
- `TimeoutError`: Request timeouts

**Example:**

```python
from mint.core.llm_interface import LLMInterface

try:
    llm = LLMInterface(model_name="invalid-model")
    response = llm.generate(messages)
except ValueError as e:
    print(f"Invalid model: {e}")
except APIError as e:
    print(f"API error: {e}")
except TimeoutError as e:
    print(f"Timeout: {e}")
```

---

## Type Definitions

### Common Types

```python
from typing import List, Dict, Any, Optional

# Training example
TrainingExample = Dict[str, Any]
# {
#     'question': str,
#     'sql': str,
#     'db_id': str,
#     'schema': Optional[str]
# }

# Prediction
Prediction = Dict[str, Any]
# {
#     'pred_sql': str,
#     'gold_sql': str,
#     'db_id': str
# }

# Evaluation result
EvaluationResult = Dict[str, Any]
# {
#     'exact_match': bool,
#     'avg_f1': float,
#     'component_f1': Dict[str, float],
#     ...
# }
```

---

## Related Documentation

- **[Quick Start](QUICKSTART.md)** - Get started
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real examples
- **[Configuration](CONFIGURATION.md)** - All settings
- **[Extending System](EXTENDING_SYSTEM.md)** - Add new components

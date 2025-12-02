# Extending the System

## Overview

Guide to extending ViPERSQL with custom components: strategies, selectors, evaluators, metrics.

**Architecture:** Strategy pattern for high modularity and extensibility.

---

## System Extension Points

ViPERSQL has 4 main extension points:

1. **Strategies** - SQL generation approaches (zero-shot, few-shot, CoT)
2. **Selectors** - Example selection methods (random, DICL, ViR2, etc.)
3. **Evaluators** - Custom evaluation logic
4. **Metrics** - Additional evaluation metrics

---

## 1. Adding a New Strategy

### Step 1: Create Strategy File

Create a new file in `mint/strategies/`:

```python
# mint/strategies/my_custom_strategy.py

from typing import Dict, Any, List
from langchain.schema import HumanMessage, SystemMessage
from mint.strategies.base_strategy import BaseStrategy
from mint.core.template_manager import TemplateManager
from mint.core.llm_interface import LLMInterface

class MyCustomStrategy(BaseStrategy):
    """
    Custom strategy: Brief description of approach.
    
    Example: Few-shot with schema-first prompting.
    """
    
    def __init__(
        self,
        llm_interface: LLMInterface,
        template_manager: TemplateManager,
        **kwargs
    ):
        """Initialize strategy."""
        super().__init__(llm_interface, template_manager)
        
        # Strategy-specific parameters
        self.custom_param = kwargs.get('custom_param', 'default_value')
    
    def generate_sql(
        self,
        question: str,
        db_id: str,
        schema: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate SQL for given question.
        
        Args:
            question: Natural language question
            db_id: Database identifier
            schema: Database schema
            **kwargs: Additional context (e.g., examples, hints)
        
        Returns:
            {
                'sql': 'SELECT ...',
                'reasoning': 'Optional reasoning steps',
                'metadata': {...}
            }
        """
        # 1. Build prompt
        prompt = self._build_prompt(question, db_id, schema, **kwargs)
        
        # 2. Call LLM
        response = self.llm_interface.generate(prompt)
        
        # 3. Parse SQL from response
        sql = self._extract_sql(response)
        
        # 4. Return result
        return {
            'sql': sql,
            'reasoning': response,  # Full response for debugging
            'metadata': {
                'strategy': 'my_custom',
                'custom_param': self.custom_param,
                'token_count': len(response)
            }
        }
    
    def _build_prompt(
        self,
        question: str,
        db_id: str,
        schema: str,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Build LLM prompt messages."""
        
        # Load template (create templates/my_custom.txt)
        template = self.template_manager.load_template('my_custom')
        
        # Fill template
        user_prompt = template.format(
            question=question,
            db_id=db_id,
            schema=schema,
            custom_context=self._build_custom_context(**kwargs)
        )
        
        return [
            SystemMessage(content="You are an expert SQL generator."),
            HumanMessage(content=user_prompt)
        ]
    
    def _build_custom_context(self, **kwargs) -> str:
        """Build strategy-specific context."""
        # Example: Add schema description first
        context = "## Database Schema Analysis\n\n"
        context += kwargs.get('schema_summary', '')
        context += "\n\n## Question\n\n"
        return context
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response."""
        # Parse SQL from markdown code blocks
        import re
        match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: return full response
        return response.strip()
```

---

### Step 2: Create Template

Tạo `templates/my_custom.txt`:

```text
## Database Schema

Database: {db_id}

{schema}

---

{custom_context}

{question}

## Instructions

1. Analyze schema structure carefully
2. Identify relevant tables and columns
3. Generate accurate SQL query

Return SQL in markdown code block:

```sql
SELECT ...
```
```

---

### Step 3: Register Strategy

Update `mint/strategies/__init__.py`:

```python
from mint.strategies.zero_shot_strategy import ZeroShotStrategy
from mint.strategies.few_shot_strategy import FewShotStrategy
from mint.strategies.cot_strategy import CoTStrategy
from mint.strategies.my_custom_strategy import MyCustomStrategy  # Add this

STRATEGY_REGISTRY = {
    'zero-shot': ZeroShotStrategy,
    'few-shot': FewShotStrategy,
    'cot': CoTStrategy,
    'my-custom': MyCustomStrategy,  # Add this
}

def get_strategy(name: str, **kwargs):
    """Get strategy instance by name."""
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGY_REGISTRY[name](**kwargs)
```

---

### Step 4: Use Strategy

```bash
python vipersql.py \
  --strategy my-custom \
  --samples 100
```

Or programmatically:

```python
from mint.strategies import get_strategy

strategy = get_strategy(
    'my-custom',
    llm_interface=llm,
    template_manager=tm,
    custom_param='value'
)

result = strategy.generate_sql(
    question="How many employees?",
    db_id="company",
    schema="CREATE TABLE employees ..."
)
```

---

## 2. Adding a New Selector

### Step 1: Create Selector File

Tạo `mint/selectors/my_custom_selector.py`:

```python
# mint/selectors/my_custom_selector.py

from typing import List, Dict, Any
from mint.selectors.base_selector import BaseSelector

class MyCustomSelector(BaseSelector):
    """
    Custom example selector: Brief description.
    
    Example: Select examples based on query complexity.
    """
    
    def __init__(self, training_data: List[Dict[str, Any]], **kwargs):
        """
        Initialize selector.
        
        Args:
            training_data: List of training examples
                [{'question': ..., 'sql': ..., 'db_id': ...}, ...]
            **kwargs: Additional parameters
        """
        super().__init__(training_data)
        
        # Custom parameters
        self.complexity_weight = kwargs.get('complexity_weight', 0.5)
        
        # Preprocess training data
        self._preprocess()
    
    def _preprocess(self):
        """Precompute features for fast selection."""
        # Example: Compute query complexity
        self.complexities = []
        for example in self.training_data:
            complexity = self._compute_complexity(example['sql'])
            self.complexities.append(complexity)
    
    def select_examples(
        self,
        query: str,
        db_id: str,
        k: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Select k most relevant examples.
        
        Args:
            query: Natural language question
            db_id: Database identifier
            k: Number of examples to select
        
        Returns:
            List of k selected examples
        """
        # 1. Compute query complexity
        query_complexity = self._compute_complexity_from_text(query)
        
        # 2. Score all examples
        scores = []
        for i, example in enumerate(self.training_data):
            # Filter by database (optional)
            if example['db_id'] != db_id:
                continue
            
            # Compute score based on complexity similarity
            complexity_diff = abs(query_complexity - self.complexities[i])
            score = 1.0 / (1.0 + complexity_diff)
            
            scores.append((score, i, example))
        
        # 3. Sort by score (descending)
        scores.sort(reverse=True, key=lambda x: x[0])
        
        # 4. Return top k
        selected = [example for _, _, example in scores[:k]]
        
        return selected
    
    def _compute_complexity(self, sql: str) -> float:
        """Compute SQL query complexity."""
        # Simple heuristic: count keywords
        keywords = ['JOIN', 'GROUP BY', 'HAVING', 'UNION', 'SUBQUERY']
        complexity = sum(1 for kw in keywords if kw in sql.upper())
        return float(complexity)
    
    def _compute_complexity_from_text(self, text: str) -> float:
        """Estimate complexity from natural language."""
        # Heuristic: count complexity indicators
        indicators = ['group', 'average', 'maximum', 'join', 'compare']
        complexity = sum(1 for ind in indicators if ind in text.lower())
        return float(complexity)
```

---

### Step 2: Register Selector

Update `mint/selectors/__init__.py`:

```python
from mint.selectors.random_selector import RandomSelector
from mint.selectors.dicl_selector import DICLSelector
from mint.selectors.vir2_selector import ViR2Selector
from mint.selectors.my_custom_selector import MyCustomSelector  # Add this

SELECTOR_REGISTRY = {
    'random': RandomSelector,
    'dicl': DICLSelector,
    'vir2': ViR2Selector,
    'my-custom': MyCustomSelector,  # Add this
}

def get_selector(name: str, training_data: List[Dict], **kwargs):
    """Get selector instance by name."""
    if name not in SELECTOR_REGISTRY:
        raise ValueError(f"Unknown selector: {name}")
    return SELECTOR_REGISTRY[name](training_data, **kwargs)
```

---

### Step 3: Use Selector

```bash
python vipersql.py \
  --strategy few-shot \
  --example-selection-strategy my-custom \
  --samples 100
```

Or programmatically:

```python
from mint.selectors import get_selector

selector = get_selector(
    'my-custom',
    training_data=train_examples,
    complexity_weight=0.7
)

examples = selector.select_examples(
    query="What is the average salary?",
    db_id="company",
    k=3
)
```

---

## 3. Adding Custom Metrics

### Step 1: Create Metric Function

Update `mint/metrics/enhanced_metrics.py`:

```python
def compute_custom_metric(pred_sql: str, gold_sql: str) -> float:
    """
    Compute custom similarity metric.
    
    Example: Structural similarity based on AST.
    
    Args:
        pred_sql: Predicted SQL
        gold_sql: Gold SQL
    
    Returns:
        Similarity score in [0, 1]
    """
    # Example: Parse SQL to AST
    pred_ast = parse_sql_to_ast(pred_sql)
    gold_ast = parse_sql_to_ast(gold_sql)
    
    # Compute tree edit distance
    distance = compute_tree_edit_distance(pred_ast, gold_ast)
    
    # Normalize to [0, 1]
    max_nodes = max(len(pred_ast), len(gold_ast))
    similarity = 1.0 - (distance / max_nodes) if max_nodes > 0 else 0.0
    
    return similarity

def parse_sql_to_ast(sql: str) -> Dict:
    """Parse SQL to abstract syntax tree."""
    # Use sqlparse or similar library
    import sqlparse
    parsed = sqlparse.parse(sql)[0]
    
    # Convert to tree structure
    ast = {
        'type': 'query',
        'children': []
    }
    # ... implement AST construction
    
    return ast

def compute_tree_edit_distance(tree1: Dict, tree2: Dict) -> int:
    """Compute edit distance between two trees."""
    # Implement tree edit distance algorithm
    # (e.g., Zhang-Shasha algorithm)
    
    # Simplified placeholder
    if tree1 == tree2:
        return 0
    else:
        return 1  # Replace with actual algorithm
```

---

### Step 2: Integrate into Evaluator

Update `mint/core/evaluator.py`:

```python
from mint.metrics.enhanced_metrics import (
    compute_exact_match,
    compute_component_f1,
    compute_custom_metric  # Add this
)

class Evaluator:
    def evaluate_single(self, pred_sql: str, gold_sql: str) -> Dict[str, Any]:
        """Evaluate single prediction."""
        
        # Existing metrics
        em = compute_exact_match(pred_sql, gold_sql)
        f1 = compute_component_f1(pred_sql, gold_sql)
        
        # Custom metric
        custom_score = compute_custom_metric(pred_sql, gold_sql)
        
        return {
            'exact_match': em,
            'avg_f1': f1['avg_f1'],
            'component_f1': f1['component_f1'],
            'custom_metric': custom_score  # Add this
        }
```

---

### Step 3: Use Metric

```python
from mint.core.evaluator import Evaluator

evaluator = Evaluator()

results = evaluator.evaluate_single(
    pred_sql="SELECT AVG(salary) FROM employees",
    gold_sql="SELECT AVG(salary) FROM employees WHERE dept='IT'"
)

print(f"Custom metric: {results['custom_metric']:.3f}")
```

---

## 4. Adding Multi-Language Support

### Step 1: Extend Language Detection

Update `mint/utils/language_detection.py`:

```python
def detect_language(text: str) -> str:
    """
    Detect language from text.
    
    Returns: 'vi', 'en', 'zh', 'fr', etc.
    """
    # Add new language detection
    if contains_chinese_chars(text):
        return 'zh'
    elif contains_french_chars(text):
        return 'fr'
    elif contains_vietnamese_chars(text):
        return 'vi'
    else:
        return 'en'

def contains_chinese_chars(text: str) -> bool:
    """Check if text contains Chinese characters."""
    chinese_ranges = [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Extension A
    ]
    return any(
        any(start <= ord(char) <= end for start, end in chinese_ranges)
        for char in text
    )
```

---

### Step 2: Add Language-Specific Embeddings

Update `mint/selectors/multilang_vir2_selector.py`:

```python
class MultiLangViR2Selector(BaseSelector):
    def __init__(self, training_data, **kwargs):
        super().__init__(training_data)
        
        # Load language-specific models
        self.embedders = {
            'vi': self._load_phobert(),
            'en': self._load_bert(),
            'zh': self._load_chinese_bert(),  # Add this
            'fr': self._load_camembert(),     # Add this
        }
    
    def _load_chinese_bert(self):
        """Load Chinese BERT model."""
        from transformers import BertModel, BertTokenizer
        model_name = 'bert-base-chinese'
        tokenizer = BertTokenizer.from_pretrained(model_name)
        model = BertModel.from_pretrained(model_name)
        return {'model': model, 'tokenizer': tokenizer}
    
    def _load_camembert(self):
        """Load French CamemBERT model."""
        from transformers import CamembertModel, CamembertTokenizer
        model_name = 'camembert-base'
        tokenizer = CamembertTokenizer.from_pretrained(model_name)
        model = CamembertModel.from_pretrained(model_name)
        return {'model': model, 'tokenizer': tokenizer}
```

---

## 5. Complete Example: Schema-First Strategy

Implements strategy that analyzes schema first, then generates SQL.

### Implementation

```python
# mint/strategies/schema_first_strategy.py

from typing import Dict, Any, List
from langchain.schema import HumanMessage, SystemMessage
from mint.strategies.base_strategy import BaseStrategy

class SchemaFirstStrategy(BaseStrategy):
    """
    Two-stage strategy:
    1. Analyze schema and identify relevant tables/columns
    2. Generate SQL based on analysis
    """
    
    def generate_sql(
        self,
        question: str,
        db_id: str,
        schema: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate SQL with schema-first approach."""
        
        # Stage 1: Schema analysis
        schema_analysis = self._analyze_schema(question, db_id, schema)
        
        # Stage 2: SQL generation
        sql = self._generate_sql_from_analysis(
            question, db_id, schema, schema_analysis
        )
        
        return {
            'sql': sql,
            'reasoning': schema_analysis,
            'metadata': {
                'strategy': 'schema-first',
                'stages': 2
            }
        }
    
    def _analyze_schema(
        self,
        question: str,
        db_id: str,
        schema: str
    ) -> str:
        """Stage 1: Analyze schema."""
        prompt = f"""
Analyze the database schema and identify relevant tables/columns for this question.

Database: {db_id}

Schema:
{schema}

Question: {question}

Provide analysis in this format:
- Relevant tables: [table names]
- Relevant columns: [column names]
- Join conditions: [if needed]
- Aggregations: [if needed]
"""
        
        messages = [
            SystemMessage(content="You are a database schema expert."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm_interface.generate(messages)
        return response
    
    def _generate_sql_from_analysis(
        self,
        question: str,
        db_id: str,
        schema: str,
        analysis: str
    ) -> str:
        """Stage 2: Generate SQL from analysis."""
        prompt = f"""
Based on the schema analysis, generate SQL query.

Schema Analysis:
{analysis}

Question: {question}

Generate SQL query:
"""
        
        messages = [
            SystemMessage(content="You are an expert SQL generator."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm_interface.generate(messages)
        return self._extract_sql(response)
```

### Usage

```bash
python vipersql.py \
  --strategy schema-first \
  --samples 100
```

---

## Best Practices

### 1. Follow Existing Patterns

- Inherit from base classes (`BaseStrategy`, `BaseSelector`)
- Implement required methods
- Use type hints
- Add docstrings

### 2. Configuration

Add parameters to `mint/config.py`:

```python
class ViPERConfig:
    # Custom strategy parameters
    CUSTOM_PARAM = os.getenv('CUSTOM_PARAM', 'default')
```

### 3. Testing

Create test file:

```python
# tests/test_my_custom_strategy.py

import pytest
from mint.strategies import get_strategy

def test_my_custom_strategy():
    strategy = get_strategy('my-custom')
    
    result = strategy.generate_sql(
        question="How many employees?",
        db_id="company",
        schema="CREATE TABLE employees (id INT, name TEXT)"
    )
    
    assert 'sql' in result
    assert result['sql'].strip() != ''
```

Run tests:

```bash
pytest tests/test_my_custom_strategy.py
```

### 4. Documentation

Update relevant docs:

- Add to `docs/STRATEGIES.md` or `docs/SELECTORS.md`
- Document parameters in `docs/CONFIGURATION.md`
- Add usage examples to `docs/USAGE_EXAMPLES.md`

---

## Related Documentation

- **[Architecture](ARCHITECTURE.md)** - System design
- **[Strategies](STRATEGIES.md)** - Existing strategies
- **[Selectors](SELECTORS.md)** - Existing selectors
- **[Configuration](CONFIGURATION.md)** - Parameters
- **[API Reference](API_REFERENCE.md)** - Detailed API

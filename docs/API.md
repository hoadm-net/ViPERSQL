# ViPERSQL API Documentation

## 🏗️ Architecture Overview

ViPERSQL follows a modular architecture with clear separation of concerns:

```
mint/
├── core/           # Core system components
├── strategies/     # SQL generation strategies  
├── selectors/      # Example selection algorithms
├── metrics/        # Evaluation and metrics
└── data/          # Data processing utilities
```

## 🎯 Core Components

### Configuration (`mint.config`)
- `ViPERConfig`: Main configuration class
- Environment-based configuration with YAML support
- Hierarchical config overrides

### Strategies (`mint.strategies`)
All strategies inherit from `BaseStrategy`:

#### `ZeroShotStrategy`
```python
strategy = ZeroShotStrategy(config)
result = strategy.generate_sql(question, schema, db_id)
```

#### `FewShotStrategy` 
```python
strategy = FewShotStrategy(config)
# Automatically loads appropriate selector based on config
result = strategy.generate_sql(question, schema, db_id)
```

#### `CoTStrategy`
```python
strategy = CoTStrategy(config)
result = strategy.generate_sql(question, schema, db_id)
```

### Selectors (`mint.selectors`)
All selectors inherit from `BaseSelector`:

#### `ViR2Selector` - Two-Stage Example Selection
```python
selector = ViR2Selector(config)
selector.load_training_data(dataset_path)
examples = selector.select_examples(question, k=3)
```

**ViR2 Algorithm:**
- **Stage 1**: PhoBERT semantic retrieval (M=50 candidates)
- **Stage 2**: Beam search with POS matching + diversity optimization

**Parameters:**
- `vir2_candidate_pool_size`: Stage 1 pool size (default: 50)
- `vir2_beam_size`: Beam search size (default: 5)
- `vir2_diversity_weight`: Diversity weight λ (default: 0.3)

#### Other Selectors
- `RandomSelector`: Random example selection
- `SkillKNNSelector`: Skill-based KNN selection
- `DICLSelector`: Domain-Independent Context Learning
- `ASTRESSelector`: AST-based Retrieval and Example Selection

### Metrics (`mint.metrics`)

#### `EnhancedEvaluationMetrics`
```python
metrics = EnhancedEvaluationMetrics()
results = metrics.comprehensive_evaluation(predicted, gold, db_ids, schema_path)
```

**Features:**
- Exact Match accuracy with SQL normalization
- Component-wise F1 scores (SELECT, FROM, WHERE, etc.)
- Query difficulty classification with fallback
- Error analysis and categorization
- POS matching for Vietnamese text

#### `POSMatcher`
```python
matcher = POSMatcher()
score = matcher.pos_match(question1, question2)
```

### Core Services (`mint.core`)

#### `UnifiedEvaluator`
```python
evaluator = UnifiedEvaluator(config)
results = evaluator.evaluate_batch(predictions, schema_path)
reports = evaluator.generate_report(results, output_dir)
```

#### `LLMInterface`
```python
llm = LLMInterface(config)
response = llm.generate(prompt, model_name)
```

#### `TemplateManager`
```python
template_manager = TemplateManager()
prompt = template_manager.format_template("few_shot", **kwargs)
```

## 🚀 Usage Examples

### Basic Usage
```python
from mint import ViPERConfig, create_strategy

# Create configuration
config = ViPERConfig(
    strategy='few-shot',
    example_selection_strategy='vir2',
    level='std'
)

# Create strategy
strategy = create_strategy(config.strategy, **config.to_dict())

# Generate SQL
sql = strategy.generate_sql(question, schema, db_id)
```

### Advanced ViR2 Usage
```python
from mint.selectors import ViR2Selector

# Initialize ViR2 with custom parameters
config.vir2_candidate_pool_size = 100
config.vir2_beam_size = 10
config.vir2_diversity_weight = 0.5

selector = ViR2Selector(config)
selector.load_training_data("dataset/ViText2SQL/std-level/dicl_candidates.json")

# Select examples for specific question
examples = selector.select_examples("Có bao nhiều sinh viên?", k=5)
```

### Evaluation Pipeline
```python
from mint.core import UnifiedEvaluator

# Create evaluator
evaluator = UnifiedEvaluator(config)

# Evaluate predictions
results = evaluator.evaluate_batch(
    predictions,
    schema_path="dataset/ViText2SQL/std-level/tables.json"
)

# Generate reports
report_files = evaluator.generate_report(results, "results/output/")
```

## 🔧 Configuration Options

### Environment Variables
```bash
DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### YAML Configuration
```yaml
model:
  name: "gpt-4o-mini"
  temperature: 0.0

strategies:
  few_shot:
    num_examples: 3
    selection_strategy: "vir2"
  
  vir2:
    candidate_pool_size: 50
    beam_size: 5
    diversity_weight: 0.3
```

### Programmatic Configuration
```python
config = ViPERConfig(
    strategy='few-shot',
    model_name='gpt-4o-mini',
    example_selection_strategy='vir2',
    vir2_candidate_pool_size=100,
    num_samples=50
)
```

## 📊 Output Format

### Prediction Format
```json
{
  "db_id": "database_name",
  "question": "Vietnamese question",
  "predicted": "Generated SQL",
  "gold": "Reference SQL"
}
```

### Evaluation Results Format
```json
{
  "exact_match": {
    "em_accuracy": 0.75,
    "total_queries": 100,
    "exact_matches": 75
  },
  "component_f1": {
    "f1_scores": {
      "SELECT": 0.85,
      "FROM": 0.90,
      "WHERE": 0.80
    },
    "avg_f1": 0.85
  },
  "difficulty_analysis": {
    "distribution": {
      "simple": {"count": 40, "percentage": 40.0},
      "moderate": {"count": 45, "percentage": 45.0},
      "complex": {"count": 15, "percentage": 15.0}
    }
  }
}
```

## 🎯 Extension Points

### Adding New Selectors
```python
from mint.selectors.base_selector import BaseSelector

class MySelector(BaseSelector):
    def select_examples(self, question, k=3, db_id=None):
        # Your selection logic here
        return selected_examples
```

### Adding New Strategies
```python
from mint.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_sql(self, question, schema, db_id):
        # Your generation logic here
        return sql_query
```

### Custom Metrics
```python
from mint.metrics import EnhancedEvaluationMetrics

class MyMetrics(EnhancedEvaluationMetrics):
    def custom_evaluation(self, predicted, gold):
        # Your evaluation logic here
        return scores
```

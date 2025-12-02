# System Architecture

## Overview

ViPERSQL follows a **modular architecture** with independent, extensible, and maintainable components.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface                            │
│                    (vipersql.py)                            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Configuration Layer                        │
│              (ViPERConfig + Environment)                     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                               ↓
┌─────────────────┐            ┌─────────────────┐
│  Strategy Layer │            │  Data Loader    │
│  - Zero-shot    │            │  - ViText2SQL   │
│  - Few-shot     │            │  - BIRD         │
│  - CoT          │            │  - Tables       │
└────────┬────────┘            └─────────────────┘
         ↓
         ↓ (Few-shot only)
┌─────────────────┐
│ Selector Layer  │
│  - Random       │
│  - DICL         │
│  - ASTRES       │
│  - Skill-KNN    │
│  - ViR2         │
└────────┬────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│               Template Management Layer                      │
│             (Prompt Template System)                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM Interface Layer                         │
│         - OpenAI (GPT-4o, GPT-4o-mini)                      │
│         - Anthropic (Claude-3.5-Sonnet)                     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
                  SQL Generation
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Evaluation Layer                            │
│         - Enhanced Metrics (Component F1)                    │
│         - Error Analysis                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
                   Results Output
```

---

## Module Organization

### Core Package Structure

```
mint/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── constants.py             # System constants
│
├── core/                    # Core system components
│   ├── __init__.py
│   ├── evaluator.py         # UnifiedEvaluator
│   ├── llm_interface.py     # LLMInterface
│   └── template_manager.py  # TemplateManager
│
├── strategies/              # SQL generation strategies
│   ├── __init__.py
│   ├── base.py              # BaseStrategy (abstract)
│   ├── zero_shot.py         # ZeroShotStrategy
│   ├── few_shot.py          # FewShotStrategy
│   └── cot.py               # CoTStrategy
│
├── selectors/               # Example selection methods
│   ├── __init__.py
│   ├── base_selector.py     # BaseSelector (abstract)
│   ├── random_selector.py   # RandomSelector
│   ├── dicl_selector.py     # DICLSelector
│   ├── astres_selector.py   # ASTRESSelector
│   ├── skill_knn_selector.py # SkillKNNSelector
│   ├── vir2_selector.py     # ViR2Selector
│   ├── vir2_no_pos_selector.py
│   ├── vir2_no_diversity_selector.py
│   ├── vir2_no_beam_search_selector.py
│   └── multilang_vir2_selector.py
│
├── metrics/                 # Evaluation metrics
│   ├── __init__.py
│   ├── enhanced_metrics.py  # EnhancedEvaluationMetrics
│   ├── pos_match.py         # POSMatcher (Vietnamese)
│   └── pos_match_multilang.py # POSMatcher (Multi-language)
│
├── data/                    # Data processing
│   ├── __init__.py
│   └── loaders.py           # Dataset loaders
│
└── utils/                   # Utility modules
    ├── __init__.py
    ├── multilang_embedder.py    # MultiLanguageEmbedder
    └── language_detector.py     # LanguageDetector
```

---

## Design Patterns

### 1. Strategy Pattern

**Purpose:** Enables switching between SQL generation strategies

**Implementation:**

```python
# Base interface
class BaseStrategy(ABC):
    @abstractmethod
    def generate_sql(self, question, schema, db_id, **kwargs) -> StrategyResult
```

**Benefits:**
- Easy to add new strategies
- Runtime selection
- Consistent interface

### 2. Factory Pattern

**Purpose:** Dynamically creates strategy and selector instances

**Implementation:**

```python
def create_strategy(strategy_name: str, config: ViPERConfig) -> BaseStrategy:
    if strategy_name == 'zero-shot':
        return ZeroShotStrategy(config)
    elif strategy_name == 'few-shot':
        return FewShotStrategy(config)
    elif strategy_name == 'cot':
        return CoTStrategy(config)
```

**Benefits:**
- Centralized creation logic
- Easy to extend
- Type safety

### 3. Template Method Pattern

**Purpose:** Defines algorithm skeleton, subclasses override specific steps

**Implementation:**

```python
class BaseSelector(ABC):
    def select_examples(self, question, k, db_id=None):
        # Template method
        self.load_training_data()
        candidates = self._filter_candidates(db_id)
        scored = self._score_candidates(question, candidates)
        return self._select_top_k(scored, k)
    
    @abstractmethod
    def _score_candidates(self, question, candidates):
        pass
```

### 4. Dependency Injection

**Purpose:** Inject configuration into all components

**Benefits:**
- Flexible configuration
- Easy testing
- Decoupled components

---

## Component Details

### 1. Configuration Management

**Class:** `ViPERConfig`

**Purpose:** Centralized configuration from multiple sources

**Priority Order:**
1. Command-line arguments (highest)
2. Environment variables
3. .env file
4. Default values (lowest)

**Key Features:**
- Type validation
- Auto-loading from .env
- Override mechanism
- Dataclass-based

### 2. Strategy Layer

#### BaseStrategy

**Interface:**

```python
class BaseStrategy(ABC):
    def __init__(self, config: ViPERConfig)
    
    @abstractmethod
    def generate_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        db_id: str,
        **kwargs
    ) -> StrategyResult
    
    @abstractmethod
    def _get_strategy_name(self) -> str
```

**Implementations:**
- `ZeroShotStrategy` - Direct translation
- `FewShotStrategy` - With examples from selector
- `CoTStrategy` - Step-by-step reasoning

### 3. Selector Layer

#### BaseSelector

**Interface:**

```python
class BaseSelector(ABC):
    def __init__(self, config: ViPERConfig)
    
    @abstractmethod
    def select_examples(
        self,
        question: str,
        k: int,
        db_id: Optional[str] = None
    ) -> List[Dict[str, Any]]
```

**Implementations:**
- `RandomSelector` - Random baseline
- `DICLSelector` - Semantic similarity
- `ASTRESSelector` - AST matching
- `SkillKNNSelector` - Skill-based
- **`ViR2Selector`** - Two-stage (main)
- `MultiLanguageViR2Selector` - Multi-language variant

### 4. LLM Interface

**Class:** `LLMInterface`

**Purpose:** Unified interface for multiple LLM providers

**Supported Models:**

**OpenAI:**
- `gpt-4o`
- `gpt-4o-mini`

**Anthropic:**
- `claude-3-5-sonnet-20241022`

**Key Methods:**

```python
class LLMInterface:
    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str
    
    def generate_with_metadata(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]  # includes latency, token counts
```

### 5. Template Manager

**Class:** `TemplateManager`

**Purpose:** Manages prompt templates for different strategies

**Template Loading:**
```python
templates/
├── vietnamese_nl2sql.txt           # Zero-shot
├── few_shot_vietnamese_nl2sql.txt  # Few-shot
├── cot_vietnamese_nl2sql.txt       # Chain-of-thought
└── skill_extraction_vietnamese.txt # Skill extraction
```

**Features:**
- Dynamic variable substitution
- Multi-language support
- Template validation

### 6. Evaluation Layer

**Class:** `UnifiedEvaluator`

**Purpose:** Enhanced evaluation beyond Exact Match

**Metrics Provided:**
- Exact Match (EM)
- Component-wise F1 (SELECT, FROM, WHERE, etc.)
- Error analysis
- Complexity-based breakdown

**Key Methods:**

```python
class UnifiedEvaluator:
    def evaluate_single(
        self,
        predicted_sql: str,
        gold_sql: str,
        db_id: str,
        schema_path: str
    ) -> Dict[str, Any]
    
    def evaluate_batch(
        self,
        predictions: List[Dict],
        schema_path: str
    ) -> Dict[str, Any]
```

---

## Data Flow

### Zero-Shot Flow

```
1. Input Question + Schema
   ↓
2. TemplateManager formats zero-shot prompt
   ↓
3. LLMInterface sends to model
   ↓
4. Extract SQL from response
   ↓
5. Evaluator compares with gold SQL
   ↓
6. Return metrics
```

### Few-Shot Flow (with ViR2)

```
1. Input Question + Schema
   ↓
2. ViR2Selector.select_examples(question, k=3)
   │
   ├─ Stage 1: PhoBERT retrieval → top-50 candidates
   │
   └─ Stage 2: Beam search re-ranking → 3 examples
   ↓
3. TemplateManager formats few-shot prompt with examples
   ↓
4. LLMInterface sends to model
   ↓
5. Extract SQL from response
   ↓
6. Evaluator compares with gold SQL
   ↓
7. Return metrics
```

### Chain-of-Thought Flow

```
1. Input Question + Schema
   ↓
2. TemplateManager formats CoT prompt (with reasoning steps)
   ↓
3. LLMInterface sends to model
   ↓
4. Model generates reasoning + SQL
   ↓
5. Extract SQL from response
   ↓
6. Evaluator compares with gold SQL
   ↓
7. Return metrics (+ reasoning trace)
```

---

## Extension Points

### Adding New Strategy

1. Create file: `mint/strategies/my_strategy.py`
2. Implement `BaseStrategy` interface
3. Register in `mint/strategies/__init__.py`
4. Update `create_strategy()` factory

### Adding New Selector

1. Create file: `mint/selectors/my_selector.py`
2. Implement `BaseSelector` interface
3. Register in `mint/selectors/__init__.py`
4. Update `FewShotStrategy._create_selector()`

### Adding New LLM Provider

1. Extend `LLMInterface._initialize_llm()`
2. Add provider-specific handling
3. Update configuration options

See **[Extending System](EXTENDING_SYSTEM.md)** for detailed guides.

---

## Configuration Flow

```
Command Line Args
      ↓
Environment Variables (.env)
      ↓
Default Values (constants.py)
      ↓
ViPERConfig (validated)
      ↓
Injected to all components
```

**Example:**

```bash
# Command line overrides everything
python vipersql.py --model gpt-4o --strategy few-shot

# Falls back to .env if not specified
DEFAULT_MODEL=claude-3-5-sonnet-20241022

# Falls back to defaults if not in .env
DEFAULT_TEMPERATURE=0.7
```

---

## Error Handling

### Strategy Level

```python
try:
    sql = strategy.generate_sql(question, schema, db_id)
except Exception as e:
    logger.error(f"Strategy failed: {e}")
    # Fallback or re-raise
```

### Selector Level

```python
try:
    examples = selector.select_examples(question, k)
except Exception as e:
    logger.warning(f"Selector failed: {e}, falling back to random")
    examples = random_selector.select_examples(question, k)
```

### LLM Level

```python
try:
    response = llm.generate(prompt)
except APIError as e:
    # Retry logic
    # Rate limiting handling
```

---

## Performance Considerations

### Caching

**Pre-computed Embeddings:**
- Meaning pool embeddings stored in `dicl_candidates.json`
- Avoid re-encoding training data

**Template Caching:**
- Templates loaded once at initialization
- Reused across multiple generations

### Batch Processing

**Sequential with Intermediate Saves:**
- Process samples one-by-one
- Save every N samples
- Enable resume on failure

### Memory Management

**Lazy Loading:**
- Load training data only when needed
- Release after selection

**Streaming:**
- Don't load entire dataset into memory
- Process in chunks

---

## Logging System

### Log Levels

```python
DEBUG   - Detailed tracing
INFO    - Progress updates
WARNING - Non-critical issues
ERROR   - Failures
```

### Log Structure

```
[timestamp] [level] [component] message
2025-12-01 10:30:15 INFO ViR2Selector Stage 1: Retrieved 50 candidates
2025-12-01 10:30:16 INFO ViR2Selector Stage 2: Selected 3 examples
```

### Configuration

```env
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

---

## Testing Architecture

### Unit Tests

```
tests/
├── test_strategies.py
├── test_selectors.py
├── test_evaluator.py
└── test_vir2.py
```

### Integration Tests

```
tests/
├── test_end_to_end.py
├── test_multilang_vir2.py
└── debug_vir2.py
```

---

## Deployment Considerations

### Requirements

- Python 3.8+
- PyTorch (for PhoBERT/BERT)
- Transformers library
- API keys for LLM providers

### Environment Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm  # English
python -m spacy download vi_core_news_sm # Vietnamese (if available)
```

### Production Checklist

- [ ] API keys configured
- [ ] Pre-computed embeddings available
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Resource limits set

---

## Related Documentation

- **[ViR2 Method](VIR2_METHOD.md)** - Detailed ViR2 algorithm
- **[Strategies](STRATEGIES.md)** - Strategy implementations
- **[Selectors](SELECTORS.md)** - Selector implementations
- **[Configuration](CONFIGURATION.md)** - All config options
- **[Extending System](EXTENDING_SYSTEM.md)** - Adding components

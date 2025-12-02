# Multi-Language Support for ViPERSQL

This document describes the multi-language extensions to ViPERSQL that enable support for both Vietnamese and English text-to-SQL conversion using the ViR2 (Two-Stage Example Selection) approach.

## 🌍 Overview

The multi-language ViPERSQL extends the original Vietnamese-only system to support:

- **Vietnamese**: PhoBERT embeddings + underthesea/spaCy POS tagging
- **English**: BERT embeddings + spaCy POS tagging  
- **Automatic Language Detection**: Smart detection based on character patterns and vocabulary
- **Cross-lingual Retrieval**: (Experimental) Cross-language example selection

## 🏗️ Architecture

### Core Components

#### 1. **LanguageDetector** (`mint/utils/language_detector.py`)
Automatically detects input language using:
- Vietnamese diacritical marks detection
- Language-specific vocabulary matching
- Confidence scoring

```python
from mint.utils.language_detector import LanguageDetector

detector = LanguageDetector()
language = detector.detect_language("Find all students")  # Returns 'en'
language = detector.detect_language("Tìm tất cả học sinh")  # Returns 'vi'
```

#### 2. **MultiLanguageEmbedder** (`mint/utils/multilang_embedder.py`)
Unified embedding interface supporting:
- **Vietnamese**: PhoBERT-base-v2 (`vinai/phobert-base-v2`)
- **English**: BERT-base-uncased (`google-bert/bert-base-uncased`)
- Automatic model selection based on language
- Efficient batching and caching

```python
from mint.utils.multilang_embedder import MultiLanguageEmbedder

embedder = MultiLanguageEmbedder()
# Auto-detect language and use appropriate model
embedding = embedder.encode("Find all students")  # Uses BERT
embedding = embedder.encode("Tìm tất cả học sinh")  # Uses PhoBERT
```

#### 3. **Multi-Language POS Matcher** (`mint/metrics/pos_match_multilang.py`)
Enhanced POS matching with:
- **Vietnamese**: underthesea (primary) + spaCy (fallback)
- **English**: spaCy (`en_core_web_sm`)
- Unified POS tag conversion
- Jensen-Shannon divergence calculation

```python
from mint.metrics.pos_match_multilang import POSMatcher

pos_matcher = POSMatcher()
score = pos_matcher.pos_match("Find students", "List pupils")  # English
score = pos_matcher.pos_match("Tìm học sinh", "Liệt kê sinh viên")  # Vietnamese
```

#### 4. **MultiLanguageViR2Selector** (`mint/selectors/multilang_vir2_selector.py`)
Two-stage example selection with language awareness:

**Stage 1**: Language-aware semantic retrieval
- Detects question language
- Uses appropriate embedding model (BERT/PhoBERT)
- Retrieves top-M semantically similar candidates

**Stage 2**: Beam search re-ranking
- POS matching using language-appropriate tools
- Diversity optimization
- Combined scoring: `λ * pos_score + (1-λ) * diversity_score`

## 🚀 Usage

### Command Line Interface

```bash
# Multi-language ViR2 with auto-detection
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --samples 10

# Force English processing
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --language en --samples 10

# Force Vietnamese processing  
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --language vi --samples 10

# Enable cross-lingual retrieval (experimental)
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --cross-lingual --samples 10
```

### Programmatic Usage

```python
from mint.config import ViPERConfig
from mint.selectors import MultiLanguageViR2Selector

# Create configuration
config = ViPERConfig(
    example_selection_strategy='multilang-vir2',
    language='auto',  # or 'vi', 'en'
    vir2_candidate_pool_size=50,
    vir2_beam_size=5,
    vir2_diversity_weight=0.3
)

# Initialize selector
selector = MultiLanguageViR2Selector(config)
selector.load_training_data("path/to/dataset")

# Select examples
examples = selector.select_examples("Find all students with high grades", k=3)
```

## ⚙️ Configuration

### Language Models

Models are configured in `mint/constants.py`:

```python
LANGUAGE_MODELS = {
    "vi": {
        "embedding_model": "vinai/phobert-base-v2",
        "pos_model": "vi_core_news_sm",
        "tokenizer_model": "vinai/phobert-base-v2"
    },
    "en": {
        "embedding_model": "google-bert/bert-base-uncased", 
        "pos_model": "en_core_web_sm",
        "tokenizer_model": "google-bert/bert-base-uncased"
    }
}
```

### ViR2 Hyperparameters

```python
config = ViPERConfig(
    # Stage 1: Semantic retrieval pool size
    vir2_candidate_pool_size=50,  # M parameter
    
    # Stage 2: Beam search size  
    vir2_beam_size=5,             # B parameter
    
    # Diversity vs POS matching weight
    vir2_diversity_weight=0.3,    # λ parameter (0-1)
    
    # Language settings
    language='auto',              # 'auto', 'vi', 'en'
    cross_lingual=False          # Enable cross-lingual retrieval
)
```

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install spaCy Language Models

```bash
# English model
python -m spacy download en_core_web_sm

# Vietnamese model (if available)
python -m spacy download vi_core_news_sm
```

### 3. Verify Installation

```bash
python tests/test_multilang_vir2.py
```

## 🔬 Experimental Features

### Cross-Lingual Retrieval

Enables retrieval from Vietnamese training data for English questions (and vice versa):

```bash
python vipersql.py --example-selection-strategy multilang-vir2 --cross-lingual
```

**Note**: Cross-lingual performance may be limited without specialized cross-lingual embeddings.

## 📊 Performance Considerations

### Model Loading
- **Memory**: Both BERT and PhoBERT models require ~1GB each
- **Loading Time**: 5-10 seconds per model on first load
- **Caching**: Models are cached in memory by default

### Optimization Tips
```python
# Disable model caching to save memory
embedder = MultiLanguageEmbedder(cache_models=False)

# Clear cache when needed
embedder.clear_cache()

# Use CPU only for smaller memory footprint
os.environ["CUDA_VISIBLE_DEVICES"] = ""
```

## 🧪 Testing

### Unit Tests
```bash
python tests/test_multilang_vir2.py
```

### Integration Tests
```bash
# Test with English questions
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --language en --samples 5

# Test with Vietnamese questions  
python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --language vi --samples 5
```

## 🔍 Debugging

### Language Detection Issues
```python
from mint.utils.language_detector import LanguageDetector

detector = LanguageDetector()
info = detector.get_language_info("your text here")
print(info)  # Shows detailed detection analysis
```

### POS Matching Analysis
```python
from mint.metrics.pos_match_multilang import POSMatcher

matcher = POSMatcher()
analysis = matcher.analyze_pos_similarity("question1", "question2")
print(analysis)  # Shows POS tags and distributions
```

### ViR2 Selection Info
```python
selector = MultiLanguageViR2Selector(config)
info = selector.get_selection_info("your question", k=3)
print(info)  # Shows detailed selection process
```

## 🚧 Known Limitations

1. **Cross-lingual Performance**: Limited without specialized cross-lingual models
2. **Vietnamese spaCy Model**: May not be available, falls back to underthesea
3. **Memory Usage**: Loading both models simultaneously requires significant RAM
4. **Language Detection**: Simple heuristics may misclassify edge cases

## 🛣️ Future Improvements

1. **Cross-lingual Embeddings**: Integrate multilingual BERT or XLM models
2. **Advanced Language Detection**: Use dedicated language detection models
3. **Dynamic Model Loading**: Load models on-demand to reduce memory usage
4. **Language-Specific Templates**: Customize prompt templates per language
5. **Evaluation Metrics**: Language-specific evaluation and comparison

## 📝 Example Output

```bash
$ python vipersql.py --strategy few-shot --example-selection-strategy multilang-vir2 --samples 5

[MultiLanguageViR2] Detected meaning pool language: en
[MultiLanguageViR2] Loaded 1000 examples with compatible embeddings
[MultiLanguageViR2] Question language: en, Pool language: en
[MultiLanguageViR2] Stage 1: Retrieved 50 candidates (similarity range: 0.234 - 0.891)
[MultiLanguageViR2] Stage 2: Beam search selected 3 examples
[FewShot] Selected 3 examples using multilang-vir2 strategy

Overall F1 Score: 89.2%
Exact Match Accuracy: 24.1%
```

# ViPERSQL Project Structure

## 📁 Refactored Directory Structure

```
ViPERSQL/
├── 📄 vipersql.py                     # Main CLI entry point
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # Environment configuration template
├── 📄 PROJECT_STRUCTURE.md           # This file
│
├── 📁 mint/                          # Core system package
│   ├── 📄 __init__.py
│   ├── 📄 config.py                  # Configuration management
│   ├── 📄 constants.py               # System constants
│   ├── 📄 utils.py                   # Utility functions
│   │
│   ├── 📁 core/                      # Core system components
│   │   ├── 📄 __init__.py
│   │   ├── 📄 llm_interface.py       # Unified LLM provider interface
│   │   ├── 📄 template_manager.py    # Prompt template system
│   │   └── 📄 evaluator.py           # Enhanced evaluation engine
│   │
│   ├── 📁 strategies/                # SQL generation strategies
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py                # Base strategy class
│   │   ├── 📄 zero_shot.py           # Zero-shot strategy
│   │   ├── 📄 few_shot.py            # Few-shot strategy
│   │   └── 📄 cot.py                 # Chain-of-thought strategy
│   │
│   ├── 📁 selectors/                 # Example selection strategies
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_selector.py       # Base selector class
│   │   ├── 📄 random_selector.py     # Random selection
│   │   ├── 📄 skill_knn_selector.py  # Skill-based KNN selection
│   │   ├── 📄 dicl_selector.py       # DICL selection
│   │   ├── 📄 astres_selector.py     # ASTRES selection
│   │   └── 📄 vir2_selector.py       # ViR2 Two-Stage selection
│   │
│   ├── 📁 metrics/                   # Evaluation metrics
│   │   ├── 📄 __init__.py
│   │   ├── 📄 enhanced_metrics.py    # Advanced metrics calculation
│   │   └── 📄 pos_match.py           # POS matching utilities
│   │
│   └── 📁 data/                      # Data processing utilities
│       ├── 📄 __init__.py
│       └── 📄 processors.py          # Data preprocessing utilities
│
├── 📁 dataset/                       # Vietnamese Text-to-SQL dataset
│   └── 📁 ViText2SQL/
│       ├── 📁 std-level/             # Standard Vietnamese
│       ├── 📁 syllable-level/        # Syllable-segmented
│       └── 📁 word-level/            # Word-segmented
│
├── 📁 templates/                     # Prompt templates
│   ├── 📄 vietnamese_nl2sql.txt      # Zero-shot template
│   ├── 📄 few_shot_vietnamese_nl2sql.txt  # Few-shot template
│   ├── 📄 cot_vietnamese_nl2sql.txt  # Chain-of-thought template
│   ├── 📄 schema_context.txt         # Schema context template
│   └── 📄 skill_extraction_vietnamese.txt # Skill extraction template
│
├── 📁 configs/                       # Configuration files
│   ├── 📄 default.yaml              # Default configuration
│   ├── 📄 development.yaml          # Development configuration
│   └── 📄 production.yaml           # Production configuration
│
├── 📁 scripts/                       # Utility scripts
│   ├── 📄 build_dicl_candidates.py   # Build DICL candidates
│   ├── 📄 normalize_to_std.py        # Text normalization
│   ├── 📄 skill_knn_preprocessing.py # Skill KNN preprocessing
│   └── 📄 sql_type_analyzer.py       # SQL analysis utilities
│
├── 📁 tests/                         # Test files
│   ├── 📄 test_vir2.py              # ViR2 selector tests
│   ├── 📄 debug_vir2.py             # ViR2 debug utilities
│   ├── 📄 debug_training_data.py    # Training data debugging
│   └── 📄 __init__.py
│
├── 📁 tools/                         # Development tools
│   ├── 📄 benchmark.py              # Benchmarking utilities
│   └── 📄 data_analysis.py          # Data analysis tools
│
├── 📁 docs/                          # Documentation
│   ├── 📄 EVALUATION_README.md      # Evaluation documentation
│   ├── 📄 README_DATASET.md         # Dataset documentation
│   ├── 📄 README_SCRIPTS.md         # Scripts documentation
│   ├── 📄 API.md                    # API documentation
│   └── 📄 CONTRIBUTING.md           # Contribution guidelines
│
├── 📁 results/                       # Evaluation results
│   ├── 📁 few-shot/                 # Few-shot results
│   ├── 📁 zero-shot/                # Zero-shot results
│   ├── 📁 cot/                      # Chain-of-thought results
│   └── 📁 benchmarks/               # Benchmark results
│
└── 📁 logs/                          # System logs
    ├── 📁 debug/                    # Debug logs
    ├── 📁 evaluation/               # Evaluation logs
    └── 📁 system/                   # System logs
```

## 🎯 Key Improvements

### **1. Better Organization**
- **Core components** separated into `mint/core/`
- **Metrics** isolated in `mint/metrics/`
- **Data utilities** in `mint/data/`
- **Tests** properly organized in `tests/`

### **2. Configuration Management**
- **YAML-based configs** in `configs/`
- **Environment-specific** configurations
- **Default settings** with override capabilities

### **3. Documentation Structure**
- **Centralized docs** in `docs/`
- **API documentation** for developers
- **Contributing guidelines** for collaboration

### **4. Results Organization**
- **Strategy-based folders** in `results/`
- **Benchmark results** separately tracked
- **Clear naming conventions**

### **5. Logging System**
- **Structured logging** in `logs/`
- **Category-based** log separation
- **Debug/production** log levels

## 🚀 Benefits

1. **Maintainability**: Clear separation of concerns
2. **Scalability**: Easy to add new strategies/selectors
3. **Testing**: Organized test structure
4. **Documentation**: Comprehensive docs for users/developers
5. **Configuration**: Flexible config management
6. **Debugging**: Better logging and debugging tools

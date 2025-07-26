# BIRD Dataset

This directory contains the BIRD (Big Bench for Large-scale Database Grounded Text-to-SQL Evaluation) dataset adapted for the ViPERSQL project, with both English and Vietnamese language support.

## Dataset Overview

BIRD is a large-scale cross-domain dataset for evaluating Text-to-SQL parsing performance. The dataset contains complex, realistic database questions with varying difficulty levels.

### Original Dataset Statistics
- **Total samples**: 1,534 questions
- **Difficulty distribution**:
  - Simple: 925 samples (60.3%)
  - Moderate: 464 samples (30.2%) 
  - Challenging: 145 samples (9.5%)

## Directory Structure

```
BIRD/
├── data.json          # Original complete BIRD dataset
├── tables.json        # Database schema definitions
├── en/               # English language subset
│   ├── tables.json   # Database schemas (copy)
│   ├── test.json     # 300 test samples
│   └── candidates.json # 50 candidate samples with BERT embeddings
└── vi/               # Vietnamese language subset  
    ├── tables.json   # Database schemas (copy)
    ├── test.json     # 300 test samples (Vietnamese)
    └── candidates.json # 50 candidate samples with PhoBERT embeddings
```

## File Descriptions

### Root Level Files

#### `data.json`
The complete original BIRD dataset containing all 1,534 samples.

**Format:**
```json
[
  {
    "question_id": 0,
    "db_id": "california_schools",
    "question": "What is the highest eligible free rate for K-12 students...",
    "evidence": "Eligible free rate for K-12 = ...",
    "SQL": "SELECT ...",
    "difficulty": "simple"
  }
]
```

**Fields:**
- `question_id`: Unique identifier for each question
- `db_id`: Database identifier
- `question`: Natural language query in English
- `evidence`: Additional context or explanation
- `SQL`: Target SQL query
- `difficulty`: Difficulty level (simple/moderate/challenging)

#### `tables.json`
Database schema definitions for all databases used in BIRD.

**Format:**
```json
[
  {
    "db_id": "california_schools",
    "table_names": ["frpm", "satscores", "schools"],
    "table_names_original": ["frpm", "satscores", "schools"],
    "column_names": [
      [-1, "*"],
      [0, "CDSCode"],
      [0, "NCESDist"],
      ...
    ],
    "column_names_original": [...],
    "column_types": ["text", "text", "text", ...],
    "foreign_keys": [[8, 2]],
    "primary_keys": [1]
  }
]
```

## Language-Specific Subsets

### English (`en/` folder)

Contains English language samples sampled from the original dataset while maintaining the original difficulty distribution.

#### `en/test.json` (300 samples)
Test set maintaining proportional difficulty distribution:
- Simple: ~181 samples (60.3%)
- Moderate: ~91 samples (30.2%)
- Challenging: ~28 samples (9.5%)

**Format:**
```json
[
  {
    "db_id": "formula_1",
    "question": "In terms of number of points acquired, how many victories...",
    "SQL": "SELECT SUM(CASE WHEN points = 91 THEN wins ELSE 0 END)..."
  }
]
```

#### `en/candidates.json` (50 samples)
Candidate set for few-shot learning and similarity search. Contains the same difficulty distribution as the test set but with additional BERT embeddings.

**Format:**
```json
[
  {
    "db_id": "formula_1", 
    "question": "How many clients who were born in 1920...",
    "SQL": "SELECT COUNT(*) FROM clients WHERE birth_year = 1920...",
    "question_embedding": [0.123, -0.456, 0.789, ...] // 768-dim BERT vector
  }
]
```

**Embeddings:**
- Generated using `bert-base-uncased` model
- 768-dimensional vectors representing question semantics
- Used for similarity-based example selection

### Vietnamese (`vi/` folder)

Contains Vietnamese translations of the English samples with Vietnamese-specific embeddings.

#### `vi/test.json` (300 samples)
Vietnamese translations of the English test set using GPT-4o-mini.

**Format:**
```json
[
  {
    "db_id": "formula_1",
    "question": "Về số điểm đã đạt được, tay đua xếp hạng 91 đã giành được bao nhiêu chiến thắng?",
    "SQL": "SELECT SUM(CASE WHEN points = 91 THEN wins ELSE 0 END)..."
  }
]
```

#### `vi/candidates.json` (50 samples)
Vietnamese translations with PhoBERT embeddings for Vietnamese-specific similarity search.

**Format:**
```json
[
  {
    "db_id": "formula_1",
    "question": "Có bao nhiêu khách hàng sinh năm 1920...",
    "SQL": "SELECT COUNT(*) FROM clients WHERE birth_year = 1920...",
    "question_embedding": [0.234, -0.567, 0.891, ...] // 768-dim PhoBERT vector
  }
]
```

**Embeddings:**
- Generated using `vinai/phobert-base-v2` model
- 768-dimensional vectors optimized for Vietnamese text
- Used for Vietnamese-specific similarity-based example selection

## Dataset Creation Process

### Sampling Strategy
- **Random sampling** maintaining original difficulty distribution
- **No overlap** between test and candidate sets
- **Reproducible** sampling using fixed random seeds

### Translation Process
- **Model**: GPT-4o-mini for high-quality Vietnamese translations
- **Batch processing** for efficiency (10 questions per API call)
- **Technical term preservation** while maintaining natural Vietnamese
- **Quality assurance** with fallback mechanisms

### Embedding Generation
- **English**: BERT-base-uncased for universal English understanding
- **Vietnamese**: PhoBERT-base-v2 for Vietnamese-specific semantics
- **Consistency**: Both models produce 768-dimensional vectors

## Usage in ViPERSQL

### Test Sets
- Used for final evaluation of Text-to-SQL models
- Supports both English and Vietnamese evaluation
- Maintains realistic difficulty distribution

### Candidate Sets  
- Used for few-shot learning and example selection
- Embedding vectors enable semantic similarity search
- Language-specific embeddings for optimal retrieval

### Schema Files
- Provide database structure information
- Support schema-aware SQL generation
- Enable proper table and column name resolution

## Quality Metrics

### Translation Quality
- Professional-grade translations using state-of-the-art LLM
- Technical database terminology accurately preserved
- Natural Vietnamese expressions while maintaining meaning

### Embedding Quality
- Language-specific models for optimal semantic representation
- Consistent dimensionality across languages
- Suitable for cross-lingual similarity comparisons

## Notes

- All files use UTF-8 encoding to support Vietnamese characters
- JSON format with proper escaping for special characters
- Consistent field naming across English and Vietnamese versions
- Ready for integration with ViPERSQL evaluation pipeline

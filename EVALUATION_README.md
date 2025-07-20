# ViPERSQL Evaluation System

Hệ thống đánh giá toàn diện cho Vietnamese Text-to-SQL với các tính năng normalization và scoring tiên tiến.

## 🎯 Tổng quan

Hệ thống đánh giá ViPERSQL được thiết kế để đánh giá chính xác các câu truy vấn SQL được sinh ra từ mô hình Text-to-SQL tiếng Việt. Hệ thống hỗ trợ nhiều loại đánh giá khác nhau và có khả năng xử lý các trường hợp phức tạp như alias normalization, operator standardization, và clause-level analysis.

## 🏗️ Kiến trúc hệ thống

```
mint/
├── metrics.py          # Core evaluation logic
├── evaluator.py        # Main evaluation orchestrator
├── config.py           # Configuration management
├── llm_interface.py    # LLM integration
└── strategies/         # Evaluation strategies
    ├── base.py         # Base strategy class
    ├── zero_shot.py    # Zero-shot evaluation
    ├── few_shot.py     # Few-shot evaluation
    └── cot.py          # Chain-of-thought evaluation
```

## 🔧 Tính năng chính

### 1. SQL Normalization
- **Alias Normalization**: Chuẩn hóa alias về table name gốc
- **Table Name Addition**: Tự động thêm table name cho fields không có alias
- **Semicolon Removal**: Loại bỏ dấu chấm phẩy dư thừa
- **Whitespace Normalization**: Chuẩn hóa khoảng trắng và xuống dòng

### 2. Operator Standardization
- **Logical Operators**: Chuẩn hóa `<>` thành `!=`
- **Quote Normalization**: Chuẩn hóa dấu ngoặc `'` và `"`
- **Case Sensitivity**: Chuẩn hóa case cho các keywords

### 3. Component-wise Evaluation
- **SELECT Clause**: Đánh giá các fields được chọn
- **FROM Clause**: Đánh giá các tables được tham chiếu
- **WHERE Clause**: Đánh giá các điều kiện lọc
- **GROUP BY Clause**: Đánh giá các nhóm
- **ORDER BY Clause**: Đánh giá thứ tự sắp xếp
- **HAVING Clause**: Đánh giá điều kiện nhóm
- **KEYWORDS**: Đánh giá các từ khóa SQL

### 4. Scoring Metrics
- **Exact Match Accuracy**: Tỷ lệ câu truy vấn hoàn toàn chính xác
- **Component F1 Score**: F1-score cho từng thành phần
- **Syntax Validity**: Kiểm tra tính hợp lệ cú pháp
- **Detailed Analysis**: Phân tích chi tiết từng clause

## 📊 Cách sử dụng

### 1. Chạy đánh giá cơ bản
```bash
python vipersql.py --strategy few-shot --samples 10 --level std --split test
```

### 2. Chạy đánh giá chi tiết
```bash
python vipersql.py --strategy few-shot --samples 50 --level std --split test --detailed
```

### 3. Các tham số có sẵn
- `--strategy`: Loại đánh giá (zero-shot, few-shot, cot)
- `--samples`: Số lượng mẫu đánh giá
- `--level`: Cấp độ dữ liệu (std, word, syllable)
- `--split`: Tập dữ liệu (train, dev, test)
- `--detailed`: Hiển thị phân tích chi tiết

## 🔍 Alias Normalization

### Vấn đề
Các câu truy vấn SQL có thể sử dụng alias khác nhau:
```sql
-- Predicted
SELECT id_kỹ_năng, mô_tả_về_kỹ_năng FROM kỹ_năng

-- Gold
SELECT t1.id_kỹ_năng, t1.mô_tả_về_kỹ_năng FROM kỹ_năng AS t1
```

### Giải pháp
Hệ thống tự động:
1. **Extract alias mapping** từ FROM/JOIN clauses
2. **Normalize aliases** về table name gốc
3. **Add table names** cho fields không có alias
4. **Compare normalized forms** để đánh giá

### Kết quả
```sql
-- Sau normalization
Predicted: kỹ_năng.id_kỹ_năng, kỹ_năng.mô_tả_về_kỹ_năng
Gold:      kỹ_năng.id_kỹ_năng, kỹ_năng.mô_tả_về_kỹ_năng
```

# Evaluation Framework

Comprehensive evaluation metrics and output analysis for Vietnamese Text-to-SQL systems in ViPERSQL.

## Overview

The ViPERSQL evaluation framework provides multi-dimensional analysis of Text-to-SQL model performance, including exact match accuracy, component-wise analysis, and detailed error categorization. The framework is designed to support rigorous research evaluation and model comparison.

## Evaluation Metrics

### 1. Exact Match (EM) Accuracy

**Definition**: Binary metric indicating whether the predicted SQL query exactly matches the gold standard query after normalization.

**Formula**:
```
EM_Accuracy = |{i : normalize(pred_i) = normalize(gold_i)}| / N
```
Where:
- `pred_i`: Predicted SQL query for sample i
- `gold_i`: Gold standard SQL query for sample i
- `normalize()`: SQL normalization function
- `N`: Total number of samples

**Normalization Process**:
- Convert to lowercase
- Remove extra whitespace
- Standardize alias naming (t1, t2, ...)
- Normalize aggregation function spacing

### 2. Component-wise F1 Scores

**Definition**: F1 scores calculated independently for each SQL component (SELECT, FROM, WHERE, etc.).

**Components Evaluated**:
- **SELECT**: Column selection and expressions
- **FROM**: Table selection and JOIN operations
- **WHERE**: Filtering conditions
- **GROUP BY**: Grouping expressions
- **ORDER BY**: Sorting specifications
- **HAVING**: Group filtering conditions
- **KEYWORDS**: SQL keywords and operators

**Formulas**:
```
Precision_c = TP_c / (TP_c + FP_c)
Recall_c = TP_c / (TP_c + FN_c)
F1_c = 2 × (Precision_c × Recall_c) / (Precision_c + Recall_c)
```
Where:
- `TP_c`: True positives for component c
- `FP_c`: False positives for component c
- `FN_c`: False negatives for component c

**Overall F1**: Macro-average across all components
```
Overall_F1 = (1/|C|) × Σ F1_c
```

### 3. Query Difficulty Classification

**Complexity Categories**:
- **Simple**: Basic SELECT with simple WHERE conditions
- **Moderate**: JOIN operations or aggregations
- **Complex**: Multiple JOINs with GROUP BY/HAVING
- **Very Complex**: Nested queries or advanced SQL constructs

**Scoring Factors**:
- Base operations: +1 point each
- JOIN operations: +0.5 points each
- Aggregations: +0.5 points each
- Subqueries: +2 points each
- Window functions: +2 points each

### 4. Error Analysis

**Error Categories**:
- **Syntax Errors**: Malformed SQL syntax
- **Semantic Errors**: Valid syntax but incorrect logic
- **Column Selection Errors**: Wrong columns chosen
- **Table Selection Errors**: Wrong tables or missing JOINs
- **Condition Errors**: Incorrect WHERE/HAVING conditions
- **Join Errors**: Missing or incorrect JOIN conditions
- **Aggregation Errors**: Wrong aggregation functions
- **Operator Errors**: Incorrect comparison operators

## Output Format

### 1. Command Line Output

The system provides real-time feedback during execution:

```
🚀 Starting ViPERSQL Evaluation
Strategy: FEW-SHOT
Model: gpt-4o-mini
Dataset: std-level, dev split
Samples: 10
============================================================

📊 ENHANCED EVALUATION SUMMARY
============================================================
🤖 Model: gpt-4o-mini
🎯 Strategy: FEW-SHOT
🎯 Exact Match Accuracy: 75.00%
   Total Queries: 10
   Exact Matches: 7

🔍 COMPONENT-WISE F1 SCORES:
--------------------------------------------------
  SELECT      :  88.89%
  FROM        : 100.00%
  WHERE       :  67.50%
  GROUP BY    :  90.00%
  ORDER BY    :  85.00%
  HAVING      :  92.50%
  KEYWORDS    :  95.00%
  Overall F1  :  88.41%
```

### 2. JSON Output (`eval_results_*.json`)

Comprehensive machine-readable evaluation results:

```json
{
  "experiment_config": {
    "model_name": "gpt-4o-mini",
    "strategy": "few-shot",
    "level": "std",
    "split": "dev",
    "num_samples": 10,
    "timestamp": "2025-07-20T07:09:08.123456",
    "schema_path": "dataset/ViText2SQL/std-level/tables.json"
  },
  "exact_match": {
    "em_accuracy": 0.75,
    "total_queries": 10,
    "exact_matches": 7,
    "match_indices": [0, 1, 3, 5, 6, 7, 9]
  },
  "component_f1": {
    "f1_scores": {
      "SELECT": 0.8889,
      "FROM": 1.0000,
      "WHERE": 0.6750,
      "GROUP BY": 0.9000,
      "ORDER BY": 0.8500,
      "HAVING": 0.9250,
      "KEYWORDS": 0.9500
    },
    "precision_scores": { ... },
    "recall_scores": { ... },
    "avg_f1": 0.8841
  },
  "difficulty_analysis": {
    "distribution": {
      "simple": {"count": 3, "percentage": 30.0},
      "moderate": {"count": 4, "percentage": 40.0},
      "complex": {"count": 2, "percentage": 20.0},
      "very_complex": {"count": 1, "percentage": 10.0}
    }
  },
  "error_analysis": {
    "syntax_errors": {"count": 1, "percentage": 10.0},
    "semantic_errors": {"count": 2, "percentage": 20.0},
    "column_selection_errors": {"count": 1, "percentage": 10.0}
  }
}
```

### 3. Text Report (`eval_report_*.txt`)

Human-readable detailed analysis:

```
================================================================================
📊 EVALUATION REPORT
================================================================================
🤖 Model: gpt-4o-mini
🎯 Strategy: FEW-SHOT
📊 Dataset: std-level, dev split
📅 Timestamp: 2025-07-20T07:09:08.123456
================================================================================
Total Samples: 10
Valid Results: 10
Exact Match Accuracy: 75.00%
Syntax Validity: 90.00%
Overall F1 Score: 88.41%

----------------------------------------
COMPONENT-WISE SCORES
----------------------------------------
Component       F1 Score   Precision    Recall
--------------------------------------------------
SELECT            88.89%      90.00%     87.50%
FROM             100.00%     100.00%    100.00%
WHERE             67.50%      70.00%     65.00%
GROUP BY          90.00%      92.00%     88.00%
ORDER BY          85.00%      86.00%     84.00%
HAVING            92.50%      94.00%     91.00%
KEYWORDS          95.00%      96.00%     94.00%

----------------------------------------
QUERY COMPLEXITY DISTRIBUTION
----------------------------------------
simple      :     3 queries (30.00%)
moderate    :     4 queries (40.00%)
complex     :     2 queries (20.00%)
very_complex:     1 queries (10.00%)

----------------------------------------
ERROR ANALYSIS
----------------------------------------
Syntax Error Rate: 10.00%
Semantic Error Rate: 20.00%
Total Queries with Errors: 3
```

### 4. Predictions Output (`predictions.json`)

Raw model predictions with metadata:

```json
{
  "predictions": [
    {
      "db_id": "university",
      "question": "Có bao nhiêu sinh viên trong trường?",
      "predicted": "SELECT COUNT(*) FROM students",
      "gold": "SELECT COUNT(*) FROM students"
    }
  ]
}
```

## Evaluation Best Practices

### 1. Experimental Setup
- Use consistent random seeds for reproducibility
- Report model temperature and sampling parameters
- Include dataset split information in results
- Document preprocessing steps

### 2. Metric Reporting
- Always report both EM accuracy and component F1 scores
- Include confidence intervals for statistical significance
- Provide error analysis for failure case understanding
- Report execution time and computational requirements

### 3. Comparison Guidelines
- Use identical evaluation settings across models
- Report on same dataset splits and sample sizes
- Include baseline comparisons
- Document any modifications to evaluation metrics

### 4. Statistical Analysis
- Perform significance testing for model comparisons
- Report standard deviations across multiple runs
- Use appropriate sample sizes for reliable estimates
- Consider stratified analysis by query complexity

## Implementation Details

### Normalization Algorithms
- **SQL Parsing**: Uses `sqlparse` library for robust SQL parsing
- **Alias Normalization**: Converts all table aliases to standard form (t1, t2, ...)
- **Unicode Handling**: Proper Vietnamese diacritic normalization
- **Whitespace Handling**: Consistent spacing and formatting

### Component Extraction
- **Regex-based Parsing**: Reliable extraction of SQL components
- **Schema-aware Analysis**: Uses database schema for validation
- **Error Handling**: Graceful handling of malformed queries
- **Alias Resolution**: Maps aliases back to original table names

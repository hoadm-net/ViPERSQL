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

## 📈 Output Format

### 1. Summary Report
```
============================================================
📊 EVALUATION SUMMARY
============================================================
Strategy: FEW-SHOT
Total samples: 100
Exact Match: 25.0%
Syntax Validity: 100.0%
Average Component F1: 0.0%

🔍 COMPONENT F1-SCORES:
----------------------------------------
  SELECT: 78.8%
  FROM: 79.6%
  WHERE: 83.3%
  GROUP BY: 90.6%
  ORDER BY: 86.7%
  HAVING: 89.6%
  KEYWORDS: 94.9%
```

### 2. Detailed Analysis
```
📝 Sample 1: assets_maintenance
Question: Những tài sản nào có 2 bộ phận và có ít hơn 2 nhật kí lỗi?
Predicted: SELECT t.id_tài_sản, t.chi_tiết_tài_sản FROM tài_sản t...
Gold:      SELECT t1.id_tài_sản, t1.chi_tiết_tài_sản FROM tài_sản AS t1...
📊 Component Analysis:
  ✅ SELECT: 100.0%
  ✅ FROM: 100.0%
  ✅ WHERE: 100.0%
  🟡 GROUP BY: 66.7%
  ✅ ORDER BY: 100.0%
  ❌ HAVING: 0.0%
  ✅ KEYWORDS: 82.4%
```

## 🛠️ Cấu hình

### 1. Model Configuration
```python
# mint/config.py
MODEL_CONFIG = {
    "model": "gpt-4.1-mini",
    "temperature": 0.0,
    "max_tokens": 2048
}
```

### 2. Evaluation Parameters
```python
# mint/metrics.py
class EvaluationMetrics:
    def __init__(self):
        self.normalize_operators = True
        self.normalize_quotes = True
        self.add_table_names = True
        self.remove_semicolons = True
```

## 🔧 Tùy chỉnh

### 1. Thêm normalization rule mới
```python
def custom_normalization(self, sql: str) -> str:
    # Thêm logic normalization tùy chỉnh
    return normalized_sql
```

### 2. Thêm scoring metric mới
```python
def custom_scoring(self, predicted: str, gold: str) -> float:
    # Thêm metric đánh giá tùy chỉnh
    return score
```

### 3. Tùy chỉnh component extraction
```python
def extract_custom_component(self, sql: str) -> set:
    # Trích xuất component tùy chỉnh
    return component_set
```

## 📁 File Structure

### Input Files
- `dataset/ViText2SQL/{level}/{split}.json`: Dữ liệu đánh giá
- `dataset/ViText2SQL/{level}/tables.json`: Schema database
- `templates/{strategy}_vietnamese_nl2sql.txt`: Template prompts

### Output Files
- `results/evaluation_{strategy}_{model}_{split}_{timestamp}.json`: Kết quả đánh giá
- `logs/`: Log files (nếu có)

## 🚀 Performance Tips

### 1. Batch Processing
- Sử dụng `--samples` lớn để đánh giá nhiều mẫu
- Hệ thống tự động xử lý batch để tối ưu performance

### 2. Caching
- Kết quả đánh giá được cache để tránh tính toán lại
- Schema được load một lần và reuse

### 3. Parallel Processing
- Có thể chạy nhiều evaluation jobs song song
- Mỗi job độc lập và thread-safe

## 🐛 Troubleshooting

### 1. Alias Mapping Issues
```python
# Debug alias extraction
print(f"Alias map: {alias_map}")
print(f"Normalized SQL: {normalized_sql}")
```

### 2. Component Extraction Issues
```python
# Debug component extraction
print(f"SELECT: {components['SELECT']}")
print(f"FROM: {components['FROM']}")
```

### 3. Scoring Issues
```python
# Debug scoring
print(f"Predicted set: {pred_set}")
print(f"Gold set: {gold_set}")
print(f"Intersection: {intersection}")
```

## 📚 References

- [SQL Normalization Techniques](https://example.com/sql-normalization)
- [Component-wise Evaluation](https://example.com/component-evaluation)
- [Alias Handling Best Practices](https://example.com/alias-handling)

## 🤝 Contributing

Để đóng góp vào hệ thống đánh giá:

1. Fork repository
2. Tạo feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

---

**ViPERSQL Evaluation System** - Hệ thống đánh giá Text-to-SQL tiếng Việt tiên tiến nhất! 🚀 